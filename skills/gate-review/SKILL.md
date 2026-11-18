---
name: gate-review
description: Prepares and records a phase-gate review - checks the exit criteria against the registers, drafts the review minutes and the go, conditional go or no-go announcement, and moves the gate through its states. Use when the user says "prepare the gate review", "are we ready for the gate", "go/no-go", "gate minutes", "gate announcement", or names a gate such as design freeze or tape-out readiness.
---

# Gate review

A gate passes only when every exit criterion is met, or each unmet criterion has a signed waiver, and no blocking issue is open. The tool enforces that; this skill prepares the evidence and the paperwork. Lifecycle and guards: `docs/LIFECYCLES.md`.

## Running the tool

Run `python3 <plugin root>/pmf <command>` from inside the program folder (`<plugin root>` is `${CLAUDE_PLUGIN_ROOT}` when set, otherwise the folder two levels above this skill's base directory). If there is no `pmf.config.json`, run `setup-program` first.

## Steps

1. Identify the gate (`python3 <plugin root>/pmf show <gate id>`). Read its exit criteria from `profile.json` and its blocking severities.
2. Before the meeting, run `python3 <plugin root>/pmf check` and `python3 <plugin root>/pmf health`, and list the open Sev 1 and Sev 2 issues (`python3 <plugin root>/pmf raid --stdout`). State plainly which criteria look met, which do not, and which blocking issues are open. Ask for evidence for each criterion; do not assume.
3. Open the review: `python3 <plugin root>/pmf gate review <gate id>`.
4. After the meeting, draft the minutes from the user's notes using `prompts/09_gate_review_minutes.md` and `templates/documents/gate_minutes.md`: who attended, what passed or failed, decisions made. Quote the user's notes; do not invent attendees or decisions.
5. Record the outcome the room decided, nothing else:
   - Go: `python3 <plugin root>/pmf gate go <gate id> --criteria-met <criteria numbers separated by semicolons> --actual-date <date>`. Criteria numbers are 1-based, in the order of the gate's list in `profile.json`; list all of them for a go.
   - Conditional go: `python3 <plugin root>/pmf gate conditional <gate id> --criteria-met <numbers> --waiver-refs <DR ids separated by semicolons>`; each unmet criterion needs a signed waiver record.
   - No-go: `python3 <plugin root>/pmf gate nogo <gate id> --criteria-met <numbers>`; each unmet criterion needs an issue logged with this gate as `gate_found`.
   Use `--dry-run` first.
6. Draft the announcement with `prompts/10_gate_announcement.md` and `templates/documents/gate_announcement.md`. Give it to the user to send.
7. After a no-go, `python3 <plugin root>/pmf gate review <gate id> --note <reason>` reopens the review once the gaps are closed.

## When the tool refuses

The message names the guard (for example `all_criteria_met` or `no_blocking_open_issues`). Report it as the real state of the gate: the fix is to meet the criterion, sign a waiver, or close the blocking issue, never to relabel it. Do not edit `criteria_met` to make a gate pass.

## Rules

- The go or no-go is the room's decision. This skill records it; it never makes it.
- Waivers are signed decision records, never verbal. Issue-triggered gates are separate from planned gates in reports.
- Nothing is announced by this skill; the user sends it.
