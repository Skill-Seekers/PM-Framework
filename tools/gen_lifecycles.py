#!/usr/bin/env python3
"""Generate docs/LIFECYCLES.md from pmf/data/lifecycles.json (stdlib only)."""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def render(L):
    out = ["# Lifecycles", "",
           "Generated from `pmf/data/lifecycles.json` by `tools/gen_lifecycles.py`. Do not edit by hand; "
           "edit the JSON and regenerate. A transition is refused unless every guard passes. "
           "Diagrams are drawn by `tools/gen_diagrams.py`; open `docs/diagrams/lifecycles.html` for all four with hover detail.", ""]
    names = {"issue": "Issue", "risk": "Risk", "change": "Change request (ECR)", "gate": "Gate"}
    for key in ("issue", "risk", "change", "gate"):
        e = L["entities"][key]
        out += ["## %s lifecycle" % names[key], "",
                "Register: `%s`. Starts in `%s`. Terminal: %s." % (
                    e["register"], e["initial"], ", ".join("`%s`" % t for t in e["terminal"])), "",
                "![%s lifecycle state diagram](diagrams/%s.svg)" % (names[key], key), ""]
        out += ["| State | Meaning |", "|---|---|"]
        for s, d in e["states"].items():
            out.append("| `%s` | %s |" % (s, d["meaning"]))
        out += ["", "| From | To | Command | Guards (all must pass) |", "|---|---|---|---|"]
        for t in e["transitions"]:
            out.append("| `%s` | `%s` | `pmf %s` | %s |" % (
                t["from"], t["to"], t["command"], ", ".join("`%s`" % g for g in t["guards"])))
        out += ["", "Rules:", ""]
        out += ["- " + r for r in e["rules"]]
        out.append("")
    ov = L["overlays"]["sev1"]
    out += ["## Sev 1 overlay", "", ov["meaning"], ""]
    out += ["- " + c for c in ov["checklist"]]
    out += ["", "## Guard reference", "", "| Guard | What it checks |", "|---|---|"]
    for g, d in sorted(L["guards"].items()):
        out.append("| `%s` | %s |" % (g, d))
    out.append("")
    return "\n".join(out)


def main(argv):
    src = os.path.join(ROOT, "pmf", "data", "lifecycles.json")
    dst = os.path.join(ROOT, "docs", "LIFECYCLES.md")
    text = render(json.load(open(src)))
    if "--check" in argv:
        cur = open(dst).read() if os.path.exists(dst) else ""
        if cur != text:
            print("docs/LIFECYCLES.md is out of date; run tools/gen_lifecycles.py")
            return 1
        return 0
    with open(dst, "w", newline="\n") as f:
        f.write(text)
    print("wrote", dst)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
