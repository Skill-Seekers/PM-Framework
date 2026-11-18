# Prompt 7: Customer Status Email

| | |
|---|---|
| **Stage** | Close & Brief (recurring or event-driven) |
| **Lifecycle state served** | none (reporting) |
| **Fills template** | `templates/documents/customer_email.md` |
| **Input** | Progress, upcoming milestones, anything customer-visible |
| **Output** | A customer status email |
| **Human step** | Remove internal jargon; confirm nothing internal-only leaked; send |

**Use when:** a customer-facing update is due, or after a customer-visible issue resolves.

```
You are helping a program manager draft a customer status email. Tone: polished,
warm-professional, confident. This goes to an external customer contact — more formal than
an internal update, no internal jargon (severity numbers, internal tool names) unless the
customer already uses that language with you.

Inputs:
- Progress this period: [paste/describe]
- Upcoming milestones + any action needed from the customer: [paste/describe]
- Anything the customer needs to know about a resolved or open issue: [paste/describe,
  omit entirely if nothing customer-visible]

Draft using the Module 06.3 structure: greeting, one-line intro, PROGRESS THIS PERIOD,
UPCOMING, ITEMS FOR YOUR ATTENTION (omit section if empty), one-line overall confidence
statement tied to the next major milestone, warm close offering a call.

If the underlying status is Amber or Red, do not hide it — state plainly what's changing
and why, without alarm language.
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
