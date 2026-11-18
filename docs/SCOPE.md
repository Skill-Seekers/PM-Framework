# Scope

## In scope

| Area | What ships |
|---|---|
| Framework | Ten modules, a glossary, and a lifecycles document generated from the state-machine definitions |
| Profiles | `silicon` (9 phases, hardware plus software/firmware worked example) and `software` (6 phases) |
| Templates | CSV registers; markdown documents for the decision record, issue brief, weekly status and ECR/waiver; office versions (xlsx, docx) planned, not in 0.1.0 |
| Prompts | Ten copy-paste prompts, one per artifact, mapped to template and lifecycle state |
| CLI | `pmf`: init, check, issue / risk / change / gate lifecycle commands, health, brief, report, dashboard, lifecycles, show |
| Dashboards | Program Health (generated, read-only), lifecycle diagrams (generated), framework explainer (static) |
| Plugin | Five skills: setup-program, log-and-triage, brief-and-report, gate-review, health-check |
| Example | "Meridian", a fictional silicon program, with a Sev 1 walkthrough that regenerates every artifact |
| Quality | Tests, CI on Python 3.8 to 3.13, privacy scan, build log, limits |

## Out of scope

| Not included | Why / what to do instead |
|---|---|
| Connectors to Jira, Linear, Asana, Monday, GitHub Issues | The tool makes no network calls. Export from your tracker to the CSV schema. |
| A web app, accounts, multi-user editing | Files in git are the shared state. |
| Editing data inside the dashboard | CSV is the edit surface; regenerate the dashboard. |
| Scheduling engines, Gantt charts, critical-path math | Keep your schedule in your own tool; enter baseline and planned dates. |
| Resource levelling and capacity optimization | Module 10 is guidance; `templates/csv/contention.csv` is a simple table, not a solver. |
| Accounting-grade budgeting, forecasting models | The burn ratio is a status signal, not a financial system. |
| Legal, compliance or export-control advice | Module 01 only points out where a compliance gate would go. |
| Sending email, notifications, calendar events | Drafts are text for you to send. |
| Any AI step that decides severity, waives, approves or closes | AI drafts; the PM decides. |
| Real program data in this repository | Program data lives in your own private workspace. |
| Statistical forecasting, Monte Carlo, earned value | Not part of the playbook. |

## Boundaries worth knowing

- The profiles are examples of how to set the numbers, not recommendations for your program.
- The metrics are a rule-based status aid. They do not predict outcomes.
- The Meridian example shows the mechanics; its numbers are made up and chosen to exercise each state.
- The skills have not been run in a live Cowork or Claude Code session at the time of writing (see LIMITS.md).
