Meridian-1 - Retrospective: I-007 supply droop (Sev 1)
Date: 2026-06-05
Author: Avery Chen

WHAT HAPPENED
Detected 2026-05-18 in an emulation run. Triaged 2026-05-19, decided 2026-05-20, fix implemented and verified by 2026-06-03, closed 2026-06-04. G4 moved from 2026-06-12 to 2026-06-26.

ROOT CAUSE
The peak-current requirement was stated as "adequate margin" at G2, so nothing could fail against it until emulation. The risk (R-001) was known and monitored but had no test attached.

WHAT WORKED
- R-001 was already in the register, so the escalation to an issue was a link, not a surprise.
- The executive note went out the day it was detected.
- The gate guard stopped G4 from passing while the Sev 1 was open.

WHAT DIDN'T
- The requirement had no number and no test at G2.
- The risk was reviewed on schedule but its mitigation had no exit date.

CHANGES GOING FORWARD
1. G2 exit criteria for power requirements: a number, a unit, and a named test.
2. Every High risk gets a mitigation with a date, reviewed at each weekly RAID.
3. Add a peak-load emulation run to the design-phase checklist before G4 review.

REFERENCED DECISIONS
- DR-007 (triage and decision)
- DR-008 (change approval)

Filed: examples/meridian/workspace/communications
