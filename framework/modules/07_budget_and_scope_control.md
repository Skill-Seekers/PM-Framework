# Module 07 — Budget & Scope Control

*How you prevent the two most common program failures: quiet budget overrun and scope creep by a thousand small changes.*

---

## 7.1 The core insight

Most programs don't blow their budget with one big overspend. They lose 3% per phase from small, un-tracked change orders. By the time anyone notices, the overrun is baked in and un-recoverable.

Same shape with scope: the SOW says X. Six weeks in, the customer asks for "just one small addition." Six weeks later, another one. Nobody re-scoped, so nobody re-priced. At release, you've delivered 1.4× the scope for 1× the budget — and it looks like an execution problem when it's actually a change-control problem.

**Both failures are prevented by the same discipline: every change gets logged, priced, and signed.**

---

## 7.2 Budget tracking — three artifacts

### 1. Budget Burn-Down Tracker

Budgeted vs. actual spend by phase, updated monthly.

| Phase | Budget | Actual to date | Forecast at completion | Variance | Status |
|---|---|---|---|---|---|
| Pre-Sales | $X | $Y | $Z | +/-% | G/A/R |
| Design / Build | | | | | |
| Integration | | | | | |
| Release | | | | | |
| Bring-up | | | | | |
| Qualification | | | | | |
| Sustain | | | | | |
| **Total** | | | | | |

**How to use:**
- Update monthly. Not quarterly — by quarterly it's too late.
- Any phase where forecast > budget goes Amber. Any phase where actual > budget goes Red.
- Flag Amber to the sponsor within one week of the update. Don't wait for the quarterly review.

Applies to any program with a fixed budget: consulting NRE, cloud infrastructure spend, contractor allocation, hardware BOM.

### 2. Change Order Cost Log

Every ECR / SOW amendment's cost delta, cumulative.

| # | Date | Change description | Cost delta | Cumulative | Sponsor sign-off |
|---|---|---|---|---|---|
| 001 | | | +$X | +$X | [name] |
| 002 | | | +$Y | +$(X+Y) | [name] |

**How to use:**
- Every ECR gets a row. Even the "small" ones.
- Cumulative column is the number that matters. When cumulative exceeds ~10% of original budget, escalate to the sponsor for a formal re-baseline.
- Never approve a change without a signed row. This is the primary defense against scope creep by a thousand small changes.

### 3. Vendor / Dependency Cost Tracking

Third-party licensing and NRE commitments, tied to delivery milestones.

| Vendor | Committed $ | Milestone | Paid on delivery? | Status |
|---|---|---|---|---|
| [Vendor A] | $X | [milestone] | Y/N | [G/A/R] |
| [Vendor B] | $Y | [milestone] | Y/N | [G/A/R] |

**Rule:** Never pay before acceptance. If a vendor requires up-front payment, price the delivery risk into the contract.

---

## 7.3 Scope control — the ECR flow

Any change to committed scope goes through this flow. No exceptions, no informal side-deals.

```
1. Request     → Customer or internal team requests a scope change
                 (verbal or written)

2. Log         → PM logs the request as a candidate ECR
                 (title, requestor, date, high-level scope)

3. Assess      → Discipline lead(s) size the change
                 - Effort (person-weeks)
                 - Cost delta
                 - Schedule impact
                 - Risk

4. Options     → PM builds a 3-option table
                 A: Accept (with cost/schedule impact)
                 B: Accept, but defer to next release
                 C: Reject with rationale

5. Approve     → Sponsor + customer sign off on chosen option
                 (or reject)

6. Amend       → If accepted:
                 - SOW amendment / change order signed
                 - Schedule re-baselined
                 - Budget line added to change order log
                 - Issue Register updated

7. Execute     → Work starts ONLY after step 6 is complete
```

**Never skip step 6.** Verbal approvals disappear the moment the person who gave them changes roles.

---

## 7.4 The "small change" trap

Most scope creep looks like this in real time:

> **Customer:** "Hey, while you're in there, could you also add [small thing]?"
> **Engineer:** "Sure, no problem, we can do that."
> **PM:** *[not in the conversation]*

Two months later, ten "small things" have added 15% to the workload with zero pricing, zero schedule adjustment, and zero written agreement.

**The counter-move — teach the team a single phrase:**

> "That sounds reasonable. Let me get the PM to log it as an ECR so we can size it and get it approved. It'll probably take a day."

Then it goes through the flow. If it's genuinely small, it clears in a day. If it's not small, the flow surfaces that fact **before** any work happens.

---

## 7.5 Approval thresholds — who signs what

Module 7.3's ECR flow says "sponsor + customer sign off" without saying who that is for a $500 change versus a $50,000 one. Define tiers before the first ECR arrives — retrofitting approval authority after someone's already annoyed about being bypassed is a worse conversation than having the table ready.

| Change size | Schedule impact | Approver | Turnaround target |
|---|---|---|---|
| Small — under $2,500 or 1 day | Negligible | PM (log only, no external approval) | Same day |
| Medium — $2,500–$25,000 or 1–5 days | Moderate | PM + delivery org lead | 2 business days |
| Large — $25,000–$100,000 or 1–4 weeks | Significant | Program sponsor + customer | 1 week |
| Major — over $100,000 or >4 weeks | Program-altering | Sponsor + customer + steering committee / change control board | Scheduled review cycle |

Adapt the dollar bands to your program's actual budget scale — the point is that every tier has a named approver and a turnaround target, so "who signs this" is never a live question when a change request lands.

---

## 7.6 Budget and change control in the tool

Approval tiers and the cumulative-change escalation percentage are in the profile (`change_control`). `pmf change assess` computes the tier from cost and schedule impact (the higher of the two); `pmf change approve` refuses until every approver the tier requires has signed; `pmf check` warns when cumulative approved cost passes the escalation percentage of the baseline budget. `budget.csv` feeds the Burn Ratio metric in [Module 08](08_program_metrics_and_health.md). The change lifecycle is in [LIFECYCLES.md](../../docs/LIFECYCLES.md).

---

**Previous:** [Module 06 — Communication Templates](06_communication_templates.md)  
**Next:** [Module 08 — Program Metrics & Health](08_program_metrics_and_health.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
