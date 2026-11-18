#!/usr/bin/env python3
"""Validate profiles and lifecycles against each other and against the playbook defaults.
Stdlib only. Exit 0 = consistent, 1 = problems found."""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = []


def bad(msg):
    problems.append(msg)


def load(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)


L = load("pmf/data/lifecycles.json")

# ---- lifecycles ----
for name, e in L["entities"].items():
    states = set(e["states"])
    if e["initial"] not in states:
        bad("%s: initial %s not a state" % (name, e["initial"]))
    for s in e["terminal"]:
        if s not in states:
            bad("%s: terminal %s not a state" % (name, s))
    reach, todo = {e["initial"]}, [e["initial"]]
    for t in e["transitions"]:
        for k in ("from", "to"):
            if t[k] not in states:
                bad("%s: transition uses unknown state %s" % (name, t[k]))
        for g in t["guards"]:
            if g not in L["guards"]:
                bad("%s: unknown guard %s" % (name, g))
    while todo:
        cur = todo.pop()
        for t in e["transitions"]:
            if t["from"] == cur and t["to"] not in reach:
                reach.add(t["to"]); todo.append(t["to"])
    for s in states - reach:
        bad("%s: state %s unreachable from %s" % (name, s, e["initial"]))
    # every state must be able to reach a terminal state
    for s in states:
        seen, todo = {s}, [s]
        while todo:
            cur = todo.pop()
            for t in e["transitions"]:
                if t["from"] == cur and t["to"] not in seen:
                    seen.add(t["to"]); todo.append(t["to"])
        if not seen & set(e["terminal"]):
            bad("%s: state %s cannot reach a terminal state" % (name, s))
    # no duplicate (from, command) with same to
    keys = [(t["from"], t["to"], t["command"]) for t in e["transitions"]]
    if len(keys) != len(set(keys)):
        bad("%s: duplicate transition" % name)

# ---- profiles ----
EXPECT = {  # playbook defaults (Modules 02, 03, 07, 08) that every shipped profile must keep
    "sev_aging": {1: (7, 14), 2: (14, 28)},
    "escape": (10, 20),
    "gate": (90, 75),
    "sv": (3, 8),
    "burn_green": [0.9, 1.1], "burn_high": 1.25,
    "risk_bands": [(15, 25), (8, 14), (4, 7), (1, 3)],
    "escalate_days": 14, "cum_pct": 10,
    "tiers": [(2500, 1), (25000, 5), (100000, 20)],
}
for pf in sorted(os.listdir(os.path.join(ROOT, "profiles"))):
    if not pf.endswith(".json"):
        continue
    P = load("profiles/" + pf)
    t = pf
    phases = {p["id"] for p in P["phases"]}
    parties = {p["id"] for p in P["parties"]}
    if len(phases) != len(P["phases"]):
        bad("%s: duplicate phase id" % t)
    for p in P["phases"]:
        if set(p["raci"]) != parties:
            bad("%s: phase %s RACI parties differ from parties list" % (t, p["id"]))
        if any(v not in "RACI" or len(v) != 1 for v in p["raci"].values()):
            bad("%s: phase %s has an invalid RACI letter" % (t, p["id"]))
    gids = [g["id"] for g in P["gates"]]
    if len(set(gids)) != len(gids):
        bad("%s: duplicate gate id" % t)
    for g in P["gates"]:
        if g["phase"] not in phases:
            bad("%s: gate %s unknown phase" % (t, g["id"]))
        if not g["exit_criteria"]:
            bad("%s: gate %s has no exit criteria" % (t, g["id"]))
    sev = {l["level"]: l for l in P["severity"]["levels"]}
    for lv in P["severity"]["brief_required_for"] + P["severity"]["exec_notice_same_day"]:
        if lv not in sev:
            bad("%s: severity %s not defined" % (t, lv))
    for lv, (gmax, amax) in EXPECT["sev_aging"].items():
        a = sev[lv]["aging_days"]
        if not a or (a["green_max"], a["amber_max"]) != (gmax, amax):
            bad("%s: Sev %s aging differs from Module 08 (%s)" % (t, lv, (gmax, amax)))
    m = P["metrics"]
    if (m["escape_rate"]["green_max_pct"], m["escape_rate"]["amber_max_pct"]) != EXPECT["escape"]:
        bad("%s: escape rate thresholds differ from Module 08" % t)
    if (m["gate_on_time"]["green_min_pct"], m["gate_on_time"]["amber_min_pct"]) != EXPECT["gate"]:
        bad("%s: gate on-time thresholds differ from Module 08" % t)
    if (m["schedule_variance"]["green_max_pct"], m["schedule_variance"]["amber_max_pct"]) != EXPECT["sv"]:
        bad("%s: schedule variance thresholds differ from Module 08" % t)
    if m["burn_ratio"]["green"] != EXPECT["burn_green"] or m["burn_ratio"]["amber_high"] != EXPECT["burn_high"]:
        bad("%s: burn ratio thresholds differ from Module 08" % t)
    bands = sorted((b["min"], b["max"]) for b in P["risk"]["bands"])
    if bands != sorted(EXPECT["risk_bands"]):
        bad("%s: risk bands differ from Module 03" % t)
    cover = set()
    for lo, hi in bands:
        cover |= set(range(lo, hi + 1))
    if cover != set(range(1, 26)):
        bad("%s: risk bands do not cover scores 1..25 exactly" % t)
    if P["escalation"]["days"] != EXPECT["escalate_days"]:
        bad("%s: escalation days differ from default" % t)
    cc = P["change_control"]
    if cc["escalate_cumulative_pct"] != EXPECT["cum_pct"]:
        bad("%s: cumulative change escalation differs from Module 07" % t)
    got = [(x["max_cost"], x["max_days"]) for x in cc["tiers"][:3]]
    if got != EXPECT["tiers"]:
        bad("%s: approval tiers differ from Module 07.5" % t)
    if cc["tiers"][-1]["max_cost"] is not None:
        bad("%s: top approval tier must be open-ended" % t)

if problems:
    print("SPEC CHECK: %d problem(s)" % len(problems))
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("SPEC CHECK: consistent (%d lifecycles, %d guards, %d profiles)" % (
    len(L["entities"]), len(L["guards"]), len([f for f in os.listdir(os.path.join(ROOT, "profiles")) if f.endswith(".json")])))
