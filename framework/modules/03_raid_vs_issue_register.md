# Module 03 — RAID vs. Issue Register

*Two different tools, two different audiences. Mixing them is the second most common PM mistake — right after not keeping a decision record.*

---

## 3.1 The distinction in one line

**The Issue Register is your daily operational tracker. The RAID Log is your weekly executive-facing snapshot.**

They share data. They are not the same document, and they do not serve the same audience.

---

## 3.2 Side by side

| | Issue Register | RAID Log |
|---|---|---|
| **Audience** | PM, tech leads, discipline owners | Program leadership, exec review, steering committee |
| **Update frequency** | Real-time; every new issue same day | Weekly (or per exec cadence) |
| **Granularity** | Every issue, all severities, one row each | Rollup — top risks, current issues, dependencies, key assumptions |
| **Fields** | ID, phase, owner, severity, schedule impact, cost impact, status | Category (R/A/I/D), title, exposure/impact, owner, next review |
| **Retention** | Living tracker; closed items archived after retro | Snapshot; each weekly version stored |
| **Format** | Spreadsheet or issue tracker (Jira, GitHub Issues, Excel) | 1-page table, part of exec status pack |
| **Template** | [issues.csv](../../templates/csv/issues.csv) | [risks.csv](../../templates/csv/risks.csv), [assumptions.csv](../../templates/csv/assumptions.csv), [dependencies.csv](../../templates/csv/dependencies.csv) |

---

## 3.3 What each letter of RAID means (and where it comes from)

| Letter | Meaning | Source |
|---|---|---|
| **R — Risks** | Things that *might* happen, that would hurt if they did | Risk register; things not yet in the issue register |
| **A — Assumptions** | What the plan assumes to be true. Untested assumptions are latent risks | Captured at planning; reviewed each cycle |
| **I — Issues** | Things that *have* happened. Sev 1 and Sev 2 rows pulled from the issue register | Rolled up from Issue Register |
| **D — Dependencies** | External deliverables the program requires. Late = new issue | Pulled from schedule + vendor tracker |

The RAID Log does **not** contain everything from the Issue Register. It contains the Sev 1/2 items that need exec visibility, plus the risk-side items (Risks, Assumptions, Dependencies) that the Issue Register does not track.

---

## 3.4 The lifecycle of a single item

```
[Risk] logged in R column of RAID
   │
   │  triggering event occurs
   ▼
[Issue] created in Issue Register (Sev 1-4)
   │
   │  Sev 1 or Sev 2?
   ├─── yes → also rolled up to I column of RAID
   │
   ▼
[Triaged] → 3-option decision → resolution
   │
   ▼
[Closed] in Issue Register
   │
   ▼
[Removed] from RAID next weekly cycle
```

**Common failure:** an item lives in the Issue Register but never makes it to the RAID Log, so leadership is surprised when it becomes critical. The rule: **any Sev 1 or Sev 2 must appear in the current week's RAID Log.**

---

## 3.5 Risk Scoring — Probability × Impact

Section 3.3 defines what a Risk is. It doesn't say how to prioritize the ones you have — and a RAID log with 15 undifferentiated risks is as useless to an executive as an unsorted issue list. Score every risk on two axes, 1–5 each, and prioritize by the product.

**Probability (1–5):** How likely is this to occur in the current plan?

| Score | Meaning |
|---|---|
| 1 | Rare — no precedent, would require multiple failures |
| 2 | Unlikely — possible but no current indicators |
| 3 | Possible — plausible given current trajectory |
| 4 | Likely — early indicators already present |
| 5 | Near-certain — already trending this way |

**Impact (1–5):** If it happens, how bad is it?

| Score | Meaning |
|---|---|
| 1 | Negligible — absorbed without any plan change |
| 2 | Minor — <3 days schedule or <2% budget |
| 3 | Moderate — 1–2 week slip or scope/contract touch |
| 4 | Major — forces a gate re-review or customer escalation |
| 5 | Severe — program-threatening; would be Sev 1 if it occurred |

**Risk Score = Probability × Impact** (range 1–25).

| Score range | Priority | Action |
|---|---|---|
| 15–25 | Critical | Weekly PM-owned mitigation plan; visible in every weekly RAID review |
| 8–14 | High | Mitigation plan exists; reviewed bi-weekly |
| 4–7 | Medium | Logged, monitored monthly, no active mitigation required yet |
| 1–3 | Low | Logged and revisited quarterly or on plan change |

This scoring lives in the **Risk Scoring** sheet of [risks.csv](../../templates/csv/risks.csv), [assumptions.csv](../../templates/csv/assumptions.csv), [dependencies.csv](../../templates/csv/dependencies.csv) — score once when a risk is logged, re-score whenever new information changes either axis. A risk that never gets re-scored is a risk nobody is actually watching.

---

## 3.6 The registers in the tool

The issue register (`issues.csv`) and the RAID inputs (`risks.csv`, `assumptions.csv`, `dependencies.csv`) are separate files. `pmf raid` builds the weekly snapshot from them and always includes every open Sev 1 and Sev 2 issue, so the failure in 3.4 cannot happen quietly. `pmf risk assess` records probability and impact, computes the score, and applies the review interval for its band from the profile. `pmf check` flags a risk that has not been re-scored within its band's interval. The risk lifecycle is in [LIFECYCLES.md](../../docs/LIFECYCLES.md).

---

**Previous:** [Module 02 — Issue Management](02_issue_management.md)  
**Next:** [Module 04 — Artifacts by Stage](04_artifacts_by_stage.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
