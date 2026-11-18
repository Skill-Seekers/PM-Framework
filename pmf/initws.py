"""`pmf init`: create a program workspace. Writes structure only; dates, owners and numbers stay blank."""
import io
import json
import os
import shutil

from pmf import profile as prof
from pmf.schemas import SCHEMAS
from pmf.util import PmfError, is_num, parse_date, write_csv

BLANK = ("issues", "risks", "assumptions", "dependencies", "budget", "changes", "vendors", "contention", "events")


def init_workspace(target, program, profile_name, baseline_start="", baseline_end="", baseline_budget=""):
    if not program or not program.strip():
        raise PmfError("--program NAME is required")
    cfg_path = os.path.join(target, prof.CONFIG_NAME)
    if os.path.exists(cfg_path):
        raise PmfError("%s already exists in %s; init never overwrites a workspace" % (prof.CONFIG_NAME, target))
    src = prof.resolve_profile_path(profile_name)
    p = prof.load_json(src, "profile")
    prof.validate_profile(p)
    for k, v in (("baseline-start", baseline_start), ("baseline-end", baseline_end)):
        if v:
            parse_date(v, "--" + k)
    if baseline_budget and not is_num(baseline_budget):
        raise PmfError("--baseline-budget %r is not a number" % baseline_budget)
    if not os.path.isdir(target):
        os.makedirs(target)
    for sub in ("decisions", "briefs", "reports"):
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    shutil.copyfile(src, os.path.join(target, "profile.json"))
    cfg = {"program": program.strip(), "profile": "profile.json", "baseline_start": baseline_start,
           "baseline_end": baseline_end, "baseline_budget": baseline_budget}
    with io.open(cfg_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")
    for name in BLANK:
        write_csv(os.path.join(target, SCHEMAS[name]["file"]), SCHEMAS[name]["columns"], [])
    raci = []
    for ph in p["phases"]:
        for party in p["parties"]:
            role = ph.get("raci", {}).get(party["id"], "")
            raci.append({"phase": ph["id"], "party": party["id"], "role": role, "note": ""})
    write_csv(os.path.join(target, "raci.csv"), SCHEMAS["raci"]["columns"], raci)
    gates = []
    for g in p["gates"]:
        gates.append({"id": g["id"], "name": g["name"], "phase": g["phase"], "type": g.get("type", "planned"),
                      "baseline_date": "", "planned_date": "", "actual_date": "", "state": "PLANNED",
                      "criteria_met": "", "waiver_refs": "", "triggered_by": ""})
    write_csv(os.path.join(target, "gates.csv"), SCHEMAS["gates"]["columns"], gates)
    return {"dir": target, "profile": p["profile_id"], "gates": len(gates), "phases": len(p["phases"])}
