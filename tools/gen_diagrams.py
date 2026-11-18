#!/usr/bin/env python3
"""Draw the four lifecycle state machines as SVG, straight from pmf/data/lifecycles.json.

Writes docs/diagrams/{issue,risk,change,gate}.svg and docs/diagrams/lifecycles.html.
The layout below is hand-placed (four small graphs), but every state and every transition comes from the
JSON: the script fails if the layout misses a state or a transition, so a diagram can never be stale.

  python3 tools/gen_diagrams.py            write the files
  python3 tools/gen_diagrams.py --check    exit 1 if the committed files differ from a fresh render

Standard library only (Python 3.8+).
"""
import html
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "diagrams")

BW, BH = 164, 50          # state box
PX, PY = 268, 132         # cell pitch
MX, MY = 56, 96           # margins (top margin leaves room for arcs)

# cell positions (col, row). "groups": states drawn inside one dashed container, with commands leaving the container.
LAYOUT = {
    "issue": {
        "pos": {"DETECTED": (0, 0), "LOGGED": (1, 0), "TRIAGED": (2, 0), "DECIDED": (3, 0), "RESOLVED": (4, 0),
                "CLOSED": (5, 0), "DEFERRED": (3, 1)},
        # (command, from, to): (route kind, args, dashed)
        "routes": {
            ("issue log", "DETECTED", "LOGGED"): ("s", "r", "l", False),
            ("issue triage", "LOGGED", "TRIAGED"): ("s", "r", "l", False),
            ("issue decide", "TRIAGED", "DECIDED"): ("s", "r", "l", False),
            ("issue resolve", "DECIDED", "RESOLVED"): ("s", "r", "l", False),
            ("issue close", "RESOLVED", "CLOSED"): ("s", "r", "l", False),
            ("issue defer", "DECIDED", "DEFERRED"): ("s", "b", "t", False),
            ("issue retriage", "DEFERRED", "TRIAGED"): ("p", [("DEFERRED", "l", 0, 0), ("TRIAGED", "c", 0, PY / float(BH)), ("TRIAGED", "b", 0, 0)], True),
            ("issue reopen", "CLOSED", "TRIAGED"): ("p", [("CLOSED", "t", 0, 0), ("CLOSED", "t", 0, -0.75), ("TRIAGED", "t", 0, -0.75), ("TRIAGED", "t", 0, 0)], True),
        },
        "groups": [],
    },
    "risk": {
        "pos": {"IDENTIFIED": (0, 0), "ASSESSED": (1, 0), "MITIGATING": (2, 0), "ACCEPTED": (2, 1), "OCCURRED": (3.5, 0), "RETIRED": (3.5, 1)},
        "routes": {
            ("risk assess", "IDENTIFIED", "ASSESSED"): ("s", "r", "l", False),
            ("risk mitigate", "ASSESSED", "MITIGATING"): ("s", "r", "l", False),
            ("risk accept", "ASSESSED", "ACCEPTED"): ("s", "b", "l", False),
        },
        # commands that leave a group container: (command, to state, route kind) ; the from-states must be exactly the members
        "groups": [{"members": ["ASSESSED", "MITIGATING", "ACCEPTED"], "label": "any one of these",
                    "exits": [("risk occur", "OCCURRED", 0), ("risk retire", "RETIRED", 1)]}],
    },
    "change": {
        "pos": {"REQUESTED": (0, 0), "ASSESSED": (1, 0), "APPROVED": (2, 0), "IMPLEMENTED": (3, 0), "VERIFIED": (4, 0),
                "DEFERRED": (1, 1), "REJECTED": (2, 1)},
        "routes": {
            ("change assess", "REQUESTED", "ASSESSED"): ("s", "r", "l", False),
            ("change approve", "ASSESSED", "APPROVED"): ("s", "r", "l", False),
            ("change implement", "APPROVED", "IMPLEMENTED"): ("s", "r", "l", False),
            ("change verify", "IMPLEMENTED", "VERIFIED"): ("s", "r", "l", False),
            ("change defer", "ASSESSED", "DEFERRED"): ("s", "b", "t", False),
            ("change reject", "ASSESSED", "REJECTED"): ("s", "b", "t", False),
        },
        "groups": [],
    },
    "gate": {
        "pos": {"PLANNED": (0, 1), "REVIEW": (1, 1), "GO": (3, 0), "CONDITIONAL_GO": (3, 1), "NO_GO": (3, 2)},
        "routes": {
            ("gate review", "PLANNED", "REVIEW"): ("s", "r", "l", False),
            ("gate go", "REVIEW", "GO"): ("s", "r", "l", False),
            ("gate conditional", "REVIEW", "CONDITIONAL_GO"): ("s", "r", "l", False),
            ("gate nogo", "REVIEW", "NO_GO"): ("s", "r", "l", False),
            ("gate review", "NO_GO", "REVIEW"): ("p", [("NO_GO", "b", 0, 0), ("NO_GO", "b", 0, 0.6), ("REVIEW", "b", 0, PY / float(BH) + 0.6), ("REVIEW", "b", 0, 0)], True),
        },
        "groups": [],
    },
}

TITLES = {"issue": "Issue lifecycle", "risk": "Risk lifecycle", "change": "Change lifecycle", "gate": "Gate lifecycle"}


def load():
    with io.open(os.path.join(ROOT, "pmf", "data", "lifecycles.json"), encoding="utf-8") as f:
        return json.load(f)


def center(pos, state):
    c, r = pos[state]
    return MX + BW / 2.0 + c * PX, MY + BH / 2.0 + r * PY


def side(pos, state, s, dx=0.0, dy=0.0):
    """Anchor point on a box side (l r t b) or its centre (c); dx, dy move it by that many pitch/box units."""
    x, y = center(pos, state)
    if s == "l":
        x -= BW / 2.0
    elif s == "r":
        x += BW / 2.0
    elif s == "t":
        y -= BH / 2.0
    elif s == "b":
        y += BH / 2.0
    return x + dx * BW, y + dy * BH


def f(n):
    s = ("%.1f" % n).rstrip("0").rstrip(".")
    return s or "0"


def esc(t):
    return html.escape(t, quote=True)


def label_box(x, y, text, cls="lbl"):
    w = max(34, len(text) * 7.0 + 14)
    return ('<g class="%s"><rect x="%s" y="%s" width="%s" height="20" rx="10"/><text x="%s" y="%s" text-anchor="middle">%s</text></g>'
            % (cls, f(x - w / 2), f(y - 10), f(w), f(x), f(y + 4), esc(text)))


STYLE = """
  .bg { fill: #ffffff; }
  .box { fill: #f6f8fa; stroke: #57606a; stroke-width: 1.5; }
  .initial .box { stroke: #0b5cad; stroke-width: 3; fill: #eaf2fb; }
  .terminal .box { fill: #e1e6eb; stroke: #57606a; stroke-width: 1.5; }
  .state text { fill: #1f2328; font: 600 13px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .edge { fill: none; stroke: #3d4650; stroke-width: 1.8; }
  .edge.back { stroke-dasharray: 7 5; }
  .tip { fill: #3d4650; }
  .lbl rect { fill: #ffffff; stroke: #8c959f; stroke-width: 1; }
  .lbl text { fill: #1f2328; font: 500 12px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  .lbl.back rect { fill: #fff8e6; }
  .group { fill: none; stroke: #8c959f; stroke-width: 1.5; stroke-dasharray: 3 4; }
  .grouplbl { fill: #57606a; font: 500 11px system-ui, sans-serif; }
  .title { fill: #1f2328; font: 700 16px system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  .legend { fill: #57606a; font: 500 11.5px system-ui, sans-serif; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #0d1117; }
    .box { fill: #161b22; stroke: #8b949e; }
    .initial .box { stroke: #58a6ff; fill: #12233a; }
    .terminal .box { fill: #21262d; stroke: #8b949e; }
    .state text { fill: #e6edf3; }
    .edge { stroke: #b6bec8; }
    .tip { fill: #b6bec8; }
    .lbl rect { fill: #0d1117; stroke: #6e7681; }
    .lbl text { fill: #e6edf3; }
    .lbl.back rect { fill: #2a2110; }
    .group { stroke: #6e7681; }
    .grouplbl, .legend { fill: #9da7b3; }
    .title { fill: #e6edf3; }
  }
"""


def render(lc, ent):
    spec = lc["entities"][ent]
    lay = LAYOUT[ent]
    pos = lay["pos"]
    states = list(spec["states"])
    miss = [s for s in states if s not in pos]
    extra = [s for s in pos if s not in states]
    if miss or extra:
        raise SystemExit("%s layout out of date: states without a place %s; places for unknown states %s" % (ent, miss, extra))

    grouped = {}
    for g in lay["groups"]:
        for cmd, to, _ in g["exits"]:
            grouped[(cmd, to)] = g
    covered = set()
    for t in spec["transitions"]:
        key = (t["command"], t["from"], t["to"])
        if key in lay["routes"]:
            covered.add(key)
        elif (t["command"], t["to"]) in grouped and t["from"] in grouped[(t["command"], t["to"])]["members"]:
            covered.add(key)
    all_t = set((t["command"], t["from"], t["to"]) for t in spec["transitions"])
    if covered != all_t:
        raise SystemExit("%s layout out of date: transitions not drawn %s" % (ent, sorted(all_t - covered)))
    stale = [k for k in lay["routes"] if k not in all_t]
    if stale:
        raise SystemExit("%s layout names transitions that no longer exist: %s" % (ent, stale))
    for g in lay["groups"]:
        for cmd, to, _ in g["exits"]:
            froms = sorted(t["from"] for t in spec["transitions"] if t["command"] == cmd and t["to"] == to)
            if froms != sorted(g["members"]):
                raise SystemExit("%s: group for %s no longer matches the transitions (%s)" % (ent, cmd, froms))

    cols = int(round(max(c for c, r in pos.values())))
    rows = max(r for c, r in pos.values())
    W = int(MX * 2 + max(c for c, r in pos.values()) * PX + BW)
    H = int(MY + rows * PY + BH + 96)
    guards = {}
    for t in spec["transitions"]:
        guards.setdefault((t["command"], t["to"]), set()).update([])
    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" aria-labelledby="t-%s d-%s">' % (W, H, W, H, ent, ent))
    out.append("<title id=\"t-%s\">%s</title>" % (ent, esc(TITLES[ent])))
    out.append('<desc id="d-%s">%s. States: %s. Transitions: %s.</desc>' % (
        ent, esc(TITLES[ent]), esc(", ".join(states)),
        esc("; ".join("%s (%s to %s)" % (t["command"], t["from"], t["to"]) for t in spec["transitions"]))))
    out.append("<style>%s</style>" % STYLE)
    out.append('<defs><marker id="ah-%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
               '<path class="tip" d="M0,0 L10,5 L0,10 z"/></marker></defs>' % ent)
    out.append('<rect class="bg" x="0" y="0" width="%d" height="%d"/>' % (W, H))
    out.append('<text class="title" x="%d" y="34">%s</text>' % (MX, esc(TITLES[ent])))
    out.append('<text class="legend" x="%d" y="%d">%s</text>' % (MX, H - 18, "Blue outline = starts here. Grey fill = end state. Solid arrow = forward step. Dashed arrow = loop back. Hover an arrow for its guards."))

    # groups first (behind boxes)
    for g in lay["groups"]:
        xs = [center(pos, m)[0] for m in g["members"]]
        ys = [center(pos, m)[1] for m in g["members"]]
        x0, x1 = min(xs) - BW / 2 - 18, max(xs) + BW / 2 + 18
        y0, y1 = min(ys) - BH / 2 - 26, max(ys) + BH / 2 + 18
        out.append('<rect class="group" x="%s" y="%s" width="%s" height="%s" rx="14"/>' % (f(x0), f(y0), f(x1 - x0), f(y1 - y0)))
        out.append('<text class="grouplbl" x="%s" y="%s">%s</text>' % (f(x0 + 12), f(y0 + 17), esc(g["label"])))
        g["_box"] = (x0, y0, x1, y1)

    gd = lc["guards"]

    def tip(t):
        gl = t["guards"]
        body = "%s: %s -> %s" % (t["command"], t["from"], t["to"])
        if gl:
            body += "\nguards: " + ", ".join(gl)
        else:
            body += "\nno guards"
        return esc(body)

    # edges
    for (cmd, fr, to), r in sorted(lay["routes"].items(), key=lambda kv: kv[0]):
        t = [x for x in spec["transitions"] if x["command"] == cmd and x["from"] == fr and x["to"] == to][0]
        verb = cmd.split(" ", 1)[1]
        if r[0] == "s":
            _, s1, s2, back = r
            p = [side(pos, fr, s1), side(pos, to, s2)]
        else:
            _, pts, back = r
            p = [side(pos, st, sd, dx, dy) for st, sd, dx, dy in pts]
        d = "M" + " L".join("%s,%s" % (f(x), f(y)) for x, y in p)
        # label near the middle of the longest segment
        best = max(range(len(p) - 1), key=lambda i: (p[i + 1][0] - p[i][0]) ** 2 + (p[i + 1][1] - p[i][1]) ** 2)
        lx = (p[best][0] + p[best + 1][0]) / 2.0
        ly = (p[best][1] + p[best + 1][1]) / 2.0
        if r[0] == "s" and r[1] == "r" and r[2] == "l" and abs(p[0][1] - p[1][1]) > 1:   # fan-out: label nearer the target
            lx = p[0][0] + (p[1][0] - p[0][0]) * 0.62
            ly = p[0][1] + (p[1][1] - p[0][1]) * 0.62
        out.append('<g><title>%s</title><path class="edge%s" d="%s" marker-end="url(#ah-%s)"/>%s</g>' % (
            tip(t), " back" if back else "", d, ent, label_box(lx, ly, verb, "lbl back" if back else "lbl")))
    # group exits
    for g in lay["groups"]:
        x0, y0, x1, y1 = g["_box"]
        for cmd, to, slot in g["exits"]:
            ts = [x for x in spec["transitions"] if x["command"] == cmd and x["to"] == to]
            gl = sorted(set(sum([x["guards"] for x in ts], [])))
            tx, ty = side(pos, to, "l")
            sy = y0 + (y1 - y0) * (0.30 if slot == 0 else 0.70)
            p = [(x1, sy), (tx - 16, sy), (tx - 16, ty), (tx, ty)] if abs(sy - ty) > 1 else [(x1, sy), (tx, ty)]
            d = "M" + " L".join("%s,%s" % (f(x), f(y)) for x, y in p)
            lx = (x1 + tx - 16) / 2.0
            body = "%s: from any of %s -> %s\nguards: %s" % (cmd, ", ".join(g["members"]), to, ", ".join(gl) if gl else "none")
            out.append('<g><title>%s</title><path class="edge" d="%s" marker-end="url(#ah-%s)"/>%s</g>' % (esc(body), d, ent, label_box(lx, sy, cmd.split(" ", 1)[1])))

    # states last
    for s in states:
        x, y = center(pos, s)
        cls = "state" + (" initial" if s == spec["initial"] else "") + (" terminal" if s in spec["terminal"] else "")
        out.append('<g class="%s"><rect class="box" x="%s" y="%s" width="%d" height="%d" rx="10"/><text x="%s" y="%s" text-anchor="middle">%s</text></g>' % (
            cls, f(x - BW / 2), f(y - BH / 2), BW, BH, f(x), f(y + 4.5), esc(s)))
    out.append("</svg>")
    return "\n".join(out) + "\n"


PAGE_CSS = """
:root{--bg:#f6f8fa;--card:#fff;--ink:#1f2328;--muted:#57606a;--line:#d0d7de;--accent:#0b5cad;--code:#eef1f4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0d1117;--card:#161b22;--ink:#e6edf3;--muted:#9da7b3;--line:#30363d;--accent:#58a6ff;--code:#21262d}}
:root[data-theme="dark"]{--bg:#0d1117;--card:#161b22;--ink:#e6edf3;--muted:#9da7b3;--line:#30363d;--accent:#58a6ff;--code:#21262d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:26px;margin:0 0 6px}h2{font-size:20px;margin:36px 0 8px;border-left:4px solid var(--accent);padding-left:10px}
p{margin:6px 0 12px}.muted{color:var(--muted)}
.diagram{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:8px;overflow-x:auto}
.diagram svg{display:block;min-width:1200px;width:100%;height:auto}
table{border-collapse:collapse;width:100%;background:var(--card);border:1px solid var(--line);border-radius:8px;margin:10px 0 4px;font-size:14px}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{background:var(--code);font-size:12.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
code{background:var(--code);padding:1px 5px;border-radius:5px;font-size:13px}
.wrap{overflow-x:auto}
"""


def page(lc):
    L = []
    L.append("<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">")
    L.append("<title>PM-Framework lifecycles</title><style>%s</style></head><body><main>" % PAGE_CSS)
    L.append("<h1>Lifecycles</h1><p class=\"muted\">Generated by <code>tools/gen_diagrams.py</code> from <code>pmf/data/lifecycles.json</code>. "
             "Each arrow is a <code>pmf</code> command; a command is refused unless every guard on it passes. "
             "On a phone, scroll the diagram sideways, or use the tables under it.</p>")
    for ent in ("issue", "risk", "change", "gate"):
        spec = lc["entities"][ent]
        L.append("<h2>%s</h2>" % esc(TITLES[ent]))
        L.append("<div class=\"diagram\">%s</div>" % render(lc, ent).split("?>")[-1])
        L.append("<div class=\"wrap\"><table><thead><tr><th>Command</th><th>From</th><th>To</th><th>Guards (all must pass)</th></tr></thead><tbody>")
        for t in spec["transitions"]:
            L.append("<tr><td><code>pmf %s</code></td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
                esc(t["command"]), esc(t["from"]), esc(t["to"]), ", ".join("<code>%s</code>" % esc(g) for g in t["guards"]) or "none"))
        L.append("</tbody></table></div>")
        for r in spec.get("rules", []):
            L.append("<p class=\"muted\">%s</p>" % esc(r))
    ov = lc.get("overlays", {}).get("sev1")
    if ov:
        L.append("<h2>Sev 1 overlay</h2><p>%s</p><ul>%s</ul>" % (esc(ov["meaning"]), "".join("<li>%s</li>" % esc(c) for c in ov["checklist"])))
    L.append("<h2>What each guard checks</h2><div class=\"wrap\"><table><thead><tr><th>Guard</th><th>Meaning</th></tr></thead><tbody>")
    for g in sorted(lc["guards"]):
        L.append("<tr><td><code>%s</code></td><td>%s</td></tr>" % (esc(g), esc(lc["guards"][g])))
    L.append("</tbody></table></div></main></body></html>")
    return "\n".join(L) + "\n"


def build():
    lc = load()
    files = {}
    for ent in ("issue", "risk", "change", "gate"):
        files["%s.svg" % ent] = render(lc, ent)
    files["lifecycles.html"] = page(lc)
    return files


def main(argv):
    files = build()
    if "--check" in argv:
        bad = 0
        for name, text in sorted(files.items()):
            p = os.path.join(OUT, name)
            have = None
            if os.path.exists(p):
                with io.open(p, encoding="utf-8", newline="") as fh:
                    have = fh.read().replace("\r\n", "\n")
            if have != text:
                print("stale:", os.path.relpath(p, ROOT))
                bad += 1
        if bad:
            print("DIAGRAM CHECK: %d file(s) out of date; run python3 tools/gen_diagrams.py" % bad)
            return 1
        print("DIAGRAM CHECK: %d files match the lifecycle definitions" % len(files))
        return 0
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    for name, text in files.items():
        with io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    print("wrote %d files to %s" % (len(files), os.path.relpath(OUT, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
