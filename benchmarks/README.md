# Benchmark Fixtures

`cases.json` contains small, deterministic benchmark prompts. The benchmark runner exports prompt plans and scores supplied response JSONL files. It does not call Pollinations or any other API.

Response JSONL format (one object per line):

```json
{"case_id":"accuracy-001","model":"MODEL_ID","response":"42","prompt_tokens":12,"completion_tokens":1,"total_tokens":13}
```

Use `python benchmark.py plan --model MODEL_ID` to export a prompt plan. After model responses have been obtained through a separately authorized process, save them in the response format above and run `python benchmark.py score responses.jsonl --output report.json`.

Coding cases include a manual-review recommendation. Automated fragment matching is only a screening check, not proof that code is correct or secure.
