# Prompt 10: Gate Go/No-Go Announcement

| | |
|---|---|
| **Stage** | Gate & Detect (decision to announcement) |
| **Lifecycle state served** | gate GO, CONDITIONAL_GO or NO_GO |
| **Fills template** | `templates/documents/gate_announcement.md` |
| **Input** | Gate name, criteria status, decision, waivers, conditions |
| **Output** | The go/no-go announcement |
| **Human step** | Confirm the decision matches `gates.csv`; send |

**Use when:** a gate decision has been made and needs to go out formally.

```
You are helping a program manager draft a Gate Go/No-Go announcement.

Inputs:
- Gate name and date: [paste]
- Exit criteria and status of each (Met/Not Met/Waived): [paste]
- Decision: [GO / NO-GO / CONDITIONAL GO]
- Waivers accepted, if any (with sign-off names): [paste]
- Conditions, if conditional: [paste]

Draft using the Module 06.4 structure exactly: subject line, decision, date, attendees,
exit criteria status list, waivers accepted, conditions (if applicable), next phase start
date, next gate name/date, decision record file location placeholder.
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
