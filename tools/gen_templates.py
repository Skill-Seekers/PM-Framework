#!/usr/bin/env python3
"""Write header-only CSV templates from pmf/schemas.py (stdlib only).
Usage: python3 tools/gen_templates.py [--check]"""
import csv, importlib.util, io, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("schemas", os.path.join(ROOT, "pmf", "schemas.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def header_text(cols):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(cols)
    return buf.getvalue()


def main(argv):
    out_dir = os.path.join(ROOT, "templates", "csv")
    os.makedirs(out_dir, exist_ok=True)
    stale = 0
    for name, s in mod.SCHEMAS.items():
        path = os.path.join(out_dir, s["file"])
        want = header_text(s["columns"])
        have = open(path, newline="").read() if os.path.exists(path) else None
        if "--check" in argv:
            if have != want:
                print("stale:", path)
                stale += 1
        else:
            with open(path, "w", newline="") as f:
                f.write(want)
    if "--check" in argv:
        return 1 if stale else 0
    print("wrote %d templates to %s" % (len(mod.SCHEMAS), out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
