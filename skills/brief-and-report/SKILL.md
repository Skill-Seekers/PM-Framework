---
name: brief-and-report
description: Drafts the written outputs of a program from its registers - the Sev 1 and Sev 2 management brief, the same-day executive note, the weekly status report, the RAID snapshot, the customer status email and the retrospective. Use when the user says "write the brief", "weekly status", "RAID snapshot", "exec note", "customer update", "retrospective", or "report on the program".
---

# Brief and report

Every draft is built from the registers, so the numbers match what the tool holds. Nothing is sent, approved or closed by this skill.

## Running the tool

Run `python3 <plugin root>/pmf <command>` from inside the program folder (`<plugin root>` is `${CLAUDE_PLUGIN_ROOT}` when set, otherwise the folder two levels above this skill's base directory). If there is no `pmf.config.json`, run `setup-program` first.

## Steps

1. Ask which output: brief, executive note, weekly status, RAID snapshot, customer email, or retrospective.
2. Generate the base draft with the tool when one exists:
   - Brief for a Sev 1 or Sev 2 issue: `python3 <plugin root>/pmf brief <issue id>` writes `briefs/B-NNN.md` and records it on the issue. Preview first with `--stdout`.
   - Weekly status: `python3 <plugin root>/pmf report weekly` writes `reports/weekly_DATE.md`.
   - RAID snapshot: `python3 <plugin root>/pmf raid` writes `reports/raid_DATE.md`. It always lists open Sev 1 and Sev 2 issues.
   - Executive note, customer email, retrospective: start from `templates/documents/` and fill from the registers.
3. Fill every `[placeholder]` with the user. The tool leaves a placeholder wherever the registers cannot know something (the impact on the customer, the decision needed by, the named recommendation). Use the matching prompt as a guide: `prompts/05_issue_brief.md`, `prompts/06_weekly_status.md`, `prompts/07_customer_status_email.md`, `prompts/08_retrospective.md`. Ask for the missing facts instead of writing around them.
4. Read the result back against the registers: dates, counts, severity and the health colours must agree with `pmf health`.
5. A brief is required before a Sev 1 or Sev 2 issue can be closed, and it must have all five sections filled (WHAT, IMPACT, OPTIONS, RECOMMENDATION, DECISION NEEDED BY).

## Rules

- Never overwrite a draft the user may have edited. `report weekly` and `raid` refuse to replace an existing file unless `--force` is passed; do not pass `--force` unless the user says to replace that file. `brief` writes one brief per issue and refuses a second; edit the existing `briefs/B-NNN.md` instead.
- Never send anything. Give the user the text; they send it.
- Management hears from the PM first. For a Sev 1 the executive note goes out the same day.
- Do not soften or round a number to sound better. Do not claim a cause that the issue record does not state.
- Customer emails state only what the customer-visible record supports.
