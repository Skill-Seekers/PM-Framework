#!/usr/bin/env python3
"""Build docs/explainer.html: five visual views of the framework on one self-contained page.

Facts come from the repository, not from this script: phases, gates and thresholds from profiles/silicon.json,
the artifact lists from framework/modules/04, gates and phases from module 01, states and commands from
pmf/data/lifecycles.json. Only the pictures' layout and the short captions live here.

  python3 tools/gen_explainer.py            write docs/explainer.html
  python3 tools/gen_explainer.py --check    exit 1 if the committed page differs from a fresh build

Standard library only (Python 3.8+). No scripts, no external resources: it opens from disk, in a mail, in print.
"""
import html
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import gen_diagrams  # noqa: E402
from pmf import __version__, dashboard  # noqa: E402

OUT = os.path.join(ROOT, "docs", "explainer.html")
MOD = "../framework/modules/"

SW_TRACK = ["Early SW architecture", "SW requirements and security", "Dev plan, CI/CD", "Virtual platform, FPGA dev",
            "Pre-silicon validation", "FW and driver code freeze", "FW and BMC bring-up", "Platform enablement",
            "Production FW, OTA updates"]
PHASE_ARTIFACTS = [
    "Feasibility Study, Make-vs-Buy Analysis, Rough NRE Estimate",
    "PRD/MRD, SW Requirements Spec, RACI Matrix and Gate Calendar (4.3)",
    "Program Schedule Baseline, Budget/NRE Baseline, Risk Register (4.3)",
    "Phase Gate Exit Criteria Checklist, Design Review Findings Log (4.2)",
    "Verification/Compliance Report, Coverage Closure Report, Rule-Check Report (4.2)",
    "Release Readiness Sign-off Package, Waiver Documents, if any (4.5)",
    "Gate Review Meeting Minutes, Bring-Up Test Plan, Bug Report/Fix Summary (4.2, 4.3)",
    "Regression/Re-run Report, Qualification Test Report, Customer Sign-off (4.4, 4.5)",
    "Revised Program Schedule, Sustain Handoff Doc, Lessons Learned (4.6)",
]
# Illustrative 24-month view: per phase (hw_left, hw_width, sw_left, sw_width, gate_left) in percent of 24 months.
GANTT = [(0.00, 4.17, 0.00, 4.17, 4.17), (4.17, 8.33, 4.17, 8.33, 12.50), (12.50, 8.33, 8.33, 12.50, 20.83),
         (20.83, 25.00, 16.67, 29.17, 45.83), (41.67, 16.67, 37.50, 20.83, 58.33), (58.33, 4.17, 58.33, 4.17, 62.50),
         (62.50, 8.33, 62.50, 12.50, 70.83), (70.83, 12.50, 70.83, 16.67, 83.33), (83.33, 8.33, 83.33, 12.50, 91.67)]
STAGE_TOOL = [("DETECTED", "pmf issue add"), ("LOGGED", "pmf issue log"), ("TRIAGED", "pmf issue triage"),
              ("DECIDED, RESOLVED or DEFERRED", "pmf issue decide, resolve, defer"), ("CLOSED", "pmf issue close")]
PLC_SEQUENCE = [("p", 0), ("p", 1), ("g", "Kickoff"), ("p", 2), ("g", "Requirements Freeze"), ("g", "Design Freeze"), ("p", 3),
                ("g", "Release Readiness"), ("p", 4), ("p", 5), ("g", "Beta Exit"), ("p", 6), ("g", "GA / Qualification Exit"),
                ("g", "Production / Sustain Handoff"), ("p", 7)]


def e(t):
    return html.escape("" if t is None else str(t), quote=True)


def read(rel):
    with io.open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def md_table_after(text, heading):
    """Rows (list of cell lists, header and rule skipped) of the first markdown table after a heading line."""
    lines = text.split("\n")
    start = next(i for i, l in enumerate(lines) if l.strip() == heading)
    rows, seen = [], False
    for l in lines[start + 1:]:
        if l.startswith("|"):
            seen = True
            cells = [c.strip() for c in l.strip().strip("|").split("|")]
            rows.append(cells)
        elif seen:
            break
    return rows[2:]


def stages():
    out = []
    cur = None
    for l in read("framework/modules/04_artifacts_by_stage.md").split("\n"):
        m = re.match(r"^## 4\.\d+ Stage (\d) — (.+)$", l)
        if m:
            cur = {"n": int(m.group(1)), "title": m.group(2), "artifacts": []}
            out.append(cur)
            continue
        if l.startswith("## "):
            cur = None
        if cur is not None:
            a = re.match(r"^\| \*\*(.+?)\*\* \|", l)
            if a:
                cur["artifacts"].append(a.group(1))
    return out


# ------------------------------------------------------------------ sections
def sec_shape():
    cards = [
        ("Governance", "Module 01", ["RACI matrix", "Gate calendar", "Phase-gate exit criteria", "Kickoff RACI announcement"],
         [("01", "01_lifecycle_and_governance.md")]),
        ("Execution", "Modules 02 to 07, and 10", ["Issue register and RAID log, with risk scoring", "The five-step issue flow (view 3)",
                                                  "Weekly status, customer email, gate go/no-go", "Budget burn-down and change-order log",
                                                  "Capacity and consensus across programs"],
         [("02", "02_issue_management.md"), ("03", "03_raid_vs_issue_register.md"), ("04", "04_artifacts_by_stage.md"),
          ("05", "05_communication_cadence.md"), ("06", "06_communication_templates.md"), ("07", "07_budget_and_scope_control.md"),
          ("10", "10_cross_program_coordination.md")]),
        ("Measurement and automation", "Modules 08 and 09", ["Five metrics (view 5)", "Worst-of rollup, never averaged", "AI prompt library: it drafts, the PM decides"],
         [("08", "08_program_metrics_and_health.md"), ("09", "09_ai_augmented_workflow.md")]),
    ]
    out = ['<section id="shape"><p class="eyebrow">View 1</p><h2>The shape of the framework</h2>'
           '<p class="lead">Governance sets the rules everyone plays by. Execution is the weekly work: issues, RAID, communication, budget. '
           'Measurement and automation is how you know it is working and how you stop hand-building every document. Say it in that order and the framework explains itself.</p>'
           '<div class="trio">']
    for title, mods, items, links in cards:
        out.append('<article class="card"><h3>%s</h3><p class="muted">%s</p><ul>%s</ul><p class="links">%s</p></article>' % (
            e(title), e(mods), "".join("<li>%s</li>" % e(i) for i in items),
            " ".join('<a href="%s%s">Module %s</a>' % (MOD, f, n) for n, f in links)))
    out.append("</div></section>")
    return "".join(out)


def sec_asic(profile):
    phases, gates = profile["phases"], profile["gates"]
    gate_of = {g["phase"]: g for g in gates}
    assert len(phases) == 9 and len(SW_TRACK) == 9 and len(GANTT) == 9 and len(PHASE_ARTIFACTS) == 9
    out = ['<section id="asic"><p class="eyebrow">View 2</p><h2>A nine-phase silicon program</h2>'
           '<p class="lead">The generic lifecycle unpacked one level, the way a real silicon program runs it: hardware and software/firmware as two parallel tracks against the same nine phases, '
           'with one planned gate at the end of each phase. These are the phases and gates of the shipped <code>silicon</code> profile.</p><div class="card"><ol class="rail">']
    for i, ph in enumerate(phases):
        g = gate_of[ph["id"]]
        out.append('<li><div class="trk hw"><span class="tl">HW</span>%d. %s</div><div class="trk sw"><span class="tl">SW/FW</span>%s</div>'
                   '<div class="gate"><span class="dia"></span><span><b>%s</b> %s</span></div></li>' % (
                       i + 1, e(ph["name"]), e(SW_TRACK[i]), e(g["id"]), e(g["name"])))
    out.append("</ol>")
    out.append('<p class="callout">Both tracks hard-stop together exactly once, at <b>Tape Out</b>. Hardware\'s stop is absolute: the layout is released to the foundry and no further RTL or layout change is physically possible. '
               'Firmware freezes in lockstep, because that image is what goes onto first silicon. Everywhere else software and firmware keep developing against the frozen spec while hardware moves through fab, and hardware often starts early feasibility work during Planning. '
               'The tracks converge again at <b>Bring-Up</b>, the first time firmware runs on real silicon.</p>')
    # quarterly view
    out.append('<h3 class="sub">Illustrative 24-month view</h3><p class="muted">A general picture, not a schedule: durations and overlaps are illustrative. A bar that starts before the previous gate is early work bleeding across a phase boundary, not a hard start. Each diamond is the gate that closes its phase.</p>'
               '<div class="gscroll"><div class="gantt"><div class="gh"></div>')
    for q in range(8):
        out.append('<div class="gh q" style="grid-column:%d / %d">Q%dY%d</div>' % (2 + q * 3, 5 + q * 3, q % 4 + 1, q // 4 + 1))
    for i, ph in enumerate(phases):
        hl, hw, sl, sw, gl = GANTT[i]
        alt = " alt" if i % 2 == 0 else ""
        label = "%d. %s" % (i + 1, ph["name"])
        gname = gate_of[ph["id"]]["name"]
        after = max(gl, hl + hw, sl + sw) + 1.2
        if after < 66:
            lab_style = "left:%.1f%%" % after
        else:       # no room to the right of the bars: put the label to their left
            lab_style = "left:auto;right:%.1f%%;text-align:right" % (100 - min(hl, sl) + 1.2)
        out.append('<div class="gl">%s</div><div class="gt%s" style="grid-column:2 / 26" title="%s"><span class="bar hw" style="left:%.2f%%;width:%.2f%%"></span>'
                   '<span class="bar sw" style="left:%.2f%%;width:%.2f%%"></span><span class="gdot" style="left:%.2f%%"></span><span class="glab" style="%s">%s</span></div>' % (
                       e(label), alt, e("%s: gate %s" % (label, gname)), hl, hw, sl, sw, gl, lab_style, e(gname)))
    out.append('<div class="gl respin">If silicon needs a re-spin</div><div class="gt respinrow" style="grid-column:2 / 26"><span class="bar respin" style="left:70.83%;width:16.67%"></span>'
               '<span class="glab" style="left:auto;right:29.9%;text-align:right">ECR/ECO decision</span><span class="glab" style="left:auto;right:1%;text-align:right">Rev B first boot</span></div></div></div>')
    out.append('<p class="muted">Dashed row: an optional branch, not the default path. If Bring-Up finds a hardware defect that firmware cannot work around, it goes through the same ECR/ECO triage as any other issue. '
               'The fix runs a compressed Tape Out, fab and Bring-Up cycle as <b>Rev B</b>, while Testing keeps running on <b>Rev A</b> for everything the defect does not block.</p>')
    out.append('<p class="legend"><span class="key"><span class="swt hw"></span> Hardware</span><span class="key"><span class="swt sw2"></span> Software / firmware</span>'
               '<span class="key"><span class="dia sm"></span> Gate</span><span class="key"><span class="swt rs"></span> Re-spin, if required</span></p>')
    out.append('<div class="wrap"><table><caption>Phase, gate and key artifacts</caption><thead><tr><th>#</th><th>Phase</th><th>Gate</th><th>Key artifacts (Module 04)</th></tr></thead><tbody>')
    for i, ph in enumerate(phases):
        g = gate_of[ph["id"]]
        out.append("<tr><td>%d</td><td>%s</td><td>%s %s</td><td>%s</td></tr>" % (i + 1, e(ph["name"]), e(g["id"]), e(g["name"]), e(PHASE_ARTIFACTS[i])))
    out.append('</tbody></table></div>')
    out.append('<p class="links">Source: <a href="%s01_lifecycle_and_governance.md">Module 01</a> section 1.6 and <a href="%s04_artifacts_by_stage.md">Module 04</a>. '
               'The same flow in the tool is in the <a href="../examples/meridian/walkthrough/SEV1_WALKTHROUGH.md">Meridian walkthrough</a>.</p></div></section>' % (MOD, MOD))
    return "".join(out)


def sec_issue(lc):
    st = stages()
    assert len(st) == 5 and len(STAGE_TOOL) == 5
    cmds = set(t["command"] for t in lc["entities"]["issue"]["transitions"])
    for _, c in STAGE_TOOL:
        for word in c.replace("pmf ", "").replace(",", " ").split():
            if word not in ("issue",) and ("issue " + word) not in cmds and word not in ("add",):
                raise SystemExit("explainer names a command that is not in lifecycles.json: %s" % word)
    out = ['<section id="issue"><p class="eyebrow">View 3</p><h2>Issue flow and artifacts</h2>'
           '<p class="lead">Five steps, no skipping, for every issue from a minor snag to a Sev 1. Each box is Module 02\'s step joined to Module 04\'s list of what you produce at that step, '
           'and to the state and command that enforce it in the tool.</p><div class="card"><ol class="stages">']
    for s, (state, cmd) in zip(st, STAGE_TOOL):
        title = s["title"].split(" (")[0]
        out.append('<li class="stage s%d"><h3><span class="n">%d</span> %s</h3><ul>%s</ul><p class="tool"><span>State</span> %s<br><span>Command</span> <code>%s</code></p></li>' % (
            s["n"], s["n"], e(title), "".join("<li>%s</li>" % e(a) for a in s["artifacts"]), e(state), e(cmd)))
    out.append('</ol><p class="callout">The Decision Record (step 5) is the artifact most PMs skip, and the one that protects you three months later when someone asks why a waiver was accepted. See Module 04, section 4.7.</p>')
    out.append('<h3 class="sub">The same flow as a state machine</h3><div class="diag">%s</div>' % gen_diagrams.render(lc, "issue"))
    out.append('<p class="links">Sources: <a href="%s02_issue_management.md">Module 02</a>, <a href="%s04_artifacts_by_stage.md">Module 04</a>, and <a href="diagrams/lifecycles.html">all four lifecycles</a> with their guards.</p></div></section>' % (MOD, MOD))
    return "".join(out)


def sec_plc():
    m1 = read("framework/modules/01_lifecycle_and_governance.md")
    phases = md_table_after(m1, "## 1.2 The generic program lifecycle")
    gates = dict((r[0], r[1]) for r in md_table_after(m1, "### Planned gates"))
    if len(phases) != 8 or len(gates) != 7:
        raise SystemExit("module 01 no longer has 8 phases and 7 planned gates")
    for kind, v in PLC_SEQUENCE:
        if kind == "g" and v not in gates:
            raise SystemExit("explainer names a gate that module 01 does not: %s" % v)
    out = ['<section id="plc"><p class="eyebrow">View 4</p><h2>The program lifecycle and its gates</h2>'
           '<p class="lead">The eight-phase spine everything else hangs off (PLC is Program Life Cycle, not Product Life Cycle). The diamonds are the seven planned gates: calendar events the customer signs off on in the SOW, never surprises. '
           'Profiles may be finer-grained; the shipped <code>silicon</code> profile has nine gates (view 2).</p><div class="card"><ol class="plc">']
    for kind, v in PLC_SEQUENCE:
        if kind == "p":
            out.append('<li class="ph"><b>%d. %s</b><span>%s</span></li>' % (v + 1, e(phases[v][1]), e(phases[v][2])))
        else:
            out.append('<li class="gt2"><span class="dia"></span><b>%s</b></li>' % e(v))
    out.append('</ol><div class="wrap"><table><caption>Planned gates and exit criteria</caption><thead><tr><th>Gate</th><th>Exit criteria</th></tr></thead><tbody>')
    for g, c in gates.items():
        out.append("<tr><td>%s</td><td>%s</td></tr>" % (e(g), e(c)))
    out.append('</tbody></table></div><p class="callout">Planned gates are calendar events. <b>Issue-triggered gates</b> (not shown) are the opposite: unscheduled, forced by a Sev 1 out of the issue flow. '
               'Mixing the two in status reporting is how executives lose the ability to tell "on plan" from "in crisis".</p>')
    out.append('<p class="links">Source: <a href="%s01_lifecycle_and_governance.md">Module 01</a> sections 1.2 and 1.4. Gate placement is the typical one implied by each gate\'s exit criteria; adjust to your own gate calendar.</p></div></section>' % MOD)
    return "".join(out)


def sec_health(profile):
    m = profile["metrics"]
    sev = dict((l["level"], l) for l in profile["severity"]["levels"])
    a1, a2 = sev[1]["aging_days"], sev[2]["aging_days"]
    g, a = m["burn_ratio"]["green"], m["burn_ratio"]["amber_high"]
    cards = [
        ("Schedule Variance", "Forecast or actual date of the last planned gate, minus its baseline date, as a share of the baseline duration",
         [("green", "%s%% behind or less (or ahead)" % m["schedule_variance"]["green_max_pct"]), ("amber", "up to %s%% behind" % m["schedule_variance"]["amber_max_pct"]),
          ("red", "more than %s%% behind, or any open gate past its planned date" % m["schedule_variance"]["amber_max_pct"])]),
        ("Gate On-Time Rate", "Completed gates passed on or before baseline, over completed gates",
         [("green", "%s%% or more" % m["gate_on_time"]["green_min_pct"]), ("amber", "%s%% to %s%%" % (m["gate_on_time"]["amber_min_pct"], m["gate_on_time"]["green_min_pct"] - 1)),
          ("red", "under %s%%" % m["gate_on_time"]["amber_min_pct"])]),
        ("Issue Aging", "Days each open Sev 1 and Sev 2 issue has been open, against its limits",
         [("green", "Sev 1 up to %d days, Sev 2 up to %d" % (a1["green_max"], a2["green_max"])), ("amber", "Sev 1 up to %d, Sev 2 up to %d" % (a1["amber_max"], a2["amber_max"])),
          ("red", "Sev 1 over %d, Sev 2 over %d" % (a1["amber_max"], a2["amber_max"]))]),
        ("Escape Rate", "Issues found later than the gate that should have caught them, over all issues, per phase",
         [("green", "under %s%%" % m["escape_rate"]["green_max_pct"]), ("amber", "%s%% to %s%%" % (m["escape_rate"]["green_max_pct"], m["escape_rate"]["amber_max_pct"])),
          ("red", "over %s%%" % m["escape_rate"]["amber_max_pct"])]),
        ("Budget Burn Ratio", "Actual spend over planned spend, to date",
         [("green", "%s to %s" % (g[0], g[1])), ("amber", "%s to %s, or below %s" % (g[1], a, g[0])), ("red", "over %s, or forecast over budget" % a)]),
    ]
    out = ['<section id="health"><p class="eyebrow">View 5</p><h2>Program health metrics</h2>'
           '<p class="lead">"Status: Amber" means nothing without a rule behind it. Five metrics, each with defined green, amber and red limits, make a status defensible instead of a gut call. '
           'A metric with too little data is shown as not rated, never as green.</p><div class="card"><div class="metrics">']
    for name, formula, rows in cards:
        out.append('<article class="metric"><h3>%s</h3><p class="muted">%s</p><ul>%s</ul></article>' % (
            e(name), e(formula), "".join("<li>%s <span>%s</span></li>" % (dashboard.chip(c), e(t)) for c, t in rows)))
    out.append('</div><p class="rollup">Program status = the worst of the five, never an average</p>'
               '<p class="muted">One red metric makes the whole program red whatever the other four say. Averaging is how a program hides one bad number behind four good ones.</p>'
               '<p class="links">Sources: <a href="%s08_program_metrics_and_health.md">Module 08</a> and <a href="../docs/DATA_SCHEMAS.md#metric-definitions">the metric definitions</a>. '
               'The numbers above come from the <code>silicon</code> profile; <code>pmf health</code> computes them and <code>pmf dashboard</code> draws them.</p></div></section>' % MOD)
    return "".join(out)


CSS = """
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1040px;margin:0 auto;padding:16px 16px 64px}
header.top{padding:20px 0 8px}
h1{font-size:26px;line-height:1.25;margin:0}
h2{font-size:21px;margin:0 0 6px;border-left:4px solid var(--s1);padding-left:10px}
h3{font-size:15px;margin:0 0 6px}
h3.sub{margin:22px 0 2px}
section{margin-top:44px;scroll-margin-top:60px}
nav.toc{position:sticky;top:0;z-index:5;background:var(--page);border-bottom:1px solid var(--border);display:flex;gap:4px 16px;flex-wrap:wrap;padding:8px 0;font-size:14px}
nav.toc a{color:var(--ink);text-decoration:none;font-weight:600;padding:2px 0}
nav.toc a:hover{text-decoration:underline}
a{color:var(--link)}
.eyebrow{margin:0 0 2px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:var(--ink2)}
.lead{color:var(--ink2);margin:4px 0 14px}
.muted{color:var(--ink2);font-size:14px;margin:4px 0 8px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:18px}
.trio{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}
.trio .card ul{margin:6px 0;padding-left:18px}
.links{font-size:14px;color:var(--ink2);margin:10px 0 0}.trio .links a{margin-right:10px;white-space:nowrap}
.callout{background:var(--grid);border-radius:10px;padding:10px 14px;font-size:14px;margin:14px 0}
code{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--grid);padding:1px 5px;border-radius:5px}
.dia{display:inline-block;width:14px;height:14px;background:var(--surface);border:2px solid var(--ink);transform:rotate(45deg);border-radius:3px;flex:none}
.dia.sm{width:10px;height:10px;margin:0 3px}
ol,ul{margin:0}
/* rail */
.rail{list-style:none;padding:0;display:grid;grid-template-columns:repeat(9,minmax(0,1fr));gap:8px}
.rail li{display:flex;flex-direction:column;gap:6px}
.trk{border-radius:8px;padding:6px 8px;font-size:13px;line-height:1.3;border:1.5px solid}
.trk .tl{display:block;font-size:10.5px;font-weight:700;letter-spacing:.05em;color:var(--ink2)}
.trk.hw{border-color:var(--s1);background:var(--s1-track);color:var(--ink);font-weight:600}
.trk.sw{border-color:var(--sw);background:var(--sw-bg);color:var(--ink)}
.gate{display:flex;gap:8px;align-items:flex-start;font-size:12.5px;line-height:1.3;padding:2px 2px}.gate .dia{margin-top:3px}
@media (max-width:900px){.rail{grid-template-columns:1fr}.rail li{flex-direction:row;flex-wrap:wrap;align-items:stretch;border-top:1px solid var(--grid);padding-top:8px}.rail .trk{flex:1 1 180px}.rail .gate{flex:1 1 100%}}
/* gantt */
.gscroll{overflow-x:auto}
.gantt{min-width:760px;display:grid;grid-template-columns:150px repeat(24,1fr);font-size:12px}
.gh{padding:3px 0;text-align:center;font-weight:700;color:var(--ink2);background:var(--grid);border-bottom:1px solid var(--axis)}
.gh.q{border-left:1px solid var(--axis)}
.gl{display:flex;align-items:center;padding:0 8px 0 2px;border-top:1px solid var(--grid);font-weight:600}
.gl.respin{font-style:italic;font-weight:500;color:var(--ink2)}
.gt{position:relative;height:34px;border-top:1px solid var(--grid)}.gt.alt{background:color-mix(in srgb,var(--grid) 45%,transparent)}
.gt.respinrow{height:30px}
.bar{position:absolute;height:9px;border-radius:2px}
.bar.hw{top:5px;background:var(--s1)}.bar.sw{top:18px;background:var(--sw)}
.bar.respin{top:11px;border:1.5px dashed var(--ink);height:11px}
.gdot{position:absolute;top:2px;width:9px;height:9px;background:var(--ink);transform:translateX(-50%) rotate(45deg);border-radius:2px}
.glab{position:absolute;top:0;line-height:34px;font-size:11px;color:var(--ink2);white-space:nowrap}
.respinrow .glab{line-height:30px}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:13px;color:var(--ink2);margin:12px 0 0}
.key{display:inline-flex;align-items:center;gap:6px}
.swt{display:inline-block;width:16px;height:9px;border-radius:2px}
.swt.hw{background:var(--s1)}.swt.sw2{background:var(--sw)}.swt.rs{border:1.5px dashed var(--ink);height:11px}
/* tables */
.wrap{overflow-x:auto;margin-top:14px}
table{border-collapse:collapse;width:100%;font-size:14px}
caption{text-align:left;font-weight:600;padding:0 0 6px}
th,td{padding:6px 10px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:top}
th{font-size:12px;color:var(--ink2);font-weight:600}
td:first-child{white-space:nowrap}
/* stages */
.stages{list-style:none;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px}
.stage{border:1px solid var(--border);border-top:4px solid var(--s1);border-radius:10px;padding:10px 12px;font-size:13.5px;position:relative;background:var(--surface)}
.stage h3{font-size:14px}.stage .n{display:inline-flex;width:22px;height:22px;border-radius:50%;background:var(--ink);color:var(--surface);align-items:center;justify-content:center;font-size:12px;margin-right:4px}
.stage ul{margin:6px 0;padding-left:16px}.stage li{margin:2px 0}
.tool{margin:8px 0 0;font-size:12.5px;border-top:1px solid var(--grid);padding-top:6px;color:var(--ink2)}.tool span{font-weight:700;color:var(--ink);font-size:11px;text-transform:uppercase;letter-spacing:.04em;margin-right:4px}
@media (max-width:900px){.stages{grid-template-columns:1fr}}
.diag{overflow-x:auto;border:1px solid var(--border);border-radius:10px;margin-top:8px}.diag svg{display:block;min-width:1200px;width:100%;height:auto}
/* plc */
.plc{list-style:none;padding:0;margin:0 0 6px;display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.ph{border:1.5px solid var(--s1);background:var(--s1-track);border-radius:10px;padding:6px 10px;font-size:13px;line-height:1.3;max-width:200px}.ph span{display:block;color:var(--ink2);font-size:12px}
.gt2{display:flex;align-items:center;gap:8px;font-size:12.5px;line-height:1.25;max-width:120px;padding:0 4px}
/* metrics */
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}
@media (min-width:1000px){.metrics{grid-template-columns:repeat(5,minmax(0,1fr))}}
.metric{border:1px solid var(--border);border-radius:10px;padding:10px 12px;background:var(--surface)}
.metric ul{list-style:none;padding:0;margin:8px 0 0}.metric li{display:flex;flex-direction:column;align-items:flex-start;gap:3px;margin:8px 0;font-size:13.5px}
.chip{display:inline-flex;align-items:center;gap:6px;padding:2px 9px 2px 6px;border:1px solid var(--axis);border-radius:999px;font-size:12.5px;font-weight:600;background:var(--surface)}
.ico{flex:none}
.rollup{margin:16px 0 0;padding:12px 16px;border:1px dashed var(--ink2);border-radius:10px;text-align:center;font-weight:700;font-size:16px}
footer{color:var(--ink2);font-size:13px;margin-top:40px}
@media print{body{background:#fff}nav.toc{display:none}section{break-inside:avoid-page}.card{break-inside:avoid}}
@media (forced-colors:active){.card,.stage,.metric{border:1px solid CanvasText}}
"""


def css():
    def block(mode):
        p = dashboard.PALETTE[mode]
        sw = "#eb6834" if mode == "light" else "#d95926"
        swbg = "#fde5da" if mode == "light" else "#3a1d12"
        link = "#0b5cad" if mode == "light" else "#6da7ec"
        return ("--page:%s;--surface:%s;--ink:%s;--ink2:%s;--grid:%s;--axis:%s;--s1:%s;--s1-track:%s;--sw:%s;--sw-bg:%s;--link:%s;--border:%s;color-scheme:%s" % (
            p["page"], p["surface"], p["ink"], p["ink2"], p["grid"], p["axis"], p["s1"], p["s1_track"], sw, swbg, link,
            "rgba(11,11,11,.10)" if mode == "light" else "rgba(255,255,255,.10)", mode))
    st = dashboard.STATUS
    return (":root{%s;--good:%s;--warning:%s;--serious:%s;--critical:%s}\n@media (prefers-color-scheme:dark){:root:where(:not([data-theme=\"light\"])){%s}}\n:root[data-theme=\"dark\"]{%s}\n"
            % (block("light"), st["good"], st["warning"], st["serious"], st["critical"], block("dark"), block("dark"))) + CSS


def build():
    profile = json.loads(read("profiles/silicon.json"))
    lc = json.loads(read("pmf/data/lifecycles.json"))
    body = [sec_shape(), sec_asic(profile), sec_issue(lc), sec_plc(), sec_health(profile)]
    nav = ('<nav class="toc" aria-label="Views"><a href="#shape">1 Shape</a><a href="#asic">2 Silicon program</a><a href="#issue">3 Issue flow</a>'
           '<a href="#plc">4 Lifecycle and gates</a><a href="#health">5 Health metrics</a></nav>')
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="color-scheme" content="light dark"><title>PM-Framework explained</title><style>%s</style></head><body><main>'
            '<header class="top"><h1>PM-Framework explained</h1><p class="lead">Five views of the framework: governance, a silicon program, the issue flow, the lifecycle and its gates, and the health metrics. '
            'Each links to the module it comes from. Version %s.</p></header>%s%s'
            '<footer>Generated by <code>tools/gen_explainer.py</code> from the profiles, the modules and the lifecycle definitions. Do not edit by hand. Illustrative figures are labelled as such.</footer>'
            '</main></body></html>\n' % (css(), e(__version__), nav, "".join(body)))


def main(argv):
    text = build()
    if "--check" in argv:
        have = None
        if os.path.exists(OUT):
            with io.open(OUT, encoding="utf-8", newline="") as f:
                have = f.read().replace("\r\n", "\n")
        if have != text:
            print("stale: docs/explainer.html; run python3 tools/gen_explainer.py")
            return 1
        print("EXPLAINER CHECK: docs/explainer.html matches its sources")
        return 0
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote docs/explainer.html (%d bytes)" % len(text.encode("utf-8")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
