# Module 08 — Program Metrics & Health

*What actually makes a workstream Green, Amber, or Red. Every other module refers to G/A/R status — this is where it gets defined instead of judged.*

---

## 8.1 Why this module exists

"Status: Amber" means nothing without a rule behind it. If G/A/R is a gut call, two PMs on the same program will color the same workstream differently — and an executive who's been burned by an optimistic PM will stop trusting anyone's colors. Metrics are what make status defensible instead of vibes-based.

This module defines the five metrics that, together, answer "is this program actually healthy" — and the thresholds that convert each one into Green/Amber/Red.

---

## 8.2 The five core metrics

### 1. Schedule Variance (SV)

How far the program is from its baseline schedule, in days or as a percentage of remaining duration.

```
SV (days) = Actual completion date (or forecast) − Baseline planned date
SV (%)    = SV (days) / total planned program duration
```

| Status | Threshold |
|---|---|
| Green | On baseline, or within ±3% of planned duration |
| Amber | 3–8% behind baseline |
| Red | >8% behind baseline, or any planned gate that is overdue (open and past its planned date). A gate that finished late counts against Gate On-Time Rate instead |

### 2. Gate On-Time Rate

Of the planned gates completed so far, what percentage hit their scheduled date without slipping.

```
Gate On-Time % = (Gates hit on date / Total gates completed) × 100
```

| Status | Threshold |
|---|---|
| Green | ≥90% |
| Amber | 75–89% |
| Red | <75% |

A program can have acceptable Schedule Variance and still be Red here — chronic small gate slips that each get absorbed are exactly the pattern that produces a surprise Red at the end.

### 3. Issue Aging

How long Sev 1/2 issues stay open, measured from detection to close.

| Severity | Green | Amber | Red |
|---|---|---|---|
| Sev 1 | Closed same week | Open 1–2 weeks | Open >2 weeks |
| Sev 2 | Closed within 2 weeks | Open 2–4 weeks | Open >4 weeks |

Track the count of issues currently past their Amber threshold — that count, not the raw open-issue total, is the number that belongs in the weekly status report.

### 4. Escape Rate

Issues that should have been caught at an earlier gate but weren't — discovered downstream instead. This is the metric that tells you whether your gate criteria are actually working.

```
Escape Rate = (Issues attributable to a missed/weak gate check / Total issues that phase) × 100
```

| Status | Threshold |
|---|---|
| Green | <10% |
| Amber | 10–20% |
| Red | >20% |

A rising escape rate is a leading indicator that gate criteria need tightening — it shows up here before it shows up as a Sev 1.

A phase with very few issues gives a noisy percentage (one issue is 100%). The tool rates a phase only when it has at least `min_issues_for_rating` issues (default 3); below that it shows *not rated*.

### 5. Budget Burn Rate

From Module 07's Burn-Down Tracker — actual spend vs. planned spend by phase, expressed as a ratio.

```
Burn Ratio = Actual spend to date / Planned spend to date (same point in schedule)
```

| Status | Threshold |
|---|---|
| Green | 0.9–1.1 (within 10% of plan) |
| Amber | 1.1–1.25, or below 0.9 (under-spend can mean under-resourced, not just savings) |
| Red | >1.25, or forecast-at-completion exceeds total budget |

---

## 8.3 Rolling up to a single program status

A workstream's overall color is the **worst** of its individual metric colors — not an average. One Red metric makes the workstream Red, regardless of how green the other four look. Averaging hides exactly the thing status reporting exists to surface.

```
Workstream Status = MIN(SV color, Gate On-Time color, Issue Aging color, Escape Rate color, Burn color)
```

Program-level status is the worst of all workstream statuses, same rule.

---

## 8.4 What goes in the weekly report vs. what stays in the dashboard

Not every metric belongs in every audience's view — this is Module 05's altitude principle applied to numbers.

| Metric | Daily standup | Weekly report | Customer review | Exec quarterly |
|---|---|---|---|---|
| Schedule Variance | — | ✓ | ✓ (headline) | ✓ (trend) |
| Gate On-Time Rate | — | ✓ | ✓ | ✓ |
| Issue Aging (count past threshold) | ✓ (Sev 1 only) | ✓ | — | ✓ (rollup) |
| Escape Rate | — | — | — | ✓ |
| Budget Burn Rate | — | ✓ | — (unless contractually visible) | ✓ (headline) |

Escape Rate is a PM/exec diagnostic, not something you show a customer — it's an internal signal about gate quality, not a customer-facing commitment.

---

## 8.5 How the tool computes the five metrics

Thresholds live in the profile (`metrics`, plus `severity.levels[].aging_days`). The exact formulas, and the places where this module is ambiguous and the tool picks a default, are in [DATA_SCHEMAS.md](../../docs/DATA_SCHEMAS.md#metric-definitions). Run `pmf health` for the colors and the rule behind each one. A metric with too little data is shown as not rated; it is never counted as Green.

---

**Previous:** [Module 07 — Budget & Scope Control](07_budget_and_scope_control.md)  
**Next:** [Module 09 — AI-Augmented Workflow](09_ai_augmented_workflow.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
