# Glossary

*Every acronym and term used across PM-Framework. Alphabetical.*

| Term | Meaning |
|---|---|
| **Aging** | Days an issue has been open, from its detected date; the input to the Issue Aging metric (Module 08) |
| **ATE** | Automated Test Equipment — hardware used to test silicon post-fabrication |
| **ATPG** | Automatic Test Pattern Generation — generates the input patterns used with DFT scan chains to test a chip post-fabrication |
| **Blast Radius** | The full scope of downstream impact from an issue or change — schedule, cost, and dependent phases |
| **BMC** | Baseboard Management Controller — a platform-management subsystem/firmware handling power sequencing, sensor monitoring, and board-level control, independent of the main OS |
| **Burn Rate / Burn-Down** | Ratio or chart of actual spend against planned spend over time |
| **CAB / CCB** | Change Advisory Board or Change Control Board — the approval body for large or program-altering changes |
| **Decision record** | Markdown file `decisions/DR-NNN.md` holding the three options, the recommendation, the chosen option, who decided and whether it is signed (DATA_SCHEMAS.md) |
| **DFT** | Design for Test — hardware design techniques that make a chip testable after fabrication |
| **DRC** | Design Rule Check — automated verification that a physical chip layout obeys foundry manufacturing rules |
| **ECO** | Engineering Change Order — a post-release fix (metal/mask-level for ASICs; hotfix/patch for software) that avoids a full re-spin or rebuild |
| **ECR** | Engineering Change Request — formal request to change locked scope, spec, or design; the trigger for the change control flow |
| **Escape Rate** | Percentage of issues that should have been caught at an earlier gate but were found downstream instead |
| **Event log** | `events.csv`: the append-only record of every state change in the registers |
| **G/A/R** | Green / Amber / Red — the three-state status color used across all reporting cadences |
| **Gate** | A defined checkpoint in the program lifecycle with formal exit criteria; see Planned Gates vs. Issue-Triggered Gates (Module 01) |
| **GDSII** | The final physical layout file format released to a foundry at tape-out — generating it is the last hardware step before fabrication |
| **Guard** | A named check that must pass before a lifecycle transition is allowed (LIFECYCLES.md) |
| **HLOS** | High-Level Operating System — the main OS (e.g. Linux) running on a platform's primary application processor, as distinct from firmware/RTOS on a BMC or microcontroller |
| **HTOL** | High Temperature Operating Life — a semiconductor reliability qualification test |
| **IR Drop** | Voltage drop across a chip's power delivery network; a physical design closure metric |
| **ITAR** | International Traffic in Arms Regulations — US export control regime; relevant to defense-adjacent or certain semiconductor programs (see Module 01, Section 1.5) |
| **JEDEC** | Joint Electron Device Engineering Council — standards body; JEDEC qualification refers to standardized reliability testing |
| **Lifecycle** | The allowed states and transitions for an issue, risk, change request or gate, defined once in `pmf/data/lifecycles.json` |
| **LVS** | Layout Versus Schematic — verification that a physical chip layout matches its logical design intent |
| **Not rated** | A metric with too little data to color; shown grey with the reason, never counted as Green |
| **NRE** | Non-Recurring Engineering — one-time design/development cost, as distinct from per-unit production cost |
| **OTA** | Over-The-Air — remote firmware/software update delivery mechanism, used for sustaining production units post-release |
| **Overdue gate** | A planned gate that is not done and whose planned date is earlier than the report date; turns Schedule Variance Red |
| **POR** | Plan of Record — the baselined scope, schedule, and budget a program is held to after kickoff (Module 01 §1.7); a tech/hardware-industry convention |
| **PPA** | Power, Performance, Area — the three core hardware design targets a chip is specced and evaluated against |
| **PPM** | Parts Per Million — a defect rate measure used in production/yield tracking |
| **Profile** | The JSON file holding a program type's phases, gates, severity model and thresholds (profiles/) |
| **RACI** | Responsible, Accountable, Consulted, Informed — a role-clarity matrix mapping who does what by phase |
| **RAID** | Risks, Assumptions, Issues, Dependencies — an executive-facing program health log (see Module 03) |
| **Report date** | The date metrics are computed for; today unless set in `pmf.config.json` |
| **Resource Contention Rate** | Percentage of shared-resource requests that hit a scheduling conflict — a portfolio-level metric, separate from Module 08's five program-level metrics (see Module 10) |
| **Resource Request** | Written, specific ask for time from a shared resource pool (skill, window, criticality, alternative if declined) — the capacity equivalent of an ECR (see Module 10) |
| **RTL** | Register-Transfer Level — the abstraction level at which digital chip logic is designed before synthesis |
| **Sev (1–4)** | Severity classification for an issue; Sev 1 is the most critical (see Module 02, Step 2) |
| **SOW** | Statement of Work — the contractual document defining scope, deliverables, and terms with a customer or vendor |
| **STA** | Static Timing Analysis — verification that a chip design meets its timing (speed) requirements across process/voltage/temperature corners |
| **SV** | Schedule Variance — how far actual/forecast progress is from the baseline plan (see Module 08) |
| **Waiver** | A formal, signed acceptance of a known deviation from spec or exit criteria, in lieu of fixing it |
| **Workspace** | One folder per program holding its config, CSV registers, decisions, briefs and generated output |
| **Worst-of rollup** | Status rule: the overall color is the worst of the individual colors, never an average |

---

**Back to:** [README](../README.md)
