# Assumptions

What the framework takes to be true. If one is false for your program, the behavior described next to it changes.

## About the program

| ID | Assumption | If false |
|---|---|---|
| AS-1 | The program has defined phases, gates with written exit criteria, and hard delivery dates. | Use the software profile as a lighter starting point, or write your own; with no gates the schedule and gate metrics are not rated. |
| AS-2 | There is a baseline schedule and budget, supplied by the user. The tool never estimates them. | Metrics show not rated until `baseline_end`, `baseline_budget` and `baseline_date` values exist. |
| AS-3 | Each issue, risk and change has one named owner. | A team name or list of names is refused at LOGGED / ASSESSED. |
| AS-4 | There are four parties: customer, delivery org, third parties, PM. Internal programs map "customer" to the sponsor or consuming team. | Edit `parties` in your profile. |
| AS-5 | The PM is the single communicator upward. Management should not learn about a Sev 1 from someone else. | The Sev 1 same-day notice check will warn but cannot enforce it. |

## About the data

| ID | Assumption | If false |
|---|---|---|
| AS-6 | One person edits a workspace at a time; files live in git. There is no locking. | Concurrent edits to one CSV can conflict; use git branches and merge. |
| AS-7 | Dates are `YYYY-MM-DD`, durations are in days, money is a plain number in one currency. | The tool refuses malformed dates and numbers. |
| AS-8 | Registers hold no customer secrets or personal data. | That is the user's responsibility; see LIMITS.md. Keep workspaces in a private repo. |
| AS-9 | The report date is today unless set in `pmf.config.json`. | Set it to reproduce an earlier week. |

## About the rules

| ID | Assumption | If false |
|---|---|---|
| AS-10 | Severity model, aging days, escalation days, risk bands, metric thresholds and approval tiers are defaults from the playbook, not universal truths. | Change them in the profile; tests read the profile, not the defaults. |
| AS-11 | RAID has four categories (risk, assumption, issue, dependency). Action items are tracked in `next_action`, `mitigation` and the decision record, not in a fifth register. | Add a register and a schema in your own fork. |
| AS-12 | An overdue planned gate (open and past its planned date) turns Schedule Variance Red; a gate that finished late counts against Gate On-Time Rate instead. This is our reading of Module 08's "any single planned gate missed". | Set `overdue_gate_is_red` to false in the profile. |
| AS-13 | Burn ratio below the green band is Amber, not Red. Module 08 leaves 0.75 to 0.9 undefined. | Edit `under_spend_amber_below`. |
| AS-14 | Escape Rate needs at least three issues in a phase to be rated. Module 08 gives no minimum. | Edit `min_issues_for_rating`. |
| AS-15 | The Module 02 triage options (fix now, waive, defer) and the Module 07 change options (accept, accept and defer, reject) are two different decisions and use two different records. | n/a |

## About the tooling

| ID | Assumption | If false |
|---|---|---|
| AS-16 | Python 3.8 or later and a modern browser are available. No other software. | The CLI exits 2 with the version it found. |
| AS-17 | A human reviews every AI-drafted artifact before it is used or sent. | Nothing in the tool enforces review; the skills stop and ask before writing. |
| AS-18 | Plugin skills run from the program workspace, with the CLI found at the plugin root. | Skills report the path problem and stop. |
| AS-19 | The example data is fictional. Matching a real program is coincidence. | n/a |
