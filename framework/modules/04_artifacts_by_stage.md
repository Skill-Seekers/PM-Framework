# Module 04 — Artifacts by Stage

*Every artifact a Sev 1 issue generates, from detection to closure. Seven to eight formal outputs. The decision record is the one most PMs skip — it is also the one that protects them three months later.*

---

## 4.1 The pattern

Every issue moves through five stages. Each stage produces its own artifacts. The full chain becomes an audit trail: what was caught, how it was classified, what options were considered, what was decided, who signed off, and what management was told.

---

## 4.2 Stage 1 — Gate & Detect (Evidence of Review)

| Artifact | Purpose | Owner |
|---|---|---|
| **Phase Gate Exit Criteria Checklist** | Per-phase gating doc — nothing proceeds without it | PM |
| **Gate Review Meeting Minutes** | Who attended, what passed/failed, decisions made | PM |
| **Design Review Findings Log** | Issues surfaced in reviews — feeds directly into the issue register | Discipline lead |
| **Verification / Compliance Report** | Static analysis, coverage, security scan, STA closure — as applicable | Discipline lead |
| **Physical / Deployment Rule-Check Report** | Clean-run output from applicable rule checks (ASIC: DRC/LVS; software: security scans; infra: config validation) | Discipline lead |
| **Coverage Closure Report** | Functional and code coverage % vs. target, per test plan | Test lead |
| **Open Items List** | Pre-register capture — everything that failed the gate before formal classification | PM |

---

## 4.3 Stage 2 — Log & Classify (Ownership + Impact)

| Artifact | Purpose | Owner |
|---|---|---|
| **Issue Register** | Living tracker (Jira / Confluence / Excel): ID, phase, owner, severity, schedule impact, cost impact, status. See [template](../../templates/csv/issues.csv) | PM |
| **Risk Register** | Things that *might* happen — parallel to issues. Feeds RAID log | PM |
| **RAID Log** | Executive-facing weekly snapshot: Risks, Assumptions, Issues, Dependencies. See [templates](../../templates/csv/risks.csv); `pmf raid` builds the snapshot | PM |
| **Severity Classification Matrix** | Reference doc defining Sev 1–4 thresholds — re-spin risk, schedule impact, scope trigger | PM (once per program) |
| **Program Schedule (baseline)** | Locked baseline — all schedule impacts measured against this | PM |

---

## 4.4 Stage 3 — Triage (Options + Blast Radius + Recommendation)

| Artifact | Purpose | Owner |
|---|---|---|
| **Triage Meeting Notes + Action Items** | Who owns what by when — an action record, not a discussion log | PM |
| **3-Option Analysis / Options Table** | Key deliverable: Fix now / Waive with conditions / Defer — each option with schedule, cost, risk. See [template](../../templates/documents/decision_record.md) | PM |
| **Blast Radius Assessment** | Schedule + cost impact + downstream phase dependencies | PM + tech lead |
| **ECR (Engineering Change Request)** | Formal doc when a scope change is involved: scope, impacted areas, re-run requirements, cost delta | Requestor + PM |
| **Impact Assessment** | Written Sev 1/2 summary — quantified impact to release date, budget, customer milestone | PM |

---

## 4.5 Stage 4 — Resolve (Executed, Documented, Formally Accepted)

| Artifact | Purpose | Owner |
|---|---|---|
| **ECR (signed)** | Scope change tracked through approval. Signed before any work starts | Sponsor / customer |
| **SOW Amendment / Change Order** | Formal contract update when scope, cost, or timeline changes. Both parties sign | Program sponsor |
| **Waiver Document** | Derating, coverage waiver, policy exception — violation, accepted risk, guideline reference, signatures | Discipline lead + customer |
| **Bug Report / Fix Summary** | Root cause, what changed, re-run results showing closure | Owner |
| **Regression / Re-run Report** | Verification output after a fix — confirms nothing else broke | Test lead |
| **Customer Sign-off / Approval** | Written record customer accepted the resolution. Never verbal only | PM |
| **ECO (post-release fix)** | ASIC: metal/mask-level change. Software: hotfix / patch. Fixes a live-system bug without a full re-spin/rebuild | Discipline lead |
| **Revised Program Schedule** | Updated critical path. Re-baselined after Sev 1 closure | PM |

---

## 4.6 Stage 5 — Close & Brief (Formally Closed + Memory Captured)

| Artifact | Purpose | Owner |
|---|---|---|
| **Issue Brief / 1-Pager** | WHAT / IMPACT / OPTIONS / RECOMMENDATION / DECISION NEEDED BY. Sev 1/2 only. See [template](../../templates/documents/issue_brief.md) | PM |
| **Program Status Report (weekly)** | Sev 2–4 issues roll here. Green / Amber / Red per workstream | PM |
| **Executive Status Update** | Sev 1 only — immediate, separate from the weekly report. Same-day | PM |
| **RAID Log Update** | Close the item or update status — must reflect current state after resolution | PM |
| **Decision Record** | Who made what decision, when, based on which option. **The artifact people skip and later regret.** | PM |
| **Customer Communication** | Status email for customer-visible issues — what happened, what was done, what's next | PM |
| **Lessons Learned / Retrospective Note** | Sev 1 only — what broke, why, what to do earlier next time. Short and factual. Into the program archive | PM |

---

## 4.7 The "why the decision record matters" point

Three months after a waiver, someone will ask: *"Why did we accept a violation on that timing corner?"* If there is no decision record, the answer is a shrug and a defensive reconstruction. If there is one, the answer is: here's the option table, here's the customer sign-off, here's the guideline reference, here's who signed. The record ends the conversation.

---

## 4.8 Which command produces which artifact

| Artifact | How it is produced |
|---|---|
| Issue Register, Risk Register | `issues.csv`, `risks.csv` (edited through `pmf issue` and `pmf risk`) |
| RAID Log | `pmf raid` |
| 3-Option Analysis, Decision Record | `decisions/DR-NNN.md` from the [template](../../templates/documents/decision_record.md); `pmf issue triage` and `decide` read it |
| Issue Brief / 1-Pager | `pmf brief <id>` drafts it from the register and the record; the PM edits |
| Program Status Report (weekly) | `pmf report weekly` drafts it from the metrics and registers |
| ECR, change order log | `changes.csv` through `pmf change` |
| Gate review, go/no-go | `gates.csv` through `pmf gate`; minutes and announcement use the prompts |
| Event trail | `events.csv`, written by every transition |

---

**Previous:** [Module 03 — RAID vs. Issue Register](03_raid_vs_issue_register.md)  
**Next:** [Module 05 — Communication Cadence](05_communication_cadence.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
