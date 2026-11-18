import unittest

from helpers import WS


class IssueFlow(WS):
    def test_create_defaults(self):
        self.ok("issue", "add", "--title", "Lab supply late")
        r = self.row("issues", "I-001")
        self.assertEqual((r["state"], r["detected"]), ("DETECTED", "2026-03-02"))
        ev = self.rows("events")
        self.assertEqual([(e["entity"], e["id"], e["from_state"], e["to_state"], e["actor"]) for e in ev],
                         [("issue", "I-001", "", "DETECTED", "tester")])

    def test_create_needs_title(self):
        self.refused(None, "issue", "add", "--description", "x")
        self.assertEqual(self.rows("issues"), [])

    def test_log_guards(self):
        self.ok("issue", "add", "--title", "T", "--phase", "design")
        self.refused("has_required_fields", "issue", "log", "I-001", "--owner", "Sam Lee", "--severity", "2")
        self.ok("issue", "add", "--title", "T2", "--description", "d", "--phase", "design")
        self.refused("single_owner", "issue", "log", "I-002", "--owner", "Sam and Lee", "--severity", "2")
        self.refused("single_owner", "issue", "log", "I-002", "--owner", "Test team", "--severity", "2")
        self.refused("valid_severity", "issue", "log", "I-002", "--owner", "Sam Lee", "--severity", "9")
        self.refused("valid_phase", "issue", "log", "I-002", "--owner", "Sam Lee", "--severity", "2", "--phase", "nope")
        self.assertEqual(self.state("issues", "I-002"), "DETECTED")

    def test_triage_guards(self):
        iid = self.new_issue()
        self.refused("decision_record_has_three_options", "issue", "triage", iid)
        self.refused("decision_record_has_three_options", "issue", "triage", iid, "--decision-ref", "DR-404")
        self.dr(a_c="[cost]")
        self.refused("decision_record_has_three_options", "issue", "triage", iid, "--decision-ref", "DR-001")
        self.dr(reco="[A|B|C] - [one-line rationale]")
        self.refused("decision_record_has_recommendation", "issue", "triage", iid, "--decision-ref", "DR-001")
        self.dr()
        self.ok("issue", "triage", iid, "--decision-ref", "DR-001")
        self.assertEqual(self.state("issues", iid), "TRIAGED")

    def test_decide_guards_and_effects(self):
        iid = self.issue_to_triaged()
        self.refused("decision_chosen", "issue", "decide", iid)
        self.decide_dr(chosen="B", signed="no")
        self.refused("decision_signed_if_waive_or_defer", "issue", "decide", iid)
        self.decide_dr(chosen="A")
        self.ok("issue", "decide", iid)
        r = self.row("issues", iid)
        self.assertEqual((r["state"], r["sched_impact_days"], r["cost_impact"]), ("DECIDED", "5", "10000"))

    def test_decide_with_signed_waiver(self):
        iid = self.issue_to_triaged()
        self.decide_dr(chosen="B", signed="yes")
        self.ok("issue", "decide", iid)
        self.assertEqual(self.row("issues", iid)["cost_impact"], "0")

    def test_resolve_guards(self):
        iid = self.issue_to_triaged()
        self.decide_dr(chosen="A")
        self.ok("issue", "decide", iid)
        self.refused("verification_ref_present", "issue", "resolve", iid)
        self.ok("issue", "resolve", iid, "--verification-ref", "RUN-42")
        self.assertEqual(self.state("issues", iid), "RESOLVED")

    def test_resolve_refuses_deferral_choice(self):
        iid = self.issue_to_triaged()
        self.decide_dr(chosen="C", signed="yes")
        self.ok("issue", "decide", iid)
        self.refused("option_is_fix_or_waive", "issue", "resolve", iid, "--verification-ref", "x")

    def test_defer_guards_and_retriage(self):
        iid = self.issue_to_triaged()
        self.decide_dr(chosen="A")
        self.ok("issue", "decide", iid)
        self.refused("option_is_defer", "issue", "defer", iid)
        self.decide_dr(chosen="C", signed="yes", cv="yes", acc="n/a")
        self.refused("customer_acceptance_if_customer_visible", "issue", "defer", iid)
        self.decide_dr(chosen="C", signed="yes", cv="yes", acc="Customer email 2026-03-01")
        self.ok("issue", "defer", iid)
        self.assertEqual(self.state("issues", iid), "DEFERRED")
        self.refused("reason_present", "issue", "retriage", iid)
        self.ok("issue", "retriage", iid, "--note", "customer changed the date")
        self.assertEqual(self.state("issues", iid), "TRIAGED")

    def full_close(self, sev):
        iid = self.issue_to_triaged(sev=sev)
        self.decide_dr(chosen="A")
        self.ok("issue", "decide", iid)
        self.ok("issue", "resolve", iid, "--verification-ref", "RUN-42")
        return iid

    def test_close_sev3_needs_only_lesson(self):
        iid = self.full_close(3)
        self.refused("lesson_present", "issue", "close", iid)
        self.ok("issue", "close", iid, "--lesson", "Order lab boards two weeks earlier")
        r = self.row("issues", iid)
        self.assertEqual((r["state"], r["closed"]), ("CLOSED", "2026-03-02"))

    def test_close_sev1_needs_complete_brief(self):
        iid = self.full_close(1)
        self.refused("brief_present_if_required", "issue", "close", iid, "--lesson", "x")
        self.ok("brief", iid)
        self.assertEqual(self.row("issues", iid)["brief_ref"], "B-001")
        err = self.refused("brief_present_if_required", "issue", "close", iid, "--lesson", "x")
        self.assertIn("placeholder", err)
        text = self.read("briefs/B-001.md")
        for token in ("[milestone]", "[names or list]", "[date]", "[Next step and who is told.]"):
            text = text.replace(token, "filled")
        import re
        text = re.sub(r"\[[^\]]*\]", "filled", text)
        self.write("briefs/B-001.md", text)
        self.ok("issue", "close", iid, "--lesson", "Order boards earlier")
        self.assertEqual(self.state("issues", iid), "CLOSED")

    def test_reopen_needs_reason_and_clears_closed(self):
        iid = self.full_close(3)
        self.ok("issue", "close", iid, "--lesson", "x")
        self.refused("reason_present", "issue", "reopen", iid)
        self.ok("issue", "reopen", iid, "--note", "fix regressed")
        r = self.row("issues", iid)
        self.assertEqual((r["state"], r["closed"]), ("TRIAGED", ""))

    def test_illegal_commands_refused_everywhere(self):
        iid = self.new_issue()
        for verb in ("decide", "resolve", "defer", "close", "retriage", "reopen"):
            err = self.refused(None, "issue", verb, iid)
            self.assertIn("not allowed", err)
        self.assertEqual(self.state("issues", iid), "LOGGED")

    def test_refusal_changes_nothing(self):
        iid = self.new_issue()
        before = self.snapshot()
        self.refused(None, "issue", "triage", iid)
        self.refused(None, "issue", "close", iid)
        self.assertEqual(before, self.snapshot())

    def test_dry_run_writes_nothing(self):
        iid = self.new_issue()
        before = self.snapshot()
        self.dr()
        before = self.snapshot()
        out = self.ok("issue", "triage", iid, "--decision-ref", "DR-001", "--dry-run")
        self.assertIn("DRY RUN", out)
        self.assertEqual(before, self.snapshot())

    def test_severity_change(self):
        iid = self.new_issue(sev=2)
        self.refused(None, "issue", "sev", iid, "1")
        self.ok("issue", "sev", iid, "1", "--note", "customer outage confirmed")
        self.assertEqual(self.row("issues", iid)["severity"], "1")
        self.refused(None, "issue", "sev", iid, "9", "--note", "x")
        ev = [e for e in self.rows("events") if e["event"] == "severity_change"]
        self.assertEqual(len(ev), 1)

    def test_unknown_column_and_bad_values_exit_2(self):
        self.ok("issue", "add", "--title", "x")
        self.could_not_run("issue", "log", "I-001", "--severity", "high")
        self.could_not_run("issue", "add", "--title", "x", "--detected", "03/02/2026")
        self.could_not_run("issue", "decide", "I-404")

    def test_csv_formula_injection_neutralised(self):
        self.ok("issue", "add", "--title", "=HYPERLINK(\"http://x\")")
        self.assertTrue(self.row("issues", "I-001")["title"].startswith("'="))


if __name__ == "__main__":
    unittest.main()
