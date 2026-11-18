#!/usr/bin/env python3
"""Check that module text, templates and the silicon profile agree (stdlib only).
Exit 0 = consistent, 1 = problems."""
import csv, importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
problems = []


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


P = json.load(open(os.path.join(ROOT, "profiles", "silicon.json")))
m = P["metrics"]

# numbers the modules print must equal the profile's numbers
def need(module, snippets):
    t = read("framework/modules/" + module)
    for s in snippets:
        if s not in t:
            problems.append("%s: expected text %r (profile value changed or module drifted)" % (module, s))

g, e, sv, b = m["gate_on_time"], m["escape_rate"], m["schedule_variance"], m["burn_ratio"]
need("08_program_metrics_and_health.md", [
    "≥%d%%" % g["green_min_pct"], "%d–%d%%" % (g["amber_min_pct"], g["green_min_pct"] - 1), "<%d%%" % g["amber_min_pct"],
    "±%d%%" % sv["green_max_pct"], "%d–%d%% behind" % (sv["green_max_pct"], sv["amber_max_pct"]), ">%d%% behind" % sv["amber_max_pct"],
    "<%d%%" % e["green_max_pct"], "%d–%d%%" % (e["green_max_pct"], e["amber_max_pct"]), ">%d%%" % e["amber_max_pct"],
    "%s–%s" % tuple(str(x) for x in b["green"]), "%s–%s" % (b["green"][1], b["amber_high"]), "below %s" % b["under_spend_amber_below"],
])
bands = sorted(P["risk"]["bands"], key=lambda x: -x["min"])
need("03_raid_vs_issue_register.md", ["%d–%d" % (x["min"], x["max"]) for x in bands] + [x["priority"] for x in bands])
cc = P["change_control"]
t07 = ["$%s" % format(x["max_cost"], ",") for x in cc["tiers"][:3]] + ["~%d%%" % cc["escalate_cumulative_pct"]]
need("07_budget_and_scope_control.md", t07)
sev = {l["level"]: l for l in P["severity"]["levels"]}
need("02_issue_management.md", ["Sev %d" % k for k in sev])
need("05_communication_cadence.md", [c["id"].capitalize() if c["id"] != "biweekly" else "Bi-weekly" for c in P["cadence"] if c["id"] != "monthly"])

# templates: csv headers equal schemas; document templates exist for each module 06 block
spec = importlib.util.spec_from_file_location("schemas", os.path.join(ROOT, "pmf", "schemas.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
for name, s in mod.SCHEMAS.items():
    p = os.path.join(ROOT, "templates", "csv", s["file"])
    if not os.path.exists(p):
        problems.append("missing template " + s["file"]); continue
    with open(p, newline="") as f:
        hdr = next(csv.reader(f))
    if hdr != s["columns"]:
        problems.append("%s header differs from schema" % s["file"])
t06 = read("framework/modules/06_communication_templates.md")
for num, fn in {"6.1": "exec_note", "6.2": "weekly_status", "6.3": "customer_email", "6.4": "gate_announcement", "6.5": "retrospective", "6.6": "kickoff_package"}.items():
    blk = re.search(r"(?s)## %s [^\n]+\n.*?```\n(.*?)```" % re.escape(num), t06).group(1).rstrip()
    doc = read("templates/documents/%s.md" % fn)
    if blk not in doc:
        problems.append("templates/documents/%s.md differs from Module 06 §%s" % (fn, num))

# decision record template must match what the CLI will parse
dr = read("templates/documents/decision_record.md")
for need_s in ["## Options", "| A |", "| B |", "| C |", "Recommendation:", "## Decision", "Chosen:", "Decided by:", "Decided on:", "Signed:"]:
    if need_s not in dr:
        problems.append("decision_record.md lacks %r" % need_s)
br = read("templates/documents/issue_brief.md")
for sec in ["## WHAT", "## IMPACT", "## OPTIONS", "## RECOMMENDATION", "## DECISION NEEDED BY"]:
    if sec not in br:
        problems.append("issue_brief.md lacks " + sec)

# nothing private or interview-related in shipped content
FORBID = re.compile(r"interview|granola|\.xlsx|\.docx|\.pptx|projects[\\/]", re.I)
for top in ("framework", "prompts", "templates", "profiles", "docs"):
    for dp, dn, fn in os.walk(os.path.join(ROOT, top)):
        for f in fn:
            p = os.path.join(dp, f)
            if f.endswith((".md", ".json", ".csv", ".html", ".svg")):
                for i, line in enumerate(open(p, encoding="utf-8"), 1):
                    mm = FORBID.search(line)
                    if mm and "ALLOW:" not in line:
                        problems.append("%s:%d contains %r" % (os.path.relpath(p, ROOT), i, mm.group(0)))

if problems:
    print("CONTENT CHECK: %d problem(s)" % len(problems))
    for x in problems:
        print(" -", x)
    sys.exit(1)
print("CONTENT CHECK: consistent")
