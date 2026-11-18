"""Shared test fixtures: a fresh workspace per test, in-process CLI runner, record writers."""
import contextlib
import io
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.dont_write_bytecode = True

from pmf import cli  # noqa: E402
from pmf.util import read_csv  # noqa: E402

NOW = "2026-03-02T09:00:00Z"


def run(argv):
    """Run the CLI in-process. Returns (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            rc = cli.main(list(argv))
        except SystemExit as e:           # argparse errors and --help
            rc = e.code if isinstance(e.code, int) else 2
    return rc, out.getvalue(), err.getvalue()


DR_TEMPLATE = """# {ref}: test record
Issue: {issue}
Date: 2026-03-02
Customer visible: {cv}

## Options
| Option | Description | Schedule (days) | Cost | Risk |
|---|---|---|---|---|
| A | Fix now | {a_s} | {a_c} | Medium |
| B | Waive with conditions | 0 | 0 | High |
| C | Defer to next revision | 0 | 0 | Medium |

Recommendation: {reco}

## Decision
Chosen: {chosen}
Decided by: {by}
Decided on: {on}
Signed: {signed}
Customer acceptance: {acc}
Conditions: n/a
"""


class WS(unittest.TestCase):
    PROFILE = "silicon"
    NOW = NOW

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="pmft-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self._env = {k: os.environ.get(k) for k in ("PMF_FAKE_NOW", "PMF_WORKSPACE", "PMF_ACTOR")}
        self.addCleanup(self._restore)
        os.environ["PMF_FAKE_NOW"] = self.NOW
        os.environ["PMF_ACTOR"] = "tester"
        self.dir = os.path.join(self.tmp, "prog")
        rc, out, err = run(["init", self.dir, "--program", "Test Program", "--profile", self.PROFILE,
                            "--baseline-start", "2026-01-05", "--baseline-end", "2026-12-18",
                            "--baseline-budget", "500000"])
        self.assertEqual(rc, 0, err)
        os.environ["PMF_WORKSPACE"] = self.dir

    def _restore(self):
        for k, v in self._env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # ---- running ----
    def pmf(self, *argv):
        return run(argv)

    def ok(self, *argv):
        rc, out, err = run(argv)
        self.assertEqual(rc, 0, "expected success for %s\nstdout: %s\nstderr: %s" % (" ".join(argv), out, err))
        return out

    def refused(self, guard, *argv):
        """Expect exit 1 and the named guard in the refusal."""
        rc, out, err = run(argv)
        self.assertEqual(rc, 1, "expected refusal for %s\nstdout: %s\nstderr: %s" % (" ".join(argv), out, err))
        if guard:
            self.assertIn("[%s]" % guard, err, "guard %s not named in: %s" % (guard, err))
        return err

    def could_not_run(self, *argv):
        rc, out, err = run(argv)
        self.assertEqual(rc, 2, "expected exit 2 for %s\nstdout: %s\nstderr: %s" % (" ".join(argv), out, err))
        return err

    # ---- files ----
    def path(self, *p):
        return os.path.join(self.dir, *p)

    def rows(self, name):
        if not name.endswith(".csv"):
            name += ".csv"
        return read_csv(self.path(name))[1]

    def row(self, name, ident):
        for r in self.rows(name):
            if r.get("id") == ident or r.get("phase") == ident:
                return r
        raise AssertionError("%s not in %s" % (ident, name))

    def state(self, name, ident):
        return self.row(name, ident)["state"]

    def snapshot(self):
        """Bytes of every file in the workspace, to prove a refused command changed nothing."""
        snap = {}
        for dp, _, fs in os.walk(self.dir):
            for f in fs:
                p = os.path.join(dp, f)
                with open(p, "rb") as fh:
                    snap[os.path.relpath(p, self.dir)] = fh.read()
        return snap

    def write(self, rel, text):
        p = self.path(rel)
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def read(self, rel):
        with io.open(self.path(rel), encoding="utf-8") as f:
            return f.read()

    def dr(self, ref="DR-001", issue="I-001", cv="no", a_s="5", a_c="10000",
           reco="A - the fix is cheap", chosen="[A|B|C]", by="[name]", on="[YYYY-MM-DD]", signed="no", acc="n/a"):
        self.write("decisions/%s.md" % ref, DR_TEMPLATE.format(
            ref=ref, issue=issue, cv=cv, a_s=a_s, a_c=a_c, reco=reco, chosen=chosen, by=by, on=on, signed=signed, acc=acc))

    def decide_dr(self, ref="DR-001", chosen="A", by="Pat Kim", on="2026-03-02", signed="no", acc="n/a", **kw):
        self.dr(ref=ref, chosen=chosen, by=by, on=on, signed=signed, acc=acc, **kw)

    # ---- drivers ----
    def new_issue(self, sev=2, owner="Sam Lee", title="Lab supply late", phase="design", ident=None):
        args = ["issue", "add", "--title", title, "--description", "Boards delayed", "--phase", phase]
        if ident:
            args += ["--id", ident]
        self.ok(*args)
        iid = ident or self.rows("issues")[-1]["id"]
        self.ok("issue", "log", iid, "--owner", owner, "--severity", str(sev))
        return iid

    def issue_to_triaged(self, sev=2, ref="DR-001", **kw):
        iid = self.new_issue(sev=sev)
        self.dr(ref=ref, issue=iid, **kw)
        self.ok("issue", "triage", iid, "--decision-ref", ref)
        return iid


from pmf.workspace import Workspace  # noqa: E402
from pmf import metrics  # noqa: E402


class WSData(WS):
    """Adds direct register editing (for metric and check fixtures) on top of the CLI helpers."""

    def edit(self, name, ident, **fields):
        ws = Workspace(self.dir)
        rows = ws.load(name)
        key = "id"
        for r in rows:
            if r.get(key) == ident:
                r.update({k: str(v) for k, v in fields.items()})
                break
        else:
            raise AssertionError("%s not in %s" % (ident, name))
        ws.save(name, rows)

    def add_row(self, register, **fields):
        from pmf.schemas import SCHEMAS
        ws = Workspace(self.dir)
        rows = ws.load(register)
        row = {c: "" for c in SCHEMAS[register]["columns"]}
        row.update({k: str(v) for k, v in fields.items()})
        rows.append(row)
        ws.save(register, rows)

    def health(self, report_date=None):
        ws = Workspace(self.dir, report_date=report_date)
        res = metrics.compute(ws)
        return {m["id"]: m for m in res["metrics"]}, res["rollup"]
