"""A program workspace: config, profile, registers, decision records, briefs, events."""
import os

from pmf import profile as prof
from pmf.schemas import SCHEMAS
from pmf.util import (PmfError, append_csv, now, parse_date, read_csv, today, write_csv)


class Workspace(object):
    def __init__(self, root, report_date=None):
        self.root = root
        self.config = prof.load_config(root)
        p = prof.load_json(prof.resolve_profile_path(self.config["profile"], root), "profile")
        prof.validate_profile(p)
        self.profile = prof.Profile(p)
        self.lifecycles = prof.lifecycles()
        rd = report_date or self.config.get("report_date")
        self.report_date = parse_date(rd, "report date") if rd else today()
        self._cache = {}

    # ---- paths ----
    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def register_path(self, name):
        return self.path(SCHEMAS[name]["file"])

    # ---- registers ----
    def load(self, name, required=True):
        if name in self._cache:
            return self._cache[name]
        path = self.register_path(name)
        if not os.path.exists(path):
            if required:
                raise PmfError("missing %s; run `pmf init` or copy templates/csv/%s" % (SCHEMAS[name]["file"], SCHEMAS[name]["file"]))
            self._cache[name] = []
            return self._cache[name]
        header, rows = read_csv(path)
        cols = SCHEMAS[name]["columns"]
        if header != cols:
            missing = [c for c in cols if c not in header]
            extra = [c for c in header if c not in cols]
            raise PmfError("%s header does not match the schema (missing: %s; unexpected: %s)" % (
                SCHEMAS[name]["file"], ", ".join(missing) or "none", ", ".join(extra) or "none"))
        self._cache[name] = rows
        return rows

    def save(self, name, rows):
        write_csv(self.register_path(name), SCHEMAS[name]["columns"], rows)
        self._cache[name] = rows

    def find(self, name, key_value):
        key = SCHEMAS[name]["key"]
        for r in self.load(name):
            if r.get(key) == key_value:
                return r
        return None

    # ---- events ----
    def add_event(self, entity, ident, event, from_state, to_state, actor, note="", ref=""):
        row = {"ts": now(), "entity": entity, "id": ident, "event": event, "from_state": from_state,
               "to_state": to_state, "actor": actor, "note": note, "ref": ref}
        append_csv(self.register_path("events"), SCHEMAS["events"]["columns"], row)
        if "events" in self._cache:
            self._cache["events"].append(row)
        return row

    def events(self):
        return self.load("events", required=False)

    # ---- documents ----
    def decision_path(self, ref):
        return self.path("decisions", "%s.md" % ref)

    def brief_path(self, ref):
        return self.path("briefs", "%s.md" % ref)

    # ---- helpers ----
    def planned_gates(self):
        return [g for g in self.load("gates") if g.get("type", "planned") == "planned"]

    def open_issues(self, severities=None):
        out = []
        for i in self.load("issues"):
            if i["state"] in self.profile.open_issue_states:
                if severities is None or _int(i.get("severity")) in severities:
                    out.append(i)
        return out


def _int(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return None


def int_or_none(x):
    return _int(x)
