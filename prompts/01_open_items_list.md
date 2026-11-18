# Prompt 1: Open Items List

| | |
|---|---|
| **Stage** | Gate & Detect |
| **Lifecycle state served** | DETECTED |
| **Fills template** | `templates/documents/open_items.md` |
| **Input** | Raw gate review notes, tool output or a transcript |
| **Output** | An Open Items table; each row becomes `pmf issue add` |
| **Human step** | Confirm each item is real, then assign owner and severity |

**Use when:** you have raw gate review notes, a tool log, or a meeting transcript and need the pre-register capture list.

```
You are helping a program manager build an Open Items List from a gate review.

Below is [a meeting transcript / raw tool output / review notes]. Extract every item that
failed the gate's exit criteria or was flagged as unresolved. Do not summarize the whole
meeting — only pull items that represent open work or risk.

Output as a table with columns: Item # | Description | Raised By | Category (Design /
Schedule / Resource / Other) | Suggested Severity (Sev 1-4, using: Sev 1 = blocks release
or forces re-spin; Sev 2 = >1 week slip or scope change; Sev 3 = <1 week, manageable
in-team; Sev 4 = logged risk, no current impact) | Suggested Owner (if named in the source).

Flag anything ambiguous with [NEEDS PM INPUT] rather than guessing.

--- RAW INPUT BELOW ---
[paste transcript / notes / log output here]
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
