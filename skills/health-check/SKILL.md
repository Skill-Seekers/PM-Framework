---
name: health-check
description: Runs the weekly program health check - validates every register, computes the five health metrics and the worst-of rollup, writes the dashboard, and turns the result into a short list of actions. Use when the user says "how is the program doing", "health check", "program status", "run the metrics", "RAG status", "dashboard", or "what needs attention".
---

# Health check

Answers "is the program actually healthy" with the five metrics and the consistency check, not a feeling. Metric definitions: `docs/DATA_SCHEMAS.md#metric-definitions` and `framework/modules/08_program_metrics_and_health.md`.

## Running the tool

Run `python3 <plugin root>/pmf <command>` from inside the program folder (`<plugin root>` is `${CLAUDE_PLUGIN_ROOT}` when set, otherwise the folder two levels above this skill's base directory). If there is no `pmf.config.json`, run `setup-program` first.

## Steps

1. Run `python3 <plugin root>/pmf check`. Errors mean the registers contradict each other or a rule is broken (exit code 1). Warnings need a human decision (a stale risk, a vendor paid before delivery, a shared-resource clash).
2. Run `python3 <plugin root>/pmf health`. Report the rollup colour and each metric with its value and the rule behind the colour. The rollup is the worst of the five, never an average. A metric shown as not rated has too little data; say so and never read it as green.
3. Run `python3 <plugin root>/pmf dashboard` to write `reports/dashboard_DATE.html`, a read-only page the user can open or share. The CSV registers stay the place to edit.
4. Give a short action list, most urgent first: open Sev 1 and Sev 2 issues past their limits, overdue gates, stale risks, budget forecast over budget, errors from `check`. For each: what the data says, who owns it, and which skill or command is the next step.
5. When asked for the weekly report, hand over to `brief-and-report`.

## Rules

- Report what the tool says. Never change a threshold, a date, a severity or a state to improve a colour.
- Explain a red or amber by naming the exact rule that produced it.
- Use `--fail-on red` or `--fail-on amber` only when the user wants a script to stop on that colour.
- The dashboard and reports are views of the registers; they do not replace the owner's judgement.
