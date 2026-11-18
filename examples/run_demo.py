#!/usr/bin/env python3
"""Rebuild the Meridian example from nothing by driving the real `pmf` command line.

Meridian is a FICTIONAL program. Every name, number and date below is made up.
It writes two folders under --out (default: examples/meridian):

  workspace/    the program as it stands on 2026-06-26 (registers, records, reports)
  walkthrough/  the transcript of the Sev 1 story and a short index

Nothing is hand-written in those folders: each file is either a `pmf` result or a document the
script writes where a person would (and says so in the transcript). Re-running gives identical output.

  python3 examples/run_demo.py             rebuild examples/meridian
  python3 examples/run_demo.py --check     rebuild in a temp folder and compare; exit 1 on any difference

Standard library only (Python 3.8+).
"""
import contextlib
import difflib
import io
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.dont_write_bytecode = True

from pmf import cli  # noqa: E402
from pmf.util import read_csv, write_csv  # noqa: E402
from pmf.schemas import SCHEMAS  # noqa: E402

PM = "Avery Chen"
DESIGN = "Jordan Patel"
VERIF = "Sam Okafor"
SPONSOR = "Riley Morgan"
CUSTOMER = "Casey Nguyen"

BASELINE = {  # gate -> (baseline date, planned date)
    "G1": "2026-01-30", "G2": "2026-02-27", "G3": "2026-03-20", "G4": "2026-06-12", "G5": "2026-08-07",
    "G6": "2026-09-04", "G7": "2026-10-16", "G8": "2026-12-04", "G9": "2026-12-18",
}
SLIPPED = {"G4": "2026-06-26", "G5": "2026-08-21", "G6": "2026-09-18", "G7": "2026-10-30", "G8": "2026-12-18", "G9": "2027-01-01"}


class Demo(object):
    def __init__(self, out):
        self.out = out
        self.ws = os.path.join(out, "workspace")
        self.md = []
        self.step_no = 0
        self.last = ""
        self.quiet_depth = 0
        self.quiet_count = 0

    # ------------------------------------------------------------ transcript helpers
    def say(self, text=""):
        if self.quiet_depth == 0:
            self.md.append(text)

    def quiet_enter(self):
        """Run the following steps for real but leave them out of the transcript until quiet_exit()."""
        self.quiet_mark = self.step_no
        self.quiet_depth += 1

    def quiet_exit(self):
        """Leave quiet mode. Returns how many steps ran quietly; the visible step numbering is not advanced."""
        self.quiet_depth -= 1
        n = self.step_no - self.quiet_mark
        self.step_no = self.quiet_mark
        self.quiet_count += n
        return n

    def chapter(self, title, intro=None):
        self.say("")
        self.say("## %s" % title)
        if intro:
            self.say("")
            self.say(intro)

    @staticmethod
    def _q(a):
        return '"%s"' % a if (" " in a or ";" in a or a == "") else a

    def clock(self, when):
        date, hhmm = (when.split(" ") + ["09:00"])[:2]
        if when < self.last:
            raise SystemExit("walkthrough steps are out of chronological order: %s comes after %s" % (when, self.last))
        self.last = when
        os.environ["PMF_FAKE_NOW"] = "%sT%s:00Z" % (date, hhmm)

    def run(self, when, who, args, expect=0, why=None):
        """Run one pmf command as `who` at `when`; fail loudly if the exit code is not what the story expects."""
        self.clock(when)
        args = list(args)
        if args[0] not in ("init", "lifecycles"):
            args += ["--actor", who] if args[0] in ("issue", "risk", "change", "gate") else []
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = cli.main(args)
        if rc != expect:
            raise SystemExit("walkthrough step failed: pmf %s\nexit %s, expected %s\n%s%s" % (" ".join(args), rc, expect, out.getvalue(), err.getvalue()))
        text = (out.getvalue() + err.getvalue()).replace(self.ws, "meridian/workspace")
        self.step_no += 1
        shown = [a.replace(self.ws, "meridian/workspace") for a in args]
        # keep the transcript tidy: --actor is shown as the heading, not repeated on every line
        if "--actor" in shown:
            i = shown.index("--actor")
            del shown[i:i + 2]
        self.say("")
        self.say("**%d. %s, %s%s**" % (self.step_no, when, who, (" - " + why) if why else ""))
        self.say("")
        self.say("```console")
        self.say("$ pmf " + " ".join(self._q(a) for a in shown))
        for line in text.rstrip("\n").splitlines():
            self.say(line)
        self.say("```")
        if expect == 1:
            self.say("")
            self.say("Exit code 1: refused. Nothing was written.")
        return text

    def doc(self, when, who, rel, text, why):
        """A person writes a document. The tool does not generate it; the transcript shows what was written."""
        self.clock(when)
        p = os.path.join(self.ws, *rel.split("/"))
        before = None
        if os.path.exists(p):
            with io.open(p, encoding="utf-8") as f:
                before = f.read()
        if not os.path.isdir(os.path.dirname(p)):
            os.makedirs(os.path.dirname(p))
        with io.open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        self.step_no += 1
        self.say("")
        if before is None:
            self.say("**%d. %s, %s - writes `%s`** (%s; not a pmf command)" % (self.step_no, when, who, rel, why))
            self.say("")
            self.say("```text")
            self.say(text.rstrip("\n"))
            self.say("```")
        else:
            self.say("**%d. %s, %s - updates `%s`** (%s; not a pmf command). What changed:" % (self.step_no, when, who, rel, why))
            self.say("")
            self.say("```diff")
            for line in difflib.unified_diff(before.splitlines(), text.splitlines(), lineterm="", n=0):
                if line.startswith(("---", "+++", "@@")):
                    continue
                self.say(line)
            self.say("```")

    def edit_csv(self, when, who, name, fn, summary):
        self.clock(when)
        reg = [k for k, v in SCHEMAS.items() if v["file"] == name][0]
        path = os.path.join(self.ws, name)
        header, rows = read_csv(path)
        before = [dict(r) for r in rows]
        fn(rows)
        write_csv(path, SCHEMAS[reg]["columns"], rows)
        self.step_no += 1
        self.say("")
        self.say("**%d. %s, %s - edits `%s`** (%s; the CSV is the edit surface, not a pmf command)" % (self.step_no, when, who, name, summary))
        key = SCHEMAS[reg]["key"] or "phase"
        changes = []
        for i, r in enumerate(rows):
            if i >= len(before):
                changes.append("+ row %s" % (r.get(key) or r.get("resource") or i + 1))
                continue
            for c in SCHEMAS[reg]["columns"]:
                if r.get(c, "") != before[i].get(c, ""):
                    changes.append("%s: %s  %r -> %r" % (r.get(key, i + 1), c, before[i].get(c, ""), r.get(c, "")))
        if changes and len(changes) <= 14:
            self.say("")
            self.say("```text")
            for c in changes:
                self.say(c)
            self.say("```")

    def read(self, rel):
        with io.open(os.path.join(self.ws, *rel.split("/")), encoding="utf-8") as f:
            return f.read()

    def show_file(self, rel, caption):
        self.say("")
        self.say("%s `%s`:" % (caption, rel))
        self.say("")
        self.say("```text")
        self.say(self.read(rel).rstrip("\n"))
        self.say("```")

    # ------------------------------------------------------------ story pieces
    def setup(self):
        self.say("# Meridian walkthrough: a Sev 1 from detection to retrospective")
        self.say("")
        self.say("*Meridian is a fictional program: every person, company, number and date here is made up. "
                 "This transcript is generated by `examples/run_demo.py`, which drives the real `pmf` command line. "
                 "Each command's output is exactly what the tool printed. A refusal shows the guard that said no.*")
        self.say("")
        self.say("**Program.** Meridian-1, a fictional AI accelerator SoC for a fictional customer, Northwind Systems. "
                 "Profile: `silicon` (9 phases, gates G1 to G9). Baseline 2026-01-05 to 2026-12-18, baseline budget 2,400,000.")
        self.say("")
        self.say("| Role | Name (fictional) |")
        self.say("|---|---|")
        for r, n in (("Program manager", PM), ("Design lead", DESIGN), ("Verification lead", VERIF), ("Sponsor", SPONSOR), ("Customer lead", CUSTOMER)):
            self.say("| %s | %s |" % (r, n))
        self.say("")
        self.say("The Sev 1 is **I-007**; reports are drafted on Fridays. Chapters: 1 Setup and history (with a customer-visible deferral, I-004), "
                 "2 Detect and log, 3 Triage, 4 Decide and change control, 5 The gate guard, 6 Resolve and close, 7 Risk review before the gate, "
                 "8 Gate G4, 9 A new Sev 2 and where things stand, 10 Event trail.")
        self.chapter("1. Setup and history",
                     "The program starts on 2026-01-05. Gates G1 to G3 pass on time. The history below is quick because it is not the point.")
        self.run("2026-01-05 09:00", PM, ["init", self.ws, "--program", "Meridian-1 AI Accelerator", "--profile", "silicon",
                                          "--baseline-start", "2026-01-05", "--baseline-end", "2026-12-18", "--baseline-budget", "2400000"],
                 why="create the workspace")
        os.environ["PMF_WORKSPACE"] = self.ws

        def gates(rows):
            for r in rows:
                r["baseline_date"] = BASELINE[r["id"]]
                r["planned_date"] = BASELINE[r["id"]]
        self.edit_csv("2026-01-05 09:30", PM, "gates.csv", gates, "baseline_date and planned_date for G1 to G9 from the approved plan")

    def small(self, iid, title, phase, owner, sev, d, dr, lesson, chosen="A", signed="no", cv="no", acc="n/a", cond="n/a"):
        """A compact closed issue. d = dict of dates: add, triage, decide, resolve, close."""
        self.run(d["add"] + " 10:00", PM, ["issue", "add", "--title", title, "--description", title + ".", "--phase", phase])
        self.run(d["add"] + " 10:30", PM, ["issue", "log", iid, "--owner", owner, "--severity", str(sev)])
        base = dict(ref=dr, title=title, issue=iid, date=d["triage"], cv=cv, a_s="2", a_c="1500", reco="A - cheapest and quickest.")
        self.doc(d["triage"] + " 09:00", PM, "decisions/%s.md" % dr, DR_TEMPLATE % dict(base, chosen="[A|B|C]", by="[name]", on="[YYYY-MM-DD]", signed="no", acc="n/a", cond="n/a"),
                 "decision record with three options")
        self.run(d["triage"] + " 09:10", PM, ["issue", "triage", iid, "--decision-ref", dr])
        self.doc(d["decide"] + " 09:00", PM, "decisions/%s.md" % dr, DR_TEMPLATE % dict(base, chosen=chosen, by=owner, on=d["decide"], signed=signed, acc=acc, cond=cond),
                 "decision recorded")
        self.run(d["decide"] + " 09:10", PM, ["issue", "decide", iid])
        self.run(d["resolve"] + " 15:00", PM, ["issue", "resolve", iid, "--verification-ref", "check run " + iid])
        self.run(d["close"] + " 11:00", PM, ["issue", "close", iid, "--lesson", lesson])

    def history(self):
        def gate(gid, review, go, crit):
            self.run(review + " 14:00", PM, ["gate", "review", gid], why="gate review meeting")
            self.run(go + " 16:00", PM, ["gate", "go", gid, "--criteria-met", crit], why="all exit criteria met")

        self.quiet_enter()
        gate("G1", "2026-01-28", "2026-01-30", "1;2;3")
        self.small("I-001", "Interface spec has two conflicting clock tables", "requirements", CUSTOMER, 3,
                   dict(add="2026-02-10", triage="2026-02-11", decide="2026-02-12", resolve="2026-02-18", close="2026-02-20"), "DR-001",
                   "Reconcile the customer spec against our own before the requirements review.")
        gate("G2", "2026-02-25", "2026-02-27", "1;2;3")

        for t, ph in (("Power-delivery margin is thin at peak load", "design"), ("Foundry mask slot slips one cycle", "tapeout"),
                      ("Customer firmware lands late", "bringup"), ("Single source for package substrate", "tapeout")):
            args = ["risk", "add", "--title", t, "--phase", ph]
            if t.startswith("Power"):
                args += ["--description", "Peak current estimate has little margin against the droop limit."]
            self.run("2026-03-05 10:00", PM, args, why="identify a risk" if t.startswith("Power") else None)
        self.run("2026-03-06 10:00", PM, ["risk", "assess", "R-001", "--owner", DESIGN, "--probability", "4", "--impact", "3"], why="12 = High, reviewed every 14 days")
        self.run("2026-03-06 10:10", PM, ["risk", "mitigate", "R-001", "--mitigation", "Add on-die droop monitors; run PDN analysis at every floorplan drop."])
        self.run("2026-03-06 10:20", PM, ["risk", "assess", "R-002", "--owner", VERIF, "--probability", "3", "--impact", "4"])
        self.run("2026-03-06 10:30", PM, ["risk", "mitigate", "R-002", "--mitigation", "Reserve a second slot; confirm the slot in writing at G5."])
        self.run("2026-03-06 10:40", PM, ["risk", "assess", "R-003", "--owner", PM, "--probability", "3", "--impact", "3"])
        self.run("2026-03-06 10:50", PM, ["risk", "mitigate", "R-003", "--mitigation", "Agree an interim firmware drop date with the customer; weekly check."])
        self.run("2026-03-06 11:00", PM, ["risk", "assess", "R-004", "--owner", VERIF, "--probability", "2", "--impact", "2"])
        self.run("2026-03-06 11:10", PM, ["risk", "accept", "R-004", "--accepted-by", SPONSOR], why="Medium risk, accepted by name")

        for name, rows_fn, summary in (
            ("assumptions.csv", lambda rows: rows.extend([
                dict(id="A-001", title="Foundry PDK 1.2 arrives by 2026-02-15", description="", owner=PM, status="validated", validate_by="2026-02-15", linked_risk=""),
                dict(id="A-002", title="Customer firmware team is ready before tape-out", description="", owner=PM, status="untested", validate_by="2026-08-01", linked_risk="R-003"),
            ]), "two assumptions"),
            ("dependencies.csv", lambda rows: rows.extend([
                dict(id="D-001", title="Foundry PDK 1.2", description="", owner=DESIGN, provider="Fabrica Foundry", needed_by="2026-02-15", status="delivered", linked_issue=""),
                dict(id="D-002", title="Customer firmware drop", description="", owner=PM, provider="Northwind Systems", needed_by="2026-09-01", status="open", linked_issue=""),
            ]), "two dependencies"),
            ("vendors.csv", lambda rows: rows.extend([
                dict(vendor="Fabrica Foundry", committed="900000", milestone="Mask set delivered", paid_on_delivery="yes", status="on track"),
                dict(vendor="Packwell Assembly", committed="150000", milestone="Substrate lot received", paid_on_delivery="no", status="on track"),
            ]), "two vendors; Packwell is paid before delivery"),
            ("contention.csv", lambda rows: rows.extend([
                dict(resource="Emulation cluster", period="2026-06", program="Meridian", demand="6", capacity="10", owner=VERIF, note=""),
                dict(resource="Emulation cluster", period="2026-06", program="Atlas", demand="5", capacity="10", owner=VERIF, note="another fictional program"),
            ]), "shared emulation cluster: 11 requested of 10"),
        ):
            self.edit_csv("2026-03-07 09:00", PM, name, rows_fn, summary)
        
        self.small("I-002", "Tool license count is below the plan", "planning", PM, 3,
                   dict(add="2026-03-09", triage="2026-03-10", decide="2026-03-11", resolve="2026-03-13", close="2026-03-16"), "DR-002",
                   "Count licenses per phase at planning time, not per program.", chosen="B", signed="yes")
        gate("G3", "2026-03-17", "2026-03-20", "1;2;3;4")
        self.small("I-003", "IO ring is one pad short", "design", DESIGN, 3,
                   dict(add="2026-04-14", triage="2026-04-15", decide="2026-04-16", resolve="2026-04-22", close="2026-04-24"), "DR-003",
                   "Run the pad-count check as part of floorplan review.")
        n = self.quiet_exit()
        self.say("")
        self.say("History run quietly so the Sev 1 stays in focus (%d real `pmf` commands and file edits, all in [events.csv](../workspace/events.csv)):" % n)
        self.say("")
        self.say("| Dates | What happened |")
        self.say("|---|---|")
        self.say("| Jan 28 to Mar 20 | Gates G1, G2 and G3 reviewed and passed on their baseline dates (`gate review`, `gate go`) |")
        self.say("| Feb 10 to Apr 24 | Three small Sev 3 issues taken through every state to CLOSED: I-001 (requirements), I-002 (planning, waived with a signed record), I-003 (design) |")
        self.say("| Mar 5 to Mar 6 | Four risks identified, assessed and mitigated or accepted: R-001 power-delivery margin, R-002 foundry slot, R-003 customer firmware, R-004 single-source substrate |")
        self.say("| Mar 7 | Assumptions, dependencies, vendors and a shared-resource table filled in as CSV |")

        self.chapter("1b. A customer-visible deferral (I-004)",
                     "State `DEFERRED` needs a signed record and, when the customer can see the issue, the customer's written acceptance.")
        self.run("2026-04-27 10:00", PM, ["issue", "add", "--title", "Spare GPIO count is below the customer request", "--phase", "design",
                                          "--description", "The package ball map leaves 6 spare GPIO; the customer asked for 8."])
        self.run("2026-04-27 10:10", PM, ["issue", "log", "I-004", "--owner", DESIGN, "--severity", "3"])
        dr = dict(ref="DR-004", title="Spare GPIO count is below the customer request", issue="I-004", date="2026-04-28", cv="yes",
                  a_s="21", a_c="60000", reco="C - defer to the next revision; the customer's first board needs 4.")
        self.doc("2026-04-28 09:00", PM, "decisions/DR-004.md", DR_TEMPLATE % dict(dr, chosen="[A|B|C]", by="[name]", on="[YYYY-MM-DD]", signed="no", acc="n/a", cond="n/a"),
                 "decision record")
        self.run("2026-04-28 09:10", PM, ["issue", "triage", "I-004", "--decision-ref", "DR-004"])
        self.doc("2026-04-29 09:00", PM, "decisions/DR-004.md", DR_TEMPLATE % dict(dr, chosen="C", by=SPONSOR, on="2026-04-29", signed="yes", acc="n/a", cond="Revisit at the next revision kickoff."),
                 "the sponsor chooses C and signs, but the customer has not yet accepted in writing")
        self.run("2026-04-29 09:10", PM, ["issue", "decide", "I-004"])
        self.run("2026-04-29 09:20", PM, ["issue", "defer", "I-004"], expect=1, why="customer visible, no recorded customer acceptance")
        self.doc("2026-04-30 09:00", PM, "decisions/DR-004.md", DR_TEMPLATE % dict(dr, chosen="C", by=SPONSOR, on="2026-04-29", signed="yes",
                                                                                    acc="Northwind email 2026-04-30 accepts 6 spare GPIO for this revision", cond="Revisit at the next revision kickoff."),
                 "customer acceptance recorded")
        self.run("2026-04-30 09:10", PM, ["issue", "defer", "I-004"], why="DEFERRED is not 'open': it no longer ages and does not block gates")

        def budget(rows):
            data = (("concept", 150000, 150000, 148000, 148000), ("requirements", 250000, 250000, 262000, 262000), ("planning", 200000, 200000, 198000, 198000),
                    ("design", 650000, 400000, 425000, 650000), ("verification", 330000, 0, 0, 330000), ("tapeout", 360000, 0, 0, 360000),
                    ("bringup", 180000, 0, 0, 180000), ("testing", 130000, 0, 0, 130000), ("production", 30000, 0, 0, 30000))
            for ph, b, pl, ac, fc in data:
                rows.append(dict(phase=ph, budget=str(b), planned_to_date=str(pl), actual_to_date=str(ac), forecast_at_completion=str(fc), updated="2026-05-01"))
        self.quiet_enter()
        self.edit_csv("2026-05-01 09:00", PM, "budget.csv", budget, "month-end figures by phase; allocated 2,280,000 of the 2,400,000 baseline, 120,000 held as contingency")
        self.small("I-005", "Lint waivers are not tracked in the repo", "design", VERIF, 3,
                   dict(add="2026-05-04", triage="2026-05-06", decide="2026-05-07", resolve="2026-05-12", close="2026-05-13"), "DR-005",
                   "Keep waivers next to the code they excuse.")
        self.small("I-006", "Clock tree report is missing the slow corner", "design", VERIF, 3,
                   dict(add="2026-05-14", triage="2026-05-15", decide="2026-05-16", resolve="2026-05-16", close="2026-05-17"), "DR-006",
                   "Generate all signoff corners from one script.")
        self.quiet_exit()
        self.say("")
        self.say("Also quiet: 2026-05-01 month-end figures typed into `budget.csv` (2,280,000 allocated of the 2,400,000 baseline; 120,000 held as contingency) and "
                 "I-005 and I-006, two small design issues taken to CLOSED by 2026-05-17.")

    def sev1(self):
        self.chapter("2. Detect and log",
                     "State `DETECTED` -> `LOGGED`. On 2026-05-18 an emulation run shows the supply voltage dropping below the limit at peak load. "
                     "R-001 (power-delivery margin) was a known risk; it has just happened.")
        self.run("2026-05-18 09:00", PM, ["issue", "add", "--title", "Supply droop exceeds the limit at peak load", "--phase", "design",
                                          "--description", "Emulation run 214 shows core supply dropping 4% below the limit under the worst-case workload."],
                 why="capture it the moment it is known (prompt 1 or 2 can draft this)")
        self.run("2026-05-18 09:30", PM, ["issue", "log", "I-007", "--owner", DESIGN, "--severity", "1", "--escape-gate", "G2",
                                          "--exec-notified", "2026-05-18", "--linked-risk", "R-001",
                                          "--next-action", "War-room daily at 10:00; re-run PDN analysis", "--due", "2026-05-20"],
                 why="one named owner, severity 1, and the executive notice date; the requirement was ambiguous at G2, so G2 is the escape gate")
        self.doc("2026-05-18 09:45", PM, "communications/exec_note_2026-05-18.md", EXEC_NOTE, "same-day executive note from the exec_note template; the PM sends it")
        self.run("2026-05-18 10:00", PM, ["risk", "occur", "R-001", "--linked-issue", "I-007", "--note", "droop exceeded the limit in emulation run 214"],
                 why="the risk becomes an issue; the link is mandatory")
        self.run("2026-05-18 10:10", PM, ["issue", "close", "I-007", "--lesson", "too early"], expect=1, why="try to skip ahead")
        self.run("2026-05-18 11:00", PM, ["health"], why="where the program stands, with a Sev 1 open")

        self.chapter("3. Triage",
                     "State `LOGGED` -> `TRIAGED`. The tool will not move on without a decision record that has three options and a recommendation.")
        self.run("2026-05-19 09:00", PM, ["issue", "triage", "I-007"], expect=1, why="try to triage with no record")
        self.doc("2026-05-19 11:00", PM, "decisions/DR-007.md", DR_TEMPLATE % dict(
            ref="DR-007", title="Supply droop exceeds the limit at peak load", issue="I-007", date="2026-05-19", cv="yes",
            a_s="14", a_c="85000", reco="A - fix now. The root cause is understood and the fix removes the risk instead of limiting the product.",
            chosen="[A|B|C]", by="[name]", on="[YYYY-MM-DD]", signed="no", acc="n/a", cond="n/a"),
            "decision record from the template; the three options come from the design lead (prompt 3 can draft them)")
        self.run("2026-05-19 11:10", PM, ["issue", "triage", "I-007", "--decision-ref", "DR-007"], why="options and recommendation present")
        self.run("2026-05-19 11:20", PM, ["issue", "decide", "I-007"], expect=1, why="try to decide before anyone has chosen")

        self.chapter("4. Decide and change control",
                     "State `TRIAGED` -> `DECIDED`. The sponsor chooses option A. The fix costs money and time, so it also goes through change control (`C-001`).")
        self.doc("2026-05-20 09:00", PM, "decisions/DR-007.md", DR_TEMPLATE % dict(
            ref="DR-007", title="Supply droop exceeds the limit at peak load", issue="I-007", date="2026-05-19", cv="yes",
            a_s="14", a_c="85000", reco="A - fix now. The root cause is understood and the fix removes the risk instead of limiting the product.",
            chosen="A", by=SPONSOR, on="2026-05-20", signed="no", acc="n/a", cond="n/a"), "the decision is recorded by the person who made it")
        self.run("2026-05-20 09:10", PM, ["issue", "decide", "I-007"], why="schedule and cost impact are copied from the chosen option, not typed again")
        self.run("2026-05-20 09:20", PM, ["brief", "I-007"], why="a Sev 1 needs a brief before it can close; the tool drafts it from the register and the record")
        self.show_file("briefs/B-001.md", "The draft, with the facts filled in and every unknown left as a [placeholder]")
        self.run("2026-05-20 10:00", PM, ["change", "request", "--title", "Re-route the power grid and add decoupling", "--requestor", PM, "--linked-issue", "I-007"])
        self.run("2026-05-20 10:30", PM, ["change", "assess", "C-001", "--effort-person-weeks", "6", "--cost-delta", "85000", "--schedule-delta-days", "14",
                                          "--risk-note", "Re-run PDN and timing sign-off on the new floorplan."], why="85,000 and 14 days: tier Large")
        self.run("2026-05-20 11:00", PM, ["change", "approve", "C-001", "--approvers-signed", "sponsor", "--decision-ref", "DR-008"], expect=1,
                 why="Large needs the sponsor and the customer, and a filed record")
        self.doc("2026-05-21 09:00", PM, "decisions/DR-008.md", ECR % dict(date="2026-05-21"), "ECR from the ecr_waiver template, signed by both approvers")
        self.run("2026-05-21 09:10", PM, ["change", "approve", "C-001", "--approvers-signed", "sponsor; customer", "--decision-ref", "DR-008"])
        self.run("2026-05-21 09:20", PM, ["change", "implement", "C-001"], expect=1, why="a cost change needs the budget forecast updated first")

        def budget(rows):
            for r in rows:
                if r["phase"] == "design":
                    r["forecast_at_completion"] = "735000"
                    r["updated"] = "2026-05-21"
        self.edit_csv("2026-05-21 09:30", PM, "budget.csv", budget, "design forecast 650,000 -> 735,000")

        def slip(rows):
            for r in rows:
                if r["id"] in SLIPPED:
                    r["planned_date"] = SLIPPED[r["id"]]
        self.edit_csv("2026-05-21 09:40", PM, "gates.csv", slip, "planned dates for G4 to G9 move 14 days; baseline dates do not move")
        self.run("2026-05-21 09:50", PM, ["change", "implement", "C-001"])
        self.run("2026-05-22 15:00", PM, ["report", "weekly"], why="Friday status draft")
        self.show_file("reports/weekly_2026-05-22.md", "The draft")
        self.run("2026-05-22 15:10", PM, ["raid"], why="RAID snapshot; the open Sev 1 is always listed")
        self.run("2026-05-22 15:20", PM, ["health"], why="Sev 1 is four days old: inside its 7-day green limit")

        self.chapter("5. The gate guard",
                     "A gate with a blocking severity cannot pass while that issue is open. The readiness review for G4 opens early to see where things stand.")
        self.run("2026-05-26 14:00", PM, ["gate", "review", "G4"], why="open the G4 readiness review")
        self.run("2026-05-26 14:30", PM, ["gate", "go", "G4", "--criteria-met", "1;2;3"], expect=1,
                 why="criteria recorded as met, but the Sev 1 is still open and G4 requires no open Sev 1 or Sev 2")

        self.run("2026-06-01 09:00", PM, ["risk", "rescore", "R-004", "--note", "no change after the monthly review"],
                 why="a routine review of an accepted risk keeps it inside its 30-day interval")

        self.chapter("6. Resolve and close",
                     "State `DECIDED` -> `RESOLVED` -> `CLOSED`. A Sev 1 cannot close with an unfinished brief or no lesson.")
        self.run("2026-06-03 16:00", PM, ["issue", "resolve", "I-007", "--verification-ref", "PDN sign-off run 233; emulation run 241 within the limit"],
                 why="resolution needs named evidence")
        self.run("2026-06-03 16:05", PM, ["change", "verify", "C-001", "--ref", "PDN sign-off run 233"], why="the change lifecycle closes with its own evidence")
        self.run("2026-06-03 16:10", PM, ["issue", "close", "I-007"], expect=1, why="the brief still has placeholders and there is no lesson")
        brief = self.read("briefs/B-001.md")
        for old, new in (
            ("Milestone threatened: [milestone].", "Milestone threatened: G4 Design Freeze."),
            ("Distribution: [names or list]", "Distribution: %s, %s, %s, %s" % (SPONSOR, CUSTOMER, DESIGN, VERIF)),
            ("Next update: [date]", "Next update: closure note, 2026-06-04"),
            ("Customer: [milestone affected, or \"internal only\"]", "Customer: G4 Design Freeze moves from 2026-06-12 to 2026-06-26; later gates move 14 days"),
            ("[Next step and who is told.]", "The fix (C-001) is approved and implemented. The sponsor was told on 2026-05-20 and the customer on 2026-05-21."),
        ):
            if old not in brief:
                raise SystemExit("brief draft changed: %r not found" % old)
            brief = brief.replace(old, new)
        self.doc("2026-06-03 17:00", PM, "briefs/B-001.md", brief, "the PM fills every placeholder (prompt 5 can help)")
        self.run("2026-06-04 09:00", PM, ["issue", "close", "I-007", "--lesson", "State the peak-current requirement as a number with a test at G2, not as 'adequate margin'."],
                 why="brief complete, lesson recorded")
        self.doc("2026-06-05 10:00", PM, "communications/retrospective_I-007.md", RETRO, "retrospective one-pager after a Sev 1 (prompt 8 can draft it)")
        self.run("2026-06-05 15:00", PM, ["report", "weekly"])
        self.run("2026-06-05 15:10", PM, ["raid"])
        self.run("2026-06-05 15:20", PM, ["health"], why="Sev 1 closed; the schedule and gate metrics now carry the cost")

    def after_sev1(self):
        self.chapter("7. Risk review before the gate",
                     "One risk is re-scored inside its review interval. Another is left alone on purpose, so the check can flag it as stale later.")
        self.run("2026-06-19 09:00", PM, ["risk", "rescore", "R-002", "--probability", "2", "--impact", "4", "--note", "second slot confirmed in writing"],
                 why="re-scored inside its 14-day review interval; R-003 is not re-scored and will show as stale")

    def gate4(self):
        self.chapter("8. Gate G4",
                     "With the Sev 1 closed, the G4 review that was opened on 2026-05-26 can finish. The gate passes 14 days after its baseline.")
        self.run("2026-06-26 14:00", PM, ["gate", "go", "G4", "--criteria-met", "1;2;3"], why="the same command that was refused on 2026-05-26")
        self.doc("2026-06-26 15:00", PM, "communications/gate_announcement_G4.md", GATE_ANNOUNCEMENT, "go/no-go announcement from the template (prompt 10 can draft it)")

    def new_sev2(self):
        self.chapter("9. A new Sev 2 and where things stand",
                     "A Sev 2 turns up in the verification phase and waits for a decision. The Friday reports show it, and the health rollup is the worst of the five metrics.")
        self.run("2026-06-29 10:00", PM, ["issue", "add", "--title", "Memory controller misses timing by 40 ps at the slow corner", "--phase", "verification",
                                          "--description", "Sign-off timing run shows a 40 ps miss on the read path at the slow corner."])
        self.run("2026-06-29 10:10", PM, ["issue", "log", "I-008", "--owner", DESIGN, "--severity", "2", "--next-action", "Decide by 2026-07-08", "--due", "2026-07-08"])
        d8 = dict(ref="DR-009", title="Memory controller misses timing by 40 ps at the slow corner", issue="I-008", date="2026-07-01", cv="no",
                  a_s="10", a_c="30000", reco="A - fix now with a pipeline stage; the other options leave a known miss.")
        self.doc("2026-07-01 09:00", PM, "decisions/DR-009.md", DR_TEMPLATE % dict(d8, chosen="[A|B|C]", by="[name]", on="[YYYY-MM-DD]", signed="no", acc="n/a", cond="n/a"),
                 "options drafted, decision not yet made")
        self.run("2026-07-01 09:10", PM, ["issue", "triage", "I-008", "--decision-ref", "DR-009"], why="I-008 now waits for a decision: it appears under DECISIONS NEEDED")
        self.run("2026-07-03 15:00", PM, ["report", "weekly"])
        self.show_file("reports/weekly_2026-07-03.md", "The draft")
        self.run("2026-07-03 15:10", PM, ["raid"])
        self.show_file("reports/raid_2026-07-03.md", "The snapshot")
        self.run("2026-07-03 15:15", PM, ["dashboard"], why="a read-only HTML view of the same numbers, for people who do not open CSV files; the registers stay the edit surface")
        self.say("")
        self.say("Open [dashboard_2026-07-03.html](../workspace/reports/dashboard_2026-07-03.html) in a browser. It follows the light or dark setting of the viewer.")
        self.run("2026-07-03 15:20", PM, ["health"], why="several amber metrics, so the rollup is amber: the worst of the five, not an average")
        self.run("2026-07-03 15:30", PM, ["check"], why="no errors; warnings that need a human (two risks not re-scored in time, a vendor paid before delivery, a shared-resource clash)")

    def trail(self):
        self.chapter("10. Event trail for I-007", "Every transition above wrote one row to `events.csv`. This is the trail for the Sev 1.")
        _, rows = read_csv(os.path.join(self.ws, "events.csv"))
        self.say("")
        self.say("| When (UTC) | Event | From | To | By | Note |")
        self.say("|---|---|---|---|---|---|")
        for r in rows:
            if r["entity"] == "issue" and r["id"] == "I-007":
                self.say("| %s | %s | %s | %s | %s | %s |" % (r["ts"], r["event"], r["from_state"] or "-", r["to_state"], r["actor"], r["note"] or ""))
        self.say("")
        self.say("Files this story produced: [issues.csv](../workspace/issues.csv), [risks.csv](../workspace/risks.csv), [changes.csv](../workspace/changes.csv), "
                 "[gates.csv](../workspace/gates.csv), [events.csv](../workspace/events.csv), decision records [DR-007](../workspace/decisions/DR-007.md) "
                 "and [DR-008](../workspace/decisions/DR-008.md), the brief [B-001](../workspace/briefs/B-001.md), the weekly drafts and RAID snapshots in "
                 "[reports](../workspace/reports/), and the PM-written notes in [communications](../workspace/communications/).")

    def write_walkthrough(self):
        d = os.path.join(self.out, "walkthrough")
        os.makedirs(d, exist_ok=True)
        text = "\n".join(self.md).replace("\r\n", "\n").rstrip("\n") + "\n"
        with io.open(os.path.join(d, "SEV1_WALKTHROUGH.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)

    def build(self):
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
        os.makedirs(self.out)
        os.environ["PMF_ACTOR"] = PM
        self.setup()
        self.history()
        self.sev1()
        self.after_sev1()
        self.gate4()
        self.new_sev2()
        self.trail()
        self.write_walkthrough()


# ---------------------------------------------------------------- documents the people write
DR_TEMPLATE = """# %(ref)s: %(title)s
Issue: %(issue)s
Date: %(date)s
Customer visible: %(cv)s

## Options
| Option | Description | Schedule (days) | Cost | Risk |
|---|---|---|---|---|
| A | Fix now | %(a_s)s | %(a_c)s | Medium |
| B | Waive with conditions | 0 | 0 | High |
| C | Defer to next revision | 0 | 0 | Medium |

Recommendation: %(reco)s

## Decision
Chosen: %(chosen)s
Decided by: %(by)s
Decided on: %(on)s
Signed: %(signed)s
Customer acceptance: %(acc)s
Conditions: %(cond)s
"""

EXEC_NOTE = """Subject: [Sev 1] Meridian-1 - supply droop exceeds the limit at peak load

WHAT
Emulation run 214 shows the core supply dropping 4% below the limit under the worst-case workload, in the design phase. G4 Design Freeze (2026-06-12) is threatened.

IMPACT
Schedule: not yet sized to G4 Design Freeze
Cost: not yet sized
Customer: Northwind Systems design review depends on G4

STATUS
Discovered: 2026-05-18 08:40
War-room started: 2026-05-18 09:30
Owner: Jordan Patel
Next update: 2026-05-19 10:00

RECOMMENDATION
Endorse a fix-now track while the three options are costed.

DECISION NEEDED BY
2026-05-20. I'll bring the full 3-option table to the call at 09:00.

- Avery Chen
"""

ECR = """# ECR C-001: Re-route the power grid and add decoupling
Related issue: I-007
Decision record: DR-007
Date: %(date)s

## Scope of change
Re-route the top-level power grid and add decoupling capacitance around the compute tiles to remove the peak-load droop.

## Impacted areas
Design phase floorplan, PDN analysis, timing sign-off. No change to the customer-facing specification.

## Re-run and verification requirements
Re-run PDN analysis and timing sign-off on the new floorplan; repeat emulation run 214 at the worst-case workload.

## Cost delta
85000

## Schedule impact
14

## Risk accepted (waivers only)
n/a

## Approval required from
Tier: large (from the profile's change_control tiers)
Approvers: sponsor, customer

## Signatures
| Name | Role | Date |
|---|---|---|
| Riley Morgan | sponsor | 2026-05-20 |
| Casey Nguyen | customer | 2026-05-21 |
"""

RETRO = """Meridian-1 - Retrospective: I-007 supply droop (Sev 1)
Date: 2026-06-05
Author: Avery Chen

WHAT HAPPENED
Detected 2026-05-18 in an emulation run. Triaged 2026-05-19, decided 2026-05-20, fix implemented and verified by 2026-06-03, closed 2026-06-04. G4 moved from 2026-06-12 to 2026-06-26.

ROOT CAUSE
The peak-current requirement was stated as "adequate margin" at G2, so nothing could fail against it until emulation. The risk (R-001) was known and monitored but had no test attached.

WHAT WORKED
- R-001 was already in the register, so the escalation to an issue was a link, not a surprise.
- The executive note went out the day it was detected.
- The gate guard stopped G4 from passing while the Sev 1 was open.

WHAT DIDN'T
- The requirement had no number and no test at G2.
- The risk was reviewed on schedule but its mitigation had no exit date.

CHANGES GOING FORWARD
1. G2 exit criteria for power requirements: a number, a unit, and a named test.
2. Every High risk gets a mitigation with a date, reviewed at each weekly RAID.
3. Add a peak-load emulation run to the design-phase checklist before G4 review.

REFERENCED DECISIONS
- DR-007 (triage and decision)
- DR-008 (change approval)

Filed: examples/meridian/workspace/communications
"""

GATE_ANNOUNCEMENT = """Subject: Meridian-1 - G4 Design Freeze - GO

DECISION: GO
Date: 2026-06-26
Attendees: Avery Chen (PM), Jordan Patel (design), Sam Okafor (verification), Riley Morgan (sponsor), Casey Nguyen (customer)

EXIT CRITERIA STATUS
Coverage targets met: Met
No open Sev 1 or Sev 2 issues: Met (I-007 closed 2026-06-04)
Customer design review complete: Met

WAIVERS ACCEPTED (if any)
- none

NEXT PHASE START: 2026-06-29
NEXT GATE: G5 Tape-Out Readiness Review - 2026-08-21 (baseline 2026-08-07)

Decision record filed: workspace/gates.csv, event trail in workspace/events.csv
"""


def tree(path):
    out = {}
    for dp, _, fs in os.walk(path):
        for f in fs:
            p = os.path.join(dp, f)
            with open(p, "rb") as fh:
                out[os.path.relpath(p, path).replace("\\", "/")] = fh.read().replace(b"\r\n", b"\n")
    return out


def main(argv):
    check = "--check" in argv
    out = os.path.join(HERE, "meridian")
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
    keep = {k: os.environ.get(k) for k in ("PMF_FAKE_NOW", "PMF_WORKSPACE", "PMF_ACTOR")}
    try:
        if check:
            tmp = tempfile.mkdtemp(prefix="meridian-")
            try:
                Demo(os.path.join(tmp, "meridian")).build()
                new = tree(os.path.join(tmp, "meridian"))
                old = {k: v for k, v in tree(out).items() if k.startswith(("workspace/", "walkthrough/"))}
                same = new == old
                if not same:
                    for k in sorted(set(new) | set(old)):
                        if new.get(k) != old.get(k):
                            print("differs: %s" % k)
                    print("MERIDIAN CHECK: committed example is out of date; run python3 examples/run_demo.py")
                else:
                    print("MERIDIAN CHECK: committed example matches a fresh run (%d files)" % len(new))
                return 0 if same else 1
            finally:
                shutil.rmtree(tmp, True)
        # rebuild only the generated folders so hand-written files beside them (README.md) survive
        for sub in ("workspace", "walkthrough"):
            shutil.rmtree(os.path.join(out, sub), True)
        tmp = tempfile.mkdtemp(prefix="meridian-")
        try:
            Demo(os.path.join(tmp, "meridian")).build()
            os.makedirs(out, exist_ok=True)
            for sub in ("workspace", "walkthrough"):
                shutil.copytree(os.path.join(tmp, "meridian", sub), os.path.join(out, sub))
        finally:
            shutil.rmtree(tmp, True)
        print("rebuilt %s" % out)
        return 0
    finally:
        for k, v in keep.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
