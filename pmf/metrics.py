"""The five health metrics and the worst-of rollup (definitions: docs/DATA_SCHEMAS.md#metric-definitions)."""
from pmf.util import fmt_num, is_date, is_num, num, parse_date

RANK = {"green": 0, "amber": 1, "red": 2}
DONE_GATE = ("GO", "CONDITIONAL_GO")


def _result(mid, name, color, value, rule, detail=None):
    return {"id": mid, "name": name, "color": color, "value": value, "rule": rule, "detail": detail or []}


def _grey(mid, name, why):
    return _result(mid, name, "grey", "not rated", why)


def _worst(colors):
    rated = [c for c in colors if c in RANK]
    if not rated:
        return "grey"
    return max(rated, key=lambda c: RANK[c])


def _d(x):
    return parse_date(x) if x and is_date(x) else None


def schedule_variance(ws):
    name = "Schedule Variance"
    m = ws.profile.d["metrics"]["schedule_variance"]
    cfg = ws.config
    start, end = _d(cfg.get("baseline_start")), _d(cfg.get("baseline_end"))
    gates = ws.planned_gates()
    dated = [g for g in gates if _d(g.get("baseline_date"))]
    if not start or not end or end <= start:
        return _grey("sv", name, "set baseline_start and baseline_end (end after start) in pmf.config.json")
    if not dated:
        return _grey("sv", name, "no planned gate has a baseline_date in gates.csv")
    last = max(dated, key=lambda g: _d(g["baseline_date"]))
    done = last["state"] in DONE_GATE and _d(last.get("actual_date"))
    fc = _d(last.get("actual_date")) if done else (_d(last.get("planned_date")) or _d(last["baseline_date"]))
    sv_days = (fc - _d(last["baseline_date"])).days
    pct = sv_days * 100.0 / (end - start).days
    overdue = []
    for g in gates:
        if g["state"] not in DONE_GATE:
            due = _d(g.get("planned_date")) or _d(g.get("baseline_date"))
            if due and due < ws.report_date:
                overdue.append("%s %s (planned %s)" % (g["id"], g.get("name", ""), due.isoformat()))
    detail = ["last gate %s: baseline %s, forecast %s" % (last["id"], last["baseline_date"], fc.isoformat()),
              "baseline duration %d days" % (end - start).days]
    if overdue:
        detail.append("overdue gates: " + "; ".join(overdue))
    gm, am = m["green_max_pct"], m["amber_max_pct"]
    if overdue and m.get("overdue_gate_is_red", True):
        color, why = "red", "a planned gate is overdue (open and past its planned date)"
    elif pct <= gm:
        color, why = "green", "within %s%% of baseline (or ahead)" % gm
    elif pct <= am:
        color, why = "amber", "%s%% to %s%% behind baseline" % (gm, am)
    else:
        color, why = "red", "more than %s%% behind baseline" % am
    return _result("sv", name, color, "%+d days (%+.1f%%)" % (sv_days, pct), why, detail)


def gate_on_time(ws):
    name = "Gate On-Time Rate"
    m = ws.profile.d["metrics"]["gate_on_time"]
    done = [g for g in ws.planned_gates() if g["state"] in DONE_GATE and _d(g.get("actual_date")) and _d(g.get("baseline_date"))]
    if not done:
        return _grey("gate", name, "no planned gate has been completed with an actual_date and baseline_date yet")
    ontime = [g for g in done if _d(g["actual_date"]) <= _d(g["baseline_date"])]
    pct = len(ontime) * 100.0 / len(done)
    if pct >= m["green_min_pct"]:
        color, why = "green", "at least %s%% of completed gates were on time" % m["green_min_pct"]
    elif pct >= m["amber_min_pct"]:
        color, why = "amber", "%s%% to %s%% on time" % (m["amber_min_pct"], m["green_min_pct"] - 1)
    else:
        color, why = "red", "under %s%% on time" % m["amber_min_pct"]
    late = [g["id"] for g in done if g not in ontime]
    detail = ["%d of %d completed gates on time" % (len(ontime), len(done))]
    if late:
        detail.append("late: " + ", ".join(late))
    return _result("gate", name, color, "%.0f%%" % pct, why, detail)


def issue_aging(ws):
    name = "Issue Aging"
    if not ws.load("issues"):
        return _grey("aging", name, "no issues logged yet (an empty register cannot be told apart from an unmaintained one)")
    worst = "green"
    detail = []
    counts = {}
    n_open = 0
    for lv, info in sorted(ws.profile.levels.items()):
        a = info.get("aging_days")
        if not a:
            continue
        past_g = past_a = 0
        for i in ws.open_issues({lv}):
            d = _d(i.get("detected"))
            if not d:
                continue
            n_open += 1
            age = (ws.report_date - d).days
            if age > a["amber_max"]:
                col = "red"; past_a += 1; past_g += 1
            elif age > a["green_max"]:
                col = "amber"; past_g += 1
            else:
                col = "green"
            worst = _worst([worst, col])
            if col != "green":
                detail.append("%s %s open %d days (%s limit %d / %d)" % (i["id"], info["label"], age, info["label"], a["green_max"], a["amber_max"]))
        counts[info["label"]] = (past_g, past_a)
    for k, v in counts.items():
        detail.append("%s: %d past the green limit, %d past the amber limit" % (k, v[0], v[1]))
    value = "%d open, %d past a green limit, %d past an amber limit" % (n_open, sum(v[0] for v in counts.values()), sum(v[1] for v in counts.values()))
    why = {"green": "every open Sev 1 and 2 is within its green limit" if n_open else "no open issue of an aged severity",
           "amber": "at least one open issue is past its green limit",
           "red": "at least one open issue is past its amber limit"}[worst]
    return _result("aging", name, worst, value, why, detail)


def escape_rate(ws):
    name = "Escape Rate"
    m = ws.profile.d["metrics"]["escape_rate"]
    minimum = m.get("min_issues_for_rating", 3)
    issues = ws.load("issues")
    by = {}
    for i in issues:
        by.setdefault(i.get("phase") or "(none)", []).append(i)
    rated = []
    detail = []
    for ph, lst in sorted(by.items()):
        esc = [i for i in lst if (i.get("escape_gate") or "").strip()]
        pct = len(esc) * 100.0 / len(lst)
        if len(lst) >= minimum:
            col = "green" if pct < m["green_max_pct"] else ("amber" if pct <= m["amber_max_pct"] else "red")
            rated.append(col)
            detail.append("%s: %d of %d issues escaped (%.0f%%) -> %s" % (ph, len(esc), len(lst), pct, col))
        else:
            detail.append("%s: %d issue(s), under the minimum of %d, not rated" % (ph, len(lst), minimum))
    total = len(issues)
    all_esc = len([i for i in issues if (i.get("escape_gate") or "").strip()])
    overall = ("%.0f%% overall (%d of %d)" % (all_esc * 100.0 / total, all_esc, total)) if total else "no issues"
    if not rated:
        r = _grey("escape", name, "no phase has at least %d issues yet (%s)" % (minimum, overall))
        r["detail"] = detail
        return r
    color = _worst(rated)
    why = {"green": "every rated phase is under %s%%" % m["green_max_pct"],
           "amber": "the worst rated phase is %s%% to %s%%" % (m["green_max_pct"], m["amber_max_pct"]),
           "red": "a rated phase is over %s%%" % m["amber_max_pct"]}[color]
    return _result("escape", name, color, overall, why, detail)


def burn_ratio(ws):
    name = "Budget Burn Ratio"
    m = ws.profile.d["metrics"]["burn_ratio"]
    rows = ws.load("budget", required=False)
    if not rows:
        return _grey("burn", name, "budget.csv has no rows")
    try:
        planned = sum(num(r["planned_to_date"]) for r in rows if (r.get("planned_to_date") or "").strip())
        actual = sum(num(r["actual_to_date"]) for r in rows if (r.get("actual_to_date") or "").strip())
        fc = sum(num(r["forecast_at_completion"]) for r in rows if (r.get("forecast_at_completion") or "").strip())
        total_budget = sum(num(r["budget"]) for r in rows if (r.get("budget") or "").strip())
    except Exception as e:
        return _grey("burn", name, "budget.csv has a non-numeric value (%s)" % e)
    if planned <= 0:
        return _grey("burn", name, "planned_to_date sums to zero")
    ratio = round(actual / planned, 6)
    cap = ws.config.get("baseline_budget")
    cap = float(cap) if cap not in (None, "") else total_budget
    lo, hi = m["green"]
    over = m.get("red_if_forecast_over_budget", True) and cap > 0 and fc > cap
    if ratio > m["amber_high"] or over:
        color = "red"
        why = "ratio over %s" % m["amber_high"] if ratio > m["amber_high"] else "forecast at completion exceeds the budget"
    elif lo <= ratio <= hi:
        color, why = "green", "ratio within %s to %s" % (lo, hi)
    elif ratio > hi:
        color, why = "amber", "ratio %s to %s" % (hi, m["amber_high"])
    else:
        color, why = "amber", "under-spend: ratio below %s (can mean under-resourced)" % m["under_spend_amber_below"]
    detail = ["actual %s / planned %s to date" % (fmt_num(actual), fmt_num(planned)),
              "forecast at completion %s against budget %s" % (fmt_num(fc), fmt_num(cap))]
    return _result("burn", name, color, "%.2f" % ratio, why, detail)


def compute(ws):
    ms = [schedule_variance(ws), gate_on_time(ws), issue_aging(ws), escape_rate(ws), burn_ratio(ws)]
    worst = _worst([m["color"] for m in ms])
    if worst == "grey":
        roll = {"color": "grey", "reason": "not enough data to rate any metric yet"}
    else:
        at = [m["name"] for m in ms if m["color"] == worst]
        roll = {"color": worst, "reason": "worst of the rated metrics: %s (%s)" % (", ".join(at), worst)}
        nr = [m["name"] for m in ms if m["color"] == "grey"]
        if nr:
            roll["reason"] += "; not rated: " + ", ".join(nr)
    return {"report_date": ws.report_date.isoformat(), "program": ws.config["program"], "metrics": ms, "rollup": roll}
