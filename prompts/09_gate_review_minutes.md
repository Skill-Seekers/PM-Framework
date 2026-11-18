# Prompt 9: Gate Review Meeting Minutes

| | |
|---|---|
| **Stage** | Gate & Detect (meeting to artifact) |
| **Lifecycle state served** | gate REVIEW |
| **Fills template** | `templates/documents/gate_minutes.md` |
| **Input** | A gate review transcript or notes |
| **Output** | Formal minutes; open items feed prompt 1 |
| **Human step** | Check no criterion is marked Met that was not actually discussed |

**Use when:** you have a transcript of a gate review meeting.

```
You are helping a program manager convert a gate review transcript into formal
Gate Review Meeting Minutes.

Transcript:
[paste transcript]

Draft using this structure: Gate Name | Date | Attendees (names/roles mentioned) | Exit
Criteria Status (list each criterion discussed: Met / Not Met / Waived, with one-line
evidence from the transcript) | Decisions Made | Open Items Raised (feed these into the
Open Items List prompt separately) | Next Steps.

Only include what was actually discussed — do not infer a criterion was met if it wasn't
explicitly addressed in the transcript. Mark unaddressed criteria as [NOT DISCUSSED —
FOLLOW UP].
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
