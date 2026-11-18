import unittest

from helpers import WS, WSData


class RiskFlow(WS):
    def new_risk(self):
        self.ok("risk", "add", "--title", "Foundry slot slips", "--phase", "design")
        return self.rows("risks")[-1]["id"]

    def test_assess_guards_and_effects(self):
        rid = self.new_risk()
        self.refused("single_owner", "risk", "assess", rid, "--probability", "4", "--impact", "4")
        self.refused("valid_probability", "risk", "assess", rid, "--owner", "Ana Ruiz", "--impact", "4")
        self.refused("valid_probability", "risk", "assess", rid, "--owner", "Ana Ruiz", "--probability", "6", "--impact", "4")
        self.refused("valid_impact", "risk", "assess", rid, "--owner", "Ana Ruiz", "--probability", "4", "--impact", "0")
        self.ok("risk", "assess", rid, "--owner", "Ana Ruiz", "--probability", "4", "--impact", "4")
        r = self.row("risks", rid)
        self.assertEqual((r["state"], r["last_scored"], r["next_review"]), ("ASSESSED", "2026-03-02", "2026-03-09"))  # 16 = Critical, 7 days

    def assessed(self, p=2, i=2):
        rid = self.new_risk()
        self.ok("risk", "assess", rid, "--owner", "Ana Ruiz", "--probability", str(p), "--impact", str(i))
        return rid

    def test_mitigate_and_retire(self):
        rid = self.assessed()
        self.refused("mitigation_present", "risk", "mitigate", rid)
        self.ok("risk", "mitigate", rid, "--mitigation", "Book a second slot")
        self.refused("reason_present", "risk", "retire", rid)
        self.ok("risk", "retire", rid, "--note", "slot confirmed")
        self.assertEqual(self.state("risks", rid), "RETIRED")

    def test_accept_needs_named_acceptor_and_note_when_high(self):
        rid = self.assessed(2, 2)                                   # score 4, Medium
        self.refused("acceptor_named", "risk", "accept", rid)
        self.ok("risk", "accept", rid, "--accepted-by", "Dana Cho")
        hi = self.assessed(4, 4)                                    # Critical
        self.refused("acceptor_named", "risk", "accept", hi, "--accepted-by", "Dana Cho")
        self.ok("risk", "accept", hi, "--accepted-by", "Dana Cho", "--note", "customer agreed to a one-week buffer")

    def test_occur_needs_a_real_linked_issue(self):
        rid = self.assessed()
        self.refused("linked_issue_exists", "risk", "occur", rid)
        self.refused("linked_issue_exists", "risk", "occur", rid, "--linked-issue", "I-404")
        iid = self.new_issue()
        self.ok("risk", "occur", rid, "--linked-issue", iid)
        self.assertEqual(self.state("risks", rid), "OCCURRED")

    def test_terminal_states_have_no_exits(self):
        rid = self.assessed()
        self.ok("risk", "retire", rid, "--note", "n/a")
        for verb in ("assess", "mitigate", "accept", "occur", "retire"):
            self.assertIn("not allowed", self.refused(None, "risk", verb, rid))

    def test_rescore(self):
        rid = self.assessed(2, 2)
        self.refused(None, "risk", "rescore", rid, "--probability", "4")
        self.ok("risk", "rescore", rid, "--probability", "5", "--impact", "5", "--note", "foundry confirmed delay")
        r = self.row("risks", rid)
        self.assertEqual((r["probability"], r["impact"], r["next_review"]), ("5", "5", "2026-03-09"))
        self.refused(None, "risk", "rescore", rid, "--probability", "9", "--note", "x")


class ChangeFlow(WS):
    def requested(self, **kw):
        self.ok("change", "request", "--title", "Add retimer", "--requestor", "Lee Park")
        return self.rows("changes")[-1]["id"]

    def assessed(self, cost, days, effort="2"):
        cid = self.requested()
        self.ok("change", "assess", cid, "--effort-person-weeks", effort, "--cost-delta", str(cost),
                "--schedule-delta-days", str(days), "--risk-note", "low")
        return cid

    def test_request_needs_requestor(self):
        self.refused(None, "change", "request", "--title", "x")

    def test_assess_needs_sizing(self):
        cid = self.requested()
        self.refused("sizing_present", "change", "assess", cid)
        self.refused("sizing_present", "change", "assess", cid, "--cost-delta", "5")
        self.could_not_run("change", "assess", cid, "--cost-delta", "lots")

    def test_tier_follows_the_higher_of_cost_and_schedule(self):
        cid = self.assessed(1000, 6)                  # cost small, schedule medium (>1, <=5? 6 days is large)
        self.dr(ref="DR-001", issue="")
        err = self.refused("all_tier_approvers_signed", "change", "approve", cid, "--decision-ref", "DR-001", "--approvers-signed", "pm; delivery_lead")
        self.assertIn("Large", err)
        self.assertIn("sponsor", err)

    def test_small_change_full_path(self):
        cid = self.assessed(0, 1)
        self.refused("all_tier_approvers_signed", "change", "approve", cid, "--decision-ref", "DR-001")
        self.refused("decision_ref_present", "change", "approve", cid, "--approvers-signed", "pm")
        self.dr(ref="DR-001", issue="")
        self.ok("change", "approve", cid, "--approvers-signed", "pm", "--decision-ref", "DR-001")
        self.ok("change", "implement", cid)                       # cost 0: no budget row needed
        self.refused("verification_ref_present", "change", "verify", cid)
        self.ok("change", "verify", cid, "--ref", "TEST-9")
        self.assertEqual(self.state("changes", cid), "VERIFIED")

    def test_cost_change_needs_budget_update(self):
        cid = self.assessed(2000, 1)
        self.dr(ref="DR-001", issue="")
        self.ok("change", "approve", cid, "--approvers-signed", "pm", "--decision-ref", "DR-001")
        self.refused("budget_row_logged", "change", "implement", cid)
        from pmf.workspace import Workspace
        from pmf.schemas import SCHEMAS
        ws = Workspace(self.dir)
        row = {c: "" for c in SCHEMAS["budget"]["columns"]}
        row.update({"phase": "design", "budget": "100000", "updated": "2026-03-02"})
        ws.save("budget", [row])
        self.ok("change", "implement", cid)

    def test_reject_and_defer_need_reason(self):
        cid = self.assessed(100, 1)
        self.refused("reason_present", "change", "reject", cid)
        self.refused("reason_present", "change", "defer", cid)
        self.ok("change", "reject", cid, "--note", "out of scope")
        self.assertEqual(self.state("changes", cid), "REJECTED")


class GateFlow(WSData):
    def test_review_then_go(self):
        self.ok("gate", "review", "G1")
        self.refused("all_criteria_met", "gate", "go", "G1")
        self.refused("all_criteria_met", "gate", "go", "G1", "--criteria-met", "1;2")
        self.ok("gate", "go", "G1", "--criteria-met", "1;2;3")
        r = self.row("gates", "G1")
        self.assertEqual((r["state"], r["actual_date"]), ("GO", "2026-03-02"))

    def test_go_blocked_by_open_severity(self):
        iid = self.new_issue(sev=1)
        self.ok("gate", "review", "G4")
        self.refused("no_blocking_open_issues", "gate", "go", "G4", "--criteria-met", "1;2;3")
        self.assertIn(iid, self.refused("no_blocking_open_issues", "gate", "conditional", "G4", "--criteria-met", "1;2", "--waiver-refs", "DR-001"))

    def test_conditional_needs_signed_waiver_per_unmet_criterion(self):
        self.ok("gate", "review", "G1")
        self.refused("waiver_for_each_unmet_criterion", "gate", "conditional", "G1", "--criteria-met", "1;2")
        self.refused("waiver_for_each_unmet_criterion", "gate", "conditional", "G1", "--criteria-met", "1;2", "--waiver-refs", "DR-404")
        self.dr(ref="DR-001", issue="", signed="no")
        self.refused("waiver_for_each_unmet_criterion", "gate", "conditional", "G1", "--criteria-met", "1;2", "--waiver-refs", "DR-001")
        self.dr(ref="DR-001", issue="", signed="yes")
        self.ok("gate", "conditional", "G1", "--criteria-met", "1;2", "--waiver-refs", "DR-001")
        self.assertEqual(self.state("gates", "G1"), "CONDITIONAL_GO")
        self.ok("gate", "review", "G2")
        self.assertIn("use `gate go`", self.refused("waiver_for_each_unmet_criterion", "gate", "conditional", "G2", "--criteria-met", "1;2;3"))

    def test_nogo_needs_an_issue_per_unmet_criterion_then_rereview(self):
        self.ok("gate", "review", "G1")
        self.refused("issue_logged_for_each_unmet_criterion", "gate", "nogo", "G1", "--criteria-met", "1;2")
        self.ok("issue", "add", "--title", "Criterion 3 failed", "--gate-found", "G1")
        self.ok("gate", "nogo", "G1", "--criteria-met", "1;2")
        self.assertEqual(self.state("gates", "G1"), "NO_GO")
        self.refused("reason_present", "gate", "review", "G1")
        self.ok("gate", "review", "G1", "--note", "criterion 3 re-tested")
        self.assertEqual(self.state("gates", "G1"), "REVIEW")

    def test_gate_without_exit_criteria_cannot_enter_review(self):
        self.add_row("gates", id="G99", name="Unknown", phase="design", type="planned", state="PLANNED")
        self.refused("exit_criteria_listed", "gate", "review", "G99")

    def test_gate_cannot_skip_review(self):
        for verb in ("go", "conditional", "nogo"):
            self.assertIn("not allowed", self.refused(None, "gate", verb, "G1"))

    def test_issue_triggered_gate_rules(self):
        self.refused(None, "gate", "add", "--name", "Re-test", "--phase", "design")
        self.refused(None, "gate", "add", "--name", "Re-test", "--phase", "design", "--triggered-by", "I-404")
        iid = self.new_issue()
        self.ok("gate", "add", "--name", "Re-test", "--phase", "design", "--triggered-by", iid)
        g = self.rows("gates")[-1]
        self.assertEqual((g["type"], g["state"]), ("issue-triggered", "PLANNED"))
        self.assertTrue(g["id"].startswith("X-"))


class IllegalTransitionsEverywhere(WSData):
    """For every entity, every state, every verb the lifecycle does not allow from that state is refused."""

    def test_all_pairs(self):
        import json, os
        from helpers import ROOT
        from pmf.lifecycle import ENTITY_REGISTER
        from pmf.workspace import Workspace
        with open(os.path.join(ROOT, "pmf", "data", "lifecycles.json")) as f:
            lc = json.load(f)
        checked = 0
        for ent, spec in lc["entities"].items():
            reg = ENTITY_REGISTER[ent]
            verbs = sorted({t["command"].split(" ", 1)[1] for t in spec["transitions"]})
            for state in spec["states"]:
                allowed = {t["command"].split(" ", 1)[1] for t in spec["transitions"] if t["from"] == state}
                for verb in verbs:
                    if verb in allowed:
                        continue
                    ident = {"issue": "I-900", "risk": "R-900", "change": "C-900", "gate": "G1"}[ent]
                    if ent == "gate":
                        self.edit("gates", "G1", state=state)
                    else:
                        self.add_row(reg, id=ident, title="t", state=state) if not any(r["id"] == ident for r in Workspace(self.dir).load(reg)) else self.edit(reg, ident, state=state)
                    before = self.snapshot()
                    err = self.refused(None, ent, verb, ident, "--note", "x")
                    self.assertIn("not allowed", err, "%s %s from %s" % (ent, verb, state))
                    self.assertEqual(before, self.snapshot(), "%s %s from %s changed files" % (ent, verb, state))
                    checked += 1
        self.assertGreater(checked, 50)


if __name__ == "__main__":
    unittest.main()
