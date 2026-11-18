"""Lifecycle engine: create items, run guarded transitions, log every change to events.csv."""
import datetime
import re

from pmf import records
from pmf.guards import GUARDS, Context
from pmf.schemas import SCHEMAS
from pmf.util import (ActionNeeded, PmfError, fmt_num, is_date, is_num, next_id, num, parse_date)

ENTITY_REGISTER = {"issue": "issues", "risk": "risks", "change": "changes", "gate": "gates"}
FROZEN_FIELDS = ("id", "state")


def spec(ws, entity):
    return ws.lifecycles["entities"][entity]


def validate_fields(register, fields):
    """Reject unknown columns and malformed dates, numbers and enumerations (PmfError, exit 2)."""
    s = SCHEMAS[register]
    for k, v in fields.items():
        if k not in s["columns"]:
            raise PmfError("%s has no column %r (columns: %s)" % (s["file"], k, ", ".join(s["columns"])))
        if v in (None, ""):
            continue
        if k in s.get("dates", []) and not is_date(v):
            raise PmfError("%s %r is not a date; use YYYY-MM-DD" % (k, v))
        if k in s.get("numbers", []) and not is_num(v):
            raise PmfError("%s %r is not a number" % (k, v))
        enum = s.get("enums", {}).get(k)
        if enum and v not in enum:
            raise PmfError("%s must be one of %s (got %r)" % (k, ", ".join(enum), v))


def _clean(fields):
    return {k: ("" if v is None else str(v)) for k, v in fields.items() if v is not None}


def create(ws, entity, fields, actor, note="", ref="", dry_run=False):
    """Create a new item in its initial state (issue add, risk add, change request, gate add)."""
    reg = ENTITY_REGISTER[entity]
    s = SCHEMAS[reg]
    fields = _clean(fields)
    fields.pop("state", None)
    validate_fields(reg, fields)
    rows = ws.load(reg)
    ident = fields.get("id") or next_id(s["id_prefix"], [r["id"] for r in rows])
    if any(r["id"] == ident for r in rows):
        raise PmfError("%s %s already exists" % (entity, ident))
    row = {c: "" for c in s["columns"]}
    row.update(fields)
    row["id"] = ident
    row["state"] = spec(ws, entity)["initial"]
    problems = []
    if not (row.get("title") or row.get("name")):
        problems.append("a title is required")
    if entity == "issue" and not row.get("detected"):
        row["detected"] = ws.report_date.isoformat()
    if entity == "risk" and not row.get("last_scored"):
        pass
    if entity == "change":
        if not row.get("date"):
            row["date"] = ws.report_date.isoformat()
        if not row.get("requestor"):
            problems.append("requestor is required")
    if entity == "gate":
        row["type"] = "issue-triggered"
        if not row.get("triggered_by"):
            problems.append("triggered_by (the issue that caused the gate) is required")
        elif ws.find("issues", row["triggered_by"]) is None:
            problems.append("triggered_by %s is not an issue in issues.csv" % row["triggered_by"])
    if problems:
        raise ActionNeeded(problems, title="cannot create %s" % entity)
    if not dry_run:
        rows.append(row)
        ws.save(reg, rows)
        ws.add_event(entity, ident, "transition", "", row["state"], actor, note, ref)
    return {"id": ident, "from": "", "to": row["state"], "row": row, "dry_run": dry_run}


def _effects(ws, entity, command, row, old):
    """Deterministic follow-on field updates. Never invents facts: it copies what the records say."""
    cmd = command
    rd = ws.report_date.isoformat()
    if entity == "issue":
        if cmd == "decide":
            rec = records.parse_decision(ws.decision_path(row.get("decision_ref", "")))
            opt = records.chosen_option(rec) if rec else None
            if opt:
                o = rec["options"][opt]
                row["sched_impact_days"] = fmt_num(num(o["schedule"]))
                row["cost_impact"] = fmt_num(num(o["cost"]))
        elif cmd == "close":
            row["closed"] = rd
        elif cmd == "reopen":
            row["closed"] = ""
    elif entity == "risk":
        if cmd == "assess":
            row["last_scored"] = rd
            score = int(float(row["probability"])) * int(float(row["impact"]))
            band = ws.profile.risk_band(score)
            if band and not row.get("next_review"):
                row["next_review"] = (ws.report_date + datetime.timedelta(days=band["review_days"])).isoformat()
    elif entity == "gate":
        if cmd in ("go", "conditional") and not row.get("actual_date"):
            row["actual_date"] = rd


def transition(ws, entity, ident, command, fields, actor, note="", ref="", dry_run=False):
    reg = ENTITY_REGISTER[entity]
    rows = ws.load(reg)
    old = next((r for r in rows if r["id"] == ident), None)
    if old is None:
        raise PmfError("%s %s not found in %s" % (entity, ident, SCHEMAS[reg]["file"]))
    sp = spec(ws, entity)
    full_cmd = "%s %s" % (entity, command)
    cands = [t for t in sp["transitions"] if t["command"] == full_cmd and t["from"] == old["state"]]
    if not cands:
        here = sorted({t["command"].split(" ", 1)[1] + " -> " + t["to"] for t in sp["transitions"] if t["from"] == old["state"]})
        known = sorted({t["command"] for t in sp["transitions"]})
        if full_cmd not in known:
            raise PmfError("unknown command %r (known: %s)" % (full_cmd, ", ".join(known)))
        raise ActionNeeded(["%s is %s; `%s` is not allowed from that state" % (ident, old["state"], full_cmd),
                            "allowed from %s: %s" % (old["state"], ", ".join(here) or "nothing (terminal)")],
                           title="refused")
    t = cands[0]
    fields = _clean(fields)
    for k in FROZEN_FIELDS:
        fields.pop(k, None)
    validate_fields(reg, fields)
    new = dict(old)
    new.update(fields)
    ctx = Context(ws, entity, new, old, command, note, ref)
    failures = []
    for g in t["guards"]:
        for msg in GUARDS[g](ctx):
            failures.append("[%s] %s" % (g, msg))
    if failures:
        raise ActionNeeded(failures, title="%s refused: %s %s -> %s" % (full_cmd, ident, old["state"], t["to"]))
    _effects(ws, entity, command, new, old)
    new["state"] = t["to"]
    changed = {k: (old.get(k, ""), new.get(k, "")) for k in SCHEMAS[reg]["columns"] if old.get(k, "") != new.get(k, "")}
    if not dry_run:
        for i, r in enumerate(rows):
            if r["id"] == ident:
                rows[i] = new
        ws.save(reg, rows)
        ws.add_event(entity, ident, "transition", old["state"], t["to"], actor, note, ref)
    return {"id": ident, "from": old["state"], "to": t["to"], "changed": changed, "row": new, "dry_run": dry_run}


def change_severity(ws, ident, level, reason, actor, dry_run=False):
    rows = ws.load("issues")
    row = next((r for r in rows if r["id"] == ident), None)
    if row is None:
        raise PmfError("issue %s not found" % ident)
    if int(level) not in ws.profile.levels:
        raise ActionNeeded(["severity %s is not one of %s" % (level, sorted(ws.profile.levels))], title="refused")
    if not reason:
        raise ActionNeeded(["a reason is required: pass --note \"why\""], title="severity change refused")
    if row["state"] == "CLOSED":
        raise ActionNeeded(["issue %s is CLOSED; reopen it first" % ident], title="severity change refused")
    old = row["severity"]
    if not dry_run:
        row["severity"] = str(int(level))
        ws.save("issues", rows)
        ws.add_event("issue", ident, "severity_change", row["state"], row["state"], actor, "%s -> %s: %s" % (old, level, reason))
    return {"id": ident, "from": old, "to": str(int(level)), "dry_run": dry_run}


def rescore_risk(ws, ident, probability, impact, reason, actor, dry_run=False):
    rows = ws.load("risks")
    row = next((r for r in rows if r["id"] == ident), None)
    if row is None:
        raise PmfError("risk %s not found" % ident)
    if row["state"] in ("OCCURRED", "RETIRED", "IDENTIFIED"):
        raise ActionNeeded(["risk %s is %s; only assessed risks can be re-scored (use `risk assess` first)" % (ident, row["state"])], title="refused")
    new = dict(row)
    if probability is not None:
        new["probability"] = str(probability)
    if impact is not None:
        new["impact"] = str(impact)
    ctx = Context(ws, "risk", new, row, "rescore", reason)
    bad = GUARDS["valid_probability"](ctx) + GUARDS["valid_impact"](ctx)
    if not reason:
        bad.append("a reason is required: pass --note \"what changed\"")
    if bad:
        raise ActionNeeded(bad, title="re-score refused")
    score = int(float(new["probability"])) * int(float(new["impact"]))
    band = ws.profile.risk_band(score)
    new["last_scored"] = ws.report_date.isoformat()
    new["next_review"] = (ws.report_date + datetime.timedelta(days=band["review_days"])).isoformat()
    if not dry_run:
        for i, r in enumerate(rows):
            if r["id"] == ident:
                rows[i] = new
        ws.save("risks", rows)
        ws.add_event("risk", ident, "rescore", row["state"], row["state"], actor,
                     "%sx%s -> %sx%s (score %d, %s): %s" % (row["probability"], row["impact"], new["probability"], new["impact"], score, band["priority"], reason))
    return {"id": ident, "score": score, "priority": band["priority"], "dry_run": dry_run}


def score_of(risk):
    try:
        return int(float(risk["probability"])) * int(float(risk["impact"]))
    except (KeyError, TypeError, ValueError):
        return None
