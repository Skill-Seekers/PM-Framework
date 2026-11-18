"""Mechanical lint of the plugin: the commands the skills tell Claude to run must parse against the real CLI, every file
they point at must exist, and every skill must carry its guardrails. This does not prove a skill behaves well in a live
session (nothing here can); it catches the drift that breaks one: a renamed flag, a moved file, a deleted guardrail."""
import contextlib
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
import zipfile

from helpers import ROOT
from pmf import __version__, cli
from pmf import profile as prof

SKILLS = os.path.join(ROOT, "skills")
EXPECTED = {"setup-program", "log-and-triage", "brief-and-report", "gate-review", "health-check"}
LC = prof.lifecycles()
COMMANDS = set(cli.build_parser(LC)._subparsers._group_actions[0].choices)
# Files a skill may name before they exist. S7 writes docs/ADAPTING.md and must then empty this set.
FORWARD = {"docs/ADAPTING.md"}
PREFIX = re.compile(r"^python3? <plugin root>/pmf\s+")


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def skill_files():
    for name in sorted(os.listdir(SKILLS)):
        d = os.path.join(SKILLS, name)
        if not os.path.isdir(d):
            continue
        for dp, _, fns in os.walk(d):
            for fn in sorted(fns):
                if fn.endswith(".md"):
                    yield name, os.path.join(dp, fn)


def command_spans(text):
    """Backtick spans and fenced lines that run the tool: 'python3 <plugin root>/pmf ...'."""
    spans = re.findall(r"`([^`\n]+)`", text)
    for block in re.findall(r"```[a-z]*\n(.*?)```", text, re.S):
        spans += [l for l in block.split("\n") if l.strip()]
    for s in spans:
        s = s.strip()
        if PREFIX.match(s):
            yield PREFIX.sub("", s)


def normalise(s):
    return re.sub(r"<[^<>]*>", "x", s)


class SkillLint(unittest.TestCase):
    def test_exactly_the_five_skills_with_frontmatter(self):
        have = {d for d in os.listdir(SKILLS) if os.path.isdir(os.path.join(SKILLS, d))}
        self.assertEqual(have, EXPECTED)
        for n in EXPECTED:
            t = read(os.path.join(SKILLS, n, "SKILL.md"))
            m = re.match(r"---\nname: (.+)\ndescription: (.+)\n---\n", t)
            self.assertTrue(m, n)
            self.assertEqual(m.group(1), n)
            self.assertLessEqual(len(m.group(2)), 1024, n)
            self.assertNotIn("<", m.group(2), n)
            self.assertNotIn(">", m.group(2), n)

    def test_commands_in_skills_parse_against_the_cli(self):
        parser = cli.build_parser(LC)
        checked = 0
        for name, path in skill_files():
            for span in command_spans(read(path)):
                argv = shlex.split(normalise(span))
                if argv[0] not in COMMANDS:
                    continue            # '<command>' placeholders
                err = io.StringIO()
                with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                    try:
                        parser.parse_args(argv)
                    except SystemExit:
                        msg = err.getvalue()
                        # missing required arguments are fine in prose; unknown flags and verbs are not
                        if "unrecognized arguments" in msg or "invalid choice" in msg or "ambiguous option" in msg:
                            self.fail('%s: "%s" -> %s' % (os.path.relpath(path, ROOT), span, msg.strip().splitlines()[-1]))
                checked += 1
        self.assertGreater(checked, 20, "the lint found too few commands to be meaningful")

    def test_every_command_family_is_covered_by_a_skill(self):
        used = set()
        for _, path in skill_files():
            for span in command_spans(read(path)):
                used.add(span.split()[0])
        self.assertTrue({"init", "issue", "risk", "gate", "brief", "report", "raid", "check", "health", "dashboard", "show"} <= used,
                        "unused: %s" % sorted({"init", "issue", "risk", "gate", "brief", "report", "raid", "check", "health", "dashboard", "show"} - used))

    def test_every_referenced_file_exists(self):
        n = 0
        for name, path in skill_files():
            text = read(path)
            for ref in re.findall(r"`((?:docs|prompts|templates|framework|profiles)/[A-Za-z0-9_./-]+)(?:#[A-Za-z0-9_-]+)?`", text):
                if ref not in FORWARD:
                    self.assertTrue(os.path.exists(os.path.join(ROOT, ref)), "%s mentions %s" % (os.path.relpath(path, ROOT), ref))
                n += 1
            for ref in re.findall(r"`(profile\.json|pmf\.config\.json|events\.csv)`", text):
                pass
        self.assertGreater(n, 15)

    def test_plugin_root_sentence_is_in_every_skill(self):
        for n in EXPECTED:
            t = read(os.path.join(SKILLS, n, "SKILL.md"))
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", t, n)
            self.assertIn("two levels above this skill's base directory", t, n)

    def test_guardrails_are_present(self):
        must = {"setup-program": ["Never invent a date, name, amount or owner", "Never edit `events.csv`", "refuses to overwrite"],
                "log-and-triage": ["AI drafts, the PM decides", "Never invent a cause, number, owner or date", "[needs number]",
                                   "Never edit a CSV by hand", "One owner per item"],
                "brief-and-report": ["Never send anything", "Never overwrite a draft", "--force", "Do not soften or round"],
                "gate-review": ["never makes it", "signed decision records", "Do not edit `criteria_met`", "--dry-run"],
                "health-check": ["Never change a threshold", "not rated", "never an average"]}
        for skill, phrases in must.items():
            t = read(os.path.join(SKILLS, skill, "SKILL.md"))
            for p in phrases:
                self.assertIn(p, t, "%s lost its guardrail text: %s" % (skill, p))

    def test_skills_do_not_tell_claude_to_bypass_a_guard(self):
        bad = re.compile(r"(?i)(skip|bypass|work around|ignore)\s+(the\s+)?(guard|refusal|check)")
        for name, path in skill_files():
            for line in read(path).splitlines():
                if bad.search(line) and not re.search(r"(?i)\b(never|not|do not|don't)\b", line):
                    self.fail("%s: %s" % (os.path.relpath(path, ROOT), line))

    def test_no_interview_framing_or_private_words_in_skills(self):
        for name, path in skill_files():
            t = read(path).lower()
            for w in ("interview", "granola", "linkedin", "resume", "hiring manager", "projects\\"):
                self.assertNotIn(w, t, "%s contains %r" % (os.path.relpath(path, ROOT), w))


class Plugin(unittest.TestCase):
    def test_manifest(self):
        m = json.loads(read(os.path.join(ROOT, ".claude-plugin", "plugin.json")))
        self.assertEqual(m["name"], "pm-framework")
        self.assertEqual(m["version"], __version__)
        self.assertEqual(m["license"], "MIT")
        mk = json.loads(read(os.path.join(ROOT, ".claude-plugin", "marketplace.json")))
        self.assertEqual(mk["owner"]["name"], "Skill-Seekers")
        self.assertEqual(mk["plugins"][0]["name"], m["name"])
        self.assertEqual(mk["plugins"][0]["source"], "./")

    def test_package_builds_with_what_the_skills_need(self):
        sys.path.insert(0, os.path.join(ROOT, "tools"))
        try:
            import build_plugin
        finally:
            sys.path.pop(0)
        with tempfile.TemporaryDirectory() as d:
            target, names = build_plugin.build(d)
            self.assertTrue(target.endswith("pm-framework-%s.plugin" % __version__))
            for n in build_plugin.REQUIRED:
                self.assertIn(n, names)
            for n in names:
                self.assertFalse(n.startswith(("tests/", "tools/", "_private/", "dist/")), n)
                self.assertNotIn("__pycache__", n)
                self.assertFalse(n.endswith((".pyc", ".pyo")), n)
            with zipfile.ZipFile(target) as z:
                self.assertIsNone(z.testzip())
                z.extractall(os.path.join(d, "x"))
            # the packaged copy must run the way the skills say: python3 <plugin root>/pmf <command>
            root = os.path.join(d, "x")
            env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
            r = subprocess.run([sys.executable, os.path.join(root, "pmf"), "--version"], cwd=d, env=env,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "pmf " + __version__)
            ws = os.path.join(d, "prog")
            r = subprocess.run([sys.executable, os.path.join(root, "pmf"), "init", ws, "--program", "Demo", "--profile", "software"],
                               cwd=d, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            env["PMF_WORKSPACE"] = ws
            for cmd in (["check"], ["health"], ["dashboard", "--stdout"]):
                r = subprocess.run([sys.executable, os.path.join(root, "pmf")] + cmd, cwd=ws, env=env,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                self.assertIn(r.returncode, (0, 1), "%s: %s%s" % (cmd, r.stdout, r.stderr))


if __name__ == "__main__":
    unittest.main()
