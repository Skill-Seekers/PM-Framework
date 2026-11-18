"""A read-only health dashboard: one self-contained HTML file built from the registers.

No scripts, no external fonts, images or links: the page works from disk, in a mail attachment, and in print.
Every value is HTML-escaped. Colour is never the only carrier: each status has an icon and a word, each bar a
number, each heat cell its risk ids. Light and dark follow the viewer's setting (a data-theme="light|dark"
attribute on <html> overrides it). Deterministic: the same registers and report date give the same bytes.
"""
import datetime
import html

from pmf import __version__, check, metrics
from pmf.lifecycle import score_of
from pmf.util import fmt_num, is_date, is_num, num, parse_date

GATE_STATE = {"GO": "Go", "CONDITIONAL_GO": "Conditional go", "NO_GO": "No-go", "REVIEW": "In review", "PLANNED": "Planned"}
STATUS_WORD = {"green": "Green", "amber": "Amber", "red": "Red", "grey": "Not rated"}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Colours (hex). Surfaces, ink, blue ramp, status and the four risk-band steps come from one validated palette;
# the risk-band steps are an ordinal blue ramp (light mode: light to dark, dark mode: dark to light).
PALETTE = {
    "light": {"page": "#f9f9f7", "surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e1e0d9",
              "axis": "#c3c2b7", "s1": "#2a78d6", "s1_track": "#b7d3f6",
              "hb": ["#86b6ef", "#256abf", "#184f95", "#0d366b"],
              "hb_ink": ["#0b0b0b", "#ffffff", "#ffffff", "#ffffff"]},
    "dark": {"page": "#0d0d0d", "surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "grid": "#2c2c2a",
             "axis": "#383835", "s1": "#3987e5", "s1_track": "#0d366b",
             "hb": ["#184f95", "#256abf", "#3987e5", "#6da7ec"],
             "hb_ink": ["#ffffff", "#ffffff", "#0b0b0b", "#0b0b0b"]},
}
STATUS = {"good": "#0ca30c", "warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b"}


def e(text):
    return html.escape("" if text is None else str(text), quote=True)


def compact(x):
    """1,284 / 12.9K / 2.4M (no currency: the registers do not say which one)."""
    x = float(x)
    a = abs(x)
    if a >= 1e6:
        return ("%.2f" % (x / 1e6)).rstrip("0").rstrip(".") + "M"
    if a >= 1e4:
        return ("%.1f" % (x / 1e3)).rstrip("0").rstrip(".") + "K"
    if a >= 1e3:
        return ("%.2f" % (x / 1e3)).rstrip("0").rstrip(".") + "K"
    return fmt_num(x)


def _d(x):
    return parse_date(x) if x and is_date(x) else None


def _pct(d, lo, hi):
    return min(100.0, max(0.0, (d - lo).days * 100.0 / max((hi - lo).days, 1)))


def _p(x):
    return ("%.2f" % x).rstrip("0").rstrip(".")


# ---------------------------------------------------------------- pieces
def status_icon(color):
    fill = {"green": STATUS["good"], "amber": STATUS["warning"], "red": STATUS["critical"]}.get(color)
    glyph = {"green": "#ffffff", "amber": "#0b0b0b", "red": "#ffffff"}.get(color)
    if color == "green":
        shape = '<circle cx="8" cy="8" r="6.6" fill="%s" stroke="var(--ink)" stroke-width="1.2"/>' % fill
        mark = '<path d="M4.8 8.3l2.2 2.2 4.2-4.6" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>' % glyph
    elif color == "amber":
        shape = '<path d="M8 1.6L15 14H1z" fill="%s" stroke="var(--ink)" stroke-width="1.2" stroke-linejoin="round"/>' % fill
        mark = '<path d="M8 6v3.6M8 11.6v.9" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round"/>' % glyph
    elif color == "red":
        shape = '<path d="M5.2 1.4h5.6l3.8 3.8v5.6l-3.8 3.8H5.2L1.4 10.8V5.2z" fill="%s" stroke="var(--ink)" stroke-width="1.2" stroke-linejoin="round"/>' % fill
        mark = '<path d="M5.6 5.6l4.8 4.8M10.4 5.6l-4.8 4.8" fill="none" stroke="%s" stroke-width="1.8" stroke-linecap="round"/>' % glyph
    else:
        shape = '<circle cx="8" cy="8" r="6.6" fill="none" stroke="var(--ink2)" stroke-width="1.4" stroke-dasharray="2.4 2.2"/>'
        mark = '<path d="M5.6 8h4.8" fill="none" stroke="var(--ink2)" stroke-width="1.6" stroke-linecap="round"/>'
    return '<svg class="ico" viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" focusable="false">%s%s</svg>' % (shape, mark)


def chip(color, word=None, big=False):
    word = word or STATUS_WORD[color]
    return '<span class="chip%s st-%s">%s<span>%s</span></span>' % (" big" if big else "", color, status_icon(color), e(word))


def _tile(m):
    det = ""
    if m["detail"]:
        det = '<details class="more"><summary>Detail</summary><ul>%s</ul></details>' % "".join("<li>%s</li>" % e(x) for x in m["detail"])
    return ('<article class="tile st-%s"><div class="tile-top"><h3>%s</h3>%s</div>'
            '<div class="tile-value%s">%s</div><p class="rule">%s</p>%s</article>' % (
                m["color"], e(m["name"]), chip(m["color"]), " long" if len(m["value"]) > 22 else "",
                e("Not rated" if m["value"] == "not rated" else m["value"]), e(m["rule"]), det))


def _gate_rows(ws):
    gates = ws.planned_gates()
    done_states = ("GO", "CONDITIONAL_GO")
    dates = [ws.report_date]
    for key in ("baseline_start", "baseline_end"):
        if _d(ws.config.get(key)):
            dates.append(_d(ws.config[key]))
    for g in gates:
        for k in ("baseline_date", "planned_date", "actual_date"):
            if _d(g.get(k)):
                dates.append(_d(g[k]))
    lo = min(dates) - datetime.timedelta(days=7)
    hi = max(dates) + datetime.timedelta(days=7)
    # month ticks
    ticks = []
    y, mth = lo.year, lo.month
    while True:
        first = datetime.date(y, mth, 1)
        if first > hi:
            break
        if first >= lo:
            ticks.append(first)
        mth += 1
        if mth == 13:
            y, mth = y + 1, 1
    tick_spans = "".join('<span class="mt" style="left:%s%%"></span>' % _p(_pct(t, lo, hi)) for t in ticks)
    axis_labels = "".join(
        '<span class="ml%s" style="left:%s%%">%s</span>' % (
            ("" if t.month in (1, 4, 7, 10) else " minor") + (" end" if _pct(t, lo, hi) > 88 else ""), _p(_pct(t, lo, hi)),
            e(MONTHS[t.month - 1] + (" " + str(t.year) if t.month == 1 or t == ticks[0] else ""))) for t in ticks)
    today_x = _p(_pct(ws.report_date, lo, hi))
    out = ['<ol class="gates">',
           '<li class="grow ghead"><div class="glabel">Gate</div><div class="gtrack axis">%s<span class="today-lbl" style="left:%s%%">Report date %s</span></div><div class="gdelta">vs baseline</div></li>'
           % (axis_labels, today_x, e(ws.report_date.isoformat()))]
    for g in gates:
        base = _d(g.get("baseline_date"))
        done = g["state"] in done_states and _d(g.get("actual_date"))
        cur = _d(g.get("actual_date")) if done else (_d(g.get("planned_date")) or base)
        st = GATE_STATE.get(g["state"], g["state"])
        if cur is None:
            delta, dcls = "no date", ""
        elif base is None:
            delta, dcls = "no baseline", ""
        else:
            dd = (cur - base).days
            overdue = (not done) and cur < ws.report_date
            if overdue:
                delta, dcls = "overdue", " late"
            elif done:
                delta, dcls = ("on time" if dd <= 0 else "+%d days late" % dd), (" late" if dd > 0 else "")
                if dd < 0:
                    delta = "%d days early" % -dd
            else:
                delta, dcls = ("on baseline" if dd == 0 else ("forecast +%d days" % dd if dd > 0 else "forecast %d days early" % -dd)), (" late" if dd > 0 else "")
        parts = []
        if base and cur:
            a, b = sorted([base, cur])
            parts.append('<span class="gline" style="left:%s%%;width:%s%%"></span>' % (_p(_pct(a, lo, hi)), _p(_pct(b, lo, hi) - _pct(a, lo, hi))))
        if base:
            parts.append('<span class="gm base" style="left:%s%%" title="Baseline %s"></span>' % (_p(_pct(base, lo, hi)), e(base.isoformat())))
        if cur:
            parts.append('<span class="gm %s" style="left:%s%%" title="%s %s"></span>' % (
                "done" if done else "plan", _p(_pct(cur, lo, hi)), "Actual" if done else "Planned", e(cur.isoformat())))
        tip = "%s %s: %s; baseline %s; %s %s" % (g["id"], g.get("name", ""), st, g.get("baseline_date") or "none",
                                                  "actual" if done else "planned", cur.isoformat() if cur else "none")
        out.append(
            '<li class="grow"><div class="glabel"><span class="gid">%s</span> %s<span class="gstate">%s%s</span></div>'
            '<div class="gtrack" title="%s">%s<span class="today" style="left:%s%%"></span>%s</div><div class="gdelta%s">%s</div></li>' % (
                e(g["id"]), e(g.get("name", "")), e(st), e(" " + cur.isoformat()) if cur else "", e(tip), tick_spans, today_x, "".join(parts), dcls, e(delta)))
    out.append("</ol>")
    legend = ('<p class="legend"><span class="key"><span class="gm base inline"></span> Baseline</span>'
              '<span class="key"><span class="gm done inline"></span> Actual (gate passed)</span>'
              '<span class="key"><span class="gm plan inline"></span> Planned or forecast</span>'
              '<span class="key"><span class="today inline"></span> Report date</span></p>')
    return "".join(out) + legend


def _aging(ws):
    rows = []
    for lv, info in sorted(ws.profile.levels.items()):
        a = info.get("aging_days")
        if not a:
            continue
        for i in ws.open_issues({lv}):
            d = _d(i.get("detected"))
            if not d:
                continue
            age = (ws.report_date - d).days
            rows.append((lv, info, a, i, age))
    if not rows:
        return '<p class="empty">No open Sev 1 or Sev 2 issues.</p>', []
    items = []
    table = []
    for lv, info, a, i, age in rows:
        scale = a["amber_max"] * 1.5
        if age > a["amber_max"]:
            word, cls = "past the amber limit", "crit"
        elif age > a["green_max"]:
            word, cls = "past the green limit", "warn"
        else:
            word, cls = "within the green limit", "good"
        w = min(100.0, age * 100.0 / scale)
        items.append(
            '<li class="arow"><div class="ahead"><span class="sev">%s</span> <b>%s</b> %s</div>'
            '<div class="abar" title="%s"><span class="afill %s" style="width:%s%%"></span>'
            '<span class="atick" style="left:%s%%"></span><span class="atick" style="left:%s%%"></span></div>'
            '<div class="atext">%d days open, %s (green to %d days, amber to %d). %s</div></li>' % (
                e(info["label"]), e(i["id"]), e(i.get("title", "")),
                e("%s: %d days open" % (i["id"], age)), cls, _p(w),
                _p(a["green_max"] * 100.0 / scale), _p(a["amber_max"] * 100.0 / scale),
                age, e(word), a["green_max"], a["amber_max"],
                e(("Owner %s." % i["owner"]) if i.get("owner") else "") + e((" Due %s." % i["due"]) if i.get("due") else "")))
        table.append([i["id"], info["label"], i.get("title", ""), i.get("owner", ""), i.get("detected", ""), str(age), word])
    return '<ul class="aging">%s</ul>' % "".join(items), table


def _band_index(bands, score):
    order = sorted(bands, key=lambda b: b["min"])
    for idx, b in enumerate(order):
        if b["min"] <= score <= b["max"]:
            return min(idx, 3), b, order
    return 0, None, order


def _heat(ws):
    p = ws.profile.d["risk"]
    lo, hi = p["scale"]["min"], p["scale"]["max"]
    terminal = set(ws.lifecycles["entities"]["risk"]["terminal"])
    risks = [r for r in ws.load("risks") if r["state"] not in terminal]
    cells = {}
    for r in risks:
        try:
            cells.setdefault((int(float(r["probability"])), int(float(r["impact"]))), []).append(r)
        except (TypeError, ValueError):
            pass
    grid = []
    for prob in range(hi, lo - 1, -1):
        grid.append('<div class="axl">%d <span>%s</span></div>' % (prob, e(p["probability"].get(str(prob), ""))))
        for imp in range(lo, hi + 1):
            score = prob * imp
            bi, band, order = _band_index(p["bands"], score)
            here = cells.get((prob, imp), [])
            tip = "Probability %d (%s) x impact %d (%s) = %d%s" % (
                prob, p["probability"].get(str(prob), ""), imp, p["impact"].get(str(imp), ""), score, ", " + band["priority"] if band else "")
            if here:
                ids = "".join("<span class=\"rid\">%s</span>" % e(r["id"]) for r in here)
                tip += ": " + "; ".join("%s %s (%s)" % (r["id"], r.get("title", ""), r["state"]) for r in here)
                grid.append('<div class="hc b%d" title="%s">%s</div>' % (bi, e(tip), ids))
            else:
                grid.append('<div class="hc empty" title="%s"><span class="sc">%d</span></div>' % (e(tip), score))
    grid.append('<div class="axl corner"></div>')
    for imp in range(lo, hi + 1):
        grid.append('<div class="axl x">%d <span>%s</span></div>' % (imp, e(p["impact"].get(str(imp), ""))))
    order = sorted(p["bands"], key=lambda b: b["min"])
    legend = '<p class="legend">%s</p>' % "".join(
        '<span class="key"><span class="sw b%d"></span> %s %d to %d</span>' % (min(i, 3), e(b["priority"]), b["min"], b["max"]) for i, b in enumerate(order))
    ranked = sorted(risks, key=lambda r: (-(score_of(r) or 0), r["id"]))
    rows = []
    for r in ranked:
        s = score_of(r)
        bi, band, _ = _band_index(p["bands"], s) if s is not None else (0, None, order)
        rows.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            e(r["id"]), e(r.get("title", "")), e("%s%s" % (s, (" " + band["priority"]) if band else "")), e(r["state"].title()), e(r.get("owner", ""))))
    lst = ('<table class="mini"><thead><tr><th>Risk</th><th>Title</th><th>Score</th><th>State</th><th>Owner</th></tr></thead><tbody>%s</tbody></table>' % "".join(rows)
           if rows else '<p class="empty">No open risks.</p>')
    head = '<div class="heatwrap"><div><div class="heatgrid" role="img" aria-label="Open risks on a probability by impact grid">%s</div>%s<p class="axis-note">Rows: probability (up is likelier). Columns: impact (right is worse).</p></div><div class="wrap">%s</div></div>' % ("".join(grid), legend, lst)
    return head


def _budget(ws):
    rows = ws.load("budget", required=False)
    if not rows:
        return '<p class="empty">No budget rows yet.</p>', []
    scale = 0.0
    for r in rows:
        for k in ("budget", "forecast_at_completion"):
            if is_num(r.get(k, "")) and (r.get(k) or "").strip():
                scale = max(scale, num(r[k]))
    scale = scale or 1.0
    items, table = [], []
    for r in rows:
        ph = ws.profile.phase(r["phase"])
        name = ph["name"] if ph else r["phase"]
        def val(k):
            return num(r[k]) if (r.get(k) or "").strip() and is_num(r[k]) else None
        bud, act, fc = val("budget"), val("actual_to_date"), val("forecast_at_completion")
        parts = []
        if bud is not None:
            parts.append('<span class="bbud" style="width:%s%%"></span>' % _p(bud * 100.0 / scale))
        if act is not None:
            parts.append('<span class="bact" style="width:%s%%"></span>' % _p(act * 100.0 / scale))
        over = None
        if bud is not None and fc is not None and fc > bud:
            over = fc - bud
            parts.append('<span class="bover" style="left:%s%%;width:%s%%"></span>' % (_p(bud * 100.0 / scale), _p(over * 100.0 / scale)))
        if fc is not None:
            parts.append('<span class="bfc" style="left:%s%%"></span>' % _p(fc * 100.0 / scale))
        txt = "%s of %s spent" % (compact(act) if act is not None else "n/a", compact(bud) if bud is not None else "n/a")
        if fc is not None:
            txt += "; forecast %s" % compact(fc)
        if over:
            txt += " (%s over budget)" % compact(over)
        items.append('<li class="brow"><div class="blabel">%s</div><div class="btrack" title="%s">%s</div><div class="bval%s">%s</div></li>' % (
            e(name), e(txt), "".join(parts), " late" if over else "", e(txt)))
        table.append([name, r.get("budget", ""), r.get("planned_to_date", ""), r.get("actual_to_date", ""), r.get("forecast_at_completion", "")])
    legend = ('<p class="legend"><span class="key"><span class="sw track"></span> Budget</span>'
              '<span class="key"><span class="sw s1"></span> Spent to date</span>'
              '<span class="key"><span class="fcmark"></span> Forecast at completion</span>'
              '<span class="key"><span class="sw over"></span> Forecast over budget</span></p>')
    return '<ul class="budget">%s</ul>%s' % ("".join(items), legend), table


def _states(ws):
    spec = ws.lifecycles["entities"]["issue"]
    rows = ws.load("issues")
    counts = dict((s, 0) for s in spec["states"])
    for i in rows:
        counts[i["state"]] = counts.get(i["state"], 0) + 1
    top = max(list(counts.values()) + [1])
    items = []
    for s in counts:
        items.append('<li class="srow"><div class="slabel">%s</div><div class="strack" title="%s: %d"><span class="sfill" style="width:%s%%"></span></div><div class="sval">%d</div></li>' % (
            e(s.title()), e(s.title()), counts[s], _p(counts[s] * 100.0 / top), counts[s]))
    return '<ul class="states">%s</ul>' % "".join(items), [[s.title(), str(c)] for s, c in counts.items()]


def _attention(ws):
    errs, warns = check.run(ws)
    items = [("red", "Error", m) for m in errs] + [("amber", "Warning", m) for m in warns]
    if not items:
        return '<p class="empty">%s Nothing flagged by <code>pmf check</code>.</p>' % chip("green", "Clean")
    shown = items[:10]
    li = "".join('<li>%s<span>%s</span></li>' % (chip(c, w), e(m)) for c, w, m in shown)
    more = '<p class="note">%d more not shown; run <code>pmf check</code> for the full list.</p>' % (len(items) - 10) if len(items) > 10 else ""
    return '<ul class="attn">%s</ul>%s<p class="note">%d error(s), %d warning(s) from <code>pmf check</code>.</p>' % (li, more, len(errs), len(warns))


def _table(headers, rows, cap):
    th = "".join("<th>%s</th>" % e(h) for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % e(c) for c in r) for r in rows)
    return '<div class="wrap"><table><caption>%s</caption><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (e(cap), th, body)


def _css():
    def block(mode):
        p = PALETTE[mode]
        v = ["--page:%s" % p["page"], "--surface:%s" % p["surface"], "--ink:%s" % p["ink"], "--ink2:%s" % p["ink2"],
             "--grid:%s" % p["grid"], "--axis:%s" % p["axis"], "--s1:%s" % p["s1"], "--s1-track:%s" % p["s1_track"],
             "--border:%s" % ("rgba(11,11,11,.10)" if mode == "light" else "rgba(255,255,255,.10)"),
             "--late:%s" % ("#8f1d1d" if mode == "light" else "#ff9d8f")]
        for i in range(4):
            v.append("--b%d:%s" % (i, p["hb"][i]))
            v.append("--b%d-ink:%s" % (i, p["hb_ink"][i]))
        return ";".join(v) + ";color-scheme:%s" % mode
    return (":root{%s;--good:%s;--warning:%s;--serious:%s;--critical:%s}\n"
            "@media (prefers-color-scheme:dark){:root:where(:not([data-theme=\"light\"])){%s}}\n"
            ":root[data-theme=\"dark\"]{%s}\n" % (block("light"), STATUS["good"], STATUS["warning"], STATUS["serious"], STATUS["critical"], block("dark"), block("dark"))) + CSS_BODY


CSS_BODY = """
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:1120px;margin:0 auto;padding:20px 16px 56px}
h1{font-size:24px;line-height:1.25;margin:0}
h2{font-size:17px;margin:0 0 4px}
h3{font-size:14px;margin:0;font-weight:600}
p{margin:6px 0}
code{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--grid);padding:1px 5px;border-radius:5px}
.sub{color:var(--ink2);margin:2px 0 0}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;margin-top:16px}
.hero{display:flex;gap:20px;align-items:center;flex-wrap:wrap}
.hero .why{flex:1;min-width:240px;color:var(--ink2)}
.chip{display:inline-flex;align-items:center;gap:6px;padding:3px 10px 3px 7px;border:1px solid var(--axis);border-radius:999px;font-size:13px;font-weight:600;white-space:nowrap;background:var(--surface)}
.chip.big{font-size:44px;line-height:1.1;padding:6px 22px 6px 16px;gap:12px;font-weight:600}
.chip.big .ico{width:40px;height:40px}
.ico{flex:none}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:16px}
.tile{background:var(--surface);border:1px solid var(--border);border-top:4px solid var(--axis);border-radius:12px;padding:12px 14px}
.tile.st-green{border-top-color:var(--good)}.tile.st-amber{border-top-color:var(--warning)}.tile.st-red{border-top-color:var(--critical)}
.tile-top{display:flex;justify-content:space-between;gap:8px;align-items:flex-start;flex-wrap:wrap}
.tile-value{font-size:24px;font-weight:600;margin:8px 0 2px;line-height:1.2}
.tile-value.long{font-size:17px}
.rule{color:var(--ink2);font-size:13px;margin:0}
.more{margin-top:8px;font-size:13px}.more summary{cursor:pointer;color:var(--ink2)}.more ul{margin:6px 0 0;padding-left:18px}
.cols{display:grid;grid-template-columns:1fr;gap:0}
@media (min-width:900px){.cols{grid-template-columns:1fr 1fr;gap:16px}.cols .card{margin-top:16px}}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;color:var(--ink2);font-size:13px;margin:10px 0 0}
.key{display:inline-flex;align-items:center;gap:6px}
.empty{color:var(--ink2);display:flex;align-items:center;gap:8px;margin:8px 0}
.wrap{overflow-x:auto}
ol,ul{list-style:none;margin:0;padding:0}
.gates{margin-top:22px}
.note{color:var(--ink2);font-size:13px;margin:10px 0 0}
/* gates */
.grow{display:grid;grid-template-columns:minmax(150px,13em) 1fr 9.5em;gap:2px 12px;align-items:center;padding:7px 0;border-top:1px solid var(--grid)}
.ghead{border-top:0;padding-bottom:2px;color:var(--ink2);font-size:12px}
.glabel{font-size:14px}.gid{font-weight:700;margin-right:4px}
.gstate{display:block;color:var(--ink2);font-size:12px}
.gtrack{position:relative;height:22px}
.gtrack.axis{height:20px}
.gtrack .mt{position:absolute;top:0;bottom:0;width:1px;background:var(--grid)}
.gtrack .today{position:absolute;top:-4px;bottom:-4px;width:2px;background:var(--ink);opacity:.55}
.today.inline{position:static;display:inline-block;width:2px;height:14px;background:var(--ink);opacity:.55}
.ml{position:absolute;top:0;font-size:11px;color:var(--ink2);transform:translateX(-1px);white-space:nowrap}
.ml.end{transform:translateX(-100%)}
.today-lbl{position:absolute;top:-17px;font-size:11px;color:var(--ink);font-weight:600;transform:translateX(-50%);white-space:nowrap}
.gline{position:absolute;top:10px;height:2px;background:var(--ink2)}
.gm{position:absolute;top:5px;width:12px;height:12px;margin-left:-6px;border-radius:50%;box-shadow:0 0 0 2px var(--surface)}
.gm.base{background:var(--surface);border:2px solid var(--ink2)}
.gm.done{background:var(--s1)}
.gm.plan{background:var(--surface);border:3px solid var(--s1)}
.gm.inline{position:static;display:inline-block;margin:0;box-shadow:none}
.gdelta{font-size:13px;color:var(--ink2);text-align:right}
.gdelta.late{color:var(--ink);font-weight:700}
.gdelta.late::before{content:"\\25B2\\00a0"}
@media (max-width:640px){.grow{grid-template-columns:1fr auto}.glabel{grid-column:1}.gdelta{grid-column:2;grid-row:1}.gtrack{grid-column:1/-1}.ml.minor{display:none}.today-lbl{transform:translateX(-80%)}}
/* aging */
.aging li{padding:8px 0;border-top:1px solid var(--grid)}.aging li:first-child{border-top:0}
.sev{display:inline-block;font-size:12px;font-weight:700;border:1px solid var(--ink2);border-radius:5px;padding:0 6px}
.abar{position:relative;height:12px;background:var(--grid);border-radius:4px;margin:6px 0 2px}
.afill{position:absolute;left:0;top:0;bottom:0;border-radius:4px 0 0 4px}
.afill.good{background:var(--good)}.afill.warn{background:var(--warning)}.afill.crit{background:var(--critical)}
.atick{position:absolute;top:-3px;bottom:-3px;width:2px;background:var(--ink);opacity:.6}
.atext{font-size:13px;color:var(--ink2)}
/* heat */
.heatwrap{display:grid;grid-template-columns:1fr;gap:16px}
@media (min-width:900px){.heatwrap{grid-template-columns:minmax(320px,1fr) 1.2fr}}
.heatgrid{display:grid;grid-template-columns:auto repeat(5,minmax(40px,1fr));gap:2px;align-items:stretch}
.axl{font-size:12px;color:var(--ink2);display:flex;flex-direction:column;justify-content:center;padding-right:6px;line-height:1.2}
.axl span{font-size:10.5px}
.axl.x{align-items:center;text-align:center;padding:4px 0 0}
.hc{min-height:48px;border-radius:4px;display:flex;flex-wrap:wrap;gap:3px;align-items:center;justify-content:center;padding:3px;font-size:11px;font-weight:700}
.hc.empty{background:transparent;border:1px solid var(--grid);color:var(--ink2);font-weight:400}
.hc .sc{font-size:11px}
.hc.b0{background:var(--b0);color:var(--b0-ink)}.hc.b1{background:var(--b1);color:var(--b1-ink)}.hc.b2{background:var(--b2);color:var(--b2-ink)}.hc.b3{background:var(--b3);color:var(--b3-ink)}
.rid{white-space:nowrap}
.sw{display:inline-block;width:14px;height:14px;border-radius:3px}
.sw.b0{background:var(--b0)}.sw.b1{background:var(--b1)}.sw.b2{background:var(--b2)}.sw.b3{background:var(--b3)}
.axis-note{font-size:12px;color:var(--ink2);margin:6px 0 0}
/* budget */
.brow{display:grid;grid-template-columns:11em 1fr;gap:2px 12px;align-items:center;padding:6px 0;border-top:1px solid var(--grid)}.brow:first-child{border-top:0}
.btrack{position:relative;height:16px}
.bbud{position:absolute;left:0;top:1px;height:14px;background:var(--s1-track);border-radius:0 4px 4px 0}
.bact{position:absolute;left:0;top:1px;height:14px;background:var(--s1);border-radius:0 4px 4px 0}
.bover{position:absolute;top:1px;height:14px;background:var(--critical);border-radius:0 4px 4px 0;margin-left:2px}
.bfc{position:absolute;top:-2px;height:20px;width:2px;background:var(--ink)}
.bval{grid-column:2;font-size:13px;color:var(--ink2)}.bval.late{color:var(--ink)}
.sw.track{background:var(--s1-track)}.sw.s1{background:var(--s1)}.sw.over{background:var(--critical)}
.fcmark{display:inline-block;width:2px;height:14px;background:var(--ink)}
@media (max-width:640px){.brow{grid-template-columns:1fr}.bval{grid-column:1}.blabel{font-weight:600}}
/* states */
.srow{display:grid;grid-template-columns:7em 1fr 2em;gap:12px;align-items:center;padding:3px 0}
.strack{height:14px}.sfill{display:block;height:14px;background:var(--s1);border-radius:0 4px 4px 0;min-width:0}
.sval{font-size:13px;color:var(--ink);font-weight:600}
/* attention */
.attn li{display:flex;gap:10px;align-items:flex-start;padding:6px 0;border-top:1px solid var(--grid)}.attn li:first-child{border-top:0}
.attn .chip{flex:none}
.attn span:last-child{font-size:14px}
/* tables */
table{border-collapse:collapse;width:100%;font-size:13.5px;margin:8px 0}
caption{text-align:left;font-weight:600;padding:8px 0 2px}
th,td{padding:5px 9px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:top}
th{color:var(--ink2);font-size:12px;font-weight:600}
table.mini td,table.mini th{padding:4px 6px}
details.tables>summary{cursor:pointer;font-weight:600}
footer{color:var(--ink2);font-size:13px;margin-top:24px}
@media (forced-colors:active){.chip,.card,.tile{border:1px solid CanvasText}.gm,.bact,.afill,.hc{forced-color-adjust:none}}
@media print{body{background:#fff}.card,.tile{break-inside:avoid}details>*{display:block}}
"""


def render(ws):
    res = metrics.compute(ws)
    roll = res["rollup"]
    aging_html, aging_rows = _aging(ws)
    budget_html, budget_rows = _budget(ws)
    states_html, state_rows = _states(ws)
    prog = ws.config["program"]
    title = "%s - project health, %s" % (prog, ws.report_date.isoformat())

    gate_rows = [[g["id"], g.get("name", ""), GATE_STATE.get(g["state"], g["state"]), g.get("baseline_date", ""),
                  g.get("planned_date", ""), g.get("actual_date", "")] for g in ws.planned_gates()]
    risk_rows = []
    for r in ws.load("risks"):
        risk_rows.append([r["id"], r.get("title", ""), r["state"], r.get("probability", ""), r.get("impact", ""),
                          str(score_of(r) if score_of(r) is not None else ""), r.get("owner", "")])
    metric_rows = [[m["name"], STATUS_WORD[m["color"]], "" if m["value"] == "not rated" else m["value"], m["rule"]] for m in res["metrics"]]

    out = []
    out.append('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
               '<meta name="viewport" content="width=device-width,initial-scale=1">'
               '<meta name="color-scheme" content="light dark">'
               '<title>%s</title><style>%s</style></head><body><main>' % (e(title), _css()))
    out.append('<header><h1>%s</h1><p class="sub">Project health as of %s. Profile: %s. Read-only view built from the CSV registers.</p></header>' % (
        e(prog), e(ws.report_date.isoformat()), e(ws.profile.id)))
    out.append('<section class="card hero" aria-labelledby="roll"><div><h2 id="roll">Overall</h2>%s</div><p class="why">%s</p></section>' % (
        chip(roll["color"], big=True), e(roll["reason"])))
    out.append('<section class="tiles" aria-label="The five health metrics">%s</section>' % "".join(_tile(m) for m in res["metrics"]))
    out.append('<section class="card"><h2>Gates against baseline</h2><p class="sub">Where each planned gate was due, and where it passed or is forecast.</p>%s</section>' % _gate_rows(ws))
    out.append('<div class="cols"><section class="card"><h2>Open Sev 1 and Sev 2 issues</h2><p class="sub">Age against the green and amber limits (ticks on the bar).</p>%s</section>'
               '<section class="card"><h2>Needs attention</h2><p class="sub">Flagged by the consistency check.</p>%s</section></div>' % (aging_html, _attention(ws)))
    out.append('<section class="card"><h2>Open risks</h2><p class="sub">Probability times impact. Terminal risks (occurred, retired) are in the table view.</p>%s</section>' % _heat(ws))
    out.append('<div class="cols"><section class="card"><h2>Budget by phase</h2><p class="sub">Spent to date against budget, with the forecast at completion.</p>%s</section>'
               '<section class="card"><h2>Issues by state</h2><p class="sub">Every issue in the register.</p>%s</section></div>' % (budget_html, states_html))
    out.append('<section class="card"><details class="tables"><summary>Table view of every chart</summary>%s%s%s%s%s%s</details></section>' % (
        _table(["Metric", "Status", "Value", "Rule"], metric_rows, "Health metrics"),
        _table(["Gate", "Name", "State", "Baseline", "Planned", "Actual"], gate_rows, "Gates"),
        _table(["Issue", "Severity", "Title", "Owner", "Detected", "Days open", "Against limit"], aging_rows, "Open Sev 1 and Sev 2 issues") if aging_rows else "",
        _table(["Risk", "Title", "State", "Probability", "Impact", "Score", "Owner"], risk_rows, "Risks"),
        _table(["Phase", "Budget", "Planned to date", "Actual to date", "Forecast at completion"], budget_rows, "Budget") if budget_rows else "",
        _table(["State", "Issues"], state_rows, "Issues by state")))
    out.append('<footer>Generated by <code>pmf dashboard</code> (PM-Framework %s). This page is read-only: change the CSV registers, then run it again. '
               'Status always shows an icon and a word as well as colour.</footer>' % e(__version__))
    out.append("</main></body></html>\n")
    return "".join(out)
