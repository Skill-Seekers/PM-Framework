import json
import os
import unittest

from helpers import WS, WSData, ROOT, run


class Check(WSData):
    def errs(self, *extra):
        rc, out, err = run(["check", "--json"] + list(extra))
        d = json.loads(out)
        return rc, d["errors"], d["warnings"]

    def test_fresh_workspace_is_clean(self):
        rc, e, w = self.errs()
        self.assertEqual((rc, e), (0, []))
        self.assertTrue(any("baseline_date" in x for x in w))

    def test_strict_fails_on_warnings(self):
        rc, _, _ = self.errs("--strict")
        self.assertEqual(rc, 1)

    def test_hand_edited_state_is_caught(self):
        iid = self.new_issue()
        self.edit("issues", iid, state="CLOSED")
        rc, e, _ = self.errs()
        self.assertEqual(rc, 1)
        self.assertTrue(any("edited by hand" in x for x in e), e)

    def test_bad_values(self):
        self.add_row("issues", id="I-001", title="t", state="LOGGED", detected="soon", severity="x", owner="A and B", phase="nope")
        rc, e, _ = self.errs()
        text = "\n".join(e)
        for needle in ("not a date", "not a number", "not one named person", "not in the profile"):
            self.assertIn(needle, text)

    def test_duplicate_ids_and_unknown_state(self):
        self.add_row("issues", id="I-001", title="a", state="DETECTED")
        self.add_row("issues", id="I-001", title="b", state="WEIRD")
        _, e, _ = self.errs()
        text = "\n".join(e)
        self.assertIn("duplicate", text)
        self.assertIn("unknown state", text)

    def test_missing_profile_gate(self):
        from pmf.workspace import Workspace
        ws = Workspace(self.dir)
        ws.save("gates", [g for g in ws.load("gates") if g["id"] != "G3"])
        _, e, _ = self.errs()
        self.assertTrue(any("G3" in x for x in e))

    def test_escalated_issue_warning(self):
        self.add_row("issues", id="I-001", title="t", state="TRIAGED", detected="2026-02-01", severity="3", owner="Sam Lee", phase="design", decision_ref="DR-001")
        self.dr()
        self.add_row("events", ts="2026-02-01T00:00:00Z", entity="issue", id="I-001", event="transition", from_state="LOGGED", to_state="TRIAGED", actor="t")
        _, e, w = self.errs()
        self.assertTrue(any("ESCALATED" in x for x in w), w)

    def test_stale_risk_warning(self):
        self.add_row("risks", id="R-001", title="t", state="ASSESSED", probability="4", impact="4", owner="Ana Ruiz", last_scored="2026-02-01")
        self.add_row("events", ts="2026-02-01T00:00:00Z", entity="risk", id="R-001", event="transition", from_state="IDENTIFIED", to_state="ASSESSED", actor="t")
        _, _, w = self.errs()
        self.assertTrue(any("STALE" in x for x in w), w)

    def test_assumption_dependency_vendor_contention_rules(self):
        self.add_row("assumptions", id="A-001", title="t", status="untested", validate_by="2026-01-01")
        self.add_row("assumptions", id="A-002", title="t", status="invalid")
        self.add_row("dependencies", id="D-001", title="t", status="late")
        self.add_row("vendors", vendor="Acme", paid_on_delivery="no")
        self.add_row("contention", resource="Test lab", period="2026-04", program="A", demand="3", capacity="4")
        self.add_row("contention", resource="Test lab", period="2026-04", program="B", demand="2", capacity="4")
        _, e, w = self.errs()
        wt = "\n".join(w)
        for needle in ("untested past", "late with no linked issue", "paid before delivery", "demand 5.0 exceeds capacity 4.0"):
            self.assertIn(needle, wt)
        self.assertTrue(any("A-002" in x and "invalid" in x for x in e), e)

    def test_cumulative_change_cost_warning(self):
        self.add_row("changes", id="C-001", date="2026-03-01", title="t", requestor="x", state="APPROVED", cost_delta="60000", decision_ref="DR-001")
        self.dr(ref="DR-001", issue="")
        self.add_row("events", ts="2026-03-01T00:00:00Z", entity="change", id="C-001", event="transition", from_state="ASSESSED", to_state="APPROVED", actor="t")
        _, _, w = self.errs()
        self.assertTrue(any("re-baseline" in x for x in w), w)

    def test_sev1_without_exec_notice_warns(self):
        iid = self.new_issue(sev=1)
        _, _, w = self.errs()
        self.assertTrue(any("exec_notified" in x for x in w), w)
        self.ok("issue", "add", "--title", "unrelated")
        self.edit("issues", iid, exec_notified="2026-03-02")
        _, _, w = self.errs()
        self.assertFalse(any(iid in x and "exec_notified" in x for x in w))

    def test_header_drift_is_exit_2(self):
        p = self.path("issues.csv")
        with open(p) as f:
            t = f.read()
        with open(p, "w") as f:
            f.write(t.replace("title,", "name,", 1))
        self.could_not_run("check")


class Reports(WS):
    def test_brief_requires_logged_issue_and_is_never_overwritten(self):
        self.ok("issue", "add", "--title", "x")
        self.refused(None, "brief", "I-001")
        self.ok("issue", "log", "I-001", "--description", "d", "--phase", "design", "--owner", "Sam Lee", "--severity", "1")
        self.ok("brief", "I-001")
        self.assertTrue(os.path.exists(self.path("briefs", "B-001.md")))
        self.assertIn("already has brief", self.refused(None, "brief", "I-001"))

    def test_brief_copies_facts_and_leaves_placeholders(self):
        iid = self.issue_to_triaged(sev=1)
        self.ok("brief", iid)
        t = self.read("briefs/B-001.md")
        self.assertIn("Severity: Sev 1", t)
        self.assertIn("A. Fix now: Fix now; schedule 5 days; cost 10000; risk Medium", t)
        self.assertIn("## RECOMMENDATION\nA - the fix is cheap", t)
        self.assertIn("[Date/time, and what happens on the call.]", t)
        self.assertIn("Author: tester", t)

    def test_weekly_is_idempotent_and_protects_edits(self):
        out = self.ok("report", "weekly")
        self.assertIn("created reports/weekly_2026-03-02.md", out)
        self.assertIn("unchanged", self.ok("report", "weekly"))
        p = self.path("reports", "weekly_2026-03-02.md")
        with open(p, "a") as f:
            f.write("my edit\n")
        self.assertIn("--force", self.refused(None, "report", "weekly"))
        self.assertIn("my edit", self.read("reports/weekly_2026-03-02.md"))
        self.assertIn("overwritten", self.ok("report", "weekly", "--force"))

    def test_weekly_content(self):
        self.new_issue(sev=1)
        t = self.ok("report", "weekly", "--stdout")
        self.assertIn("HEADLINE", t)
        self.assertIn("OPEN ISSUES (Sev 1/2)\n- I-001 Lab supply late (Sev 1, LOGGED)", t)
        self.assertIn("Decide I-001", t)
        self.assertIn("Next gate: G1", t)

    def test_raid_always_lists_open_sev12(self):
        self.new_issue(sev=1)
        self.new_issue(sev=2, ident="I-050")
        self.ok("risk", "add", "--title", "Foundry slot slips")
        t = self.ok("raid", "--stdout")
        self.assertIn("I-001", t)
        self.assertIn("I-050", t)
        self.assertIn("## Risks", t)

    def test_dry_run_writes_no_report(self):
        out = self.ok("report", "weekly", "--dry-run")
        self.assertIn("DRY RUN", out)
        self.assertFalse(os.path.exists(self.path("reports", "weekly_2026-03-02.md")))


class InitAndCli(WS):
    def test_init_never_overwrites(self):
        self.could_not_run("init", self.dir, "--program", "Again")

    def test_init_content(self):
        gates = self.rows("gates")
        self.assertEqual(len(gates), 9)
        self.assertTrue(all(g["state"] == "PLANNED" and g["baseline_date"] == "" for g in gates))
        raci = self.rows("raci")
        self.assertEqual(len(raci), 9 * 4)
        self.assertEqual(self.read("profile.json")[:1], "{")
        for f in ("issues", "risks", "changes", "events"):
            self.assertEqual(self.rows(f), [])

    def test_init_rejects_bad_input(self):
        t = os.path.join(self.tmp, "other")
        self.could_not_run("init", t, "--program", "X", "--profile", "nope")
        self.could_not_run("init", t, "--program", "X", "--baseline-start", "tomorrow")
        self.could_not_run("init", t, "--program", "X", "--baseline-budget", "lots")
        self.assertFalse(os.path.exists(os.path.join(t, "pmf.config.json")))

    def test_software_profile_workspace(self):
        t = os.path.join(self.tmp, "sw")
        self.ok("init", t, "--program", "SW", "--profile", "software")
        os.environ["PMF_WORKSPACE"] = t
        self.dir = t
        self.assertEqual(len(self.rows("gates")), 6)
        self.ok("check")

    def test_exit_codes(self):
        self.assertEqual(run(["health"])[0], 0)
        self.assertEqual(run(["issue", "decide", "I-404"])[0], 2)
        self.assertEqual(run([])[0], 2)
        os.environ.pop("PMF_WORKSPACE")
        rc, out, err = run(["-h"])
        self.assertEqual(rc, 0)
        here = os.getcwd()
        self.addCleanup(os.chdir, here)
        os.chdir(self.tmp)
        self.assertEqual(run(["check"])[0], 2)

    def test_health_fail_on(self):
        self.assertEqual(run(["health", "--fail-on", "red"])[0], 0)
        self.new_issue(sev=1)
        self.ok("health", "--json")

    def test_show_history(self):
        iid = self.new_issue()
        out = self.ok("show", iid)
        self.assertIn("LOGGED", out)
        self.assertIn("history:", out)

    def test_lifecycles_command_lists_every_transition(self):
        out = self.ok("lifecycles")
        for c in ("issue triage", "risk accept", "change approve", "gate conditional"):
            self.assertIn(c, out)

    def test_actor_precedence(self):
        self.ok("issue", "add", "--title", "a", "--actor", "Zed")
        self.assertEqual(self.rows("events")[-1]["actor"], "Zed")


if __name__ == "__main__":
    unittest.main()
