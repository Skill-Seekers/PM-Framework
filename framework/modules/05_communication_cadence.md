# Module 05 — Communication Cadence

*Five cadences, five audiences, five altitudes. Mixing them turns status into noise.*

---

## 5.1 The principle

A daily standup during active build is a different conversation than a quarterly exec review — same program, different altitude. If your weekly status report reads like a standup, executives will stop reading it. If your standup reads like an exec deck, engineers will stop attending.

Match altitude to audience. That is the entire discipline.

---

## 5.2 The five cadences

| Cadence | Audience | Content | Format | Length |
|---|---|---|---|---|
| **Daily** (active phases only) | Design/dev team + PM | Blockers, Sev 1 status, today's commitments | Standup | 15 min |
| **Weekly** | Internal cross-functional + vendors | Schedule status, open issues, RAID review, upcoming gates | Status report + call | 30–45 min |
| **Bi-weekly / Monthly** | Customer / external stakeholders | Milestone progress, risk items, upcoming gates, decisions needed | Formal review deck | 60 min |
| **Quarterly** | Executive / leadership / steering committee | Program health, budget vs. plan, strategic risks, roadmap adjustments | Exec review deck | 30–60 min |
| **Ad hoc** | Whoever is affected | Sev 1 escalation, gate go/no-go, unplanned decisions | 1-pager + call | Same day |

---

## 5.3 When to run each

- **Daily:** Only during active build, integration, or Sev 1 war-room. Turn them off when the program is coasting — a standing daily with nothing new burns team credit.
- **Weekly:** Every week the program is active. This is the one non-negotiable cadence.
- **Bi-weekly / Monthly customer review:** Set at kickoff. Skip once and it gets rescheduled every future time.
- **Quarterly exec:** Aligned to the org's business review cycle if possible. Otherwise anchored to a program milestone.
- **Ad hoc:** For Sev 1 only. Anything less doesn't warrant interrupting exec calendars.

---

## 5.4 What each cadence produces

| Cadence | Deliverable that lives after the meeting |
|---|---|
| Daily | (Nothing formal — updates in the issue tracker or standup channel) |
| Weekly | Weekly Status Report (see [Module 06](06_communication_templates.md)); RAID Log updated |
| Bi-weekly / Monthly | Customer Review Deck; minutes; action items with owners |
| Quarterly | Exec Review Deck; budget update; decisions logged |
| Ad hoc | 1-pager (see [issue_brief.md](../../templates/documents/issue_brief.md)); decision record |

---

## 5.5 The four communication anti-patterns

1. **Escalating through a weekly report.** If a Sev 1 shows up in the weekly report before it shows up as an ad hoc 1-pager, the exec heard about it too late.
2. **Standup that runs 45 minutes.** That's a working session in disguise. Cut it or split it.
3. **Customer review that reads the status report aloud.** The customer already got the report. The meeting is for discussion — decisions, risks, and the customer's questions.
4. **Quarterly deck that mixes program metrics with tactical detail.** Executives cannot triage 47 bullet points. Aggregate.

---

## 5.6 Cadence in the profile

The five cadences, their audiences and when they run are listed under `cadence` in the profile, so a program can change them without editing this module. The weekly report is drafted by `pmf report weekly`; the other deliverables use the [communication templates](06_communication_templates.md).

---

**Previous:** [Module 04 — Artifacts by Stage](04_artifacts_by_stage.md)  
**Next:** [Module 06 — Communication Templates](06_communication_templates.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
