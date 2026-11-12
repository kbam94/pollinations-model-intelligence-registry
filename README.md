# Pollinations Model Intelligence Registry

**A simple, local toolkit for testing, comparing, and keeping track of AI models available through Pollinations.**

This project helps answer practical questions:

- Does a model respond successfully through the API?
- Does it follow instructions and produce useful answers?
- Which model actually handled a request?
- How do different models compare on the same test questions?
- What model details have changed between catalog snapshots?

It keeps test history, benchmark results, and catalog information separate so a model's listing or a successful API response is not mistaken for proof that it is accurate, capable, or free to use.

> **New here?** You do not need to understand every feature. Start with the Quick Start below, or run the interactive menu with python menu.py.

## What this project does

| Feature | In plain English |
| --- | --- |
| Model registry | Keeps a local history of model tests and their outcomes. |
| Benchmarks | Provides 15 repeatable questions covering accuracy, reasoning, instructions, JSON, and coding. |
| Live test runner | Lets you deliberately send one selected test question to one approved model. |
| Model comparison | Summarizes and compares results already collected. |
| Model catalog | Stores dated snapshots of published model information. |
| Catalog differences | Shows which models or published details changed between two snapshots. |
| Interactive menu | Puts the main tools behind a numbered menu for easier use. |

The project runs independently on your own computer. It does not require an agent, a hosted service, or integration with another project.

## Quick start

### 1. Requirements

- Python 3.9 or newer is recommended.
- Git, if you are cloning the repository.
- No third-party Python packages are required for the core tools. The project uses Python's standard library.

### 2. Download the project

Open a terminal and run:

```sh
git clone https://github.com/kbam94/pollinations-model-intelligence-registry.git
cd pollinations-model-intelligence-registry
```

### 3. Open the interactive menu

```sh
python menu.py
```

Choose an option by entering its number. The menu puts the main tools in one place and keeps live testing separate from offline work.

### 4. Or run a few commands directly

View a summary of saved test history:

```sh
python registry.py summary
```

List recent test records:

```sh
python registry.py list --limit 10
```

See the benchmark questions:

```sh
python benchmark.py list-cases
```

Compare previously recorded results:

```sh
python compare.py history
```

Browse locally imported model catalog information:

```sh
python catalog.py list
```

These commands work with local data. They do not send model prompts to an API.

## Understanding the results

- **Requested model:** the model ID the test asked the service to use.
- **Actual routed model:** the model ID reported as having handled the request. It can differ from the requested ID.
- **Compatibility:** whether the request worked at the API level.
- **Quality:** whether the answer passed the benchmark's checks. A successful HTTP response is not automatically a good answer.
- **Catalog metadata:** published information such as context size, tool support, pricing text, and provider. This is not a performance measurement.
- **Evidence level:** how much test data exists. A result based on one or two attempts is weak evidence, not a reliable ranking.

The benchmark currently contains 15 deterministic cases in five categories. It is a useful starting point, not a scientific or comprehensive evaluation. Coding checks are limited and may require manual review.

## How testing works

### Offline tests and reports

Most features are offline. You can inspect history, list benchmark cases, create a test plan, score responses collected elsewhere, compare saved results, browse catalog snapshots, and run the test suite without making model requests.

Create an offline benchmark plan:

```sh
python benchmark.py plan --model openai/gpt-5-nano > ~/tmp/model-plan.jsonl
```

Score responses that have already been collected:

```sh
python benchmark.py score ~/tmp/model-responses.jsonl
```

### Live model tests

Live tests are intentionally cautious because requests may consume earned **Quest Pollen**.

First preview a test. Previewing does not make an API request or read credentials:

```sh
python live_runner.py preview --model openai/gpt-5-nano --case accuracy-001
```

Only run a live test if you understand and accept the possible Pollen cost:

```sh
python live_runner.py run --model openai/gpt-5-nano --case accuracy-001
```

The live runner:
- Runs one question per invocation. There is no batch mode.
- Requires an interactive terminal and an exact typed confirmation.
- Uses only the original Quest-only key when it matches the configured shell environment key.
- Does not read or use the separate paid-enabled diagnostic key.
- Limits the output to a maximum of 128 tokens.
- Saves test metadata and reported usage, not raw prompts or response bodies.

The initial live-test allowlist contains only models previously smoke-tested with the Quest-only key. This local safeguard is not a guarantee that a future request will be accepted or cost no Pollen.

**If you are unsure, use preview mode and offline features only.**

## Model comparison

Compare saved test history:

```sh
python compare.py history
```

Compare models in a saved benchmark report:

```sh
python compare.py benchmark ~/tmp/model-benchmark-report.json
```

The comparison report can show pass rates, sample sizes, actual routed model IDs, provider information, latency, and reported token usage. It distinguishes scored results from all attempts and labels very small samples. Missing measurements are left missing rather than treated as zero.

Do not treat a small sample or a single successful smoke test as a definitive leaderboard.

## Model catalog snapshots

The catalog stores published model metadata in a database separate from test history. Importing a snapshot is an explicit local action; the project does not automatically discover models or fetch a catalog at startup.

Initialize the catalog database:

```sh
python catalog.py init
```

Import a JSONL snapshot file:

```sh
python catalog.py import-jsonl ~/tmp/pollinations-catalog.jsonl
```

Browse snapshots:

```sh
python catalog.py list
python catalog.py list --all-snapshots
```

Compare the two newest local snapshots:

```sh
python catalog.py diff
```

Catalog fields such as a zero-looking price or paid_only=false do **not** prove that a model can be used with a Quest-only key. The catalog intentionally does not infer Quest eligibility.

## Where your data is stored

By default, local databases are created under the project's data/ directory:

- data/model_tests.sqlite3 — test history.
- data/model_catalog.sqlite3 — catalog snapshots.

These are local runtime files, not part of the public source release. Keep your own backups if the recorded history matters to you. Do not publish API keys, raw private prompts, or response data.

## Run the tests

From the project directory:

```sh
python -m unittest discover -s tests -v
```

The tests check core behavior, validation, safe live-runner safeguards, readable output, and catalog comparison behavior. They do not prove that every model or remote API will work.

## Frequently asked questions

### Does this project run AI models on my device?
No. It records and evaluates model tests and can send a deliberately approved live request through the Pollinations service. It is not a local model runtime.

### Does opening the menu use Pollen?
No. Opening the menu and using its offline features do not make model requests. The live-test action is separate and may consume earned Quest Pollen.

### Does a model appearing in the catalog mean it is free?
No. Catalog metadata is informational and may be incomplete or change. It does not prove that a model accepts a particular key or has no usage cost.

### Does a successful request mean the model is intelligent or accurate?
No. It means the request succeeded. Answer quality is evaluated separately, and even benchmark scores are only evidence from the tested questions and sample size.

### Does it upload my database?
No automatic database upload is part of the project. The registry and catalog are local SQLite databases. You can explicitly export registry history to JSONL.

### Is it connected to an AI agent or another project?
No integration is required. The project is standalone. Its JSONL exports can be used by other tools if you choose, but that is optional.

### What should I read next?
- [WHAT_IS.md](WHAT_IS.md) — short project explanation.
- [FAQ.md](FAQ.md) — common questions.
- [PROJECT_STATUS.md](PROJECT_STATUS.md) — what is implemented today.
- [ROADMAP.md](ROADMAP.md) — planned work.
- [benchmarks/README.md](benchmarks/README.md) — benchmark details.
- [CONTRIBUTING.md](CONTRIBUTING.md) — contribution guidance.

## Project status

Current version: **0.8.0**

The registry, offline benchmark engine, guarded one-question live runner, interactive menu, comparison center, catalog snapshot store, and offline catalog difference reports are implemented.

Some roadmap items remain unfinished. See [ROADMAP.md](ROADMAP.md) for the current plan.

## License

See the repository's license file if one is present. If no license file is included, the source is publicly viewable but reuse and redistribution are not automatically granted.
