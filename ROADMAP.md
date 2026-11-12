# Roadmap

## Phase 1: Local registry
- [x] SQLite schema and JSONL import.
- [x] Requested versus actual model tracking.
- [x] Compatibility and quality outcome separation.
- [x] Import, duplicate protection, summary, and export validation.

## Phase 2: Offline benchmark engine
- [x] Fifteen deterministic cases across five categories.
- [x] JSONL prompt-plan export.
- [x] Offline response scoring and JSON reports.
- [x] Unit tests for pass/fail behavior and malformed JSON.
- [ ] Expand to 30-50 balanced cases and repeated-run consistency scoring.

## Phase 3: Guarded live testing
- [x] Separate one-question live runner.
- [x] Preview mode with no API request.
- [x] Require original Quest-only key file to match shell environment key.
- [x] Interactive confirmation for each request; no batch mode.
- [x] Strict output-token cap and metadata-only persistence.
- [ ] Conduct first explicitly approved live test and validate actual API behavior.
- [ ] Add safe retry handling only if provider errors justify it.

## Phase 4: Interactive menu
- [x] Standard-library Termux menu.
- [x] Registry, benchmark, plan, preview, live, scoring, export, and validation actions.
- [x] Model selection sourced from the live runner allowlist.
- [x] Preserve live runner's independent exact confirmation.
- [x] Safe overwrite prompts for generated files.
- [x] Offline Model Comparison Center on menu option 9.

## Phase 5: Offline comparison center
- [x] Aggregate historical outcomes, actual routes, providers, latency, and token usage.
- [x] Distinguish scored pass rate from pass/all-attempt rate.
- [x] Label sample size and missing measurements; identify paid-Pollen-required models.
- [x] Compare saved offline benchmark reports.
- [x] Add menu option 9 and automated tests.

## Phase 6: Catalog enrichment
- [x] Store catalog metadata snapshots separately from observed test outcomes.
- [x] Track paid_only, price strings, context window, tool support, provider, source, and notes as catalog metadata, not proof of Quest eligibility.
- [x] Add validated, duplicate-safe local JSONL import and read-only browsing.
- [x] Reject unknown Quest-eligibility fields to prevent catalog data from being mistaken for verified compatibility.
- [x] Add menu option 10 and automated tests.

## Phase 7: Catalog change detection
- [x] Compare two local catalog snapshots without network access.
- [x] Detect added and removed model identifiers.
- [x] Detect changes to published pricing, paid-only status, context window, tool support, and provider.
- [x] Support automatic latest-two comparison and explicit timestamp selection.
- [x] Add text/JSON reports and tests for additions, removals, changes, and missing data.

## Phase 8: Optional agent integration
- [ ] Read-only JSON export contract.
- [ ] Optional adapter for external agents, disabled by default.

## Phase 9: Public catalog discovery (opt-in)
- [ ] Verify the current official Pollinations catalog endpoint and response schema.
- [ ] Add an explicitly triggered public metadata fetch, with no API key and no inference.
- [ ] Add response-size/time limits, provenance, and strict JSON validation.
- [ ] Never fetch automatically during menu startup, tests, or validation.
