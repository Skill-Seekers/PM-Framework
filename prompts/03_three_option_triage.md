# Prompt 3: 3-Option Triage Table

| | |
|---|---|
| **Stage** | Triage |
| **Lifecycle state served** | TRIAGED |
| **Fills template** | `templates/documents/decision_record.md` |
| **Input** | An issue row plus prior similar decision records |
| **Output** | The Options table and a Recommendation line for decisions/DR-NNN.md |
| **Human step** | Revise live with the team; run `pmf issue triage` |

**Use when:** an issue is ready for triage and you need the options drafted before the meeting.

```
You are helping a program manager prepare a 3-option triage table ahead of a
triage meeting. This is a DRAFT for discussion — the PM and team will revise it live.

Issue: [paste issue description / Issue Register row]

Prior similar decisions (if any, paste past Decision Records or describe pattern):
[paste here, or write "none available"]

Draft three options in this exact structure:
- Option A — Fix Now: [description] | Schedule impact | Cost impact | Risk (Low/Med/High)
- Option B — Waive with Conditions: [description] | Schedule impact | Cost impact | Risk
- Option C — Defer to Next Revision: [description] | Schedule impact | Cost impact | Risk

Then draft a Recommendation line: which option, and a one-line rationale grounded in the
issue details — do not default to Option A without justification.

Mark any assumption you made with [ASSUMPTION] so the PM can correct it before the meeting.
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
