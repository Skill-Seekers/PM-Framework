# Prompts

Ten copy-paste prompts, one per artifact. Each file says which lifecycle state it serves, which template its output fills, what to paste in, and what the human does afterwards. They work in any chat assistant; the plugin skills in [skills/](../skills/) call the same files instead of copying them.

| # | Prompt | Stage | State served |
|---|---|---|---|
| 1 | [Open Items List](01_open_items_list.md) | Gate & Detect | DETECTED |
| 2 | [Issue Register Entry](02_issue_register_entry.md) | Log & Classify | LOGGED |
| 3 | [3-Option Triage Table](03_three_option_triage.md) | Triage | TRIAGED |
| 4 | [ECR / Waiver Document](04_ecr_waiver.md) | Resolve | DECIDED to RESOLVED |
| 5 | [Issue Brief 1-Pager](05_issue_brief.md) | Close & Brief | CLOSED (Sev 1 and 2) |
| 6 | [Weekly Status Report](06_weekly_status.md) | Close & Brief (recurring) | none (reporting) |
| 7 | [Customer Status Email](07_customer_status_email.md) | Close & Brief (recurring or event-driven) | none (reporting) |
| 8 | [Retrospective One-Pager](08_retrospective.md) | Close & Brief (after a Sev 1 or program close) | after CLOSED |
| 9 | [Gate Review Meeting Minutes](09_gate_review_minutes.md) | Gate & Detect (meeting to artifact) | gate REVIEW |
| 10 | [Gate Go/No-Go Announcement](10_gate_announcement.md) | Gate & Detect (decision to announcement) | gate GO, CONDITIONAL_GO or NO_GO |

Chain prompts for a Sev 1: one register row plus its decision record can feed prompts 5, 6 and 7 back to back, so the brief, the status section and the customer email come from the same source.

Nothing here sends, approves or closes anything. The PM reviews every draft ([Module 09](../framework/modules/09_ai_augmented_workflow.md)).
