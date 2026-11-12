# Pollinations Model Intelligence Registry

A standalone Termux utility for recording model tests, evaluating responses, and performing carefully gated one-question live tests.

## Human-readable output

Interactive reports now default to **plain text**. Use `--format json` when another program needs structured JSON.

Examples:

```sh
python registry.py summary
python registry.py summary --format json
python registry.py list --limit 10
python registry.py list --model gpt-5-nano --format json
python benchmark.py list-cases
python benchmark.py list-cases --format json
python live_runner.py preview --model openai/gpt-5-nano --case accuracy-001
python live_runner.py preview --model openai/gpt-5-nano --case accuracy-001 --format json
```

## Safety and scope

- Registry commands and benchmark scoring are offline and make no model API calls.
- Live testing is a separate command, one question per invocation, with an interactive typed confirmation.
- Live testing accepts only the original `~/.config/pollinations/api_key` when it exactly matches `POLLINATIONS_API_KEY` in the shell. The paid-enabled diagnostic key is never read or used.
- Live test prompts and response bodies are not stored in SQLite. Only metadata, evaluation outcome, reported token counts, and a short reason are recorded.
- Every live request may consume earned Quest Pollen. No model is assumed free merely from catalog pricing or metadata.
- HTTP 200 is not automatically a quality pass.

## Registry

```sh
cd ~/projects/active/pollinations/model-intelligence-registry
python registry.py summary
python registry.py list --limit 50
python registry.py import-jsonl data/initial_results.jsonl
python registry.py export-jsonl backup.jsonl
```

Add `--format json` to summary, list, init, or import-jsonl when machine-readable output is needed.

## Offline benchmarks

List cases:

```sh
python benchmark.py list-cases
```

Export prompts as JSONL without making a request:

```sh
python benchmark.py plan --model openai/gpt-5-nano > ~/tmp/gpt5nano-plan.jsonl
```

Score separately collected responses:

```sh
python benchmark.py score ~/tmp/gpt5nano-responses.jsonl
python benchmark.py score ~/tmp/gpt5nano-responses.jsonl --format json --output ~/tmp/gpt5nano-report.json
```

Scoring prints a readable report by default. If `--output` is supplied, the saved report remains JSON for portability and further processing.

There are 15 deterministic cases across accuracy, instruction following, JSON, reasoning, and coding. Coding checks recommend manual review and are not proof of correctness or security.

## Live runner: preview first

Preview one case. This does not make an API request or read credentials:

```sh
python live_runner.py preview --model openai/gpt-5-nano --case accuracy-001
```

Run one live question only when you deliberately choose to spend possible Quest Pollen:

```sh
python live_runner.py run --model openai/gpt-5-nano --case accuracy-001
```

The runner verifies that the shell key exactly matches the original Quest-only key file, requires an interactive terminal, displays the model/prompt/output cap and Pollen warning, then requires the exact phrase `RUN ONE QUEST-ONLY TEST`. Any other input cancels. The initial allowlist contains only models previously smoke-tested with the Quest-only key. The runner has no batch mode and a maximum output cap of 128 tokens.

Live preview and result displays default to plain text. Add `--format json` for structured output.

## Model Comparison Center

Compare historical registry outcomes without modifying the database or making API calls:

```sh
python compare.py history
python compare.py history --format json
```

Compare models from a saved offline benchmark report:

```sh
python compare.py benchmark ~/tmp/gpt5nano-report.json
```

The report separates scored pass rate from pass rate across all attempts, shows actual routed model IDs, provider, token/latency samples, and evidence level. Very small samples are explicitly labeled. Missing measurements are not treated as zero, and a paid-Pollen-required result is clearly identified. A passing smoke test is not a reliable leaderboard by itself.

## Model Catalog Intelligence

The catalog is a separate SQLite database (`data/model_catalog.sqlite3`) for dated metadata snapshots. It is deliberately separate from observed model-test outcomes.

Create a local JSONL snapshot file with one record per model. Example:

```json
{"model_id":"openai/gpt-5-nano","snapshot_at":"2026-11-11T12:00:00Z","paid_only":false,"input_price":"catalog value as published","output_price":"catalog value as published","context_window":128000,"supports_tools":true,"provider":"Pollinations","source":"Pollinations text model catalog","notes":"metadata snapshot only"}
```

Import and browse snapshots:

```sh
python catalog.py init
python catalog.py import-jsonl ~/tmp/pollinations-catalog.jsonl
python catalog.py list
python catalog.py list --all-snapshots
python catalog.py list --model gpt-5-nano --format json
```

Catalog browsing is read-only. Imports are explicit and duplicate-safe. Price fields are retained as published strings because units and billing semantics can vary. The catalog does not infer Quest eligibility: `paid_only=false`, a zero-looking price, or any catalog listing is not proof that a model accepts your Quest-only key. The importer rejects fields such as `quest_eligible` to prevent that distinction from being blurred.

Compare the two newest local snapshots:

```sh
python catalog.py diff
python catalog.py diff --format json
```

Choose exact snapshots when needed:

```sh
python catalog.py diff --from-snapshot '2026-11-10T12:00:00Z' --to-snapshot '2026-11-11T12:00:00Z'
```

The diff reports added/removed models and changes to published paid-only status, price strings, context window, tool support, and provider. It is entirely offline and does not establish Quest-key eligibility or model performance.

## Tests

```sh
python -m unittest discover -s tests -v
```

## Data handling

Default database: `data/model_tests.sqlite3`. Token counts are provider-reported and are not a Pollen balance ledger. Never commit credentials or raw prompt/response data.


## Interactive Termux menu

Start from the project directory:

    cd ~/projects/active/pollinations/model-intelligence-registry
    python menu.py

Menu actions:
1. View model registry and test history.
2. Browse the 15 benchmark questions.
3. Generate an offline JSONL benchmark plan. No model call.
4. Preview one live model test. No API call or credential read.
5. Run one live model test. This may consume earned Quest Pollen and requires the menu acknowledgement plus the live runner's separate exact confirmation.
6. Score a previously collected response JSONL file offline.
7. Export registry history to JSONL.
8. Run Python compilation and the complete unit-test suite.
9. Compare historical model results locally. This is read-only and makes no API calls.
10. Browse model catalog snapshots locally. No API calls.

The menu uses only Python's standard library and existing project modules. Model choices are read from the live runner's allowlist. Generated files default to timestamped paths under ~/tmp; existing files are never overwritten without an explicit YES confirmation.

Important: Options 1-4 and 6-10 are local/offline operations. Option 5 is the only menu action that sends a model request. No paid-enabled diagnostic key is accessed, and the menu does not include paid-only models.
