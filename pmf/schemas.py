"""Register schemas: the single source for CSV columns, keys and enumerations.

docs/DATA_SCHEMAS.md describes these; tests check that every column named here appears in
that document and that templates/csv/*.csv headers match exactly."""

SCHEMAS = {
    "issues": {
        "file": "issues.csv", "key": "id", "id_prefix": "I",
        "columns": ["id", "title", "description", "phase", "owner", "severity", "detected", "state",
                    "gate_found", "escape_gate", "sched_impact_days", "cost_impact", "decision_ref",
                    "verification_ref", "brief_ref", "lesson", "exec_notified", "next_action", "due",
                    "linked_risk", "closed"],
        "dates": ["detected", "exec_notified", "due", "closed"],
        "numbers": ["severity", "sched_impact_days", "cost_impact"],
        "computed": ["escalated", "age_days"],
    },
    "risks": {
        "file": "risks.csv", "key": "id", "id_prefix": "R",
        "columns": ["id", "title", "description", "phase", "owner", "probability", "impact", "state",
                    "mitigation", "next_review", "last_scored", "accepted_by", "linked_issue"],
        "dates": ["next_review", "last_scored"],
        "numbers": ["probability", "impact"],
        "computed": ["score", "priority", "stale"],
    },
    "assumptions": {
        "file": "assumptions.csv", "key": "id", "id_prefix": "A",
        "columns": ["id", "title", "description", "owner", "status", "validate_by", "linked_risk"],
        "dates": ["validate_by"], "numbers": [],
        "enums": {"status": ["untested", "validated", "invalid"]},
        "computed": [],
    },
    "dependencies": {
        "file": "dependencies.csv", "key": "id", "id_prefix": "D",
        "columns": ["id", "title", "description", "owner", "provider", "needed_by", "status", "linked_issue"],
        "dates": ["needed_by"], "numbers": [],
        "enums": {"status": ["open", "at_risk", "delivered", "late"]},
        "computed": [],
    },
    "gates": {
        "file": "gates.csv", "key": "id", "id_prefix": "X",
        "columns": ["id", "name", "phase", "type", "baseline_date", "planned_date", "actual_date", "state",
                    "criteria_met", "waiver_refs", "triggered_by"],
        "dates": ["baseline_date", "planned_date", "actual_date"], "numbers": [],
        "enums": {"type": ["planned", "issue-triggered"]},
        "computed": [],
    },
    "raci": {
        "file": "raci.csv", "key": None,
        "columns": ["phase", "party", "role", "note"],
        "dates": [], "numbers": [],
        "enums": {"role": ["R", "A", "C", "I"]},
        "computed": [],
    },
    "budget": {
        "file": "budget.csv", "key": "phase",
        "columns": ["phase", "budget", "planned_to_date", "actual_to_date", "forecast_at_completion", "updated"],
        "dates": ["updated"],
        "numbers": ["budget", "planned_to_date", "actual_to_date", "forecast_at_completion"],
        "computed": ["variance_pct", "status"],
    },
    "changes": {
        "file": "changes.csv", "key": "id", "id_prefix": "C",
        "columns": ["id", "date", "title", "requestor", "state", "effort_person_weeks", "cost_delta",
                    "schedule_delta_days", "risk_note", "decision_ref", "approvers_signed", "linked_issue"],
        "dates": ["date"],
        "numbers": ["effort_person_weeks", "cost_delta", "schedule_delta_days"],
        "computed": ["tier", "cumulative_cost", "required_approvers"],
    },
    "vendors": {
        "file": "vendors.csv", "key": "vendor",
        "columns": ["vendor", "committed", "milestone", "paid_on_delivery", "status"],
        "dates": [], "numbers": ["committed"],
        "enums": {"paid_on_delivery": ["yes", "no"]},
        "computed": [],
    },
    "contention": {
        "file": "contention.csv", "key": None,
        "columns": ["resource", "period", "program", "demand", "capacity", "owner", "note"],
        "dates": [], "numbers": ["demand", "capacity"],
        "computed": [],
    },
    "events": {
        "file": "events.csv", "key": None,
        "columns": ["ts", "entity", "id", "event", "from_state", "to_state", "actor", "note", "ref"],
        "dates": [], "numbers": [],
        "enums": {"entity": ["issue", "risk", "change", "gate"],
                  "event": ["transition", "rescore", "severity_change", "edit"]},
        "computed": [],
    },
}
