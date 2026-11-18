# Module 09 — AI-Augmented Workflow

*Every artifact in this framework has a defined template and a defined trigger. That is exactly what makes it automatable — an AI assistant needs structure to draft into, and every module here already provides it.*

---

## 9.1 The principle

"I used an AI tool to write an email once" is not a workflow. A workflow exists when every artifact has a fixed template and a fixed trigger, so raw input can be turned into a formatted draft the same way every time, not only when someone remembers to try.

The pattern is always three steps:

```
Raw input  →  AI drafts into the template  →  PM reviews, edits, sends
(notes,        (fills the exact fields          (judgment stays
 transcript,    Modules 04 and 06 define)        human — always)
 log output)
```

The AI never sends anything and never makes the triage decision. It removes the blank page, not the judgment. This is a rule of the framework, not a preference: nothing in the CLI or the plugin skills approves, waives, defers or closes on its own, and every skill stops for the PM's approval before it writes.

---

## 9.2 What to automate, by stage

| Stage | Manual today | AI-augmented |
|---|---|---|
| **1. Gate & Detect** | Read review notes and tool logs, hand-build the Open Items List | Give the transcript or raw output; the AI drafts the Open Items List in register format ([prompt 1](../../prompts/01_open_items_list.md)) |
| **2. Log & Classify** | Fill register fields, judge severity from memory of the matrix | Paste the raw description; the AI proposes id, phase, owner and severity against the profile's severity table ([prompt 2](../../prompts/02_issue_register_entry.md)); the PM approves or overrides |
| **3. Triage** | Build the 3-option table from scratch each time | The AI drafts options A, B and C from the issue and prior decision records ([prompt 3](../../prompts/03_three_option_triage.md)) |
| **4. Resolve** | Write the ECR, waiver and sign-off request by hand | Once the decision record is filled, the AI drafts the ECR or waiver and the sign-off request ([prompt 4](../../prompts/04_ecr_waiver.md)) |
| **5. Close & Brief** | Write the brief, weekly status and customer email separately | One register row plus the decision record produce all three drafts in their Module 06 formats ([prompts 5 to 8](../../prompts/)) |
| **Gates** | Write minutes and the go/no-go note after the meeting | Meeting notes become minutes and the announcement ([prompts 9 and 10](../../prompts/)) |

Two things in this table are deterministic and do not need an AI at all: `pmf brief <id>` and `pmf report weekly` build first drafts straight from the registers. Use the prompts when the input is messy text (notes, transcripts); use the CLI drafts when the data is already in the registers. Either way the PM edits before anything is sent.

---

## 9.3 Habits that make it work

1. **Log the raw input, not just the conclusion.** If an issue is triaged out loud and only the decision is written down, the AI has nothing to draft from next time. Capture the discussion, even roughly.
2. **Correct the draft, don't just accept it.** Each edit is a signal about the PM's judgment and voice. Over time drafts need less editing — not because the AI got smarter, but because the PM's own patterns became easier to anticipate.
3. **Keep the data in the registers.** A status line typed only into an email cannot feed the next draft or the metrics.
4. **Redact before pasting.** Remove customer secrets and personal data from anything given to an AI tool; the registers are meant to be free of them (see [LIMITS.md](../../docs/LIMITS.md)).

---

## 9.4 Honest limits

- AI drafts are only as good as the raw input. Poor notes give a poor draft; this does not replace running a good meeting.
- Never let a draft go out unreviewed, especially anything customer-facing or a Sev 1 executive note. The review step is not optional and not a formality.
- Severity and triage are judgment calls that depend on context an AI does not have: politics, relationship history, what leadership will tolerate. Treat the AI's severity and option suggestions as a first draft to challenge.
- The prompts and skills have not been validated against every model or tool. Check the output against the template every time.

---

## 9.5 Appendix — example tooling

The prompts in [prompts/](../../prompts/) are plain text and work in any chat assistant. The plugin in [skills/](../../skills/) packages five of them for Cowork and Claude Code. Beyond that, patterns teams commonly add (none are shipped or required):

- **Meeting transcripts to artifacts.** A note-taking tool's transcript for a gate review or triage meeting goes straight into prompt 9 or prompt 3.
- **Scheduled drafts.** A recurring task that runs `pmf report weekly` on Friday morning so the draft is waiting for review.
- **Tracker exports.** If your issues live in a tracker, export them to the `issues.csv` schema ([DATA_SCHEMAS.md](../../docs/DATA_SCHEMAS.md)); this repository makes no network calls and has no tracker connectors.

---

**Previous:** [Module 08 — Program Metrics & Health](08_program_metrics_and_health.md)  
**Next:** [Module 10 — Cross-Program Coordination: Capacity & Consensus](10_cross_program_coordination.md)  
[README](../../README.md) · [Glossary](../GLOSSARY.md) · [Lifecycles](../../docs/LIFECYCLES.md)
