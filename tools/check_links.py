#!/usr/bin/env python3
"""Check relative links in every markdown file, and that backtick-quoted repo paths in prompts exist.
Stdlib only. Usage: python3 tools/check_links.py [--allow-missing a,b,c]
Exit 0 = all links resolve, 1 = broken links."""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
allow = []
if "--allow-missing" in sys.argv:
    allow = sys.argv[sys.argv.index("--allow-missing") + 1].split(",")

LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
bad = []
count = 0
for dp, dn, fn in os.walk(ROOT):
    dn[:] = [d for d in dn if d not in (".git", "__pycache__", "_private", "node_modules")]
    for f in fn:
        if not f.endswith(".md"):
            continue
        p = os.path.join(dp, f)
        text = open(p, encoding="utf-8").read()
        text = re.sub(r"(?s)```.*?```", "", text)  # ignore code blocks
        for m in LINK.finditer(text):
            tgt = m.group(1)
            if re.match(r"^[a-z]+:", tgt) or tgt.startswith("#"):
                continue
            path = tgt.split("#")[0]
            if not path:
                continue
            count += 1
            full = os.path.normpath(os.path.join(os.path.dirname(p), path))
            rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
            if not os.path.exists(full) and not any(rel == a or rel.startswith(a.rstrip("/") + "/") for a in allow if a):
                bad.append("%s -> %s" % (os.path.relpath(p, ROOT).replace(os.sep, "/"), rel))
# prompts must name an existing template
for f in sorted(os.listdir(os.path.join(ROOT, "prompts"))):
    if re.match(r"\d\d_.*\.md$", f):
        t = open(os.path.join(ROOT, "prompts", f), encoding="utf-8").read()
        m = re.search(r"\*\*Fills template\*\* \| `([^`]+)`", t)
        if not m or not os.path.exists(os.path.join(ROOT, m.group(1))):
            bad.append("prompts/%s: template %s missing" % (f, m.group(1) if m else "(none)"))
if bad:
    print("LINK CHECK: %d broken" % len(bad))
    for b in sorted(set(bad)):
        print(" -", b)
    sys.exit(1)
print("LINK CHECK: %d links ok" % count)
