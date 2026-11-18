---
name: setup-program
description: Creates a program workspace for the PM-Framework and walks the PM through filling it in - program name, profile (silicon or software), baseline dates and budget, the RACI, and the planned gate dates. Use when the user says "set up a program", "start a new program", "create a workspace", "initialise PM-Framework", "kick off a program", or when any other PM-Framework skill finds no pmf.config.json.
---

# Set up a program

Creates one folder per program that holds the registers (CSV), decision records, briefs and reports. Every other skill works inside that folder.

## Running the tool

Run `python3 <plugin root>/pmf <command>` from inside the program folder. `<plugin root>` is `${CLAUDE_PLUGIN_ROOT}` when set, otherwise the folder two levels above this skill's base directory (the one that holds `skills/` and `pmf/`). Flags for any command: `python3 <plugin root>/pmf <command> --help`. File formats: `docs/DATA_SCHEMAS.md`. Lifecycles and guards: `docs/LIFECYCLES.md`.

## Steps

1. Ask for what the tool cannot know. Do not guess any of it:
   - the program name;
   - the profile: `silicon` (nine phases and gates, ASIC and SoC style) or `software` (six). If neither fits, point to `docs/ADAPTING.md` for writing a profile and use its path;
   - baseline start date, baseline end date, baseline budget (a plain number; no currency is assumed). These are stored in `pmf.config.json`; leave a flag off if the user does not know it yet.
2. Choose the folder with the user. Create it with `python3 <plugin root>/pmf init <folder> --program <name> --profile <profile> --baseline-start <date> --baseline-end <date> --baseline-budget <number>`. It refuses to overwrite an existing workspace; do not work around that.
3. Show what was created: `pmf.config.json`, `profile.json` (a copy of the profile, safe to edit for this program), blank registers, `raci.csv` and `gates.csv` (gate ids and names, dates blank) pre-filled from the profile, and the folders `decisions/`, `briefs/`, `reports/`.
4. Fill the inputs the user supplies, by editing the CSV files directly (they are the edit surface; keep the header row exactly as it is):
   - `gates.csv`: `baseline_date` and `planned_date` for each planned gate. Ask for every date. Leave a cell empty rather than inventing one.
   - `raci.csv`: one row per phase and party with an R, A, C or I letter, pre-filled from the profile. Review it with the user. Change a letter only when the user says so, and keep exactly one A per phase. Parties are roles (for example customer, delivery); real names go on issue and risk owners, not here.
   - `budget.csv`: one row per phase when the user has the numbers (`budget`, `planned_to_date`, `actual_to_date`, `forecast_at_completion`).
5. Run `python3 <plugin root>/pmf check` and `python3 <plugin root>/pmf health`. Explain the result in plain words. A fresh workspace shows metrics as not rated, which is correct: it means there is not enough data yet, not that all is well.
6. Tell the user the next skills: `log-and-triage` for the first issue or risk, `health-check` for the weekly rhythm.

## Rules

- AI drafts, the PM decides. Never invent a date, name, amount or owner; ask, or leave the cell empty.
- Never edit `events.csv`. It is the append-only record of every state change.
- To change thresholds or severity rules, edit the workspace copy `profile.json` with the user and say what changed. Never edit it to make a metric turn green.
- A profile is the single place phases, gates, severities and thresholds live. Do not hard-code them into documents.
