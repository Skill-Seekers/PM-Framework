# Requirements

What PM-Framework must do. Each requirement has an ID that tests, docs and the build log refer to. "Must" is required for release; "should" is wanted but may slip with a note in LIMITS.md.

## Framework content

| ID | Requirement |
|---|---|
| FW-1 | Must provide ten modules, each answering one named question a program manager faces: lifecycle and governance; issue management; RAID vs. issue register; artifacts by stage; communication cadence; communication templates; budget and scope control; metrics and health; AI-augmented workflow; cross-program coordination. |
| FW-2 | Must be domain-agnostic in the core text. Domain detail (silicon, software) lives in profiles and worked examples, never in module rules. |
| FW-3 | Must contain no employer, customer, vendor or person names from real programs. Examples use fictional names only. |
| FW-4 | Must define every term used in a glossary. |
| FW-5 | Should state, per module, what it is not for (limits). |

## Data and profiles

| ID | Requirement |
|---|---|
| DA-1 | Registers are plain CSV with the schemas in [DATA_SCHEMAS.md](DATA_SCHEMAS.md). No database, no spreadsheet engine at run time. |
| DA-2 | One profile file holds all phase, gate, severity, aging, escalation, risk, metric and approval-tier values. No other file hard-codes them. |
| DA-3 | Two profiles ship (`silicon`, `software`). A user can write a third by copying one (see ADAPTING.md). |
| DA-4 | Every number in Module 07 and Module 08 appears in the profile and is tested against the module text, so docs and behavior cannot drift. |
| DA-5 | Every change to an issue, risk, change request or gate appends one row to `events.csv`. The file is never rewritten by the tool. |

## Lifecycles

| ID | Requirement |
|---|---|
| LC-1 | Issue, risk, change-request and gate lifecycles are explicit state machines in `pmf/data/lifecycles.json`. |
| LC-2 | A transition is refused, with the failing guard named, when its guards are not met. Nothing is half-written on refusal. |
| LC-3 | Waive, defer and scope-change decisions require a signed decision record. Verbal approval is not accepted by the tool. |
| LC-4 | `docs/LIFECYCLES.md` and the lifecycle diagrams are generated from `lifecycles.json`. |
| LC-5 | The Meridian example walks one Sev 1 through every issue state and produces each artifact. |

## Metrics and status

| ID | Requirement |
|---|---|
| ME-1 | Status colors are computed from the five metrics with the definitions in DATA_SCHEMAS.md. A color cannot be typed in. |
| ME-2 | Rollup is the worst color, never an average. |
| ME-3 | A metric with too little data is shown as not rated, with the reason. It never defaults to Green. |
| ME-4 | Every metric result states the rule that produced its color, in words. |

## CLI and scripts

| ID | Requirement |
|---|---|
| CL-1 | One CLI (`python3 pmf ...`), Python 3.8 or later, standard library only. |
| CL-2 | Exit codes: 0 done, 1 action needed (a check failed, a guard refused), 2 could not run (bad input, missing file). |
| CL-3 | Mutating commands support `--dry-run` and print the change before writing. |
| CL-4 | The tool never invents data. A missing input stops with a message saying what is needed. |
| CL-5 | Reports and briefs are drafts built deterministically from the registers. The tool never sends, approves, waives or closes on its own. |
| CL-6 | The tool makes no network calls. |

## Dashboards

| ID | Requirement |
|---|---|
| DB-1 | `pmf dashboard` writes one self-contained HTML file: no external scripts, fonts or images. |
| DB-2 | It shows the five metrics with color and rule, the rollup, gates, issues by lifecycle state, aging, RAID, budget burn. |
| DB-3 | It works in light and dark mode, at phone width, and every chart has a table view. |
| DB-4 | It is read-only. Edit the CSV and regenerate. |
| DB-5 | Colors are never the only signal (labels or icons accompany them). |

## AI layer

| ID | Requirement |
|---|---|
| AI-1 | Ten prompts, one per artifact, each stating its input, the template it fills, and the lifecycle state it serves. |
| AI-2 | Five plugin skills call the same CLI and prompts; skills never duplicate the prompt text. |
| AI-3 | Every skill states that the human reviews and decides, and stops for approval before any write. |
| AI-4 | Prompts and skills work without any specific vendor tool; tool-specific advice is in an appendix. |

## Quality and release

| ID | Requirement |
|---|---|
| QA-1 | Automated tests cover each lifecycle (allowed and refused transitions), each metric (boundary values), profile validation, and doc-to-profile consistency. |
| QA-2 | CI runs the tests on Python 3.8 to 3.13. |
| QA-3 | The privacy scan (denylist, secrets, paths, metadata, git history) passes with no FAIL before any release. |
| QA-4 | Release is private only: Skill-Seekers organization, collaborators with Read access. |
| QA-5 | LIMITS.md states what has and has not been verified, including skills not run in a live session. |
