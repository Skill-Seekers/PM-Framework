# Prompt 4: ECR / Waiver Document

| | |
|---|---|
| **Stage** | Resolve |
| **Lifecycle state served** | DECIDED to RESOLVED |
| **Fills template** | `templates/documents/ecr_waiver.md` |
| **Input** | A completed decision record |
| **Output** | A formal ECR or waiver ready for signature |
| **Human step** | Check the computed approval tier; obtain real signatures |

**Use when:** a triage decision is made and needs to become a formal Engineering Change Request or Waiver.

```
You are helping a program manager draft an ECR (Engineering Change Request) or
Waiver document from a completed triage decision.

Decision Record details:
- Issue: [paste]
- Decision: [Option A/B/C selected]
- Decided by: [name/role]
- Rationale: [paste]
- Conditions: [paste, if any]

Draft the document with these sections: Title | Scope of Change | Impacted Areas |
Re-run/Verification Requirements | Cost Delta | Schedule Impact | Risk Accepted (if a
waiver) | Approval Required From (per the Module 07 §7.5 approval tiers: state which tier this falls
into based on the cost/schedule figures given) | Signature block (name, role, date — blank
for signing).

Keep it formal — this is a document that gets signed and filed, not a summary.
```

**Rules for every prompt:** paste real input only; the prompt is built to flag gaps (`[NEEDS PM INPUT]`, `[ASSUMPTION]`, `[NOT DISCUSSED]`) instead of inventing details, so do not ask for a "complete" draft with no gaps; the severity, option and recommendation calls are drafts to challenge, not decisions. See [Module 09](../framework/modules/09_ai_augmented_workflow.md).
