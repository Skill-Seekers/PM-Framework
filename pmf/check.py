"""`pmf check`: validate every register against its schema, the lifecycles and each other.
Returns (errors, warnings), lists of messages."""
import datetime
import os

from pmf import records
from pmf.lifecycle import ENTITY_REGISTER, score_of
from pmf.schemas import SCHEMAS
from pmf.util import is_date, is_num, num, parse_date, single_owner_problem, split_list


OPTIONAL = ("assumptions", "dependencies", "budget", "raci", "vendors", "contention", "events")


def run(ws):
    err, warn = [], []
    rd = ws.report_date
    prof = ws.profile

    # ---- per-register format ----
    for name, s in SCHEMAS.items():
        if name in OPTIONAL and not os.path.exists(ws.register_path(name)):
            continue
        try:
            rows = ws.load(name)
        except Exception as e:
            err.append(str(e))
            continue
        seen = set()
        for r in rows:
            key = s.get("key")
            label = "%s %s" % (s["file"], r.get(key, "")) if key else s["file"]
            if key:
                if not r.get(key):
                    err.append("%s: a row has an empty %s" % (s["file"], key))
                elif r[key] in seen:
                    err.append("%s: duplicate %s %s" % (s["file"], key, r[key]))
                seen.add(r.get(key))
            for c in s.get("dates", []):
                if r.get(c) and not is_date(r[c]):
                    err.append("%s: %s %r is not a date" % (label, c, r[c]))
            for c in s.get("numbers", []):
                if r.get(c) and not is_num(r[c]):
                    err.append("%s: %s %r is not a number" % (label, c, r[c]))
            for c, allowed in s.get("enums", {}).items():
                if r.get(c) and r[c] not in allowed:
                    err.append("%s: %s %r not in %s" % (label, c, r[c], "/".join(allowed)))

    # ---- states valid per lifecycle ----
    for ent, reg in ENTITY_REGISTER.items():
        states = set(ws.lifecycles["entities"][ent]["states"])
        for r in ws.load(reg):
            if r["state"] not in states:
                err.append("%s %s has unknown state %r" % (ent, r["id"], r["state"]))

    issues = ws.load("issues")
    risks = ws.load("risks")
    ids_issue = {i["id"] for i in issues}

    # ---- issues ----
    for i in issues:
        if i["state"] != "DETECTED":
            p = single_owner_problem(i.get("owner"))
            if p:
                err.append("issue %s: %s" % (i["id"], p))
            if i.get("phase") not in prof.phase_ids:
                err.append("issue %s: phase %r not in the profile" % (i["id"], i.get("phase")))
            if is_num(i.get("severity", "")) and int(float(i["severity"])) not in prof.levels:
                err.append("issue %s: severity %s not defined in the profile" % (i["id"], i["severity"]))
        if i["state"] in ("DECIDED", "RESOLVED", "CLOSED", "DEFERRED", "TRIAGED") and not i.get("decision_ref"):
            err.append("issue %s is %s but has no decision_ref" % (i["id"], i["state"]))
        if i.get("decision_ref") and not os.path.exists(ws.decision_path(i["decision_ref"])):
            err.append("issue %s: decision record %s not found" % (i["id"], i["decision_ref"]))
        if i.get("brief_ref") and not os.path.exists(ws.brief_path(i["brief_ref"])):
            err.append("issue %s: brief %s not found" % (i["id"], i["brief_ref"]))
        if i.get("escape_gate") and not _gate_exists(ws, i["escape_gate"]):
            err.append("issue %s: escape_gate %s is not a gate" % (i["id"], i["escape_gate"]))
        if i.get("detected") and is_date(i["detected"]):
            d = parse_date(i["detected"])
            if d > rd:
                warn.append("issue %s detected %s is after the report date %s" % (i["id"], i["detected"], rd))
            elif i["state"] in prof.open_issue_states and (rd - d).days > prof.escalation_days:
                warn.append("issue %s ESCALATED: %s for %d days (limit %d)" % (i["id"], i["state"], (rd - d).days, prof.escalation_days))
            if (is_num(i.get("severity", "")) and int(float(i["severity"])) in prof.exec_notice_same_day
                    and i["state"] != "DETECTED"):
                if not i.get("exec_notified"):
                    warn.append("issue %s is Sev %s: no exec_notified date recorded" % (i["id"], i["severity"]))
                elif is_date(i["exec_notified"]) and parse_date(i["exec_notified"]) > d:
                    warn.append("issue %s: exec notified %s, a day or more after detection %s" % (i["id"], i["exec_notified"], i["detected"]))
        if i.get("linked_risk") and ws.find("risks", i["linked_risk"]) is None:
            err.append("issue %s: linked_risk %s not found" % (i["id"], i["linked_risk"]))

    # ---- risks ----
    for r in risks:
        if r["state"] != "IDENTIFIED":
            p = single_owner_problem(r.get("owner"))
            if p:
                err.append("risk %s: %s" % (r["id"], p))
            if score_of(r) is None:
                err.append("risk %s is %s but has no probability/impact" % (r["id"], r["state"]))
        if r.get("linked_issue") and r["linked_issue"] not in ids_issue:
            err.append("risk %s: linked_issue %s not found" % (r["id"], r["linked_issue"]))
        if r["state"] == "OCCURRED" and not r.get("linked_issue"):
            err.append("risk %s is OCCURRED but has no linked_issue" % r["id"])
        if r["state"] in ("ASSESSED", "MITIGATING", "ACCEPTED") and score_of(r) is not None and is_date(r.get("last_scored", "")):
            band = prof.risk_band(score_of(r))
            age = (rd - parse_date(r["last_scored"])).days
            if band and age > band["review_days"]:
                warn.append("risk %s is STALE: %s risk last scored %d days ago (review every %d)" % (r["id"], band["priority"], age, band["review_days"]))

    # ---- assumptions, dependencies ----
    for a in ws.load("assumptions", required=False):
        if a.get("status") == "untested" and is_date(a.get("validate_by", "")) and parse_date(a["validate_by"]) < rd:
            warn.append("assumption %s is untested past its validate_by date %s" % (a["id"], a["validate_by"]))
        if a.get("status") == "invalid" and not (a.get("linked_risk") or "").strip():
            err.append("assumption %s is invalid but links no risk or issue" % a["id"])
        if a.get("linked_risk") and ws.find("risks", a["linked_risk"]) is None and a["linked_risk"] not in ids_issue:
            err.append("assumption %s: linked_risk %s not found" % (a["id"], a["linked_risk"]))
    for d in ws.load("dependencies", required=False):
        if d.get("status") == "late" and not (d.get("linked_issue") or "").strip():
            warn.append("dependency %s is late with no linked issue" % d["id"])
        if d.get("linked_issue") and d["linked_issue"] not in ids_issue:
            err.append("dependency %s: linked_issue %s not found" % (d["id"], d["linked_issue"]))

    # ---- gates ----
    have = {g["id"]: g for g in ws.load("gates")}
    for g in prof.gates:
        if g["id"] not in have:
            err.append("gate %s (%s) from the profile is missing in gates.csv" % (g["id"], g["name"]))
    for g in have.values():
        if g["state"] in ("GO", "CONDITIONAL_GO") and not g.get("actual_date"):
            err.append("gate %s is %s but has no actual_date" % (g["id"], g["state"]))
        if g["state"] == "CONDITIONAL_GO" and not g.get("waiver_refs"):
            err.append("gate %s is CONDITIONAL_GO with no waiver_refs" % g["id"])
        if g.get("type") == "issue-triggered" and g.get("triggered_by") not in ids_issue:
            err.append("gate %s: triggered_by %s not found" % (g["id"], g.get("triggered_by")))
        for ref in split_list(g.get("waiver_refs")):
            if not os.path.exists(ws.decision_path(ref)):
                err.append("gate %s: waiver %s not found" % (g["id"], ref))

    # ---- RAID rule: every open Sev 1/2 is visible (informational) ----
    # ---- changes ----
    cum = 0.0
    budget_cap = ws.config.get("baseline_budget")
    for c in ws.load("changes"):
        if c["state"] in ("APPROVED", "IMPLEMENTED", "VERIFIED") and is_num(c.get("cost_delta", "")):
            cum += num(c["cost_delta"])
        if c["state"] in ("APPROVED", "IMPLEMENTED", "VERIFIED") and not c.get("decision_ref"):
            err.append("change %s is %s but has no decision_ref" % (c["id"], c["state"]))
        if c.get("linked_issue") and c["linked_issue"] not in ids_issue:
            err.append("change %s: linked_issue %s not found" % (c["id"], c["linked_issue"]))
    if budget_cap not in (None, "") and float(budget_cap) > 0:
        pct = cum * 100.0 / float(budget_cap)
        if pct > prof.d["change_control"]["escalate_cumulative_pct"]:
            warn.append("approved changes total %.1f%% of the baseline budget (limit %s%%): a formal re-baseline is due" % (
                pct, prof.d["change_control"]["escalate_cumulative_pct"]))

    # ---- vendors, contention ----
    for v in ws.load("vendors", required=False):
        if v.get("paid_on_delivery") == "no":
            warn.append("vendor %s is paid before delivery: pay only after acceptance, or price the risk into the contract" % v["vendor"])
    tot = {}
    cap = {}
    for c in ws.load("contention", required=False):
        k = (c.get("resource"), c.get("period"))
        if is_num(c.get("demand", "")):
            tot[k] = tot.get(k, 0) + num(c["demand"])
        if is_num(c.get("capacity", "")):
            cap[k] = max(cap.get(k, 0), num(c["capacity"]))
    for k, d in sorted(tot.items()):
        if k in cap and d > cap[k]:
            warn.append("resource %s in %s: demand %s exceeds capacity %s" % (k[0], k[1], d, cap[k]))

    # ---- events consistent with state ----
    last = {}
    for e in ws.events():
        last[(e["entity"], e["id"])] = e
    for ent, reg in ENTITY_REGISTER.items():
        for r in ws.load(reg):
            e = last.get((ent, r["id"]))
            if e is None:
                if r["state"] != ws.lifecycles["entities"][ent]["initial"]:
                    warn.append("%s %s is %s but has no event history (edited outside the tool?)" % (ent, r["id"], r["state"]))
            elif e["to_state"] != r["state"]:
                err.append("%s %s: state %s but the last event says %s (edited by hand?)" % (ent, r["id"], r["state"], e["to_state"]))

    # ---- raci and budget reference the profile ----
    for r in ws.load("raci", required=False):
        if r.get("phase") not in prof.phase_ids:
            err.append("raci.csv: phase %r is not in the profile" % r.get("phase"))
        if r.get("party") not in prof.parties:
            err.append("raci.csv: party %r is not in the profile (%s)" % (r.get("party"), ", ".join(prof.parties)))
    for b in ws.load("budget", required=False):
        if b.get("phase") not in prof.phase_ids:
            err.append("budget.csv: phase %r is not in the profile" % b.get("phase"))

    # ---- missing baselines (metrics will show not rated) ----
    for k in ("baseline_start", "baseline_end"):
        if not ws.config.get(k):
            warn.append("pmf.config.json: %s is not set; Schedule Variance will be not rated" % k)
    if not any(g.get("baseline_date") for g in ws.load("gates")):
        warn.append("no gate has a baseline_date; Schedule Variance and Gate On-Time will be not rated")
    return err, warn


def _gate_exists(ws, gid):
    return any(g["id"] == gid for g in ws.load("gates"))
