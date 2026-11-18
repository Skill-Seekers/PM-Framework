# Contributing

## Ground rules

- **No real data.** Never commit employer, customer, vendor, person or requisition names, personal contact details, salary or cost figures from a real program, or private file paths. Examples use the fictional Meridian program only.
- **The framework text is domain-agnostic.** Domain detail (silicon, software) belongs in a profile or in a worked example, not in module rules.
- **Standard library only** in `pmf/`, `tools/` and `tests/`. Python 3.8 syntax must parse.
- **The tool never decides.** Do not add a step that sets severity, waives, approves, sends or closes without a human.

## Before you open a change

1. Run the test suite: `python3 -m unittest discover -s tests`
2. Run the checkers: `python3 tools/check_spec.py`, `python3 tools/check_content.py`, `python3 tools/check_links.py`
3. If you changed Meridian or the CLI output: `python3 examples/run_demo.py` (it rewrites the example) and commit the result.
4. If you changed a profile or lifecycle: `python3 tools/gen_lifecycles.py` and `python3 tools/gen_templates.py`.
5. Run the privacy scan against your own denylist file kept outside the repository: `python3 tools/privacy_scan.py scan . --denylist <path-outside-repo>`

## Adding a guard or a state

A new guard must come with a test that expects a refusal from it. The test `test_every_guard_is_exercised_by_a_refusal_test` fails otherwise. Update `pmf/data/lifecycles.json` and the generated lifecycle document together.

## Changelog

Add an entry under the next version in `CHANGELOG.md`. Version numbers follow the profile and schema versions: a schema change is a minor version, a rule change that alters a metric result is called out explicitly.
