"""Parse decision records (decisions/DR-NNN.md) and management briefs (briefs/B-NNN.md)."""
import io
import os
import re

from pmf.util import is_date, is_num, is_placeholder

BRIEF_SECTIONS = ["WHAT", "IMPACT", "OPTIONS", "RECOMMENDATION", "DECISION NEEDED BY"]


def _read(path):
    if not os.path.exists(path):
        return None
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def _field(text, name):
    m = re.search(r"(?mi)^%s:[ \t]*(.*)$" % re.escape(name), text)
    return m.group(1).strip() if m else None


def parse_decision(path):
    """Return a dict, or None when the file does not exist."""
    text = _read(path)
    if text is None:
        return None
    rec = {"options": {}, "text": text}
    in_opts = False
    for line in text.splitlines():
        if line.strip().startswith("## Options"):
            in_opts = True
            continue
        if in_opts and line.startswith("## "):
            in_opts = False
        if in_opts and line.strip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and cells[0] in ("A", "B", "C") and len(cells) >= 5:
                rec["options"][cells[0]] = {"description": cells[1], "schedule": cells[2], "cost": cells[3], "risk": cells[4]}
    rec["recommendation"] = _field(text, "Recommendation")
    rec["chosen"] = _field(text, "Chosen")
    rec["decided_by"] = _field(text, "Decided by")
    rec["decided_on"] = _field(text, "Decided on")
    rec["signed"] = _field(text, "Signed")
    rec["customer_visible"] = _field(text, "Customer visible")
    rec["customer_acceptance"] = _field(text, "Customer acceptance")
    rec["issue"] = _field(text, "Issue")
    return rec


def option_problems(rec):
    """Messages for a record whose Options table is not complete."""
    out = []
    for k in ("A", "B", "C"):
        o = rec["options"].get(k)
        if not o:
            out.append("option %s is missing from the Options table" % k)
            continue
        if is_placeholder(o["description"]):
            out.append("option %s has no description" % k)
        for f in ("schedule", "cost"):
            if is_placeholder(o[f]) or not is_num(o[f]):
                out.append("option %s %s %r is not a number" % (k, f, o[f]))
    return out


def chosen_option(rec):
    c = (rec.get("chosen") or "").strip().upper()
    return c if c in ("A", "B", "C") else None


def decision_problems(rec):
    out = []
    if chosen_option(rec) is None:
        out.append("Chosen must be A, B or C (found %r)" % rec.get("chosen"))
    if is_placeholder(rec.get("decided_by")):
        out.append("Decided by is empty")
    if not is_date(rec.get("decided_on") or ""):
        out.append("Decided on must be a date (YYYY-MM-DD)")
    return out


def parse_brief(path):
    text = _read(path)
    if text is None:
        return None
    sections = {}
    cur = None
    for line in text.splitlines():
        m = re.match(r"^## (.+?)\s*$", line)
        if m:
            cur = m.group(1).strip()
            sections[cur] = []
        elif cur is not None:
            sections[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def brief_problems(brief):
    out = []
    for s in BRIEF_SECTIONS:
        body = brief.get(s)
        if body is None:
            out.append("section %s is missing" % s)
        elif not body.strip() or re.search(r"\[[^\]]*\]", body):
            out.append("section %s is empty or still has a [placeholder]" % s)
    return out
