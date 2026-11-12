# Changelog

## 0.8.0 - 2026-11-11
- Added offline catalog snapshot comparison with automatic latest-two and explicit timestamp selection.
- Detects model additions, removals, unchanged records, and changes to paid-only status, price strings, context window, tool support, and provider.
- Added readable text and JSON diff reports; catalog database is opened read-only.
- Added four catalog-diff tests. No network requests, inference, credential access, or Pollen spending.

## 0.7.0 - 2026-11-11
- Added an independent SQLite model-catalog snapshot store (catalog.py).
- Added validated JSONL import with duplicate protection and timestamped history.
- Tracks paid_only, provider-reported price strings, context window, tool support, source, and notes as catalog metadata.
- Explicitly refuses unknown fields such as quest_eligible; catalog metadata never establishes Quest-key eligibility.
- Catalog browsing is read-only and does not create a missing database.
- Added menu option 10 and six catalog tests.
- No network requests, model inference, credential access, or Pollen spending.

## 0.6.0 - 2026-11-11
- Added offline Model Comparison Center (compare.py) for registry history and saved benchmark reports.
- Historical comparison separates scored pass rate from pass/all-attempt rate and shows actual routed models, provider, sample size, latency, and token usage.
- Added explicit evidence labels and Quest-only observed-status / Paid-Pollen-required distinctions.
- Opens the registry database read-only; no API calls, credential access, or Pollen spending.
- Added menu option 9 and five comparison tests.
- Full project validation: Python compilation and 22 unit tests passed.

## 0.5.0 - 2026-11-11
- Added an interactive standard-library Termux menu (menu.py).
- Added registry/history, benchmark browsing, offline plan generation, live-test preview, guarded one-question live execution, offline scoring, JSONL export, and system validation.
- Model selection is sourced from the live runner's six-model Quest-tested allowlist.
- Live execution preserves the runner's interactive terminal and separate exact confirmation.
- Added safe overwrite prompts for generated plan/export files and optional score reports.
- Added four menu unit tests.
- No live inference requests or Pollen spending during menu development.

## 0.4.0 - 2026-11-11
- Changed registry summary/history, benchmark listing/scoring, and live displays to readable plain text by default.
- Retained machine-readable JSON options.
- Added four plain-text rendering tests.

## 0.3.0 - 2026-11-11
- Added one-question live runner with preview-only and interactive confirmation modes.
- Added Quest-key file/environment equality check; paid-enabled diagnostic key is never accessed.
- Added a six-model allowlist, 128-token output cap, and metadata-only SQLite persistence.

## 0.2.1 - 2026-11-11
- Expanded benchmark suite to 15 cases across five categories.
- Added automated tests and verified 15-case prompt-plan export.

## 0.2.0 - 2026-11-11
- Added offline benchmark planner, response scorer, JSONL prompt plans, and JSON reports.

## 0.1.0 - 2026-11-11
- Created standalone model test registry with metadata-only SQLite storage and JSONL import/export.
