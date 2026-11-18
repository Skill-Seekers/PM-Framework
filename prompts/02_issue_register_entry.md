# Prompt 2: Issue Register Entry

| | |
|---|---|
| **Stage** | Log & Classify |
| **Lifecycle state served** | LOGGED |
| **Fills template** | `templates/csv/issues.csv` |
| **Input** | A raw issue description (message, email, verbal report) |
| **Output** | One issues.csv row, with the severity reasoning |
| **Human step** | Approve or override the severity; run `pmf issue log` |

**Use when:** you have a raw issue description (Slack message, email, verbal report) and need it formatted for the register.

```
You are helping a program manager log an issue into the Issue Register.

Given the raw description below, draft a single Issue Register row with these exact fields:
ID (leave as [ASSIGN]) | Phase | Title (short) | Description | Owner (if named, else
[NEEDS OWNER]) | Severity | Discovered (today's date if not stated) | Schedule Impact (days,
estimate if not explicit, mark as [ESTIMATE]) | Cost Impact ($, same rule) | Status (default:
Logged) | Next Action.

Severity classification rules (defaults; replace these four lines with your profile's severity table if it differs):
- Sev 1 (Red): blocks release / forces re-spin / customer-visible outage
- Sev 2 (Amber): >1 week slip or scope/contract change required
- Sev 3 (Yellow): <1 week impact, manageable in-team
- Sev 4 (Green): logged risk, no current impact

State your severity reasoning in one line so the PM can override quickly if wrong.

--- RAW ISSUE DESCRIPTION BELOW ---
[paste here]
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
