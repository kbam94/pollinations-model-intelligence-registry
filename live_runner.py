#!/usr/bin/env python3
"""One-at-a-time Pollinations live test runner with readable text output."""
from __future__ import annotations
import argparse, json, os, stat, sys, time, uuid
import urllib.error, urllib.request
from datetime import datetime, timezone
from pathlib import Path
import benchmark, registry

API_URL="https://gen.pollinations.ai/v1/chat/completions"
KEY_FILE=Path.home()/".config"/"pollinations"/"api_key"
MAX_TOKENS=128
ALLOWED_MODELS={
    "stealth/glyph-cluster","openai/gpt-5-nano",
    "minimax/minimax-m3.1-flash","openai/gpt-6-luna",
    "community/Davizigjojo/blazerrouter",
    "community/tomdacatto/llama-3.1-8B",
}

def get_case(case_id):
    for case in benchmark.load_cases(benchmark.DEFAULT_CASES):
        if case["id"]==case_id: return case
    raise ValueError(f"Unknown benchmark case: {case_id}")

def render_preview(model,case):
    return "\n".join([
        "LIVE TEST PREVIEW","="*64,
        "Mode                 : PREVIEW ONLY (no API request)",
        f"Requested model      : {model}",
        f"Benchmark case       : {case['id']}",
        f"Category             : {case['category'].replace('_',' ').title()}",
        f"Endpoint             : {API_URL}",
        f"Maximum output tokens: {MAX_TOKENS}",
        f"Prompt length        : {len(case['prompt'])} characters",
        "Credential policy    : original Quest-only key file must match environment key",
        "Pollen warning       : live request may consume earned Quest Pollen",
        "-"*64,"QUESTION:",case["prompt"],"="*64
    ])

def preview(model,case,output_format="text"):
    data={"mode":"PREVIEW_ONLY","live_request":False,"model":model,
          "case_id":case["id"],"category":case["category"],"endpoint":API_URL,
          "max_output_tokens":MAX_TOKENS,"prompt_characters":len(case["prompt"]),
          "credential_policy":"environment key must exactly match original Quest-only key file",
          "potential_quest_pollen_usage":"A live request may consume earned Quest Pollen",
          "prompt":case["prompt"]}
    print(render_preview(model,case) if output_format=="text" else json.dumps(data,indent=2,ensure_ascii=False))

def load_quest_key():
    key=os.environ.get("POLLINATIONS_API_KEY","")
    if not key: raise RuntimeError("POLLINATIONS_API_KEY is not present in this shell.")
    if not KEY_FILE.is_file(): raise RuntimeError("Original Quest key file is missing; refusing to run.")
    mode=stat.S_IMODE(KEY_FILE.stat().st_mode)
    if mode & 0o077: raise RuntimeError("Quest key file permissions are too open; expected owner-only access.")
    stored=KEY_FILE.read_text(encoding="utf-8").strip()
    if not stored or key!=stored:
        raise RuntimeError("Environment key does not match the original Quest-only key file. Refusing to send.")
    return key

def save_record(record,db_path=registry.DEFAULT_DB):
    import tempfile
    fd,temp_path=tempfile.mkstemp(prefix="pollinations-live-",suffix=".jsonl")
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            f.write(json.dumps(record,ensure_ascii=False)+"\n")
        return registry.import_jsonl(temp_path,db_path)
    finally:
        try: os.unlink(temp_path)
        except FileNotFoundError: pass

def render_live_result(model,record,case_id,response_text,saved):
    usage=f"prompt {record['prompt_tokens'] or '—'} | completion {record['completion_tokens'] or '—'} | total {record['total_tokens'] or '—'}"
    return "\n".join([
        "LIVE TEST RESULT","="*64,
        f"Requested model : {model}",
        f"Actual model    : {record['actual_model'] or 'Not reported'}",
        f"Benchmark case : {case_id}",
        f"HTTP status    : {record['http_status'] if record['http_status'] is not None else 'Not available'}",
        f"Outcome        : {record['outcome'].upper()}",
        f"Evaluation     : {record['notes'] or '—'}",
        f"Token usage    : {usage}",
        f"Latency        : {record['latency_ms']} ms",
        f"Error code     : {record['error_code'] or 'None'}",
        f"Registry       : {saved.get('inserted_records',0)} record(s) saved",
        "Response saved : No (response is display-only)",
        "-"*64,"MODEL RESPONSE:",
        response_text[:1200] if response_text else "(No response text returned)",
        "="*64
    ])

def run_one(model,case,output_format="text"):
    if model not in ALLOWED_MODELS:
        raise RuntimeError("Model is not in the initial Quest-tested allowlist. No request sent.")
    if not sys.stdin.isatty():
        raise RuntimeError("Live testing requires an interactive terminal. No request sent.")
    key=load_quest_key()
    print("\nLIVE REQUEST SUMMARY")
    print(f"Model: {model}")
    print(f"Case: {case['id']} ({case['category']})")
    print(f"Endpoint: {API_URL}")
    print(f"Maximum output tokens: {MAX_TOKENS}")
    print("Credential: verified match to ~/.config/pollinations/api_key")
    print("WARNING: This request may consume earned Quest Pollen.")
    print("Exactly ONE benchmark question will be sent.")
    confirmation=input("Type RUN ONE QUEST-ONLY TEST to proceed: ").strip()
    if confirmation!="RUN ONE QUEST-ONLY TEST":
        print("Cancelled. No request sent."); return 0

    payload={"model":model,"messages":[{"role":"user","content":case["prompt"]}],
             "max_tokens":MAX_TOKENS,"temperature":0,"stream":False}
    request=urllib.request.Request(API_URL,data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    started=time.monotonic(); status=None; data={}; error_code=None; notes=None; response_text=""; outcome="error"
    try:
        with urllib.request.urlopen(request,timeout=45) as response:
            status=response.status; data=json.loads(response.read().decode("utf-8"))
        choices=data.get("choices") or []
        if choices:
            message=choices[0].get("message") or {}; content=message.get("content")
            if isinstance(content,str): response_text=content
            elif isinstance(content,list):
                response_text="".join(part.get("text","") for part in content if isinstance(part,dict))
        if response_text:
            passed,reason=benchmark.evaluate(case,response_text)
            outcome="pass" if passed else "quality_fail"; notes="benchmark:"+reason
        else:
            error_code="empty_or_unrecognized_response"; notes="HTTP success without usable message content"
    except urllib.error.HTTPError as exc:
        status=exc.code
        try:
            err_data=json.loads(exc.read().decode("utf-8")); err=err_data.get("error",{})
            error_code=err.get("code") or err.get("type") or "http_error"
            notes=err.get("message","HTTP error")
        except Exception:
            error_code="http_error"; notes="HTTP error response could not be parsed"
    except Exception as exc:
        error_code=type(exc).__name__; notes=str(exc)[:240]

    latency=round((time.monotonic()-started)*1000,2); usage=data.get("usage") or {}
    record={"test_id":"live-"+uuid.uuid4().hex,"tested_at":datetime.now(timezone.utc).isoformat(),
        "requested_model":model,"actual_model":data.get("model"),"provider":"Pollinations",
        "endpoint":"/v1/chat/completions","key_policy":"quest_only","http_status":status,
        "outcome":outcome,"prompt_tokens":usage.get("prompt_tokens"),
        "completion_tokens":usage.get("completion_tokens"),"total_tokens":usage.get("total_tokens"),
        "latency_ms":latency,"error_code":error_code,"notes":notes}
    saved=save_record(record)
    if output_format=="json":
        print(json.dumps({"requested_model":model,"actual_model":record["actual_model"],
            "case_id":case["id"],"http_status":status,"outcome":outcome,"evaluation":notes,
            "usage":usage,"latency_ms":latency,"registry":saved,
            "response":response_text[:1200] if response_text else None,"response_stored":False},
            indent=2,ensure_ascii=False))
    else:
        print(render_live_result(model,record,case["id"],response_text,saved))
    return 0 if outcome=="pass" else 1

def main():
    parser=argparse.ArgumentParser(description="Quest-only one-question Pollinations live tester")
    sub=parser.add_subparsers(dest="action",required=True)
    p=sub.add_parser("preview",help="Show a test without making a request")
    p.add_argument("--model",required=True,choices=sorted(ALLOWED_MODELS)); p.add_argument("--case",required=True)
    p.add_argument("--format",choices=("text","json"),default="text")
    r=sub.add_parser("run",help="Interactively approve exactly one live request")
    r.add_argument("--model",required=True,choices=sorted(ALLOWED_MODELS)); r.add_argument("--case",required=True)
    r.add_argument("--format",choices=("text","json"),default="text")
    args=parser.parse_args(); case=get_case(args.case)
    if args.action=="preview": preview(args.model,case,args.format); return 0
    return run_one(args.model,case,args.format)

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print("REFUSED/ERROR: "+str(exc),file=sys.stderr); raise SystemExit(2)
