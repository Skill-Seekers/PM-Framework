"""The HTML dashboard: read-only, self-contained, escaped, deterministic, and legible in both colour modes."""
import os
import re
import unittest

from helpers import ROOT, WS, run
from pmf import dashboard


def _lum(hexcolor):
    h = hexcolor.lstrip("#")
    ch = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a, b):
    la, lb = sorted([_lum(a), _lum(b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


class Palette(unittest.TestCase):
    def test_text_inside_risk_cells_is_readable(self):
        for mode, p in dashboard.PALETTE.items():
            for fill, ink in zip(p["hb"], p["hb_ink"]):
                self.assertGreaterEqual(contrast(fill, ink), 4.5, "%s %s on %s" % (mode, ink, fill))

    def test_marks_clear_three_to_one_on_the_surface(self):
        for mode, p in dashboard.PALETTE.items():
            self.assertGreaterEqual(contrast(p["s1"], p["surface"]), 3.0, mode)
            self.assertGreaterEqual(contrast(dashboard.STATUS["critical"], p["surface"]), 3.0, mode)

    def test_body_text_clears_four_and_a_half(self):
        for mode, p in dashboard.PALETTE.items():
            self.assertGreaterEqual(contrast(p["ink"], p["surface"]), 4.5, mode)
            self.assertGreaterEqual(contrast(p["ink2"], p["surface"]), 4.5, mode)

    def test_every_status_icon_glyph_is_visible_on_its_fill(self):
        fills = {"green": ("#0ca30c", "#ffffff"), "amber": ("#fab219", "#0b0b0b"), "red": ("#d03b3b", "#ffffff")}
        for name, (fill, glyph) in fills.items():
            self.assertGreaterEqual(contrast(fill, glyph), 3.0, name)


class Meridian(unittest.TestCase):
    def setUp(self):
        self.ws = os.path.join(ROOT, "examples", "meridian", "workspace")
        self._old = {k: os.environ.get(k) for k in ("PMF_WORKSPACE", "PMF_FAKE_NOW")}
        os.environ["PMF_WORKSPACE"] = self.ws
        os.environ["PMF_FAKE_NOW"] = "2026-07-03T15:00:00Z"
        self.addCleanup(self._restore)

    def _restore(self):
        for k, v in self._old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def page(self):
        rc, out, err = run(["dashboard", "--stdout"])
        self.assertEqual(rc, 0, err)
        return out

    def test_content(self):
        h = self.page()
        for want in ("Meridian-1 AI Accelerator", "Amber", "Schedule Variance", "G4", "Design Freeze", "I-008", "R-003",
                     "Table view of every chart", "+14 days late", "85K over budget"):
            self.assertIn(want, h)

    def test_self_contained_and_read_only(self):
        h = self.page()
        self.assertNotRegex(h, r"(?i)<script")
        self.assertNotRegex(h, r"(?i)https?://")
        self.assertNotRegex(h, r"(?i)<(link|img|iframe|form|input|button)\b")
        self.assertNotRegex(h, r"(?i)\bon[a-z]+=")

    def test_status_is_never_colour_alone(self):
        h = self.page()
        chips = re.findall(r'<span class="chip[^"]*st-\w+">(<svg.*?</svg>)<span>([A-Za-z ]+)</span></span>', h)
        self.assertGreaterEqual(len(chips), 6)
        self.assertEqual(len(chips), h.count('<span class="chip'))

    def test_both_colour_modes_and_a_theme_override(self):
        h = self.page()
        self.assertIn("prefers-color-scheme:dark", h)
        self.assertIn('[data-theme="dark"]', h)
        self.assertIn('[data-theme="light"]', h)

    def test_deterministic(self):
        self.assertEqual(self.page(), self.page())

    def test_every_rolled_up_metric_appears(self):
        h = self.page()
        for name in ("Schedule Variance", "Gate On-Time Rate", "Issue Aging", "Escape Rate", "Budget Burn Ratio"):
            self.assertEqual(h.count("<h3>%s</h3>" % name), 1, name)


class Fresh(WS):
    def test_empty_workspace_renders_and_is_not_rated(self):
        out = self.ok("dashboard", "--stdout")
        self.assertIn("Not rated", out)
        self.assertIn("No open Sev 1 or Sev 2 issues.", out)
        self.assertIn("No open risks.", out)

    def test_text_from_the_registers_is_escaped(self):
        self.ok("issue", "add", "--title", "<script>alert(1)</script> & \"quotes\"", "--phase", "design", "--owner", "<b>Avery</b>",
                "--severity", "1", "--detected", "2026-03-01")
        h = self.ok("dashboard", "--stdout")
        self.assertNotIn("<script>alert(1)", h)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", h)
        self.assertNotIn("<b>Avery</b>", h)

    def test_writes_the_dated_file_and_is_idempotent(self):
        out = self.ok("dashboard")
        self.assertIn("created reports/dashboard_2026-03-02.html", out)
        self.assertTrue(os.path.exists(self.path("reports", "dashboard_2026-03-02.html")))
        self.assertIn("unchanged", self.ok("dashboard"))

    def test_regenerates_when_the_data_changes(self):
        self.ok("dashboard")
        self.ok("issue", "add", "--title", "Late clock spec", "--phase", "design", "--owner", "Avery", "--severity", "2",
                "--detected", "2026-03-01")
        self.assertIn("updated reports/dashboard_2026-03-02.html", self.ok("dashboard"))
        self.assertIn("Late clock spec", self.read("reports/dashboard_2026-03-02.html"))

    def test_dry_run_and_stdout_write_nothing(self):
        before = self.snapshot()
        self.ok("dashboard", "--dry-run")
        self.ok("dashboard", "--stdout")
        self.assertEqual(before, self.snapshot())

    def test_out_path(self):
        target = os.path.join(self.tmp, "elsewhere.html")
        self.ok("dashboard", "--out", target)
        self.assertTrue(os.path.exists(target))
        self.assertFalse(os.path.exists(self.path("reports", "dashboard_2026-03-02.html")))

    def test_never_changes_a_register(self):
        before = self.snapshot()
        self.ok("dashboard")
        after = self.snapshot()
        changed = [k for k in after if k in before and before[k] != after[k]]
        self.assertEqual(changed, [])


class SoftwareFresh(WS):
    PROFILE = "software"

    def test_software_profile_renders(self):
        out = self.ok("dashboard", "--stdout")
        self.assertIn("<html", out)
        self.assertIn("Not rated", out)


if __name__ == "__main__":
    unittest.main()
