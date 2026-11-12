# Frequently Asked Questions

## Do I need to install Python packages?
No third-party packages are required for the core tools. Use Python 3.9 or newer.

## Will the project spend Pollen automatically?
No. Offline commands and menu startup do not send model requests. A live test is a separate action, requires exact typed confirmation, and may consume earned Quest Pollen.

## Is a model free because the catalog lists it?
No. Catalog information is a dated metadata snapshot, not a guarantee of access, price, or Quest-key eligibility.

## Does a successful API response prove good model quality?
No. API compatibility and answer quality are recorded separately. Benchmark results are limited by the questions and number of attempts.

## Does the tool store my prompts and answers?
The live runner stores metadata and reported usage, not raw prompts or response bodies. Avoid putting secrets or private information into test prompts.

## Does it need an AI agent?
No. It runs as an independent Python project. Other tools may optionally consume exported JSONL data.

## Where is my data?
The default SQLite databases are stored in the project's data/ directory. They are local runtime data and should be backed up separately if needed.

## How do I run the test suite?
Run python -m unittest discover -s tests -v from the project directory.
