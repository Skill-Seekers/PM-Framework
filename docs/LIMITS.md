# Limits

> **Read first.** The skills have not been run live. Everything below is the reason to test before relying on the framework.

What has been verified, what has not, and what the framework will not do. Read this before relying on the framework for a real program.

## Verified

| What | How | Result at 0.1.0 |
|---|---|---|
| Unit and integration tests | `python3 -m unittest discover -s tests` | 140 tests pass on the build machine (Python 3.10) |
| Python 3.8 syntax | `test_every_file_parses_as_python_3_8` | Passes |
| Standard library only | `test_standard_library_only` | Passes |
| Every guard has a refusal test | `test_every_guard_is_exercised_by_a_refusal_test` | Passes |
| Profiles and lifecycles agree | `tools/check_spec.py` | Consistent: 4 lifecycles, 29 guards, 2 profiles |
| Document and content consistency | `tools/check_content.py`, `tools/check_links.py` | Consistent; 134 internal links resolve |
| Worked example reproduces | `examples/run_demo.py --check` | Matches a fresh run |
| Privacy scanner works | `tools/privacy_scan.py selftest` | Passes |
| Privacy scan of the release tree | `tools/privacy_scan.py scan` against a private denylist | No failures, no warnings (146 files) |
| Generated files match generators | `gen_lifecycles.py --check`, `gen_templates.py --check` | Match |

The privacy scan result above depends on a denylist that is kept outside the repository and is not shipped. Anyone releasing the repository must run the scan with their own denylist.

## Not verified

- **The skills have not been run in a live assistant session.** The `SKILL.md` files are written against the command line and tested only as text (`test_skills.py` checks structure, not behavior). Before depending on them, run each skill once against the Meridian workspace and against a scratch workspace, and check every draft by eye.
- **Office versions (xlsx, docx) are not in this release.** Templates ship as CSV and markdown only. The plan's optional office generator has not been built. Until it is, SCOPE.md's mention of office versions is a plan, not a feature.
- **Dashboard rendering was checked in the test suite by structure, not by screenshot.** Open the Meridian dashboard in two browsers before showing it to anyone.
- **Windows path handling** has been exercised on Linux only. Run the test suite on Windows once before adopting the tool there.
- **Real program data** has never been run through the framework. The Meridian example is fictional and was built to exercise each state, so its numbers are not evidence of how the metrics behave on a real program.

## Design limits

- **One writer at a time.** Files live in git; there is no locking. Two people editing the same CSV will produce a merge conflict, which is intended to be resolved by a person.
- **Metrics are a status aid, not a forecast.** Each metric is a rule applied to the registers. They describe the current state and cannot predict a slip.
- **Thresholds are defaults.** They come from the playbook and are not universal. A program can change them in its profile, and the framework will not warn that a threshold is unusual for its industry.
- **Baseline schedule and budget are not estimated.** The tool needs them from you. Until they are entered, the metrics that depend on them show as not rated.
- **RAID has four categories.** Action items live in `next_action`, `mitigation` and decision records. There is no separate action register.
- **Dates must be ISO, money must be a plain number.** The tool refuses other formats rather than guessing.

## Out of scope

- No connection to Jira, Linear, Asana, Monday or any other tracker, and no network calls.
- No editing inside the dashboard. The CSV registers are the edit surface.
- No scheduling engine, critical-path calculation, earned-value, or resource levelling.
- No legal, compliance, export-control or tax advice. Module 01 marks where a compliance gate would go; it does not define one.
- No sending of email, notifications or calendar invitations.
- No step that decides severity, waives, approves or closes. An AI assistant may draft; a person decides.

## Data and privacy

- Registers must not hold customer secrets, credentials, or personal data. The tool does not detect them. This is the user's responsibility.
- Keep each program workspace in a private repository. The framework repository itself contains only fictional examples.
- The privacy scan finds what its denylist describes. A clean scan does not prove a file is free of sensitive content; read the manifest before every release.
