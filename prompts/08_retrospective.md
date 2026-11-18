# Prompt 8: Retrospective One-Pager

| | |
|---|---|
| **Stage** | Close & Brief (after a Sev 1 or program close) |
| **Lifecycle state served** | after CLOSED |
| **Fills template** | `templates/documents/retrospective.md` |
| **Input** | Timeline, root cause, decision records |
| **Output** | A factual one-page retrospective |
| **Human step** | Check it is process-focused and names no individuals under WHAT DIDN'T |

**Use when:** a Sev 1 has closed, or the program has ended, and a retro needs to be written.

```
You are helping a program manager draft a retrospective one-pager. This is
factual and short — not a narrative, not a blame document. Do not name individuals in the
WHAT DIDN'T section; describe process/system gaps, not people.

Inputs:
- What happened (timeline): [paste/describe]
- Root cause (technical + process, if known): [paste/describe]
- Decision Records referenced: [paste links/IDs]

Draft using the Module 06.5 structure: WHAT HAPPENED (2-3 sentences, timeline not
narrative), ROOT CAUSE (1-2 sentences), WHAT WORKED (bullets), WHAT DIDN'T (bullets,
process-focused), CHANGES GOING FORWARD (numbered, concrete — each one should be specific
enough to action, not "communicate better").
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
