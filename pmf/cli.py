"""pmf command line. Exit codes: 0 done, 1 action needed (a check or guard said no), 2 could not run."""
import argparse
import getpass
import io
import json
import os
import sys

from pmf import __version__, check, dashboard, lifecycle, metrics, reports
from pmf import profile as prof
from pmf.initws import init_workspace
from pmf.schemas import SCHEMAS
from pmf.util import (EXIT_ACTION, EXIT_COULD_NOT_RUN, EXIT_DONE, ActionNeeded, PmfError, is_num, parse_date)
from pmf.workspace import Workspace

ENTITIES = ("issue", "risk", "change", "gate")
CREATE_VERB = {"issue": "add", "risk": "add", "change": "request", "gate": "add"}
SKIP_FLAGS = ("id", "state")
RESERVED = ("note", "ref", "actor", "workspace", "dry_run", "report_date", "json")


def _flag(col):
    return "--" + col.replace("_", "-")


def _common(p):
    p.add_argument("-w", "--workspace", help="program workspace folder (default: search upward for pmf.config.json, or $PMF_WORKSPACE)")
    p.add_argument("--actor", help="who is acting (default: $PMF_ACTOR, then your login name)")
    p.add_argument("--note", default="", help="why; stored in events.csv")
    p.add_argument("--ref", default="", help="a document or ticket reference; stored in events.csv")
    p.add_argument("--dry-run", action="store_true", help="show what would change; write nothing")
    p.add_argument("--report-date", help="treat this YYYY-MM-DD as today (default: today, or report_date in the config)")


def _field_flags(p, register):
    for c in SCHEMAS[register]["columns"]:
        if c in SKIP_FLAGS or c in RESERVED:
            continue
        p.add_argument(_flag(c), dest="f_" + c, default=None, metavar=c.upper())


def build_parser(lc):
    ap = argparse.ArgumentParser(prog="pmf", description="PM-Framework: keep a program's registers honest. The tool never invents data, "
                                 "never sends, approves or closes on your behalf, and refuses transitions the lifecycle does not allow.")
    ap.add_argument("--version", action="version", version="pmf " + __version__)
    sub = ap.add_subparsers(dest="cmd", metavar="COMMAND")

    # init
    p = sub.add_parser("init", help="create a program workspace")
    p.add_argument("dir", nargs="?", default=".", help="folder to create or use (default: here)")
    p.add_argument("--program", required=True)
    p.add_argument("--profile", default="silicon", help="shipped profile (%s) or a path" % ", ".join(prof.shipped_profiles() or ["silicon", "software"]))
    p.add_argument("--baseline-start", default="")
    p.add_argument("--baseline-end", default="")
    p.add_argument("--baseline-budget", default="")

    # lifecycle entities
    for ent in ENTITIES:
        spec = lc["entities"][ent]
        reg = lifecycle.ENTITY_REGISTER[ent]
        ep = sub.add_parser(ent, help="%s lifecycle (%s)" % (ent, " -> ".join(list(spec["states"])[:5])))
        es = ep.add_subparsers(dest="verb", metavar="VERB")
        cp = es.add_parser(CREATE_VERB[ent], help="create a %s in %s" % (ent, spec["initial"]))
        _common(cp)
        _field_flags(cp, reg)
        cp.add_argument("--id", default=None)
        verbs = []
        for t in spec["transitions"]:
            v = t["command"].split(" ", 1)[1]
            if v not in verbs:
                verbs.append(v)
        for v in verbs:
            tos = sorted({t["to"] for t in spec["transitions"] if t["command"] == "%s %s" % (ent, v)})
            vp = es.add_parser(v, help="-> %s" % "/".join(tos))
            vp.add_argument("id")
            _common(vp)
            _field_flags(vp, reg)
        if ent == "issue":
            sp = es.add_parser("sev", help="change an issue's severity (needs --note)")
            sp.add_argument("id")
            sp.add_argument("level", type=int)
            _common(sp)
        if ent == "risk":
            rp = es.add_parser("rescore", help="re-score probability/impact (needs --note)")
            rp.add_argument("id")
            rp.add_argument("--probability", type=int)
            rp.add_argument("--impact", type=int)
            _common(rp)

    # reports and views
    p = sub.add_parser("check", help="validate every register, record and cross-reference")
    _common(p)
    p.add_argument("--strict", action="store_true", help="warnings also exit 1")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("health", help="the five metrics and the worst-of rollup")
    _common(p)
    p.add_argument("--json", action="store_true")
    p.add_argument("--fail-on", choices=["amber", "red"], help="exit 1 when the rollup is at least this bad")
    p = sub.add_parser("brief", help="draft a management brief for a Sev 1/2 issue (briefs/B-NNN.md)")
    p.add_argument("id")
    _common(p)
    p.add_argument("--stdout", action="store_true")
    p = sub.add_parser("report", help="draft a report")
    rs = p.add_subparsers(dest="kind", metavar="KIND")
    for k, h in (("weekly", "weekly status draft"),):
        q = rs.add_parser(k, help=h)
        _common(q)
        q.add_argument("--stdout", action="store_true")
        q.add_argument("--force", action="store_true")
    p = sub.add_parser("raid", help="RAID snapshot; always includes open Sev 1/2 issues")
    _common(p)
    p.add_argument("--stdout", action="store_true")
    p.add_argument("--force", action="store_true")
    p = sub.add_parser("dashboard", help="write a read-only HTML health dashboard (reports/dashboard_DATE.html)")
    _common(p)
    p.add_argument("--stdout", action="store_true", help="print the HTML instead of writing a file")
    p.add_argument("--out", help="write to this path instead of reports/dashboard_DATE.html")
    p = sub.add_parser("show", help="show one item and its event history")
    p.add_argument("id")
    _common(p)
    p = sub.add_parser("lifecycles", help="print the lifecycle tables")
    p.add_argument("entity", nargs="?", choices=ENTITIES)
    return ap


# ------------------------------------------------------------------ helpers
def _actor(args, ws):
    if getattr(args, "actor", None):
        return args.actor
    if os.environ.get("PMF_ACTOR"):
        return os.environ["PMF_ACTOR"]
    if ws and ws.config.get("default_actor"):
        return ws.config["default_actor"]
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


def _open(args):
    root = prof.find_workspace_root(explicit=getattr(args, "workspace", None))
    return Workspace(root, report_date=getattr(args, "report_date", None))


def _fields(args):
    return {k[2:]: v for k, v in vars(args).items() if k.startswith("f_") and v is not None}


def _out(msg=""):
    sys.stdout.write(msg + "\n")


def _err(msg):
    sys.stderr.write(msg + "\n")


def _show_change(res, ent):
    prefix = "DRY RUN (nothing written): " if res.get("dry_run") else ""
    if res["from"]:
        _out("%s%s %s %s -> %s" % (prefix, ent, res["id"], res["from"], res["to"]))
    else:
        _out("%s%s %s created in %s" % (prefix, ent, res["id"], res["to"]))
    for k, (a, b) in sorted(res.get("changed", {}).items()):
        if k != "state":
            _out("  %s: %r -> %r" % (k, a, b))


# ------------------------------------------------------------------ handlers
def cmd_init(args):
    target = os.path.abspath(args.dir)
    r = init_workspace(target, args.program, args.profile, args.baseline_start, args.baseline_end, args.baseline_budget)
    _out("workspace created in %s" % target)
    _out("  profile %s: %d phases, %d gates" % (r["profile"], r["phases"], r["gates"]))
    _out("  dates, owners and numbers are blank on purpose; fill gates.csv baseline_date and set baseline_start/end/budget in %s" % prof.CONFIG_NAME)
    _out("  next: pmf check")
    return EXIT_DONE


def cmd_entity(args, ws, lc):
    ent = args.cmd
    verb = args.verb
    actor = _actor(args, ws)
    if verb == CREATE_VERB[ent]:
        fields = _fields(args)
        if args.id:
            fields["id"] = args.id
        res = lifecycle.create(ws, ent, fields, actor, args.note, args.ref, args.dry_run)
        _show_change(res, ent)
        return EXIT_DONE
    if ent == "issue" and verb == "sev":
        res = lifecycle.change_severity(ws, args.id, args.level, args.note, actor, args.dry_run)
        _out("%sissue %s severity %s -> %s" % ("DRY RUN (nothing written): " if args.dry_run else "", res["id"], res["from"], res["to"]))
        return EXIT_DONE
    if ent == "risk" and verb == "rescore":
        res = lifecycle.rescore_risk(ws, args.id, args.probability, args.impact, args.note, actor, args.dry_run)
        _out("%srisk %s re-scored: %s (%s)" % ("DRY RUN (nothing written): " if args.dry_run else "", res["id"], res["score"], res["priority"]))
        return EXIT_DONE
    res = lifecycle.transition(ws, ent, args.id, verb, _fields(args), actor, args.note, args.ref, args.dry_run)
    _show_change(res, ent)
    return EXIT_DONE


def cmd_check(args, ws):
    errs, warns = check.run(ws)
    if args.json:
        _out(json.dumps({"errors": errs, "warnings": warns}, indent=2))
    else:
        for m in errs:
            _out("ERROR  " + m)
        for m in warns:
            _out("WARN   " + m)
        _out("%d error(s), %d warning(s)" % (len(errs), len(warns)))
    if errs or (args.strict and warns):
        return EXIT_ACTION
    return EXIT_DONE


def cmd_health(args, ws):
    res = metrics.compute(ws)
    if args.json:
        _out(json.dumps(res, indent=2))
    else:
        _out("%s - %s" % (res["program"], res["report_date"]))
        for m in res["metrics"]:
            value = "" if m["value"] == "not rated" else m["value"] + " | "
            _out("%-20s %-9s %s%s" % (m["name"], m["color"].upper() if m["color"] != "grey" else "NOT RATED", value, m["rule"]))
            for d in m["detail"]:
                _out("    " + d)
        _out("ROLLUP %s - %s" % (res["rollup"]["color"].upper(), res["rollup"]["reason"]))
    if args.fail_on:
        worst = {"green": 0, "grey": 0, "amber": 1, "red": 2}[res["rollup"]["color"]]
        if worst >= {"amber": 1, "red": 2}[args.fail_on]:
            return EXIT_ACTION
    return EXIT_DONE


def cmd_brief(args, ws):
    bid, text = reports.draft_brief(ws, args.id, _actor(args, ws))
    if args.stdout:
        _out(text)
        return EXIT_DONE
    path = ws.brief_path(bid)
    if args.dry_run:
        _out("DRY RUN (nothing written): would create briefs/%s.md and set %s brief_ref=%s" % (bid, args.id, bid))
        return EXIT_DONE
    reports.write_draft(path, text)
    rows = ws.load("issues")
    for r in rows:
        if r["id"] == args.id:
            r["brief_ref"] = bid
    ws.save("issues", rows)
    ws.add_event("issue", args.id, "edit", next(r["state"] for r in rows if r["id"] == args.id),
                 next(r["state"] for r in rows if r["id"] == args.id), _actor(args, ws), "brief %s drafted" % bid, bid)
    _out("drafted briefs/%s.md for %s; edit every [placeholder] before `issue close`" % (bid, args.id))
    return EXIT_DONE


def _emit(ws, args, relpath, text):
    if args.stdout:
        _out(text)
        return EXIT_DONE
    path = ws.path(*relpath)
    if args.dry_run:
        _out("DRY RUN (nothing written): would write %s" % "/".join(relpath))
        return EXIT_DONE
    how = reports.write_draft(path, text, force=args.force, label="/".join(relpath))
    _out("%s %s" % (how, "/".join(relpath)))
    return EXIT_DONE


def cmd_report(args, ws):
    if args.kind != "weekly":
        raise PmfError("choose a report: weekly")
    return _emit(ws, args, ("reports", "weekly_%s.md" % ws.report_date.isoformat()), reports.weekly(ws))


def cmd_raid(args, ws):
    return _emit(ws, args, ("reports", "raid_%s.md" % ws.report_date.isoformat()), reports.raid(ws))


def cmd_dashboard(args, ws):
    text = dashboard.render(ws)
    if args.stdout:
        sys.stdout.write(text)
        return EXIT_DONE
    name = "dashboard_%s.html" % ws.report_date.isoformat()
    path = args.out or ws.path("reports", name)
    label = (args.out or "reports/" + name).replace("\\", "/")
    if args.dry_run:
        _out("DRY RUN (nothing written): would write %s" % label)
        return EXIT_DONE
    existing = None
    if os.path.exists(path):
        with io.open(path, encoding="utf-8", newline="") as f:
            existing = f.read()
    if existing == text:
        _out("unchanged %s" % label)
        return EXIT_DONE
    reports._write(path, text)
    _out("%s %s (read-only view; the CSV registers stay the edit surface)" % ("updated" if existing is not None else "created", label))
    return EXIT_DONE


def cmd_show(args, ws):
    prefixes = {"I": ("issue", "issues"), "R": ("risk", "risks"), "C": ("change", "changes"), "X": ("gate", "gates")}
    kind = None
    for pfx, (ent, reg) in prefixes.items():
        if args.id.startswith(pfx + "-") or (pfx == "X" and args.id.startswith("G")):
            kind = (ent, reg)
    row = None
    if kind:
        row = ws.find(kind[1], args.id)
    if row is None:
        for ent, reg in (("issue", "issues"), ("risk", "risks"), ("change", "changes"), ("gate", "gates")):
            row = ws.find(reg, args.id)
            if row:
                kind = (ent, reg)
                break
    if row is None:
        raise PmfError("%s not found in issues, risks, changes or gates" % args.id)
    _out("%s %s" % (kind[0], args.id))
    for k in SCHEMAS[kind[1]]["columns"]:
        if row.get(k):
            _out("  %-18s %s" % (k, row[k]))
    _out("history:")
    for e in ws.events():
        if e["entity"] == kind[0] and e["id"] == args.id:
            _out("  %s  %s  %s -> %s  by %s%s" % (e["ts"], e["event"], e["from_state"] or "-", e["to_state"], e["actor"], ("  (%s)" % e["note"]) if e["note"] else ""))
    return EXIT_DONE


def cmd_lifecycles(args, lc):
    ents = [args.entity] if args.entity else list(ENTITIES)
    for ent in ents:
        sp = lc["entities"][ent]
        _out("%s  (register %s, starts %s)" % (ent, SCHEMAS[lifecycle.ENTITY_REGISTER[ent]]["file"], sp["initial"]))
        for t in sp["transitions"]:
            _out("  %-14s %-15s -> %-15s guards: %s" % (t["command"], t["from"], t["to"], ", ".join(t["guards"]) or "none"))
    return EXIT_DONE


# ------------------------------------------------------------------ main
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        lc = prof.lifecycles()
        ap = build_parser(lc)
        args = ap.parse_args(argv)
        if not args.cmd:
            ap.print_help()
            return EXIT_COULD_NOT_RUN
        if args.cmd == "init":
            return cmd_init(args)
        if args.cmd == "lifecycles":
            return cmd_lifecycles(args, lc)
        if args.cmd in ENTITIES and not args.verb:
            ap.parse_args([args.cmd, "--help"])
        if args.cmd == "report" and not args.kind:
            ap.parse_args(["report", "--help"])
        ws = _open(args)
        if args.cmd in ENTITIES:
            return cmd_entity(args, ws, lc)
        handler = {"check": cmd_check, "health": cmd_health, "brief": cmd_brief, "report": cmd_report, "dashboard": cmd_dashboard,
                   "raid": cmd_raid, "show": cmd_show}[args.cmd]
        return handler(args, ws)
    except ActionNeeded as e:
        _err("%s" % (e.title or "action needed"))
        for m in e.messages:
            _err("  - " + m)
        return EXIT_ACTION
    except PmfError as e:
        _err("pmf: " + str(e))
        return EXIT_COULD_NOT_RUN
    except KeyboardInterrupt:
        return EXIT_COULD_NOT_RUN


if __name__ == "__main__":
    sys.exit(main())
