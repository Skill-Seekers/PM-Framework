"""Drafts: management brief, weekly status, RAID snapshot. Deterministic text built from the registers.
Anything the registers cannot know stays a [bracketed placeholder] for the PM to fill; nothing is invented."""
import datetime
import io
import os
import re

from pmf import metrics, records
from pmf.lifecycle import score_of
from pmf.util import (ActionNeeded, PmfError, fmt_num, is_date, is_num, is_placeholder, next_id, num, parse_date)

COLOR_WORD = {"green": "Green", "amber": "Amber", "red": "Red", "grey": "Not rated"}


def _write(path, text):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)


def _read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def write_draft(path, text, force=False, label=None):
    """Never overwrite a draft the PM may have edited. Returns 'created', 'unchanged' or 'overwritten'."""
    if os.path.exists(path):
        if _read(path) == text:
            return "unchanged"
        if not force:
            raise ActionNeeded(["%s already exists and differs; it may hold your edits. Pass --force to replace it, "
                                "or --stdout to print the new draft" % (label or os.path.basename(path))], title="not overwritten")
        _write(path, text)
        return "overwritten"
    _write(path, text)
    return "created"


# ------------------------------------------------------------------ brief
def next_brief_id(ws):
    d = ws.path("briefs")
    existing = []
    if os.path.isdir(d):
        existing = [f[:-3] for f in os.listdir(d) if re.match(r"^B-\d+\.md$", f)]
    for i in ws.load("issues"):
        if i.get("brief_ref"):
            existing.append(i["brief_ref"])
    return next_id("B", existing)


def _opt_line(label, o):
    parts = [o["description"]]
    bits = []
    if not is_placeholder(o["schedule"]):
        bits.append("schedule %s days" % o["schedule"].lstrip("+"))
    if not is_placeholder(o["cost"]):
        bits.append("cost %s" % o["cost"])
    if not is_placeholder(o["risk"]):
        bits.append("risk %s" % o["risk"])
    return "- %s. %s: %s" % (label[0], label[1], "; ".join([o["description"]] + bits) if o["description"] else "; ".join(bits))


def draft_brief(ws, issue_id, actor):
    """Return (brief_id, text). Raises ActionNeeded when there is nothing to draft from."""
    issue = ws.find("issues", issue_id)
    if issue is None:
        raise PmfError("issue %s not found" % issue_id)
    if issue["state"] == "DETECTED":
        raise ActionNeeded(["issue %s is only DETECTED; log it first (`pmf issue log`)" % issue_id], title="no brief yet")
    if issue.get("brief_ref"):
        raise ActionNeeded(["issue %s already has brief %s; edit briefs/%s.md directly" % (issue_id, issue["brief_ref"], issue["brief_ref"])],
                           title="brief exists")
    rec = None
    if issue.get("decision_ref"):
        rec = records.parse_decision(ws.decision_path(issue["decision_ref"]))
    bid = next_brief_id(ws)
    sev = issue.get("severity", "")
    label = ws.profile.levels.get(int(float(sev)), {}).get("label", "Sev " + sev) if is_num(sev) else "[severity]"

    what = "%s, found in the %s phase." % (issue["title"].rstrip("."), issue.get("phase") or "[phase]")
    what += " Milestone threatened: [milestone]."
    sched = issue.get("sched_impact_days", "")
    cost = issue.get("cost_impact", "")
    cust = "[milestone affected, or \"internal only\"]"
    if rec and (rec.get("customer_visible") or "").strip().lower() == "no":
        cust = "internal only"
    impact = ["Schedule: %s" % (("%+d days" % int(float(sched))) if is_num(sched) and sched != "" else "[+X days] to [milestone]"),
              "Cost: %s" % (fmt_num(num(cost)) if is_num(cost) and cost != "" else "[amount]"),
              "Customer: %s" % cust]
    if rec and rec["options"]:
        names = {"A": "Fix now", "B": "Waive with conditions", "C": "Defer to next revision"}
        opts = [_opt_line((k, names[k]), rec["options"][k]) for k in ("A", "B", "C") if k in rec["options"]]
        opt_text = "\n".join(opts)
    else:
        opt_text = "- A. Fix now: [one-line trade-off]\n- B. Waive with conditions: [one-line trade-off]\n- C. Defer to next revision: [one-line trade-off]"
    reco = "[PM's call and a one-line rationale.]"
    if rec and not is_placeholder(rec.get("recommendation")):
        reco = rec["recommendation"]
    chosen = records.chosen_option(rec) if rec else None
    if chosen and rec.get("decided_on") and not is_placeholder(rec.get("decided_by")):
        need = "Decided on %s by %s: option %s. [Next step and who is told.]" % (rec["decided_on"], rec["decided_by"], chosen)
    elif issue.get("due") and is_date(issue["due"]):
        need = "%s. [What happens on the call.]" % issue["due"]
    else:
        need = "[Date/time, and what happens on the call.]"
    text = "\n".join([
        "# %s: %s" % (bid, issue["title"]),
        "Program: %s" % ws.config["program"],
        "Issue: %s" % issue["id"],
        "Severity: %s" % label,
        "Discovered: %s" % (issue.get("detected") or "[YYYY-MM-DD]"),
        "Author: %s" % actor,
        "Distribution: [names or list]",
        "Next update: [date]",
        "",
        "## WHAT", what, "",
        "## IMPACT", "\n".join(impact), "",
        "## OPTIONS", opt_text, "",
        "## RECOMMENDATION", reco, "",
        "## DECISION NEEDED BY", need, ""])
    return bid, text


# ------------------------------------------------------------------ helpers for weekly / raid
def _d(x):
    return parse_date(x) if x and is_date(x) else None


def _age(ws, issue):
    d = _d(issue.get("detected"))
    return (ws.report_date - d).days if d else None


def _gate_color(ws, g):
    b, p = _d(g.get("baseline_date")), _d(g.get("planned_date"))
    due = p or b
    if g["state"] in ("GO", "CONDITIONAL_GO"):
        a = _d(g.get("actual_date"))
        return "green" if (a and b and a <= b) else ("amber" if a and b else "grey")
    if due and due < ws.report_date:
        return "red"
    if p and b and p > b:
        return "amber"
    return "green" if due else "grey"


def _open_sev12(ws):
    keep = set(ws.profile.brief_required_for) or {1, 2}
    out = [i for i in ws.open_issues() if is_num(i.get("severity", "")) and int(float(i["severity"])) in keep]
    return sorted(out, key=lambda i: (int(float(i["severity"])), i.get("detected", ""), i["id"]))


def _issue_line(ws, i):
    bits = ["%s %s (Sev %s, %s)" % (i["id"], i["title"], i.get("severity", "?"), i["state"]), "owner %s" % (i.get("owner") or "[owner]")]
    imp = []
    if i.get("sched_impact_days") and is_num(i["sched_impact_days"]):
        imp.append("%+d days" % int(float(i["sched_impact_days"])))
    if i.get("cost_impact") and is_num(i["cost_impact"]):
        imp.append(fmt_num(num(i["cost_impact"])))
    bits.append("impact %s" % (" / ".join(imp) if imp else "[not yet sized]"))
    a = _age(ws, i)
    if a is not None:
        bits.append("open %d days" % a)
    bits.append("next action %s" % (i.get("next_action") or "[what, by when]") + ((" (due %s)" % i["due"]) if i.get("due") and is_date(i["due"]) else ""))
    return "- " + " - ".join(bits)


def _week_events(ws):
    start = ws.report_date - datetime.timedelta(days=7)
    out = []
    for e in ws.events():
        ts = (e.get("ts") or "")[:10]
        if is_date(ts) and start < parse_date(ts) <= ws.report_date:
            out.append(e)
    return out


# ------------------------------------------------------------------ weekly
def weekly(ws):
    m = metrics.compute(ws)
    roll = m["rollup"]
    L = []
    L.append("<!-- Draft generated by `pmf report weekly` on %s from the registers. Replace every [bracketed field] before it goes out. -->" % ws.report_date.isoformat())
    L.append("Subject: %s - Weekly Status - Week of %s" % (ws.config["program"], ws.report_date.isoformat()))
    L.append("")
    L.append("HEADLINE")
    L.append("Overall status: %s - %s" % (COLOR_WORD[roll["color"]], roll["reason"]))
    L.append("")
    L.append("METRICS")
    for x in m["metrics"]:
        L.append("- %s: %s (%s) - %s" % (x["name"], COLOR_WORD[x["color"]], x["value"], x["rule"]))
    L.append("")
    L.append("MILESTONES")
    pend = [g for g in ws.load("gates") if g["state"] not in ("GO", "CONDITIONAL_GO")]
    pend.sort(key=lambda g: (_d(g.get("planned_date")) or _d(g.get("baseline_date")) or datetime.date(9999, 12, 31), g["id"]))
    if pend:
        g = pend[0]
        L.append("Next gate: %s %s - planned %s (baseline %s) - status %s - %s" % (
            g["id"], g.get("name", ""), g.get("planned_date") or "[date]", g.get("baseline_date") or "[date]",
            COLOR_WORD[_gate_color(ws, g)], g["state"]))
    else:
        L.append("Next gate: none open")
    wk = _week_events(ws)
    hit = [e for e in wk if e["entity"] == "gate" and e["to_state"] in ("GO", "CONDITIONAL_GO", "NO_GO")]
    if hit:
        for e in hit:
            L.append("Milestone this week: %s %s on %s" % (e["id"], e["to_state"].replace("_", " "), e["ts"][:10]))
    else:
        L.append("Milestone this week: no gate decision recorded this week")
    L.append("")
    L.append("WORKSTREAM STATUS")
    L.append("[Workstream 1]: [G/A/R] - [one line]   (workstreams are not tracked in the registers; add yours)")
    L.append("")
    L.append("OPEN ISSUES (Sev 1/2)")
    sev = _open_sev12(ws)
    L.extend([_issue_line(ws, i) for i in sev] or ["- none open"])
    L.append("")
    L.append("RAID CHANGES THIS WEEK")
    added = [e["id"] for e in wk if e["entity"] == "risk" and not e["from_state"]]
    esc = [e for e in wk if e["entity"] == "risk" and e["to_state"] == "OCCURRED"]
    closed = [e["id"] for e in wk if (e["entity"] == "risk" and e["to_state"] == "RETIRED") or (e["entity"] == "issue" and e["to_state"] == "CLOSED")]
    L.append("Added: %s" % (", ".join(added) or "none"))
    esc_txt = []
    for e in esc:
        r = ws.find("risks", e["id"])
        esc_txt.append("%s -> %s" % (e["id"], (r or {}).get("linked_issue") or "[issue]"))
    L.append("Escalated (R -> I): %s" % (", ".join(esc_txt) or "none"))
    L.append("Closed: %s" % (", ".join(closed) or "none"))
    L.append("")
    L.append("DECISIONS NEEDED")
    dec = []
    for i in ws.load("issues"):
        if i["state"] in ("LOGGED", "TRIAGED"):
            dec.append("- Decide %s %s (%s) - needed by %s - from [decider]" % (
                i["id"], i["title"], "options ready" if i["state"] == "TRIAGED" else "needs triage record",
                i.get("due") if i.get("due") and is_date(i["due"]) else "[date]"))
    for c in ws.load("changes"):
        if c["state"] == "ASSESSED":
            t = ws.profile.tier_for(num(c.get("cost_delta") or 0), num(c.get("schedule_delta_days") or 0)) if (is_num(c.get("cost_delta", "")) or is_num(c.get("schedule_delta_days", ""))) else None
            dec.append("- Approve or reject %s %s%s - needed by [date] - from %s" % (
                c["id"], c["title"], (" (tier %s)" % t["label"]) if t else "", ", ".join(t["approvers"]) if t else "[approvers]"))
    for g in ws.load("gates"):
        if g["state"] == "REVIEW":
            dec.append("- Gate decision for %s %s - needed by %s - from [decider]" % (g["id"], g.get("name", ""), g.get("planned_date") or "[date]"))
    L.extend(dec or ["- none"])
    L.append("")
    L.append("UPCOMING")
    L.append("Next week: [key activities]")
    if pend:
        g = pend[0]
        gd = next((x for x in ws.profile.gates if x["id"] == g["id"]), None)
        blockers = []
        if gd:
            blockers = [i["id"] for i in ws.open_issues(set(gd.get("requires_no_open_severity", [])))]
        n = len(gd["exit_criteria"]) if gd else 0
        met = len([x for x in (g.get("criteria_met") or "").replace(",", ";").split(";") if x.strip()])
        L.append("Next gate: %s - %s - criteria recorded met %d of %d%s" % (
            g.get("planned_date") or g.get("baseline_date") or "[date]", g["id"], met, n,
            ("; blocked by open issues %s" % ", ".join(blockers)) if blockers else ""))
    L.append("")
    return "\n".join(L)


# ------------------------------------------------------------------ raid
def raid(ws):
    L = ["# RAID snapshot - %s - %s" % (ws.config["program"], ws.report_date.isoformat()), "",
         "Generated by `pmf raid` from risks.csv, assumptions.csv, dependencies.csv and issues.csv. Every open Sev 1 and Sev 2 issue is always listed.", ""]
    L.append("## Issues (open Sev 1 and Sev 2)")
    sev = _open_sev12(ws)
    L.extend([_issue_line(ws, i) for i in sev] or ["- none open"])
    L.append("")
    L.append("## Risks")
    rows = []
    for r in ws.load("risks"):
        if r["state"] in ("RETIRED", "OCCURRED"):
            continue
        sc = score_of(r)
        band = ws.profile.risk_band(sc) if sc is not None else None
        stale = ""
        if band and _d(r.get("last_scored")) and (ws.report_date - _d(r["last_scored"])).days > band["review_days"]:
            stale = " STALE"
        rows.append((-(sc or 0), r["id"], "- %s %s - %s - score %s%s - owner %s - mitigation %s" % (
            r["id"], r["title"], r["state"], ("%d (%s)" % (sc, band["priority"])) if sc is not None else "not scored",
            stale, r.get("owner") or "[owner]", r.get("mitigation") or "[none yet]")))
    rows.sort()
    L.extend([x[2] for x in rows] or ["- none open"])
    L.append("")
    L.append("## Assumptions not yet validated")
    a = [x for x in ws.load("assumptions", required=False) if x.get("status") != "validated"]
    L.extend(["- %s %s - %s - validate by %s" % (x["id"], x["title"], x.get("status", ""), x.get("validate_by") or "[date]") for x in a] or ["- none"])
    L.append("")
    L.append("## Dependencies not yet delivered")
    d = [x for x in ws.load("dependencies", required=False) if x.get("status") != "delivered"]
    L.extend(["- %s %s - %s from %s - needed by %s%s" % (x["id"], x["title"], x.get("status", ""), x.get("provider") or "[provider]",
                                                       x.get("needed_by") or "[date]",
                                                       (" - issue %s" % x["linked_issue"]) if x.get("linked_issue") else "") for x in d] or ["- none"])
    L.append("")
    return "\n".join(L)
