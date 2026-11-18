"""Named guard checks for lifecycle transitions. Each takes a Context and returns a list of
failure messages (empty list = passed). The names match pmf/data/lifecycles.json."""
import os
import re

from pmf import records
from pmf.util import (is_date, is_placeholder, num, is_num, single_owner_problem, split_list)


class Context(object):
    def __init__(self, ws, entity, row, old, cmd, note="", ref=""):
        self.ws = ws
        self.entity = entity
        self.row = row
        self.old = old
        self.cmd = cmd
        self.note = (note or "").strip()
        self.ref = (ref or "").strip()

    @property
    def profile(self):
        return self.ws.profile


def _int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def _decision(ctx):
    ref = (ctx.row.get("decision_ref") or "").strip()
    if not ref:
        return None, ["decision_ref is empty; create decisions/DR-NNN.md from templates/documents/decision_record.md and pass --decision-ref"]
    rec = records.parse_decision(ctx.ws.decision_path(ref))
    if rec is None:
        return None, ["decision record %s not found at decisions/%s.md" % (ref, ref)]
    return rec, []


# ---------------- issue ----------------
def has_required_fields(ctx):
    need = ["id", "title", "description", "phase", "owner", "severity", "detected"]
    return ["%s is required" % k for k in need if is_placeholder(ctx.row.get(k))]


def single_owner(ctx):
    p = single_owner_problem(ctx.row.get("owner"))
    return [p] if p else []


def valid_severity(ctx):
    s = _int(ctx.row.get("severity"))
    if s not in ctx.profile.levels:
        return ["severity %r is not one of %s" % (ctx.row.get("severity"), sorted(ctx.profile.levels))]
    return []


def valid_phase(ctx):
    if ctx.row.get("phase") not in ctx.profile.phase_ids:
        return ["phase %r is not in the profile (%s)" % (ctx.row.get("phase"), ", ".join(ctx.profile.phase_ids))]
    return []


def decision_record_has_three_options(ctx):
    rec, err = _decision(ctx)
    return err or records.option_problems(rec)


def decision_record_has_recommendation(ctx):
    rec, err = _decision(ctx)
    if err:
        return err
    if is_placeholder(rec.get("recommendation")):
        return ["the decision record has no Recommendation line"]
    return []


def decision_chosen(ctx):
    rec, err = _decision(ctx)
    return err or records.decision_problems(rec)


def decision_signed_if_waive_or_defer(ctx):
    rec, err = _decision(ctx)
    if err:
        return err
    if records.chosen_option(rec) in ("B", "C") and (rec.get("signed") or "").strip().lower() != "yes":
        return ["option %s needs a signed record: set 'Signed: yes' in the decision record once it is actually signed" % records.chosen_option(rec)]
    return []


def option_is_fix_or_waive(ctx):
    rec, err = _decision(ctx)
    if err:
        return err
    if records.chosen_option(rec) not in ("A", "B"):
        return ["the chosen option is %s; resolve applies to A (fix) or B (waive). Use `issue defer` for C" % rec.get("chosen")]
    return []


def option_is_defer(ctx):
    rec, err = _decision(ctx)
    if err:
        return err
    if records.chosen_option(rec) != "C":
        return ["the chosen option is %s; defer applies to C only" % rec.get("chosen")]
    return []


def customer_acceptance_if_customer_visible(ctx):
    rec, err = _decision(ctx)
    if err:
        return err
    if (rec.get("customer_visible") or "").strip().lower() == "yes":
        acc = (rec.get("customer_acceptance") or "").strip()
        if is_placeholder(acc) or acc.lower() in ("n/a", "na", "none"):
            return ["the issue is customer visible; record the customer's acceptance of the deferral under 'Customer acceptance:'"]
    return []


def verification_ref_present(ctx):
    if (ctx.row.get("verification_ref") or "").strip() or ctx.ref:
        return []
    what = "verification_ref (--verification-ref)" if ctx.entity == "issue" else "a verification reference (--ref)"
    return ["%s is empty; name the evidence (report, run id, waiver conditions)" % what]


def brief_present_if_required(ctx):
    sev = _int(ctx.row.get("severity"))
    if sev not in ctx.profile.brief_required_for:
        return []
    ref = (ctx.row.get("brief_ref") or "").strip()
    if not ref:
        return ["Sev %s needs a management brief: run `pmf brief %s`, edit briefs/B-NNN.md, then pass --brief-ref" % (sev, ctx.row.get("id"))]
    b = records.parse_brief(ctx.ws.brief_path(ref))
    if b is None:
        return ["brief %s not found at briefs/%s.md" % (ref, ref)]
    return ["brief %s: %s" % (ref, m) for m in records.brief_problems(b)]


def lesson_present(ctx):
    return [] if (ctx.row.get("lesson") or "").strip() else ["lesson is empty; add a one-line lesson (--lesson)"]


def reason_present(ctx):
    return [] if ctx.note else ["a reason is required; pass --note \"why\""]


# ---------------- risk ----------------
def _scale(ctx):
    sc = ctx.profile.d["risk"]["scale"]
    return sc["min"], sc["max"]


def _in_scale(ctx, field):
    lo, hi = _scale(ctx)
    v = ctx.row.get(field)
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ["%s %r is not a whole number from %d to %d" % (field, v, lo, hi)]
    if f != int(f) or not (lo <= f <= hi):
        return ["%s %r is not a whole number from %d to %d" % (field, v, lo, hi)]
    return []


def valid_probability(ctx):
    return _in_scale(ctx, "probability")


def valid_impact(ctx):
    return _in_scale(ctx, "impact")


def mitigation_present(ctx):
    return [] if (ctx.row.get("mitigation") or "").strip() else ["mitigation is empty; write the plan (--mitigation)"]


def acceptor_named(ctx):
    out = []
    if not (ctx.row.get("accepted_by") or "").strip():
        out.append("accepted_by is empty; name who accepted the exposure (--accepted-by)")
    try:
        score = int(float(ctx.row["probability"])) * int(float(ctx.row["impact"]))
        band = ctx.profile.risk_band(score)
    except (KeyError, ValueError, TypeError):
        band = None
    if band and band["priority"] in ("Critical", "High") and not ctx.note:
        out.append("a %s risk needs a note explaining why it is accepted (--note)" % band["priority"])
    return out


def linked_issue_exists(ctx):
    ref = (ctx.row.get("linked_issue") or "").strip()
    if not ref:
        return ["linked_issue is empty; log the issue first (`pmf issue add`) and pass --linked-issue"]
    if ctx.ws.find("issues", ref) is None:
        return ["linked issue %s does not exist in issues.csv" % ref]
    return []


# ---------------- change ----------------
def sizing_present(ctx):
    need = ["effort_person_weeks", "cost_delta", "schedule_delta_days", "risk_note"]
    out = ["%s is required" % k for k in need if is_placeholder(ctx.row.get(k))]
    for k in need[:3]:
        v = ctx.row.get(k)
        if v and not is_placeholder(v) and not is_num(v):
            out.append("%s %r is not a number" % (k, v))
    return out


def required_approvers(ctx):
    cost = num(ctx.row.get("cost_delta") or 0, "cost_delta")
    days = num(ctx.row.get("schedule_delta_days") or 0, "schedule_delta_days")
    t = ctx.profile.tier_for(cost, days)
    return t, t["approvers"]


def all_tier_approvers_signed(ctx):
    try:
        t, need = required_approvers(ctx)
    except Exception as e:
        return [str(e)]
    have = [x.lower() for x in split_list(ctx.row.get("approvers_signed"))]
    miss = [a for a in need if a.lower() not in have]
    if miss:
        return ["tier %s needs sign-off from: %s (signed so far: %s)" % (t["label"], ", ".join(need), ", ".join(have) or "nobody")]
    return []


def decision_ref_present(ctx):
    ref = (ctx.row.get("decision_ref") or "").strip()
    if not ref:
        return ["decision_ref is empty; file the signed approval as decisions/DR-NNN.md and pass --decision-ref"]
    if not os.path.exists(ctx.ws.decision_path(ref)):
        return ["decision record %s not found at decisions/%s.md" % (ref, ref)]
    return []


def budget_row_logged(ctx):
    try:
        cost = num(ctx.row.get("cost_delta") or 0, "cost_delta")
    except Exception as e:
        return [str(e)]
    if cost == 0:
        return []
    since = ctx.row.get("date") or ""
    for b in ctx.ws.load("budget", required=False):
        if is_date(b.get("updated", "")) and is_date(since) and b["updated"] >= since:
            return []
    return ["a cost change needs a budget.csv forecast update dated on or after %s; update budget.csv first" % (since or "the change date")]


# ---------------- gate ----------------
def _gate_criteria(ctx):
    g = ctx.profile.gate(ctx.row.get("id"))
    if g:
        return g["exit_criteria"]
    if ctx.row.get("type") == "issue-triggered":
        return ["Triggering issue resolved"]
    return []


def exit_criteria_listed(ctx):
    if ctx.row.get("type") == "issue-triggered" and not (ctx.row.get("triggered_by") or "").strip():
        return ["an issue-triggered gate needs triggered_by (the issue that caused it)"]
    return [] if _gate_criteria(ctx) else ["gate %s has no exit criteria in the profile" % ctx.row.get("id")]


def _met(ctx):
    n = len(_gate_criteria(ctx))
    met = set()
    for x in split_list(ctx.row.get("criteria_met")):
        if x.isdigit() and 1 <= int(x) <= n:
            met.add(int(x))
    return n, met


def all_criteria_met(ctx):
    n, met = _met(ctx)
    miss = [i for i in range(1, n + 1) if i not in met]
    if miss:
        crit = _gate_criteria(ctx)
        return ["criteria not met: " + "; ".join("%d. %s" % (i, crit[i - 1]) for i in miss)]
    return []


def no_blocking_open_issues(ctx):
    g = ctx.profile.gate(ctx.row.get("id"))
    sev = (g or {}).get("requires_no_open_severity", [])
    if not sev:
        return []
    blocking = ctx.ws.open_issues(set(sev))
    if blocking:
        return ["open Sev %s issue(s) block this gate: %s" % ("/".join(str(s) for s in sev), ", ".join(i["id"] for i in blocking))]
    return []


def waiver_for_each_unmet_criterion(ctx):
    n, met = _met(ctx)
    unmet = n - len(met)
    if unmet <= 0:
        return ["use `gate go`: every criterion is met"]
    signed = 0
    problems = []
    for ref in split_list(ctx.row.get("waiver_refs")):
        rec = records.parse_decision(ctx.ws.decision_path(ref))
        if rec is None:
            problems.append("waiver %s not found at decisions/%s.md" % (ref, ref))
        elif (rec.get("signed") or "").strip().lower() == "yes":
            signed += 1
        else:
            problems.append("waiver %s is not signed" % ref)
    if signed < unmet:
        problems.append("%d unmet criteri%s, %d signed waiver(s)" % (unmet, "on" if unmet == 1 else "a", signed))
    return problems


def issue_logged_for_each_unmet_criterion(ctx):
    n, met = _met(ctx)
    unmet = n - len(met)
    if unmet <= 0:
        return ["use `gate go`: every criterion is met"]
    have = [i for i in ctx.ws.load("issues") if i.get("gate_found") == ctx.row.get("id")]
    if len(have) < unmet:
        return ["%d unmet criteri%s but %d issue(s) logged with gate_found=%s; log the rest first" % (
            unmet, "on" if unmet == 1 else "a", len(have), ctx.row.get("id"))]
    return []


GUARDS = {
    "has_required_fields": has_required_fields, "single_owner": single_owner, "valid_severity": valid_severity,
    "valid_phase": valid_phase, "decision_record_has_three_options": decision_record_has_three_options,
    "decision_record_has_recommendation": decision_record_has_recommendation, "decision_chosen": decision_chosen,
    "decision_signed_if_waive_or_defer": decision_signed_if_waive_or_defer, "option_is_fix_or_waive": option_is_fix_or_waive,
    "verification_ref_present": verification_ref_present, "option_is_defer": option_is_defer,
    "customer_acceptance_if_customer_visible": customer_acceptance_if_customer_visible,
    "brief_present_if_required": brief_present_if_required, "lesson_present": lesson_present, "reason_present": reason_present,
    "valid_probability": valid_probability, "valid_impact": valid_impact, "mitigation_present": mitigation_present,
    "acceptor_named": acceptor_named, "linked_issue_exists": linked_issue_exists, "sizing_present": sizing_present,
    "all_tier_approvers_signed": all_tier_approvers_signed, "decision_ref_present": decision_ref_present,
    "budget_row_logged": budget_row_logged, "exit_criteria_listed": exit_criteria_listed, "all_criteria_met": all_criteria_met,
    "no_blocking_open_issues": no_blocking_open_issues, "waiver_for_each_unmet_criterion": waiver_for_each_unmet_criterion,
    "issue_logged_for_each_unmet_criterion": issue_logged_for_each_unmet_criterion,
}
