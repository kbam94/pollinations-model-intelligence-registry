# Directory Map

## Start here
- README.md — beginner-friendly overview, quick start, commands, safety notes, and FAQs.
- WHAT_IS.md — short explanation of the project's purpose and boundaries.
- FAQ.md — common questions about setup, Pollen usage, data, and model results.

## Main tools
- menu.py — interactive Termux menu for common registry and benchmark workflows.
- registry.py — local SQLite registry CLI; text output by default, optional JSON.
- benchmark.py — offline benchmark planner and scorer; readable reports, JSONL plans.
- live_runner.py — one-question Quest-only live runner with preview, typed confirmation, and readable output.
- compare.py — read-only historical registry and saved benchmark report comparison; no API calls.
- catalog.py — explicit JSONL import, read-only browsing, and offline comparison of dated catalog metadata snapshots.

## Benchmarks and tests
- benchmarks/cases.json — 15 deterministic benchmark cases.
- benchmarks/README.md — response format and benchmark instructions.
- tests/ — automated tests for benchmark scoring, catalog behavior, comparison, live-runner safeguards, menu behavior, and readable output.

## Local runtime data
- data/model_catalog.sqlite3 — separate catalog snapshot database, created only by explicit init/import.
- data/initial_results.jsonl — metadata-only historical test results, local data.
- data/model_tests.sqlite3 — local test-history database.

## Project maintenance
- PROJECT_STATUS.md — implementation and validation state.
- ROADMAP.md — planned phases.
- NEXT_SESSION.md — next-session checklist.
- CHANGELOG.md — implementation history.
- CONTRIBUTING.md — change and safety rules.
- .gitignore — excludes local runtime data, credentials, and generated files from Git.
