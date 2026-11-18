"""Generated pictures and the explainer page: fresh, self-contained, consistent with their sources."""
import copy
import json
import os
import re
import subprocess
import sys
import unittest

from helpers import ROOT

sys.path.insert(0, os.path.join(ROOT, "tools"))
import gen_diagrams  # noqa: E402
import gen_explainer  # noqa: E402


def tool(name, *args):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run([sys.executable, os.path.join("tools", name)] + list(args), cwd=ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)


def read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


class Diagrams(unittest.TestCase):
    def test_committed_files_are_fresh(self):
        r = tool("gen_diagrams.py", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_every_state_and_command_is_drawn(self):
        lc = json.loads(read("pmf/data/lifecycles.json"))
        for ent, spec in lc["entities"].items():
            svg = read("docs/diagrams/%s.svg" % ent)
            for state in spec["states"]:
                self.assertIn(">%s</text>" % state, svg, (ent, state))
            for t in spec["transitions"]:
                self.assertIn(">%s</text>" % t["command"].split(" ", 1)[1], svg, (ent, t["command"]))

    def test_every_guard_is_in_the_hover_text(self):
        lc = json.loads(read("pmf/data/lifecycles.json"))
        svg = read("docs/diagrams/issue.svg")
        for t in lc["entities"]["issue"]["transitions"]:
            for g in t["guards"]:
                self.assertIn(g, svg)

    def test_a_new_state_without_a_place_is_refused(self):
        lc = json.loads(read("pmf/data/lifecycles.json"))
        bad = copy.deepcopy(lc)
        bad["entities"]["issue"]["states"]["ESCALATED"] = {"meaning": "x"}
        with self.assertRaises(SystemExit) as cm:
            gen_diagrams.render(bad, "issue")
        self.assertIn("ESCALATED", str(cm.exception))

    def test_a_new_transition_without_a_route_is_refused(self):
        lc = json.loads(read("pmf/data/lifecycles.json"))
        bad = copy.deepcopy(lc)
        bad["entities"]["issue"]["transitions"].append({"from": "LOGGED", "to": "CLOSED", "command": "issue skip", "guards": []})
        with self.assertRaises(SystemExit):
            gen_diagrams.render(bad, "issue")

    def test_svg_is_valid_xml_and_ids_are_unique_per_page(self):
        import xml.dom.minidom
        for ent in ("issue", "risk", "change", "gate"):
            xml.dom.minidom.parseString(read("docs/diagrams/%s.svg" % ent))
        ids = re.findall(r'id="([^"]+)"', read("docs/diagrams/lifecycles.html"))
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_scripts_or_external_references(self):
        for name in ("issue.svg", "risk.svg", "change.svg", "gate.svg", "lifecycles.html"):
            t = read("docs/diagrams/" + name)
            self.assertNotRegex(t, r"(?i)<script")
            self.assertNotRegex(t.replace('xmlns="http://www.w3.org/2000/svg"', ""), r"(?i)https?://")


class Explainer(unittest.TestCase):
    def setUp(self):
        self.page = read("docs/explainer.html")

    def test_committed_page_is_fresh(self):
        r = tool("gen_explainer.py", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_self_contained(self):
        self.assertNotRegex(self.page, r"(?i)<script")
        self.assertNotRegex(self.page.replace('xmlns="http://www.w3.org/2000/svg"', ""), r"(?i)https?://")
        self.assertNotRegex(self.page, r"(?i)<(link|img|iframe|form|input|button)\b")
        self.assertNotRegex(self.page, r"(?i)\bon[a-z]+=")

    def test_nothing_personal_or_interview_related(self):
        for word in ("interview", "granola", "linkedin", "resume", "hiring manager", "projects\\"):
            self.assertNotIn(word, self.page.lower(), word)

    def test_relative_links_resolve(self):
        base = os.path.join(ROOT, "docs")
        ids = set(re.findall(r'id="([^"]+)"', self.page))
        for href in re.findall(r'href="([^"]+)"', self.page):
            if href.startswith("#"):
                self.assertIn(href[1:], ids, href)
                continue
            path = href.split("#")[0]
            self.assertTrue(os.path.exists(os.path.normpath(os.path.join(base, path))), href)

    def test_five_views_in_order(self):
        order = [self.page.index('id="%s"' % i) for i in ("shape", "asic", "issue", "plc", "health")]
        self.assertEqual(order, sorted(order))

    def test_gates_phases_and_numbers_come_from_the_profile(self):
        p = json.loads(read("profiles/silicon.json"))
        for g in p["gates"]:
            self.assertIn(gen_explainer.e(g["name"]), self.page)
        for ph in p["phases"]:
            self.assertIn(gen_explainer.e(ph["name"]), self.page)
        m = p["metrics"]
        self.assertIn("%s%% or more" % m["gate_on_time"]["green_min_pct"], self.page)
        self.assertIn("over %s%%" % m["escape_rate"]["amber_max_pct"], self.page)
        self.assertIn("%s to %s" % tuple(m["burn_ratio"]["green"]), self.page)

    def test_every_artifact_in_module_04_is_on_the_page(self):
        stages = gen_explainer.stages()
        self.assertEqual(len(stages), 5)
        for s in stages:
            self.assertGreaterEqual(len(s["artifacts"]), 5)
            for a in s["artifacts"]:
                self.assertIn(gen_explainer.e(a), self.page)

    def test_module_01_gates_and_phases_are_what_the_page_uses(self):
        m1 = read("framework/modules/01_lifecycle_and_governance.md")
        self.assertEqual(len(gen_explainer.md_table_after(m1, "## 1.2 The generic program lifecycle")), 8)
        self.assertEqual(len(gen_explainer.md_table_after(m1, "### Planned gates")), 7)

    def test_status_chips_have_icon_and_word(self):
        chips = re.findall(r'<span class="chip[^"]*st-\w+">(<svg.*?</svg>)<span>([A-Za-z ]+)</span></span>', self.page)
        self.assertEqual(len(chips), self.page.count('<span class="chip'))
        self.assertEqual(len(chips), 15)


if __name__ == "__main__":
    unittest.main()
