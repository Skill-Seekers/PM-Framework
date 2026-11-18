---
name: log-and-triage
description: Takes an issue or a risk from a meeting note, email or gate finding into the registers - logs it with one owner and a severity, drafts the three-option decision record, and moves it to triage. Use when the user says "log this issue", "we found a problem", "add a risk", "triage this", "draft the options", "three-option table", or pastes meeting notes with problems in them.
---

# Log and triage

Turns raw findings into register rows and a decision record, step by step, using the real lifecycle so nothing skips a stage. The lifecycle and what each step refuses without: `docs/LIFECYCLES.md`.

## Running the tool

Run `python3 <plugin root>/pmf <command>` from inside the program folder (`<plugin root>` is `${CLAUDE_PLUGIN_ROOT}` when set, otherwise the folder two levels above this skill's base directory). If there is no `pmf.config.json` above the current folder, run the `setup-program` skill first. Use `--dry-run` first on any command that changes state.

## Steps for an issue

1. Read the material the user gave. List each distinct problem and ask which to log. Use `prompts/01_open_items_list.md` when the source is a meeting or a gate review.
2. Create it: `python3 <plugin root>/pmf issue add --title <text> --description <text> --phase <phase id> --detected <date>`. The id is assigned by the tool.
3. Confirm with the user, then log it: `python3 <plugin root>/pmf issue log <id> --owner <one name> --severity <1 to 4>`. Severity and phase come from `profile.json`; read it for the definitions (`docs/DATA_SCHEMAS.md`). The owner is one person, never a team. If the user does not know yet, stop at DETECTED.
4. For triage, draft the decision record from `templates/documents/decision_record.md` using `prompts/03_three_option_triage.md`: options A (fix now), B (waive with conditions) and C (defer), each with schedule and cost, plus a Recommendation line grounded in the issue. Save it as `decisions/DR-<number>.md`. Leave unknown numbers as `[needs number]`. Do not invent cost or schedule figures.
5. Review the draft with the user and fix it. Then: `python3 <plugin root>/pmf issue triage <id> --decision-ref DR-<number>`.
6. Stop. Choosing an option is a human decision: when the user states the choice, record it in the decision record (Chosen, Decided by, Decided on, and Signed: yes for a waive or defer), then run `python3 <plugin root>/pmf issue decide <id>`.

For a Sev 1, also remind the user that the same-day executive note is due; the `brief-and-report` skill drafts it.

## Steps for a risk

`python3 <plugin root>/pmf risk add --title <text> --phase <phase id>`, then `python3 <plugin root>/pmf risk assess <id> --owner <one name> --probability <1 to 5> --impact <1 to 5>`. Scores are the user's judgement; offer the scale from the profile and let them choose. Then `risk mitigate`, `risk accept` (a named approver), `risk occur` (needs a linked issue) or `risk retire` as the user decides.

## When the tool refuses

Exit code 1 means a guard said no, and the message names it. Explain which guard and what is missing, fix the real gap with the user, and try again. Nothing is written when a command is refused. Never edit a CSV by hand to get past a refusal, and never change `events.csv`.

## Rules

- AI drafts, the PM decides: severity, owner, chosen option and signatures are the user's.
- Never invent a cause, number, owner or date. Quote the source or write a bracketed placeholder.
- One owner per item. Waivers and deferrals need a signed record.
