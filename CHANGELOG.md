# Changelog

## 0.1.0

First internal release.

- Ten framework modules, glossary, and a generated lifecycles document.
- `pmf` command line (stdlib only): init, check, issue / risk / change / gate lifecycle commands, health, brief, report, raid, dashboard, show, lifecycles.
- Two profiles: `silicon` (nine phases) and `software` (six phases).
- Four guarded lifecycles (issue, risk, change, gate) with an append-only events log.
- Five health metrics with a worst-of rollup, and a read-only HTML dashboard with no network requests.
- Templates as CSV registers and markdown documents. Office versions are not in 0.1.0.
- Ten prompts mapped to templates and lifecycle states.
- Five skills: setup-program, log-and-triage, brief-and-report, gate-review, health-check.
- Fictional worked example, Meridian, with a Sev 1 walkthrough rebuilt by `examples/run_demo.py`.
- Test suite (140 tests), repository checkers, and a privacy scan with a self-test.
