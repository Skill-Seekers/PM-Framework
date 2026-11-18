"""Profiles, lifecycles and workspace config loading."""
import io
import json
import os

from pmf.util import PmfError, parse_date

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(PKG_DIR)
CONFIG_NAME = "pmf.config.json"


def load_json(path, what):
    try:
        with io.open(path, encoding="utf-8") as f:
            return json.load(f)
    except IOError:
        raise PmfError("cannot read %s: %s" % (what, path))
    except ValueError as e:
        raise PmfError("%s is not valid JSON (%s): %s" % (what, e, path))


def lifecycles():
    return load_json(os.path.join(PKG_DIR, "data", "lifecycles.json"), "lifecycles")


def shipped_profiles():
    d = os.path.join(ROOT_DIR, "profiles")
    if not os.path.isdir(d):
        return []
    return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))


def resolve_profile_path(name, workspace_root=None):
    """name can be a shipped profile id, or a path (absolute, or relative to the workspace)."""
    if not name:
        raise PmfError("no profile set; put \"profile\": \"silicon\" (or a path) in %s" % CONFIG_NAME)
    cands = []
    if workspace_root:
        cands.append(os.path.join(workspace_root, name))
    cands.append(name)
    cands.append(os.path.join(ROOT_DIR, "profiles", name + ".json"))
    cands.append(os.path.join(ROOT_DIR, "profiles", name))
    for c in cands:
        if os.path.isfile(c):
            return c
    raise PmfError("profile %r not found (shipped profiles: %s)" % (name, ", ".join(shipped_profiles()) or "none"))


REQUIRED_PROFILE_KEYS = ["profile_id", "parties", "phases", "gates", "severity", "escalation", "risk",
                         "metrics", "change_control"]


def validate_profile(p, where="profile"):
    miss = [k for k in REQUIRED_PROFILE_KEYS if k not in p]
    if miss:
        raise PmfError("%s is missing: %s" % (where, ", ".join(miss)))
    phases = [x["id"] for x in p["phases"]]
    if len(set(phases)) != len(phases):
        raise PmfError("%s: duplicate phase ids" % where)
    gids = [g["id"] for g in p["gates"]]
    if len(set(gids)) != len(gids):
        raise PmfError("%s: duplicate gate ids" % where)
    for g in p["gates"]:
        if g["phase"] not in phases:
            raise PmfError("%s: gate %s uses unknown phase %s" % (where, g["id"], g["phase"]))
    levels = [l["level"] for l in p["severity"]["levels"]]
    for lv in p["severity"].get("brief_required_for", []):
        if lv not in levels:
            raise PmfError("%s: brief_required_for names undefined severity %s" % (where, lv))
    return p


class Profile(object):
    def __init__(self, data):
        self.d = data
        self.id = data["profile_id"]
        self.phase_ids = [x["id"] for x in data["phases"]]
        self.gates = data["gates"]
        self.levels = {l["level"]: l for l in data["severity"]["levels"]}
        self.parties = [x["id"] for x in data["parties"]]

    def phase(self, pid):
        for p in self.d["phases"]:
            if p["id"] == pid:
                return p
        return None

    def gate(self, gid):
        for g in self.gates:
            if g["id"] == gid:
                return g
        return None

    @property
    def brief_required_for(self):
        return self.d["severity"].get("brief_required_for", [])

    @property
    def exec_notice_same_day(self):
        return self.d["severity"].get("exec_notice_same_day", [])

    @property
    def open_issue_states(self):
        return self.d["escalation"]["open_states_issue"]

    @property
    def escalation_days(self):
        return self.d["escalation"]["days"]

    def risk_band(self, score):
        for b in self.d["risk"]["bands"]:
            if b["min"] <= score <= b["max"]:
                return b
        return None

    def tier_for(self, cost, days):
        """Highest tier reached by cost or by schedule."""
        tiers = self.d["change_control"]["tiers"]
        def idx(value, key):
            if value is None:
                return 0
            for i, t in enumerate(tiers):
                if t[key] is None or value <= t[key]:
                    return i
            return len(tiers) - 1
        i = max(idx(abs(cost or 0), "max_cost"), idx(abs(days or 0), "max_days"))
        return tiers[i]


def find_workspace_root(start=None, explicit=None):
    if explicit:
        p = os.path.abspath(explicit)
        if os.path.isfile(p):
            p = os.path.dirname(p)
        if not os.path.isfile(os.path.join(p, CONFIG_NAME)):
            raise PmfError("no %s in %s (run `pmf init` there first)" % (CONFIG_NAME, p))
        return p
    env = os.environ.get("PMF_WORKSPACE")
    if env:
        return find_workspace_root(explicit=env)
    cur = os.path.abspath(start or os.getcwd())
    while True:
        if os.path.isfile(os.path.join(cur, CONFIG_NAME)):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            raise PmfError("no %s found here or in a parent folder; cd into your program workspace, "
                           "pass --workspace, or run `pmf init`" % CONFIG_NAME)
        cur = parent


def load_config(root):
    cfg = load_json(os.path.join(root, CONFIG_NAME), CONFIG_NAME)
    for k in ("program", "profile"):
        if not cfg.get(k):
            raise PmfError("%s: %r is required" % (CONFIG_NAME, k))
    for k in ("baseline_start", "baseline_end", "report_date"):
        if cfg.get(k):
            parse_date(cfg[k], k)
    if cfg.get("baseline_budget") not in (None, ""):
        try:
            float(cfg["baseline_budget"])
        except (TypeError, ValueError):
            raise PmfError("%s: baseline_budget must be a number" % CONFIG_NAME)
    return cfg
