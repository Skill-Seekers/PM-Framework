# Module 10 — Cross-Program Coordination: Capacity & Consensus

*How you get things done when you don't own the resources and don't have authority over the people you need. Two failure modes, same root cause — no single owner governs the boundary between programs or orgs — and the same fix: make coordination a structural habit instead of a personality contest.*

---

## 10.1 Why this module exists

Every other module in this playbook assumes you're running *one* program with a defined RACI inside it. Two real situations fall outside that frame, and neither is covered by Modules 01–09:

1. **Resource/capacity contention** — two or more concurrent programs need the same design, test, or engineering resource at the same time, and neither program's RACI has authority over the other's.
2. **Consensus without authority** — you need an org that doesn't report to you, and isn't contractually obligated to you the way a customer or vendor is, to commit time or make a decision on your timeline.

Both are "TPM operates across a boundary nobody governs" problems. Part A below covers the first; Part B covers the second. §10.4 shows why they're one module, not two.

---

## 10.2 Part A — Resource & Capacity Contention Across Concurrent Programs

### 10.2.1 The problem in one sentence

Two programs need the same person, lab, or test cell in the same window, and by the time anyone notices, both schedules already assume they'll get it.

### 10.2.2 Make contention visible before it's a crisis

The single highest-leverage move: a **shared resource calendar** that every program planner writes to, not just their own. If Program A and Program B both silently pencil in the same test engineer for the same four weeks, the conflict is invisible until week one — when it becomes a Sev 1 for both programs simultaneously. A shared calendar surfaces the collision at planning time, when it's a scheduling problem, not a crisis.

**How to use it:** any resource shared across more than one active program goes on one calendar, owned by whoever manages that resource pool (a discipline lead, a lab manager) — not by either program's PM. Both programs' planners check it before finalizing their own schedule, not after.

### 10.2.3 The Resource Request — a lightweight ECR for capacity

When a program needs time from a shared resource, it goes through a named request, the same discipline Module 02/07 already apply to scope and budget changes: **written, not verbal; specific, not vague.**

| Field | Example |
|---|---|
| Requesting program | Program A |
| Resource / skill needed | Test engineer, 1 FTE |
| Window | Weeks of Oct 6 – Oct 31 |
| Criticality if not met | Slips Design Freeze gate by 3 weeks |
| Alternative if declined | Contract test support, +$35K |

A request this specific gets a real answer. "Can we get some test help in October" gets a shrug.

### 10.2.4 When two programs collide — the 3-way trade-off table

Same pattern as Module 02's 3-option triage table, applied to capacity instead of a technical issue. Whoever owns the resource (or the escalation body in §10.2.5) picks one, with a stated rationale — never a silent default to "whoever asked first."

| Option | Description | When it's the right call |
|---|---|---|
| **A — Sequence** | One program waits, the other goes first | Clear priority difference (revenue, contractual date, exec visibility) |
| **B — Split** | Resource time-boxed between both programs (e.g. 3 days/week each) | Both programs can tolerate a slower burn rate on this workstream |
| **C — Backfill** | Contract or borrow external capacity to cover one program | Budget exists and the skill is contractable; protects both schedules at a cost |

### 10.2.5 Escalation: someone above both programs has to own the call

A TPM on Program A cannot unilaterally decide that Program B waits — that's a peer overriding a peer, and it will resurface as a relationship problem even if it "wins" once. Contention that both PMs can't resolve in one conversation escalates to whoever sits above both programs: a portfolio lead, an engineering director, a resource governance forum. The ask is the same shape as any other escalation in this playbook (Module 02 Step 5): **three options, a recommendation, a decision needed by date** — not "help me decide," but "here's the trade-off, here's my recommendation, I need a call by Friday."

### 10.2.6 Add a Resource Owner to the RACI when pools are shared

If your program regularly draws from a pool shared with other programs (a shared lab, a shared verification team), add that pool's owner as a fifth RACI party for the affected phases — Responsible for allocation, Consulted before either program finalizes a schedule that depends on them. This is an extension of Module 01's four-party RACI (§1.3), not a replacement for it.

### 10.2.7 A portfolio-level metric, separate from Module 08's five

Module 08's five program-health metrics are scoped to a single program and stay exactly as defined there — don't fold this in and dilute "five metrics, not a feeling." **Resource Contention Rate** is a different, portfolio-level number, useful only if you're coordinating multiple concurrent programs:

```
Resource Contention Rate = (Shared-resource requests that hit a scheduling conflict / Total shared-resource requests) × 100
```

Rising contention rate is a leading indicator that the org is running more concurrent programs than its shared capacity supports — a staffing/portfolio conversation, not something a single PM can fix by working harder.

---

## 10.3 Part B — Building Consensus Without Authority

### 10.3.1 The core principle

You have no positional power over the orgs you're coordinating, so authority gets substituted with three things: a track record of small reliable delivery, a framing that speaks to the other org's own incentives, and a written artifact that carries the argument instead of you personally.

### 10.3.2 Before you need anything

- **Bank credibility on small things first.** Deliver reliably on minor commitments early in a relationship before asking for anything that costs another org real effort.
- **Learn each stakeholder's scorecard.** What does their manager measure them on? An ask framed around their KPIs lands differently than one framed around your program's KPIs — same ask, very different response rate.
- **Own the shared artifact.** Volunteer to maintain the cross-org schedule, RAID log, or tracker. Whoever owns the single source of truth has de facto coordination power nobody had to grant them.

### 10.3.3 Getting to yes

- **Pre-wire the decision — never negotiate live in a group.** Work every real objection 1:1 before the group meeting. The group forum ratifies something already agreed; it isn't where disagreement first surfaces.
- **Trade, don't demand.** Know what the other org needs from the broader program and offer it explicitly in the same conversation as your ask.
- **Make the ask small, specific, and time-boxed.** "Can you commit Sam for two weeks starting the 15th" gets a decision. "Can your team support this program" gets a non-answer.
- **Let the data argue, not you.** A written impact assessment or 3-option table (Module 02 §2.2, Step 3) depersonalizes the ask — people can disagree with a document without it becoming a conflict with you.

### 10.3.4 When you're stuck

- **Escalate through structure, not personality.** Route through the RACI and steering committee set up at kickoff (Module 01), not personal pressure on an individual. "The program needs a decision by Thursday's gate review" is repeatable; "I need you to just say yes" burns a relationship.
- **Protect the relationship over winning the room.** Take disagreement offline. A public win for them and a private conversation to resolve friction beats being right in a meeting and losing the relationship for the next ask.

### 10.3.5 The structural trick most people miss

A public RACI sign-off at kickoff (Module 01 §1.3) is the single highest-leverage move here — getting each org lead to explicitly agree to their role in front of peers converts an implicit expectation into a social commitment. Later, "you agreed to this at kickoff" is a very different conversation than "I need you to do this." Pair it with a same-day, shared Decision Record (Module 02 §2.2 Step 5, Module 04 §4.6) on every real decision — it removes the ambiguity that consensus usually erodes into weeks later.

---

## 10.4 How Part A and Part B connect

Both problems exist because a program's own RACI (Module 01) only governs *inside* that program — the moment you need something from a peer program or a non-obligated org, you've stepped outside it. The fix in both cases is the same move: replace personal authority you don't have with a **structure everyone already agreed to** (a shared calendar, a RACI sign-off, an escalation path) so the ask is depersonalized and repeatable instead of a one-off negotiation you have to win by force of personality every time.

---

## 10.5 Resource contention in the tool

`contention.csv` ([template](../../templates/csv/contention.csv)) holds one row per resource, period and program. `pmf check` flags any resource and period where summed demand exceeds capacity. This is a visibility aid for the shared calendar in 10.2.2, not a scheduling solver.

---

## 10.6 Cross-references

- Module 01 (§1.3 RACI, §1.4 Gates) — the structure both parts of this module extend past a single program's boundary
- Module 02 (§2.2 Step 3 Triage, Step 5 Close & Brief) — the 3-option table and Decision Record pattern reused in §10.2.4 and §10.3.5
- Module 04 (§4.6) — Decision Record artifact
- Module 07 (§7.3 ECR flow) — the written-request discipline the Resource Request in §10.2.3 is modeled on
- Module 08 — Resource Contention Rate (§10.2.7) is a portfolio-level metric, kept separate from Module 08's five program-level metrics

---

**Previous:** [Module 09 — AI-Augmented Workflow](09_ai_augmented_workflow.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
