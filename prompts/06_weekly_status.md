# Prompt 6: Weekly Status Report

| | |
|---|---|
| **Stage** | Close & Brief (recurring) |
| **Lifecycle state served** | none (reporting) |
| **Fills template** | `templates/documents/weekly_status.md` |
| **Input** | Register state, RAID state, milestones, standup notes |
| **Output** | The weekly status report; `pmf report weekly` drafts the same from the registers |
| **Human step** | Verify every number against the registers; send |

**Use when:** the week's status is due.

```
You are helping a program manager draft the weekly status report.

Inputs:
- Issue Register (current state): [paste rows, or export summary]
- RAID Log (current state): [paste]
- Milestones this week / next gate: [paste or describe]
- Anything notable from daily standups: [paste or describe]

Draft using this exact structure:
HEADLINE — Overall status (Green/Amber/Red) + one-sentence why. Use Module 08 rule: status
is the WORST of the underlying metrics, not an average.
MILESTONES — next gate, date, status; this week's hit/missed milestone
WORKSTREAM STATUS — one line per workstream, G/A/R + reason
OPEN ISSUES (Sev 1/2 only) — ID, title, owner, impact, next action
RAID CHANGES THIS WEEK — added / escalated (risk→issue) / closed
DECISIONS NEEDED — what, needed by when, from whom
UPCOMING — next week's key activities, next gate readiness

Flag any field where the input didn't give you enough to fill it confidently, rather than
inventing a plausible-sounding number.
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
