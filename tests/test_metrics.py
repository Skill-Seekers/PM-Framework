import unittest

from helpers import WSData


class ScheduleVariance(WSData):
    """Baseline 2026-01-05 .. 2026-12-18 = 347 days. 3% = 10.41 days, 8% = 27.76 days."""

    def last_gate(self, forecast, state="REVIEW", actual=""):
        self.edit("gates", "G9", baseline_date="2026-12-18", planned_date=forecast, state=state, actual_date=actual)

    def test_not_rated_without_dates(self):
        m, roll = self.health()
        self.assertEqual(m["sv"]["color"], "grey")
        self.assertEqual(roll["color"], "grey")

    def test_boundaries(self):
        cases = [("2026-12-18", "green"), ("2026-12-28", "green"),   # +10 days = 2.9%
                 ("2026-12-29", "amber"),                            # +11 days = 3.2%
                 ("2027-01-14", "amber"),                            # +27 days = 7.8%
                 ("2027-01-15", "red")]                              # +28 days = 8.1%
        for fc, want in cases:
            self.last_gate(fc)
            m, _ = self.health(report_date="2026-03-02")
            self.assertEqual(m["sv"]["color"], want, "%s -> %s" % (fc, m["sv"]))

    def test_ahead_of_baseline_is_green(self):
        self.last_gate("2026-12-01")
        m, _ = self.health()
        self.assertEqual(m["sv"]["color"], "green")

    def test_overdue_open_gate_is_red_even_if_last_gate_is_on_baseline(self):
        self.last_gate("2026-12-18")
        self.edit("gates", "G1", baseline_date="2026-02-01", planned_date="2026-02-01", state="PLANNED")
        m, _ = self.health(report_date="2026-03-02")
        self.assertEqual(m["sv"]["color"], "red")
        self.assertIn("overdue", " ".join(m["sv"]["detail"]))

    def test_completed_gate_uses_actual_date(self):
        self.last_gate("2026-12-18", state="GO", actual="2027-02-01")
        m, _ = self.health()
        self.assertEqual(m["sv"]["color"], "red")


class GateOnTime(WSData):
    def done(self, gid, baseline, actual):
        self.edit("gates", gid, baseline_date=baseline, actual_date=actual, state="GO")

    def test_not_rated_with_nothing_complete(self):
        self.assertEqual(self.health()[0]["gate"]["color"], "grey")

    def test_boundaries(self):
        # 10 completed gates would be needed for 90%; use the first 9 of silicon and 4 of 4 etc.
        ids = ["G1", "G2", "G3", "G4"]
        for g in ids:
            self.done(g, "2026-02-01", "2026-02-01")
        self.assertEqual(self.health()[0]["gate"]["color"], "green")   # 4/4
        self.done("G4", "2026-02-01", "2026-02-02")                     # 3/4 = 75% -> amber
        self.assertEqual(self.health()[0]["gate"]["color"], "amber")
        self.done("G3", "2026-02-01", "2026-02-02")                     # 2/4 = 50% -> red
        self.assertEqual(self.health()[0]["gate"]["color"], "red")

    def test_exactly_ninety_percent_is_green(self):
        for i in range(1, 10):
            self.done("G%d" % i, "2026-02-01", "2026-02-01")
        self.done("G9", "2026-02-01", "2026-02-02")                     # 8/9 = 88.9% -> amber
        self.assertEqual(self.health()[0]["gate"]["color"], "amber")

    def test_issue_triggered_gates_are_excluded(self):
        self.done("G1", "2026-02-01", "2026-02-01")
        self.add_row("gates", id="X-001", name="Extra", phase="design", type="issue-triggered", baseline_date="2026-02-01",
                     actual_date="2026-05-01", state="GO", triggered_by="I-001")
        self.assertEqual(self.health()[0]["gate"]["value"], "100%")


class IssueAging(WSData):
    def issue(self, ident, sev, detected, state="TRIAGED"):
        self.add_row("issues", id=ident, title=ident, phase="design", owner="Sam Lee", severity=sev, detected=detected, state=state)

    def test_sev1_boundaries(self):
        # report date 2026-03-02: age = days since detected. Sev 1: green <= 7, amber <= 14.
        for detected, want in (("2026-02-23", "green"), ("2026-02-22", "amber"), ("2026-02-16", "amber"), ("2026-02-15", "red")):
            self.edit("issues", "I-001", detected=detected) if False else None
            self.tearDownIssues()
            self.issue("I-001", 1, detected)
            self.assertEqual(self.health()[0]["aging"]["color"], want, detected)

    def tearDownIssues(self):
        from pmf.workspace import Workspace
        ws = Workspace(self.dir)
        ws.save("issues", [])

    def test_sev2_limits_are_14_and_28(self):
        self.issue("I-001", 2, "2026-02-16")      # 14 days -> green
        self.assertEqual(self.health()[0]["aging"]["color"], "green")
        self.edit("issues", "I-001", detected="2026-02-15")   # 15 days -> amber
        self.assertEqual(self.health()[0]["aging"]["color"], "amber")
        self.edit("issues", "I-001", detected="2026-01-31")   # 30 days -> red
        self.assertEqual(self.health()[0]["aging"]["color"], "red")

    def test_sev3_and_closed_issues_do_not_age(self):
        self.issue("I-001", 3, "2025-01-01")
        self.issue("I-002", 1, "2025-01-01", state="CLOSED")
        self.issue("I-003", 1, "2025-01-01", state="RESOLVED")
        self.assertEqual(self.health()[0]["aging"]["color"], "green")

    def test_deferred_is_not_open(self):
        self.issue("I-001", 1, "2025-01-01", state="DEFERRED")
        self.assertEqual(self.health()[0]["aging"]["color"], "green")


class EscapeRate(WSData):
    def phase_issues(self, n, escaped, phase="design"):
        from pmf.workspace import Workspace
        ws = Workspace(self.dir)
        rows = []
        for i in range(n):
            rows.append({"id": "I-%03d" % (i + 1), "title": "t", "phase": phase, "state": "LOGGED", "severity": "3",
                         "escape_gate": "G2" if i < escaped else ""})
        from pmf.schemas import SCHEMAS
        full = []
        for r in rows:
            x = {c: "" for c in SCHEMAS["issues"]["columns"]}
            x.update(r)
            full.append(x)
        ws.save("issues", full)

    def test_under_minimum_not_rated(self):
        self.phase_issues(2, 2)
        self.assertEqual(self.health()[0]["escape"]["color"], "grey")

    def test_boundaries(self):
        for n, esc, want in ((10, 0, "green"), (11, 1, "green"),    # 9.1%
                             (10, 1, "amber"),                       # 10% is not under 10
                             (5, 1, "amber"),                        # 20% is amber
                             (9, 2, "red"),                          # 22%
                             (4, 1, "red"), (3, 1, "red")):          # 25% / 33%
            self.phase_issues(n, esc)
            self.assertEqual(self.health()[0]["escape"]["color"], want, "%d/%d" % (esc, n))


class BurnRatio(WSData):
    def budget(self, planned, actual, forecast, budget="500000"):
        self.add_row("budget", phase="design", budget=budget, planned_to_date=planned, actual_to_date=actual, forecast_at_completion=forecast)

    def test_boundaries(self):
        cases = [(1000, 900, "green"), (1000, 1100, "green"), (1000, 1101, "amber"), (1000, 1250, "amber"),
                 (1000, 1251, "red"), (1000, 899, "amber"), (1000, 100, "amber")]
        for planned, actual, want in cases:
            from pmf.workspace import Workspace
            Workspace(self.dir).save("budget", [])
            self.budget(planned, actual, 400000)
            self.assertEqual(self.health()[0]["burn"]["color"], want, "%s/%s" % (actual, planned))

    def test_forecast_over_budget_is_red_even_with_good_ratio(self):
        self.budget(1000, 1000, 500001)
        self.assertEqual(self.health()[0]["burn"]["color"], "red")

    def test_no_rows_not_rated(self):
        self.assertEqual(self.health()[0]["burn"]["color"], "grey")


class Rollup(WSData):
    def test_worst_of_not_average(self):
        self.add_row("budget", phase="design", budget="500000", planned_to_date="1000", actual_to_date="1000", forecast_at_completion="400000")
        self.add_row("issues", id="I-001", title="t", phase="design", owner="Sam Lee", severity="1", detected="2026-01-01", state="TRIAGED")
        m, roll = self.health()
        self.assertEqual(m["burn"]["color"], "green")
        self.assertEqual(roll["color"], "red")
        self.assertIn("Issue Aging", roll["reason"])

    def test_grey_is_never_counted_green(self):
        m, roll = self.health()
        self.assertEqual(roll["color"], "grey")


if __name__ == "__main__":
    unittest.main()
