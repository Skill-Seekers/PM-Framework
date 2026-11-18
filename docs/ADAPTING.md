# Adapting PM-Framework

How to make the framework fit your program: a different lifecycle, your own thresholds, or your own phase names. Read [ASSUMPTIONS.md](ASSUMPTIONS.md) first; each assumption says what changes when it is false.

## What you can change without touching code

Everything that is a number, name or list lives in the profile (`profiles/*.json`, copied into your workspace as the program's profile). Start from the profile closest to your program and copy it.

| Section | What to change | Example |
|---|---|---|
| `parties` | The four RACI parties and what they mean for your program | Internal programs: "customer" becomes the sponsor or consuming team |
| `phases` | Phase names, order and descriptions | Rename the nine silicon phases, or use six |
| `gates` | Gate names, the phase each gate closes, its exit criteria | Add an export-control gate before release |
| `severity` | Severity labels and the definition of each level | Sev 1 means "blocks a release" in your organization |
| `escalation` | Days before an item is escalated, by severity | Escalate Sev 2 after 5 days instead of 7 |
| `risk` | Score bands and the probability and impact scales | A 3-by-3 matrix instead of 5-by-5 |
| `metrics` | The thresholds for green, amber and red on each of the five metrics | A stricter Schedule Variance band |
| `change_control` | Approval tiers by cost and schedule impact | Who approves a change over $100K |
| `cadence` | The meeting and report rhythm | Weekly status on Thursdays |

Every key is commented by a `_doc` entry in the profile. The profile is plain JSON, so you can read it directly. `python3 -m pmf lifecycles` prints the state tables the tool enforces.

## Steps

1. Copy the closest profile into your workspace and rename it.
2. Edit the sections in the table above. Keep the same keys and types; the loader refuses a profile with missing or misspelled keys.
3. Run `python3 -m pmf check` in the workspace. It reports any profile problem.
4. If you are maintaining a copy of the framework repository, add the profile to `profiles/` and run `python3 tools/check_spec.py`. It checks the shipped profiles and lifecycles against each other and against the playbook defaults.
5. Write one short note in `decisions/` recording each change and why. The profile is then reviewable like any other decision.

## What you cannot change without code

- The lifecycle states and their order (DETECTED to CLOSED for issues, and so on). These are in `pmf/data/lifecycles.json` and are the same for every profile.
- The guards. A guard can be relaxed only by changing its definition, which requires a matching refusal test (see [CONTRIBUTING.md](../CONTRIBUTING.md)).
- The five metric definitions. You can change their thresholds, not what they measure.
- The append-only events log.

If a change you need falls in this list, that is a fork, not an adaptation. Keep the fork's version in its own CHANGELOG entry.

## Writing a new profile from nothing

Avoid it unless the two shipped profiles are clearly wrong for your work. Begin by copying `software.json`, since it is the smaller of the two, and then add or remove phases. Run the checks after every edit; a profile that passes `check_spec.py` and `pmf check` on an empty workspace is structurally sound. Whether it is the right profile is a judgment only you can make.
