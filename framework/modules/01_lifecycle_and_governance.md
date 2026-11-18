# Module 01 — Lifecycle & Governance

*How you run a program end-to-end: phases, RACI, and the planned gate structure.*

---

## 1.1 Why this module exists

Most program failures aren't caused by execution mistakes inside a phase — they're caused by ownership gaps between phases. This module defines who owns what across the lifecycle and where the non-negotiable checkpoints are.

Two things every program needs from day one:
- A **RACI** everyone agrees to before real work starts.
- A **gate calendar** the customer signs off on in the SOW (or equivalent commitment doc).

If those two exist, the odds of a Sev 1 caused by ambiguity drop dramatically.

---

## 1.2 The generic program lifecycle

Any hardware, software, or infrastructure program can be described as some version of these eight phases:

| # | Generic phase | ASIC example |
|---|---|---|
| 1 | Pre-Sales / Feasibility | Customer requirements, feasibility study, rough NRE quote |
| 2 | Award / Contract | SOW signed, scope locked, kickoff |
| 3 | Design / Build | RTL design + verification |
| 4 | Integration / Hardening | Synthesis, DFT, physical design |
| 5 | Release | Tape-out |
| 6 | Bring-up / Beta | First silicon, ATE correlation |
| 7 | Qualification / GA | HTOL, ESD, JEDEC, customer acceptance |
| 8 | Sustain / Production | Mass production, yield tracking, sustaining engineering |

Rename these to match your domain. The point isn't the labels — it's that every program has a design phase, an integration phase, a release, a validation window, and a sustain phase. If you can't tell someone which phase your program is in, you've lost governance.

---

## 1.3 RACI — the four parties that matter

Every non-trivial program has (at least) four parties whose ownership never fully overlaps:

1. **The customer** — the party paying, receiving, or accepting the deliverable.
2. **The delivery org** — engineering, design center, dev team; whoever builds.
3. **Third-party dependencies** — vendors, IP suppliers, external teams, foundry, cloud provider.
4. **The PM** — the only role that touches all three continuously.

The classic failure mode: everyone assumes someone else owns the gate.

### Reference RACI (adapt per program)

| Phase | Customer | Delivery Org | 3rd-Party Deps | PM |
|---|---|---|---|---|
| Pre-Sales | Requirements (R) | Feasibility (C) | Availability check (C) | Owns proposal (A) |
| Award / Contract | Approves (A) | Scopes (R) | Commits (R) | Owns negotiation (A) |
| Design / Build | Reviews (C) | Executes (R) | Delivers dependencies (R) | Owns schedule (A) |
| Integration | Informed (I) | Executes (R) | Support (C) | Owns readiness (A) |
| Release | Approves (A) | Sign-off (R) | Sign-off (C) | Owns go/no-go (A) |
| Bring-up / Beta | Co-drives (R) | Executes (R) | Support (C) | Owns coordination (A) |
| Qualification | Approves acceptance (A) | Executes (R) | Support (C) | Owns test plan (A) |
| Sustain / Production | Consumes (I) | Sustains (R) | Sustains (C) | Owns SLA / metrics (A) |

**R** = Responsible (does the work) · **A** = Accountable (owns the outcome) · **C** = Consulted · **I** = Informed

### How to publish it

- Distribute at kickoff, not later. Do not proceed to detailed planning until every party has signed off.
- One page, phase across the top, party down the side. No prose.
- Store it wherever your program schedule lives so anyone joining mid-flight can find it.

---

## 1.4 Planned gates vs. issue-triggered gates

There are two kinds of gates. Don't confuse them.

### Planned gates
Scheduled from day one. The customer signs off on the gate calendar in the SOW. These are **calendar events**, not surprises.

| Gate | Exit criteria |
|---|---|
| Kickoff | SOW signed, RACI published, tools/access provisioned, holiday/vacation calendar shared |
| Requirements Freeze | Requirements locked, customer sign-off obtained. Change after this requires an ECR |
| Design Freeze | Code/design coverage targets met, no open Sev 1/2 issues, customer review complete |
| Release Readiness | All validation clean, sign-offs complete, waivers documented and signed, final customer approval |
| Beta Exit | Deliverable functional in target environment, acceptance criteria met |
| GA / Qualification Exit | Qualification tests passed, customer acceptance testing passed against spec |
| Production / Sustain Handoff | Metrics stable at target, ops model handed off |

These seven are the generic calendar. A profile may use finer-grained gates; the `silicon` profile has nine (one per phase), the `software` profile six. The rules are the same: every gate has written exit criteria, and nothing proceeds without them or a signed waiver.

### Issue-triggered gates
Unscheduled by definition. These come out of the Issue Management framework (see [Module 02](02_issue_management.md)) when a Sev 1 forces a re-review before proceeding.

**Rule of thumb:** Planned gates are on the calendar. Issue-triggered gates are unplanned by definition. Mixing them in status reporting is how executives lose the ability to distinguish "on plan" from "in crisis."

---

## 1.5 Scope note — compliance & export control

This playbook intentionally does not include a compliance/legal-review gate. Programs involving export-controlled technology (ITAR, EAR), regulated data (HIPAA, PCI, GDPR), or safety-critical systems need an additional gate — typically a Legal/Compliance sign-off inserted at Award/Contract and again at Release. If your program has any of these constraints, add a "Compliance Review" row to the RACI (Legal as a new party, R at contract and release, C elsewhere) and a corresponding exit criterion on the Kickoff and Release Readiness gates. Left out of v1 deliberately — bolt it on rather than treating its absence as an oversight.

---

## 1.6 Worked example — ASIC 9-phase flow with parallel SW/FW track

The 8-phase generic lifecycle in §1.2 is deliberately coarse — it's meant to fit any program. In practice, the two phases with the most execution risk (Design/Build and Integration/Hardening) are usually run as several distinct phases, and a real Si program tracks hardware and software/firmware as two parallel tracks, not one sequential line. This worked example unpacks §1.2 one level further, using the same ASIC domain as the rest of this playbook, and ties each phase to its Module 04 artifacts.

| # | Phase | Maps to §1.2 | Gate / milestone | HW deliverable | SW/FW deliverable | Key artifacts (Module 04 ref) |
|---|---|---|---|---|---|---|
| 1 | Concept | Pre-Sales/Feasibility | Concept Approval / Investment Decision | Feasibility study, make-vs-buy | Early SW architecture exploration | Feasibility Study, Make-vs-Buy Analysis, Rough NRE Estimate |
| 2 | Requirements | Award/Contract (early) | Requirements Freeze / PRD Sign-off | PRD/MRD, PPA targets | SW requirements spec, security reqs | PRD/MRD, SW Requirements Spec, RACI Matrix + Gate Calendar (§1.3–1.4) |
| 3 | Planning | Award/Contract (late) / Kickoff | PoR Baseline | Program schedule, RACI, budget | SW dev plan, toolchain/CI-CD setup | Program Schedule Baseline, Budget/NRE Baseline, Risk Register (§4.3) |
| 4 | Design | Design/Build | Design Freeze | RTL, floorplan, DFT | Early SW dev on virtual platform/FPGA | Phase Gate Exit Criteria Checklist, Design Review Findings Log (§4.2) |
| 5 | Verification & Sign-off | Integration/Hardening | Tape-Out Readiness Review | DRC/LVS/STA, power sign-off | Pre-silicon validation, co-simulation | Verification/Compliance Report, Coverage Closure Report, Rule-Check Report (§4.2) |
| 6 | Tape Out | Release | Tape-Out Sign-off | GDSII release to foundry | FW/driver code freeze | Release Readiness Sign-off Package, Waiver Documents, if any (§4.5) |
| 7 | Bring-Up | Bring-up/Beta | Power-On Success / First Boot | First silicon, ATE correlation | FW/BMC bring-up, HLOS porting | Gate Review Meeting Minutes, Bring-Up Test Plan, Bug Report/Fix Summary (§4.2–4.3) |
| 8 | Testing (Post-Silicon Validation) | Qualification/GA | Qualification Exit / Customer Acceptance | HTOL/ESD/JEDEC, yield analysis | Platform enablement, integration testing | Regression/Re-run Report, Qualification Test Report, Customer Sign-off (§4.4–4.5) |
| 9 | Production Release | Sustain/Production | GA / Mass Production Release | Mass production ramp, PPM tracking | Production FW release, OTA infrastructure | Revised Program Schedule, Sustain Handoff Doc, Lessons Learned (§4.6) |

### 1.6.1 Why HW and SW/FW timing overlaps, not sequences

Plotted on a timeline, the two tracks don't line up phase-for-phase — they overlap and bleed into each other, except at Tape Out, where both tracks hard-stop at once:

- **HW's one hard stop is Tape Out, and it's absolute.** GDSII is released to the foundry and the mask is cut — no further RTL or layout changes are physically possible without a re-spin. This is the literal point of no return; there is no bleed across this boundary on the HW track.
- **SW/FW hard-stops in lockstep, for the same reason.** Everywhere else, driver and firmware teams keep working against a frozen spec while hardware physically moves through fab — the SW/FW bar for one phase is still finishing while the next phase's work has already started. Tape Out (§4.5) is the one exception: the firmware/driver image freezes exactly when HW freezes, because that image is what goes onto first silicon at Bring-Up.
- **HW itself starts early on the RTL/architecture side.** Feasibility spikes and IP-reuse studies for Design commonly start during Planning, before the formal Design gate, to de-risk schedule — so the HW track shows a similar lead-in on Design and Verification. That lead-in bleed is real; the Tape Out stop is not.
- **The two tracks converge again at Bring-Up.** That's the first time firmware runs on real silicon, and it's the highest-risk week in the whole program — everything before it was pre-silicon (simulation, emulation, FPGA); everything after it is validating what actually happened on the part.

This is a planning pattern, not a governance exception — the gates in §1.4 still apply to both tracks. The overlap describes when engineering effort actually happens; it doesn't remove any exit criteria.

### 1.6.2 If first silicon needs a re-spin

Bring-Up isn't guaranteed to pass clean. If validation on first silicon (**Si vA**) finds a hardware-level defect that firmware can't work around, the fix goes through the same ECR/ECO path as any other issue (Module 02, Step 3 — Triage) — not a special process invented for this case:

- **Triage decides fix vs. waive vs. defer**, same as always. For a silicon bug, "fix" means a metal/mask-level ECO (cheap, fast, limited to specific layers) or a full re-tape-out — **Si vB**.
- **The re-spin runs its own compressed Tape Out → fab → Bring-Up cycle**, starting from the ECR/ECO decision point, in parallel with the rest of the program schedule — it doesn't pause everything else.
- **Phase 8 (Testing) keeps running on Si vA** for everything the defect doesn't block — yield characterization, non-blocking regression, anything not gated on the fix. Testing is not idle while Si vB is in fab.
- **Production Release qualifies off whichever revision passes** — Si vA if the issue was waived, Si vB if it required a re-spin.

This isn't a rare edge case in Si programs — it's common enough that the ECR/ECO artifacts in Module 04 exist largely because of it. Draw it as a dashed, clearly optional branch alongside Bring-Up and Testing, not folded into the primary nine-phase timeline — it is a deviation from the default path, not the default path itself.

### 1.6.3 The same flow in the tool

The nine phases, their gates, exit criteria and the reference RACI are the `silicon` profile ([profiles/silicon.json](../../profiles/silicon.json)). The fictional program "Meridian" in [examples/meridian](../../examples/meridian) runs it end to end, including a Sev 1 found at the integration gate. To use a different lifecycle, copy a profile and change the phases and gates (see [ADAPTING.md](../../docs/ADAPTING.md)); the lifecycles and metrics work unchanged.

## 1.7 Building a successful Plan of Record (POR)

*"POR" isn't a formal PMI term — it's the tech/hardware-industry convention for the baselined scope, schedule, and budget a program gets held to after kickoff. The Kickoff gate (§1.4) is where it's signed; this section is what actually goes into it and how to build one when you're not running just one program at a time.*

### 1.7.1 What "successful" means here

A POR is successful if it survives contact with reality without becoming fiction — meaning the org can still measure progress against it six months in, instead of quietly abandoning it the first time a date slips. That's a lower bar than "nothing changes" and a higher bar than "we wrote a schedule." Most POR failures trace back to one of two root causes: an assumption nobody wrote down, or a date that was set before anyone who'd do the work was asked.

### 1.7.2 The components

A POR that will actually hold has six parts. Skipping any one of them is where the other five start to erode.

| Component | What it answers | Owner |
|---|---|---|
| **Scope statement with exit criteria** | Not a feature list — what does "done" look like, checkable, not subjective | PM + delivery org |
| **Program Schedule (baseline)** | Integrated critical path across all workstreams — see Module 04 §4.3 | PM |
| **Budget / NRE Baseline** | Locked cost baseline (engineering, tooling, third-party) — all cost impacts measured against this | PM + finance |
| **RACI + gate calendar** | Who owns what, when the calendar events are — §1.3, §1.4 | PM |
| **Risk Register** | What *might* happen, logged before it does — Module 04 §4.3 | PM |
| **Assumptions & dependencies log** | Everything the schedule silently depends on that isn't yet a commitment | PM |

The assumptions log is the one most PORs skip, and it's the one that causes the most damage later — "we assumed the foundry slot would hold" isn't a risk anyone logged, it's an assumption nobody wrote down, and it surfaces as a surprise instead of a managed risk.

### 1.7.3 The process, not just the document

- **Build bottom-up, reconcile top-down.** Estimate from the people who'll do the work, not from the date leadership wants. Then reconcile against real constraints (target date, budget ceiling) — and when the two don't meet, that gap is itself the first risk on the register, not something to paper over with optimistic padding.
- **One integrated schedule, not five function-owned ones.** If HW, SW/FW, and test each keep their own schedule and only reconcile at status meetings, the critical path is whatever nobody's watching. Same principle as the two-track HW/SW-FW Gantt in §1.6 — the tracks have to live on one sheet to see where they actually collide.
- **Make the sign-off a ritual, not a formality.** Getting each RACI party (§1.3) to explicitly commit at kickoff — in front of the others, not in a side email — converts an implicit expectation into a social one. "You agreed to this at kickoff" is a different conversation three months later than "I need you to do this now."
- **Re-baseline deliberately, not silently.** A POR changes when scope changes — that's normal. What erodes trust is a schedule that quietly drifts without anyone declaring a new baseline. When scope or schedule changes materially, run it through the same ECR path as any other change (Module 02, Module 07 §7.3) and publish the new baseline explicitly, don't just let the old one go stale.

### 1.7.4 Running more than one POR at a time

Everything above assumes you're building one POR. The harder version is protecting several at once — and the failure mode is specific: you, the PM, become the shared resource every program's schedule silently assumes it has full access to, the same way two programs can silently assume the same test engineer (Module 10 §10.2.2). Nobody schedules a conflict on purpose; it just accumulates.

- **Put your own time on the calendar other programs have to check.** Module 10's shared-resource calendar discipline applies to you, not just to engineering pools — if Program B's planner doesn't know Program A's Design Freeze already has your full attention that week, they'll build a POR that assumes otherwise.
- **Stagger gate calendars where you control them.** Don't let two PORs' Kickoff or Design Freeze gates land in the same week if you can help it — that's a self-inflicted version of the exact contention Module 10 describes, except the contended resource is you.
- **Tier your programs instead of governing all of them identically.** Not every POR you touch needs the same weekly depth of engagement. Decide up front which 1–2 get hands-on governance and which run on a lighter, templated cadence — trying to run every program at maximum personal involvement is how all of them end up under-attended.
- **Reuse the template; don't rebuild the RACI/gate-calendar/artifact set from scratch each time.** The marginal cost of POR #3 should be much lower than POR #1. This is the actual value of having a playbook instead of reinventing governance per program.
- **Keep one rolled-up view across every active POR.** A single G/A/R status view across all your programs (feeding the same metrics as Module 08) means a crisis on the program you're not currently staring at doesn't surprise you later.

## 1.8 Governance in the tool

`pmf init` writes `raci.csv` and `gates.csv` from the profile, so the RACI and the gate calendar exist from day one. `pmf gate review`, `go`, `conditional` and `nogo` move a gate through its lifecycle and refuse a GO while an open issue of a blocking severity remains (see [LIFECYCLES.md](../../docs/LIFECYCLES.md)). Planned and issue-triggered gates are kept as separate types in `gates.csv`, so reports never mix them.

---

**Next:** [Module 02 — Issue Management](02_issue_management.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
