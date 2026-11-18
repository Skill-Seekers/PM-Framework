"""Small shared helpers: errors, dates, numbers, atomic CSV IO. Standard library only (Python 3.8+)."""
import csv
import datetime
import io
import os
import re
import tempfile

EXIT_DONE = 0
EXIT_ACTION = 1   # a check failed or a guard refused: the user must act
EXIT_COULD_NOT_RUN = 2


class PmfError(Exception):
    """Could not run: bad input, missing file, bad setting. Exit code 2."""
    code = EXIT_COULD_NOT_RUN


class ActionNeeded(Exception):
    """The command ran but refused or found problems. Exit code 1."""
    code = EXIT_ACTION

    def __init__(self, messages, title=None):
        if isinstance(messages, str):
            messages = [messages]
        self.messages = list(messages)
        self.title = title
        Exception.__init__(self, "; ".join(self.messages))


def now():
    """UTC timestamp. PMF_FAKE_NOW (ISO) pins it for tests and the demo."""
    fake = os.environ.get("PMF_FAKE_NOW")
    if fake:
        return fake
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def today():
    fake = os.environ.get("PMF_FAKE_NOW")
    if fake:
        return parse_date(fake[:10], "PMF_FAKE_NOW")
    return datetime.date.today()


def parse_date(text, what="date"):
    if isinstance(text, datetime.date):
        return text
    s = (text or "").strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        raise PmfError("%s %r is not a date; use YYYY-MM-DD" % (what, text))
    try:
        return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except ValueError:
        raise PmfError("%s %r is not a real calendar date" % (what, text))


def is_date(text):
    try:
        parse_date(text)
        return True
    except PmfError:
        return False


def num(text, what="number"):
    """Parse a plain number. Accepts +3, -2, 1,500 and $1,500; returns float. Raises PmfError."""
    if isinstance(text, (int, float)):
        return float(text)
    s = (text or "").strip().replace(",", "").replace("$", "")
    if s.startswith("+"):
        s = s[1:]
    try:
        return float(s)
    except ValueError:
        raise PmfError("%s %r is not a number" % (what, text))


def is_num(text):
    try:
        num(text)
        return True
    except PmfError:
        return False


def is_placeholder(text):
    """True for empty text or template placeholders such as [name] or [YYYY-MM-DD]."""
    s = (text or "").strip()
    return s == "" or bool(re.search(r"\[[^\]]*\]", s))


def split_list(text):
    return [x.strip() for x in (text or "").replace(",", ";").split(";") if x.strip()]


def fmt_num(x):
    if x is None:
        return ""
    if float(x) == int(x):
        return str(int(x))
    return ("%.2f" % x).rstrip("0").rstrip(".")


def read_csv(path, columns=None):
    """Return (header, rows) where rows are dicts. Missing file -> PmfError."""
    if not os.path.exists(path):
        raise PmfError("missing file: %s" % path)
    with io.open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        try:
            header = next(rd)
        except StopIteration:
            raise PmfError("%s is empty (needs a header row)" % path)
        rows = []
        for i, rec in enumerate(rd, 2):
            if not any(c.strip() for c in rec):
                continue
            if len(rec) > len(header):
                raise PmfError("%s line %d has %d fields but the header has %d" % (path, i, len(rec), len(header)))
            rec = rec + [""] * (len(header) - len(rec))
            rows.append(dict(zip(header, rec)))
    return header, rows


def csv_safe(value):
    """Neutralise spreadsheet formula injection for text we write (a leading = + - @ becomes literal)."""
    s = "" if value is None else str(value)
    if s[:1] in ("=", "@") or (s[:1] in ("+", "-") and not is_num(s)):
        return "'" + s
    return s


def write_csv(path, columns, rows):
    """Atomic write: temp file in the same folder, then rename."""
    d = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".pmf-", suffix=".tmp", dir=d)
    try:
        with io.open(fd, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(columns)
            for r in rows:
                w.writerow([csv_safe(r.get(c, "")) if c not in ("ts",) else r.get(c, "") for c in columns])
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def append_csv(path, columns, row):
    """Append one row (events log). Creates the file with a header if absent."""
    exists = os.path.exists(path) and os.path.getsize(path) > 0
    with io.open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        if not exists:
            w.writerow(columns)
        w.writerow([csv_safe(row.get(c, "")) if c != "ts" else row.get(c, "") for c in columns])


def next_id(prefix, existing):
    n = 0
    for e in existing:
        m = re.match(r"^%s-(\d+)$" % re.escape(prefix), e or "")
        if m:
            n = max(n, int(m.group(1)))
    return "%s-%03d" % (prefix, n + 1)


def days_between(a, b):
    return (b - a).days


def single_owner_problem(owner):
    """Return a message if owner is not exactly one named person, else None."""
    s = (owner or "").strip()
    if not s:
        return "owner is empty"
    if re.search(r"[/,;&]|\band\b|\bteam\b|\bgroup\b", s, re.I):
        return "owner %r is not one named person (no lists, 'and', or 'team')" % s
    return None
