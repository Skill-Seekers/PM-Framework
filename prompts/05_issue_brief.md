# Prompt 5: Issue Brief 1-Pager

| | |
|---|---|
| **Stage** | Close & Brief |
| **Lifecycle state served** | CLOSED (Sev 1 and 2) |
| **Fills template** | `templates/documents/issue_brief.md` |
| **Input** | The register row, the options, the decision (or pending) |
| **Output** | A WHAT / IMPACT / OPTIONS / RECOMMENDATION / DECISION NEEDED BY brief for briefs/B-NNN.md |
| **Human step** | Edit for accuracy; send as its own thread, never as a reply-all |

**Use when:** a Sev 1 or Sev 2 issue needs the executive-facing brief.

```
You are helping a program manager draft a Sev 1/2 Issue Brief — a 90-second-read
executive one-pager. Tone: calm, factual, no hedging, no panic.

Source material:
- Issue Register row: [paste]
- Triage options considered: [paste]
- Decision made (if any yet): [paste, or "pending — decision needed by [date]"]

Draft in this exact structure, one line each unless noted:
WHAT — one sentence: what broke, which phase, which milestone is threatened
IMPACT — Schedule (+X days), Cost ($Y), Customer (affected milestone or "internal only")
OPTIONS — the three options with one-line trade-offs each
RECOMMENDATION — PM's call + one-line rationale
DECISION NEEDED BY — date, with a note on what happens on the call

Do not editorialize or add reassurance language ("don't worry," "we've got this") — the
brief should read as complete confidence through clarity, not through tone.
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
