#!/usr/bin/env python3
"""Evidence-based, offline comparison of model test history and benchmark reports."""
from __future__ import annotations
import argparse
import json
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "model_tests.sqlite3"


def read_history(db_path=DEFAULT_DB):
    path = Path(db_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Registry database not found: {path}")
    uri = path.as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT requested_model, actual_model, provider, key_policy, outcome, "
            "prompt_tokens, completion_tokens, total_tokens, latency_ms, error_code "
            "FROM model_tests ORDER BY requested_model, tested_at"
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def aggregate_history(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["requested_model"]].append(row)
    output = []
    for model, attempts in grouped.items():
        paid_blocked = sum(r.get("error_code") == "paid_pollen_required" for r in attempts)
        passes = sum(r["outcome"] == "pass" for r in attempts)
        quality_fails = sum(r["outcome"] == "quality_fail" for r in attempts)
        errors = sum(r["outcome"] == "error" for r in attempts)
        inconclusive = sum(r["outcome"] == "inconclusive" for r in attempts)
        evaluated = passes + quality_fails
        latencies = [r["latency_ms"] for r in attempts if r.get("latency_ms") is not None]
        tokens = [r["total_tokens"] for r in attempts if r.get("total_tokens") is not None]
        actual = sorted({r["actual_model"] for r in attempts if r.get("actual_model")})
        providers = sorted({r["provider"] for r in attempts if r.get("provider")})
        if paid_blocked and paid_blocked == len(attempts):
            eligibility = "PAID POLLEN REQUIRED"
        elif all(r.get("key_policy") == "quest_only" for r in attempts) and passes:
            eligibility = "QUEST TEST PASS RECORDED"
        else:
            eligibility = "NOT ESTABLISHED"
        output.append({
            "model": model, "actual_models": actual, "providers": providers,
            "attempts": len(attempts), "passes": passes,
            "quality_fails": quality_fails, "errors": errors,
            "inconclusive": inconclusive, "paid_blocked": paid_blocked,
            "evaluated": evaluated,
            "pass_rate": round(100 * passes / evaluated, 1) if evaluated else None,
            "attempt_pass_rate": round(100 * passes / len(attempts), 1) if attempts else 0.0,
            "avg_latency_ms": round(sum(latencies) / len(latencies), 1) if latencies else None,
            "avg_total_tokens": round(sum(tokens) / len(tokens), 1) if tokens else None,
            "latency_samples": len(latencies), "token_samples": len(tokens),
            "eligibility": eligibility,
            "evidence": "VERY LIMITED" if len(attempts) < 5 else "EARLY EVIDENCE" if len(attempts) < 20 else "MORE DATA",
        })
    return sorted(output, key=lambda r: (
        r["eligibility"] == "PAID POLLEN REQUIRED",
        -(r["pass_rate"] if r["pass_rate"] is not None else -1),
        -r["attempts"], r["model"]
    ))


def render_history(items):
    lines = [
        "MODEL COMPARISON CENTER",
        "=" * 88,
        "Source: local registry history | Mode: read-only | No model/API calls",
        "",
        "This is an evidence summary, not a definitive leaderboard.",
        "Pass rate uses only scored outcomes (PASS + QUALITY_FAIL).",
        "Attempt pass rate includes errors and inconclusive attempts.",
        "",
    ]
    if not items:
        return "\n".join(lines + ["No model test records found."])
    for index, item in enumerate(items, 1):
        pass_rate = "N/A" if item["pass_rate"] is None else f'{item["pass_rate"]:.1f}%'
        latency = "not recorded" if item["avg_latency_ms"] is None else f'{item["avg_latency_ms"]} ms'
        tokens = "not recorded" if item["avg_total_tokens"] is None else str(item["avg_total_tokens"])
        lines.extend([
            f'{index}. {item["model"]}',
            f'   Status             : {item["eligibility"]}',
            f'   Actual routed model: {", ".join(item["actual_models"]) or "not recorded"}',
            f'   Provider           : {", ".join(item["providers"]) or "not recorded"}',
            f'   Attempts           : {item["attempts"]}  | Pass {item["passes"]} | Quality fail {item["quality_fails"]} | Error {item["errors"]} | Inconclusive {item["inconclusive"]}',
            f'   Scored pass rate   : {pass_rate} ({item["passes"]}/{item["evaluated"]} scored)',
            f'   Pass / all attempts: {item["attempt_pass_rate"]:.1f}%',
            f'   Average latency    : {latency} ({item["latency_samples"]} samples)',
            f'   Average total tokens: {tokens} ({item["token_samples"]} samples)',
            f'   Evidence level     : {item["evidence"]}',
            "-" * 88,
        ])
    lines += [
        "",
        "READ THIS BEFORE PICKING A WINNER",
        "- A single passing smoke test is not proof of consistent quality.",
        "- Missing latency/token data is shown as missing, never treated as zero.",
        "- Different providers, routes, prompts, and test conditions may affect results.",
        "- Paid-Pollen-required models are identified and are not Quest-eligible choices.",
    ]
    return "\n".join(lines)


def read_benchmark_report(path):
    report = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if report.get("mode") != "offline_scoring_no_api_calls":
        raise ValueError("This does not look like a supported offline benchmark report.")
    if not isinstance(report.get("summaries"), list):
        raise ValueError("Benchmark report is missing summaries.")
    return report


def render_benchmark(report):
    lines = [
        "BENCHMARK COMPARISON",
        "=" * 88,
        "Source: saved offline benchmark report | No model/API calls",
        f'Response records: {report.get("response_records", 0)}',
        "",
    ]
    if not report["summaries"]:
        lines.append("No scored model responses in this report.")
    for summary in sorted(report["summaries"], key=lambda x: (-x.get("accuracy_percent", 0), x["model"])):
        lines.extend([
            f'MODEL: {summary["model"]}',
            f'Overall: {summary["passed"]}/{summary["tested"]} passed ({summary["accuracy_percent"]}%)',
            f'Manual reviews recommended: {summary.get("manual_reviews", 0)}',
        ])
        for category, counts in sorted(summary.get("categories", {}).items()):
            passed, total = counts["passed"], counts["total"]
            percent = 100 * passed / total if total else 0
            lines.append(f'  {category.replace("_", " ").title():25} {passed}/{total} ({percent:.1f}%)')
        lines.append("-" * 88)
    lines += [
        "Note: category comparisons are meaningful only when models were tested on the same cases.",
        "Coding checks may require manual review and do not establish code security.",
    ]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline model comparison center; no API calls")
    sub = parser.add_subparsers(dest="action", required=True)
    history = sub.add_parser("history", help="Compare models using local registry history")
    history.add_argument("--db", default=str(DEFAULT_DB))
    history.add_argument("--format", choices=("text", "json"), default="text")
    bench = sub.add_parser("benchmark", help="Compare models from a saved benchmark report JSON")
    bench.add_argument("report")
    bench.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    if args.action == "history":
        items = aggregate_history(read_history(args.db))
        if args.format == "json":
            print(json.dumps({"mode": "offline_registry_comparison", "models": items}, indent=2))
        else:
            print(render_history(items))
    else:
        report = read_benchmark_report(args.report)
        if args.format == "json":
            print(json.dumps(report, indent=2))
        else:
            print(render_benchmark(report))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
