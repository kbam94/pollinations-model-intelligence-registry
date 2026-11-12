# Project Status

**Version:** 0.8.0
**Status:** Registry, offline benchmark engine, guarded live runner, interactive menu, readable text output, offline Model Comparison Center, catalog snapshot store, and offline catalog change detection implemented. Catalog import is explicit; catalog browsing and validation make no inference requests.

## Interactive Termux menu
- Start with: python menu.py
- Ten actions cover registry/history, benchmark browsing, offline plan creation, live preview, one guarded live test, offline scoring, JSONL export, system validation, offline model comparison, and catalog browsing.
- Option 9 runs the Model Comparison Center against local history without API calls.
- Option 10 browses local model-catalog snapshots without API calls.
- Uses Python standard library plus existing project modules; no installation required.
- Model choices come directly from live_runner.ALLOWED_MODELS.
- Generated plans and exports use timestamped paths under ~/tmp by default and ask before overwriting.
- Live testing retains two separate safeguards: menu acknowledgement and the live runner's exact per-request confirmation.
- Live requests may consume earned Quest Pollen; menu development and validation make no API calls.

## Registry
- SQLite test-history schema and JSONL metadata import with duplicate protection.
- Summary, filtered history, and JSONL export.
- Requested versus actual model tracking.
- Eleven historical test records covering nine requested model IDs.
- Human-readable summary and history by default; JSON remains available.

## Offline benchmark engine
- Fifteen deterministic cases across five categories.
- JSONL prompt-plan export and offline response evaluation.
- JSON report output; coding checks flag manual review.
- Human-readable case listing and score report by default.

## Guarded live runner
- One benchmark case per invocation; no batch mode.
- Preview makes no API request and does not read credentials.
- Live mode requires an interactive terminal and exact typed confirmation.
- Uses only POLLINATIONS_API_KEY when it exactly matches ~/.config/pollinations/api_key.
- Does not read the paid-enabled diagnostic key.
- Six previously Quest-smoke-tested models in the initial allowlist.
- Maximum output-token cap: 128.
- Stores metadata and provider-reported usage, not raw prompts or response bodies.

## Model Comparison Center
- `compare.py history` aggregates local test outcomes, actual routed model IDs, providers, latency, token usage, and observed Quest-key pass evidence.
- `compare.py benchmark REPORT.json` compares models from saved offline benchmark reports.
- Opens the SQLite registry in read-only mode; does not change history or make network requests.
- Separates scored pass rate from pass/all-attempt rate and labels small samples VERY LIMITED or EARLY EVIDENCE.
- Missing latency/token measurements remain explicitly missing.
- Paid-Pollen-required models are labeled and excluded from Quest-eligible status.

## Model Catalog Intelligence
- `catalog.py` stores dated metadata snapshots in a separate `data/model_catalog.sqlite3` database.
- Explicit JSONL import supports paid_only, price strings, context window, tool support, provider, source, and notes.
- Duplicate snapshots are ignored; validation rejects unknown fields and invalid boolean/numeric types.
- Catalog listing uses SQLite read-only mode and does not create a missing database.
- Catalog metadata never establishes Quest-only key eligibility; no automatic network discovery is performed.

## Catalog Change Detection (v0.8.0)
- `catalog.py diff` compares two locally stored catalog timestamps without network access.
- Detects added models, removed models, changed tracked metadata, and unchanged models.
- Tracks changes to published paid-only status, input/output price strings, context window, tool support, and provider.
- Defaults to comparing the two newest distinct snapshot timestamps; explicit `--from-snapshot` and `--to-snapshot` values are supported.
- Supports readable text and JSON reports; opens the catalog database read-only.
- Missing databases, insufficient snapshots, and unknown timestamps are reported without creating or modifying catalog data.
- Four dedicated tests cover additions/removals/changes, unchanged models, explicit selection, and safe empty-state behavior.

## Safety and limitations
- Live requests may consume earned Quest Pollen and require explicit per-request approval.
- Quest-only key matching is a local safeguard, not an external guarantee of model eligibility.
- The 15-case benchmark is an initial smoke suite, not a definitive ranking.
- Coding fragment checks are not execution or security tests.
- No automatic commits or agent integrations.
