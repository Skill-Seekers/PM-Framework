"""Repository-level checks: syntax floor, profiles, docs vs code, every guard exercised."""
import ast
import glob
import json
import os
import subprocess
import sys
import unittest

from helpers import ROOT

from pmf import profile as prof
from pmf.guards import GUARDS
from pmf.schemas import SCHEMAS


def py_files():
    out = []
    for d in ("pmf", "tools", "tests", "examples"):
        for dp, _, fs in os.walk(os.path.join(ROOT, d)):
            out += [os.path.join(dp, f) for f in fs if f.endswith(".py")]
    return sorted(out)


class Python38(unittest.TestCase):
    def test_every_file_parses_as_python_3_8(self):
        files = py_files()
        self.assertGreater(len(files), 10)
        for p in files:
            with open(p, encoding="utf-8") as f:
                src = f.read()
            try:
                ast.parse(src, filename=p, feature_version=(3, 8))
            except SyntaxError as e:
                self.fail("%s is not Python 3.8 syntax: %s" % (os.path.relpath(p, ROOT), e))

    def test_standard_library_only(self):
        std = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else None
        local = {"pmf", "helpers", "test_consistency", "gen_diagrams", "gen_explainer", "build_plugin"}
        for p in py_files():
            with open(p, encoding="utf-8") as f:
                tree = ast.parse(f.read())
            for n in ast.walk(tree):
                mods = []
                if isinstance(n, ast.Import):
                    mods = [a.name.split(".")[0] for a in n.names]
                elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                    mods = [n.module.split(".")[0]]
                for m in mods:
                    if std is not None and m not in std and m not in local and not m.startswith("test_"):
                        self.fail("%s imports non-stdlib module %s" % (os.path.relpath(p, ROOT), m))


class Profiles(unittest.TestCase):
    def test_shipped_profiles_validate(self):
        names = prof.shipped_profiles()
        self.assertEqual(names, ["silicon", "software"])
        for n in names:
            p = prof.load_json(prof.resolve_profile_path(n), n)
            prof.validate_profile(p, n)
            for ph in p["phases"]:
                self.assertEqual(sorted(ph["raci"]), sorted(x["id"] for x in p["parties"]), "%s %s" % (n, ph["id"]))
            for lv in p["severity"]["levels"]:
                a = lv.get("aging_days")
                if a:
                    self.assertLess(a["green_max"], a["amber_max"])
            bands = sorted((b["min"], b["max"]) for b in p["risk"]["bands"])
            top = p["risk"]["scale"]["max"] ** 2
            self.assertEqual(bands[0][0], 1)
            self.assertEqual(bands[-1][1], top)
            for (a, b), (c, d) in zip(bands, bands[1:]):
                self.assertEqual(b + 1, c, "risk bands in %s leave a gap or overlap" % n)

    def test_bad_profile_rejected(self):
        from pmf.util import PmfError
        p = prof.load_json(prof.resolve_profile_path("silicon"), "silicon")
        p["gates"][0]["phase"] = "nope"
        with self.assertRaises(PmfError):
            prof.validate_profile(p)
        p = prof.load_json(prof.resolve_profile_path("silicon"), "silicon")
        del p["metrics"]
        with self.assertRaises(PmfError):
            prof.validate_profile(p)

    def test_tier_rule_takes_the_higher_of_cost_and_schedule(self):
        P = prof.Profile(prof.load_json(prof.resolve_profile_path("silicon"), "s"))
        for cost, days, want in ((0, 0, "small"), (2500, 1, "small"), (2501, 1, "medium"), (0, 2, "medium"),
                                 (25000, 5, "medium"), (25001, 0, "large"), (0, 6, "large"), (100000, 20, "large"),
                                 (100001, 0, "major"), (0, 21, "major"), (-5000, 0, "medium")):
            self.assertEqual(P.tier_for(cost, days)["id"], want, (cost, days))


class Guards(unittest.TestCase):
    def test_every_guard_is_exercised_by_a_refusal_test(self):
        text = ""
        for p in glob.glob(os.path.join(ROOT, "tests", "test_*.py")):
            if p.endswith("test_consistency.py"):
                continue
            with open(p, encoding="utf-8") as f:
                text += f.read()
        missing = [g for g in GUARDS if '"%s"' % g not in text]
        self.assertEqual(missing, [], "no test expects a refusal from: %s" % ", ".join(missing))

    def test_guards_match_lifecycle_file(self):
        lc = prof.lifecycles()
        used = {g for e in lc["entities"].values() for t in e["transitions"] for g in t["guards"]}
        self.assertEqual(used, set(GUARDS))
        self.assertEqual(set(lc["guards"]), set(GUARDS))


class Docs(unittest.TestCase):
    def test_every_schema_column_is_documented(self):
        with open(os.path.join(ROOT, "docs", "DATA_SCHEMAS.md"), encoding="utf-8") as f:
            doc = f.read()
        missing = []
        for name, s in SCHEMAS.items():
            for c in s["columns"]:
                if "`%s`" % c not in doc:
                    missing.append("%s.%s" % (name, c))
        self.assertEqual(missing, [])

    def test_repo_checkers_pass(self):
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        cmds = [["tools/check_spec.py"], ["tools/gen_lifecycles.py", "--check"], ["tools/gen_templates.py", "--check"],
                ["tools/check_content.py"],
                ["tools/check_links.py", "--allow-missing", "docs/ADAPTING.md,docs/LIMITS.md,README.md,examples/meridian"]]
        for c in cmds:
            r = subprocess.run([sys.executable] + c, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(r.returncode, 0, "%s\n%s%s" % (" ".join(c), r.stdout, r.stderr))


if __name__ == "__main__":
    unittest.main()
