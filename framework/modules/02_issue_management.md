# Module 02 — Issue Management

*How you handle problems inside a phase. A 5-step framework that runs every week, escalating only when severity demands it.*

---

## 2.1 The framework in one sentence

**Detect at a gate, log with an owner, triage with three options, resolve with a signed record, close with a management brief.**

Every step is deliberate. Nothing is ad-hoc. The framework runs whether the issue is a critical timing violation, a missed API deadline, a cloud provider outage, or a customer-driven scope change.

---

## 2.2 The 5 steps

### Step 1 — Gate & Detect

Issues surface through phase-gate reviews, not ad-hoc pings. Each gate has formal exit criteria. Anything that fails a gate goes into the register **before** the next phase starts.

**Examples of gate checks that surface issues:**

- **Requirements gate:** missing customer sign-off, conflicting inputs across stakeholders
- **Design freeze:** design-to-spec delta review — catches late scope drift
- **Integration:** static analysis / STA reports — violations against target
- **Physical/deployment:** clean-run rule checks (DRC/LVS for ASICs; policy/security scans for software)
- **Validation:** coverage report — functional or code coverage below target

**Rule of thumb:** Every phase has a checklist. Nothing moves forward until exit criteria are met — or we've formally triaged what's not met and accepted the risk in writing.
---

### Step 2 — Log & Classify (Issue Register)

Every issue enters the [Issue Register](../../templates/csv/issues.csv) immediately — same day, not the next meeting.

**Fields:** ID · Phase · Owner (one name) · Severity (1–4) · Schedule impact (days) · Cost impact · Status

**Severity model:**

| Sev | Color | Trigger | Cadence |
|---|---|---|---|
| **Sev 1** | Red | Blocks release / forces re-spin / customer-visible outage | Same-day exec notification. War-room cadence |
| **Sev 2** | Amber | >1 week slip or scope/contract change required | Weekly exec visibility |
| **Sev 3** | Yellow | <1 week impact, manageable in-team | Weekly triage |
| **Sev 4** | Green | Logged risk, no current impact | Monthly review |

The severity model must match your program's actual risk tolerance. A weekly triage of Sev 3s that never move should be re-classified as Sev 4 — otherwise triage becomes noise.

---

### Step 3 — Triage — The 3-Option Table

**Weekly triage:** PM + design/tech lead + relevant discipline leads.
**Daily war-room:** for any open Sev 1.

Output is always a 3-option table. Management cannot make a decision without options.

| Option | Description | When it's the right call |
|---|---|---|
| **A — Fix now** | Schedule cost (+X days), low risk | Required for customer-visible or safety-critical issues |
| **B — Waive with conditions** | Formal sign-off + documented risk, zero schedule impact | Use when within vendor/foundry/policy guideline |
| **C — Defer to next revision** | Carry as known issue, fix next release | High risk if customer-visible; needs explicit customer acceptance |

The [decision_record.md](../../templates/documents/decision_record.md) template holds this table plus the decision line.

---

### Step 4 — Resolve — Phase-Specific Paths

Resolution paths differ by the type of change. The pattern is the same: assessment → approval → execution → verification → sign-off.

| Change type | Path |
|---|---|
| **Scope / spec change** | ECR (Engineering Change Request) → impact assessment → SOW amendment → written approval **before** any work starts |
| **Design bug** | Bug filed with owner + due date. Post-freeze changes require ECR |
| **Timing / performance** | Discipline owns fix. PM drives daily standup. Fix vs. derating waiver — waiver requires design lead + customer sign-off |
| **Environment / infrastructure** | Config or capacity change through change control. Escalate to Sev 1 if blocking |
| **Validation / coverage** | Formal closure plan + re-run schedule. Waivers require customer risk acceptance |

**Universal rule:** waivers, deferrals, and scope changes always leave a **written, signed record**. Never verbal-only.

---

### Step 5 — Close & Brief Management

Management hears from **you** — not from the customer, not from the vendor, not from the escalation email that got forwarded to them.

**Format:** 1-pager, 90 seconds to read. Template: [issue_brief.md](../../templates/documents/issue_brief.md).

- **WHAT:** One sentence — what broke, which phase, which milestone threatened
- **IMPACT:** Schedule (+X days). Cost ($Y). Customer milestone affected
- **OPTIONS:** Three options from triage with trade-offs
- **RECOMMENDATION:** PM's call + one-line rationale
- **DECISION NEEDED BY:** [Date] — urgency without panic

**Cadence:**
- Sev 1: same-day exec call + daily update until closed
- Sev 2: weekly report, dedicated section
- Sev 3/4: weekly triage summary rollup

---

## 2.3 The five steps in the tool

Each step is a lifecycle state change enforced by the CLI (full table in [LIFECYCLES.md](../../docs/LIFECYCLES.md)):

| Step | State reached | Command | What the tool refuses without |
|---|---|---|---|
| 1. Gate & Detect | `DETECTED` | `pmf issue add` | id, title, detected date |
| 2. Log & Classify | `LOGGED` | `pmf issue log` | phase, one owner, severity |
| 3. Triage | `TRIAGED` | `pmf issue triage` | a decision record with options A, B, C and a recommendation |
| 4. Resolve | `DECIDED`, `RESOLVED` or `DEFERRED` | `pmf issue decide`, `resolve`, `defer` | a chosen option; a signed record for waive or defer; verification evidence |
| 5. Close & Brief | `CLOSED` | `pmf issue close` | a brief (Sev 1 and 2) and a one-line lesson |

Severity names, triggers, cadences and aging limits come from the profile; the table in 2.2 shows the shipped defaults.

---

**Previous:** [Module 01 — Lifecycle & Governance](01_lifecycle_and_governance.md)  
**Next:** [Module 03 — RAID vs. Issue Register](03_raid_vs_issue_register.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
