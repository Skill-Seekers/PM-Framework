# Module 06 — Communication Templates

*Ready-to-use snippets. Copy, adapt the bracketed fields, send. Each template names its audience and typical trigger up top.*

---

## 6.1 Sev 1 same-day executive note

**Audience:** Program sponsor, VP/GM, whoever needs to know now.
**Trigger:** Sev 1 issue confirmed — blocks release, forces re-spin, or is customer-visible.
**Format:** Email or Slack DM. Under 200 words. Follow with a call within 4 hours.

```
Subject: [Sev 1] [Program name] — [one-line description]

WHAT
[One sentence. What broke, which phase, which milestone is threatened.]

IMPACT
Schedule: [+X days] to [milestone name]
Cost: [$Y estimated exposure]
Customer: [milestone/commitment affected, or "internal only"]

STATUS
Discovered: [date/time]
War-room started: [date/time]
Owner: [name]
Next update: [date/time]

RECOMMENDATION
[One line. What you're asking leadership to endorse or decide.]

DECISION NEEDED BY
[Date/time]. I'll bring the full 3-option table to the call at [time].

— [Your name]
```

---

## 6.2 Weekly status report

**Audience:** Internal cross-functional stakeholders + vendors.
**Trigger:** Every week the program is active.
**Format:** Structured email or shared doc. Sent by end of day the same weekday each week.

```
Subject: [Program name] — Weekly Status — Week of [date]

HEADLINE
Overall status: [Green / Amber / Red] — [one-sentence explanation]

MILESTONES
Next gate: [name] — [date] — status [G/A/R]
Milestone this week: [what was hit or missed]

WORKSTREAM STATUS
[Workstream 1]: [G/A/R] — [one line]
[Workstream 2]: [G/A/R] — [one line]
[Workstream 3]: [G/A/R] — [one line]

OPEN ISSUES (Sev 1/2)
- [ID] [Title] — Owner [name] — Impact [+X days / $Y] — Next action [what, by when]

RAID CHANGES THIS WEEK
Added: [risks/deps]
Escalated (R → I): [items moving from risk to issue]
Closed: [items]

DECISIONS NEEDED
- [Decision 1] — needed by [date] — from [decider]

UPCOMING
Next week: [key activities]
Next gate: [date] — [readiness status]
```

---

## 6.3 Customer status email

**Audience:** External customer contact(s).
**Trigger:** Weekly or per contracted cadence; also immediately after any customer-visible Sev 1 resolution.
**Format:** Formal email. Slightly more polished than internal.

```
Subject: [Program name] — Status Update — [date]

Hi [Customer contact],

Quick status update on [program name].

PROGRESS THIS PERIOD
- [Completed milestone / deliverable]
- [Completed milestone / deliverable]

UPCOMING
- [Next milestone] — target [date]
- [Gate/review] — [date] — action needed from your side: [what]

ITEMS FOR YOUR ATTENTION
- [Decision needed / sign-off needed / risk to flag]

We're on track for [next major milestone] on [date]. [If not on track: one sentence on what's changing and why.]

Please let me know if any of this needs a call — happy to walk through it.

Thanks,
[Your name]
```

---

## 6.4 Gate go/no-go announcement

**Audience:** Everyone with a stake in the gate — internal, customer, vendors.
**Trigger:** After the gate review meeting; captures the decision formally.
**Format:** Email or program tracker post. Timestamped.

```
Subject: [Program name] — [Gate name] — [GO / NO-GO / CONDITIONAL GO]

DECISION: [GO / NO-GO / CONDITIONAL GO]
Date: [date]
Attendees: [names/roles]

EXIT CRITERIA STATUS
[Criterion 1]: [Met / Not met / Waived]
[Criterion 2]: [Met / Not met / Waived]
[Criterion 3]: [Met / Not met / Waived]

WAIVERS ACCEPTED (if any)
- [Waiver 1] — signed by [name/role] — rationale [reference]

CONDITIONS (if conditional go)
- [Condition 1] — owner [name] — due [date]

NEXT PHASE START: [date]
NEXT GATE: [gate name] — [date]

Decision record filed: [link/location]
```

---

## 6.5 Retrospective one-pager

**Audience:** Program team + leadership.
**Trigger:** After any Sev 1 closure. Also at program close.
**Format:** One page. Short and factual. Not a blame doc.

```
[Program name] — Retrospective: [Event / Sev 1 ID]
Date: [date]
Author: [PM]

WHAT HAPPENED
[2–3 sentences. Timeline, not narrative. When it was detected, when it was closed, what changed in between.]

ROOT CAUSE
[1–2 sentences. Technical + process cause. Both.]

WHAT WORKED
- [Something the process caught early]
- [Something the team did well]

WHAT DIDN'T
- [Gap in detection / triage / escalation]
- [Where the framework broke down]

CHANGES GOING FORWARD
1. [Concrete change to gate criteria / cadence / template]
2. [Concrete change to RACI or ownership]
3. [Concrete change to metrics or thresholds]

REFERENCED DECISIONS
- [Decision record 1]
- [Decision record 2]

Filed: [program archive location]
```

---

## 6.6 Kickoff RACI announcement

**Audience:** All parties at kickoff.
**Trigger:** Program kickoff.
**Format:** Email with attached RACI + gate calendar.

```
Subject: [Program name] — Kickoff Package — RACI + Gate Calendar

Team,

Attached:
1. RACI (all phases, all parties)
2. Gate calendar (all planned gates through [end phase])
3. Communication cadence (daily/weekly/monthly/quarterly cadence + audiences)

Please review by [date] and flag any ownership question you disagree with. Once we start Phase [X], the RACI is our reference — if there's a gap or a mismatch, we fix it now, not after the first missed gate.

Kickoff meeting: [date/time/link]

Thanks,
[Your name]
```

---

## 6.7 Rules of thumb

- **Never send a Sev 1 update as a reply-all to a status email.** Break it out into its own thread with `[Sev 1]` in the subject.
- **The first line of any status update is the headline.** If someone reads only that line, they should still know if the program is Green, Amber, or Red.
- **Bracketed fields are placeholders.** Delete them before sending. A weekly status with `[+X days]` still in it destroys credibility for a month.
- **Attach the decision record.** If a template references a decision, include the link. Otherwise the record fades from memory.

---

**Previous:** [Module 05 — Communication Cadence](05_communication_cadence.md)  
**Next:** [Module 07 — Budget & Scope Control](07_budget_and_scope_control.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
