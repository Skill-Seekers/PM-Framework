# Instructions

How to run a program with PM-Framework, from setup to the weekly routine. Every command below is run from the program folder unless it says otherwise. Add `--help` to any command for its full options.

## 1. Set up a program

```
python3 <plugin root>/pmf init my-program --program "My Program" --profile silicon --baseline-start 2026-01-05 --baseline-end 2026-12-18 --baseline-budget 2500000
```

This creates the workspace: `pmf.config.json`, the CSV registers, `events.csv`, and the `decisions/` and `briefs/` folders. Then, by hand:

1. Fill `raci.csv` with the four parties and the named owners (see `framework/modules/01_lifecycle_and_governance.md`).
2. Fill `gates.csv` with the planned gates and their dates (`pmf gate add`).
3. Enter the baseline budget in `budget.csv`.
4. Run `python3 <plugin root>/pmf check` until it reports no problems.

`<plugin root>` is the folder that holds `pmf/`. If you are inside the repository, use `python3 -m pmf` from its root with `PYTHONPATH` set to that root.

## 2. Log what happens

Every finding goes in through a lifecycle command, not by editing a CSV directly. Each command is shown with `--dry-run` first if you want to see the change before it is written.

| Situation | Commands |
|---|---|
| A new problem | `pmf issue add` → `pmf issue log` (needs owner, severity 1 to 4, phase) |
| Options drafted | `pmf issue triage` (needs exactly three options and a recommendation) |
| Decision taken | `pmf issue decide` (needs the decision record reference) |
| Fix verified | `pmf issue resolve`, then `pmf issue close` (Sev 1 and 2 need a brief) |
| A new risk | `pmf risk add`, `pmf risk assess`, `pmf risk mitigate` or `accept` |
| A risk becomes real | `pmf risk occur`, which links a new issue |
| A change request | `pmf change request`, `assess`, `approve` or `reject`, `implement`, `verify` |
| A gate review | `pmf gate review`, then `go`, `conditional` or `nogo` |

A refused command writes nothing and names the guard that refused it. The refusal is the tool doing its job: the fix is usually the missing field or the missing record.

## 3. Write the paperwork

- `pmf brief <issue-id>` drafts the management brief for a Sev 1 or Sev 2 issue into `briefs/`.
- `pmf report weekly` drafts the weekly status report.
- `pmf raid` writes the RAID snapshot; it always includes open Sev 1 and Sev 2 issues.

Drafts are text for you to read, edit and send. The tool does not send anything.

## 4. The weekly routine

1. `pmf check`: fix any register problem first.
2. `pmf health`: the five metrics and the worst-of rollup. Use `--fail-on red` in a script if you want a non-zero exit when the program is red.
3. `pmf dashboard`: write the read-only HTML dashboard and open it.
4. `pmf report weekly` and `pmf raid`: the drafts for the week.
5. Read the open Sev 1 and Sev 2 items and their next actions.

## 5. Gate day

Run `pmf check` and `pmf health`, then the gate review steps in `skills/gate-review/SKILL.md`. A gate passes only when every exit criterion is met or has a signed waiver, and no blocking issue is open. The tool refuses `go` otherwise.

## 6. Using the skills

The five skills in `skills/` are instructions an AI assistant follows to drive the same command line. Each skill states what it may draft and what it must leave to a person. Every draft should be read before it is used. See [LIMITS.md](LIMITS.md) for what has been verified with the skills.

## 7. Where things live

| Path | What it is | Edit by hand? |
|---|---|---|
| `issues.csv`, `risks.csv`, `changes.csv`, `gates.csv` | Registers | Only to fix a typo; use the commands otherwise |
| `events.csv` | Append-only log of every change | Never |
| `decisions/` | Triage and decision records | Yes, it is prose |
| `briefs/` | Management briefs | Yes, before sending |
| `reports/`, `out/` | Generated drafts and dashboards | No; regenerate them (safe to delete) |
| `pmf.config.json` | Program settings, including the report date | Yes |

Keep the workspace in a private repository. It holds your program's data.
