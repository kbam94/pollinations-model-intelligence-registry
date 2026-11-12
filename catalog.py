#!/usr/bin/env python3
"""Offline model catalog snapshot store. Catalog metadata never proves Quest eligibility."""
from __future__ import annotations
import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "model_catalog.sqlite3"
SCHEMA = """
CREATE TABLE IF NOT EXISTS catalog_snapshots (
 snapshot_id TEXT PRIMARY KEY,
 model_id TEXT NOT NULL,
 snapshot_at TEXT NOT NULL,
 paid_only INTEGER,
 input_price TEXT,
 output_price TEXT,
 context_window INTEGER,
 supports_tools INTEGER,
 provider TEXT,
 source TEXT,
 notes TEXT,
 UNIQUE(model_id, snapshot_at)
);
CREATE INDEX IF NOT EXISTS idx_catalog_model_time
 ON catalog_snapshots(model_id, snapshot_at DESC);
"""

FIELDS = {
    "snapshot_id", "model_id", "snapshot_at", "paid_only",
    "input_price", "output_price", "context_window", "supports_tools",
    "provider", "source", "notes"
}

def connect(path=DEFAULT_DB):
    db = Path(path)
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def _optional_bool(value, field):
    if value is None:
        return None
    if type(value) is not bool:
        raise ValueError(f"{field} must be true, false, or null")
    return int(value)

def validate_record(item, line_no):
    if not isinstance(item, dict):
        raise ValueError(f"Line {line_no}: each JSONL record must be an object")
    extra = set(item) - FIELDS
    if extra:
        raise ValueError(f"Line {line_no}: unsupported fields: {sorted(extra)}")
    for key in ("model_id", "snapshot_at"):
        if not isinstance(item.get(key), str) or not item[key].strip():
            raise ValueError(f"Line {line_no}: {key} is required")
    record = {key: item.get(key) for key in FIELDS}
    if record["context_window"] is not None:
        value = record["context_window"]
        if type(value) is not int or value <= 0:
            raise ValueError(f"Line {line_no}: context_window must be a positive integer or null")
    for key in ("input_price", "output_price", "provider", "source", "notes"):
        value = record[key]
        if value is not None and not isinstance(value, str):
            raise ValueError(f"Line {line_no}: {key} must be a string or null")
    record["paid_only"] = _optional_bool(record["paid_only"], "paid_only")
    record["supports_tools"] = _optional_bool(record["supports_tools"], "supports_tools")
    if not record["snapshot_id"]:
        record["snapshot_id"] = f"{record['model_id']}@{record['snapshot_at']}"
    return record

def import_jsonl(source, db_path=DEFAULT_DB):
    records = []
    with open(source, encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Line {line_no}: invalid JSON: {exc.msg}") from exc
            records.append(validate_record(item, line_no))
    conn = connect(db_path)
    try:
        before = conn.total_changes
        conn.execute("BEGIN")
        for record in records:
            cols = list(record)
            conn.execute(
                "INSERT OR IGNORE INTO catalog_snapshots (" + ",".join(cols) +
                ") VALUES (" + ",".join("?" for _ in cols) + ")",
                [record[key] for key in cols]
            )
        conn.commit()
        return {"input_records": len(records), "inserted_records": conn.total_changes-before}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def list_snapshots(db_path=DEFAULT_DB, model=None, latest=False):
    db = Path(db_path)
    if not db.is_file():
        return []
    conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        where = "WHERE model_id LIKE ?" if model else ""
        args = ["%" + model + "%"] if model else []
        rows = conn.execute(
            "SELECT * FROM catalog_snapshots " + where +
            " ORDER BY model_id, snapshot_at DESC", args
        ).fetchall()
        result = [dict(row) for row in rows]
        if latest:
            seen = set()
            result = [row for row in result
                      if not (row["model_id"] in seen or seen.add(row["model_id"]))]
        return result
    finally:
        conn.close()

def catalog_label(row):
    if row["paid_only"] == 1:
        return "CATALOG MARKED PAID-ONLY"
    if row["paid_only"] == 0:
        return "CATALOG DOES NOT MARK PAID-ONLY"
    return "PAID-ONLY STATUS UNKNOWN"

def render(rows):
    if not rows:
        return "MODEL CATALOG\nNo catalog snapshots found. Import a local JSONL snapshot to begin."
    lines = ["POLLINATIONS MODEL CATALOG", "=" * 78]
    for index, row in enumerate(rows, 1):
        lines.extend([
            f"{index}. {row['model_id']}",
            f"   Snapshot       : {row['snapshot_at']}",
            f"   Catalog status : {catalog_label(row)}",
            f"   Provider       : {row['provider'] or 'not recorded'}",
            f"   Input price    : {row['input_price'] or 'not recorded'}",
            f"   Output price   : {row['output_price'] or 'not recorded'}",
            f"   Context window : {row['context_window'] if row['context_window'] is not None else 'not recorded'}",
            f"   Tool support   : {('yes' if row['supports_tools'] else 'no') if row['supports_tools'] is not None else 'not recorded'}",
            f"   Source         : {row['source'] or 'not recorded'}",
            "   Quest status   : NOT ESTABLISHED BY CATALOG METADATA",
            "-" * 78
        ])
    lines.extend([
        "NOTICE: Catalog pricing and paid_only metadata do not prove Quest-key eligibility.",
        "Only an explicitly authorized Quest-only test can establish observed compatibility."
    ])
    return "\n".join(lines)

CHANGE_FIELDS = ("paid_only", "input_price", "output_price", "context_window", "supports_tools", "provider")


def compare_snapshots(db_path=DEFAULT_DB, from_snapshot=None, to_snapshot=None):
    """Compare two catalog timestamps using local data only."""
    db = Path(db_path)
    if not db.is_file():
        return {"from_snapshot": from_snapshot, "to_snapshot": to_snapshot,
                "added": [], "removed": [], "changed": [], "unchanged": [],
                "error": "Catalog database does not exist."}
    conn = sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        timestamps = [row[0] for row in conn.execute(
            "SELECT DISTINCT snapshot_at FROM catalog_snapshots ORDER BY snapshot_at DESC"
        ).fetchall()]
        if from_snapshot is None or to_snapshot is None:
            if len(timestamps) < 2:
                return {"from_snapshot": from_snapshot, "to_snapshot": to_snapshot,
                        "added": [], "removed": [], "changed": [], "unchanged": [],
                        "error": "At least two distinct catalog snapshots are required."}
            to_snapshot = to_snapshot or timestamps[0]
            from_snapshot = from_snapshot or next((stamp for stamp in timestamps if stamp != to_snapshot), None)
        if from_snapshot == to_snapshot:
            raise ValueError("The comparison snapshots must be different.")
        def load(stamp):
            rows = conn.execute(
                "SELECT * FROM catalog_snapshots WHERE snapshot_at = ? ORDER BY model_id", (stamp,)
            ).fetchall()
            return {row["model_id"]: dict(row) for row in rows}
        old = load(from_snapshot)
        new = load(to_snapshot)
        if not old or not new:
            return {"from_snapshot": from_snapshot, "to_snapshot": to_snapshot,
                    "added": [], "removed": [], "changed": [], "unchanged": [],
                    "error": "One or both selected snapshot timestamps were not found."}
        old_ids, new_ids = set(old), set(new)
        added = [new[key] for key in sorted(new_ids - old_ids)]
        removed = [old[key] for key in sorted(old_ids - new_ids)]
        changed, unchanged = [], []
        for model_id in sorted(old_ids & new_ids):
            differences = {
                field: {"before": old[model_id][field], "after": new[model_id][field]}
                for field in CHANGE_FIELDS if old[model_id][field] != new[model_id][field]
            }
            if differences:
                changed.append({"model_id": model_id, "fields": differences})
            else:
                unchanged.append(model_id)
        return {"from_snapshot": from_snapshot, "to_snapshot": to_snapshot,
                "added": added, "removed": removed, "changed": changed,
                "unchanged": unchanged, "error": None}
    finally:
        conn.close()


def render_diff(report):
    if report.get("error"):
        return "CATALOG CHANGE REPORT\n" + report["error"]
    lines = [
        "POLLINATIONS MODEL CATALOG CHANGE REPORT", "=" * 78,
        f"Previous snapshot : {report['from_snapshot']}",
        f"Current snapshot  : {report['to_snapshot']}",
        f"Added models      : {len(report['added'])}",
        f"Removed models    : {len(report['removed'])}",
        f"Changed models    : {len(report['changed'])}",
        f"Unchanged models  : {len(report['unchanged'])}", "-" * 78
    ]
    if report["added"]:
        lines.append("ADDED MODELS")
        lines.extend(f"  + {row['model_id']}" for row in report["added"])
    if report["removed"]:
        lines.append("REMOVED MODELS")
        lines.extend(f"  - {row['model_id']}" for row in report["removed"])
    if report["changed"]:
        lines.append("CHANGED MODEL METADATA")
        for item in report["changed"]:
            lines.append(f"  * {item['model_id']}")
            for field, values in item["fields"].items():
                lines.append(f"      {field}: {values['before']!r} -> {values['after']!r}")
    if not any((report["added"], report["removed"], report["changed"])):
        lines.append("No model additions, removals, or tracked metadata changes detected.")
    lines.extend(["-" * 78, "NOTE: This compares published catalog snapshots only.",
                  "It does not establish Quest-key eligibility or model performance."])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Offline Pollinations model catalog snapshots")
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("init")
    init.add_argument("--db", default=str(DEFAULT_DB))
    imp = sub.add_parser("import-jsonl")
    imp.add_argument("source")
    imp.add_argument("--db", default=str(DEFAULT_DB))
    ls = sub.add_parser("list")
    ls.add_argument("--db", default=str(DEFAULT_DB))
    ls.add_argument("--model")
    ls.add_argument("--all-snapshots", action="store_true")
    ls.add_argument("--format", choices=("text", "json"), default="text")
    diff = sub.add_parser("diff", help="Compare two locally stored catalog snapshots")
    diff.add_argument("--db", default=str(DEFAULT_DB))
    diff.add_argument("--from-snapshot")
    diff.add_argument("--to-snapshot")
    diff.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    if args.action == "init":
        conn = connect(args.db)
        conn.close()
        print(f"Catalog database initialized: {args.db}")
    elif args.action == "import-jsonl":
        result = import_jsonl(args.source, args.db)
        print(f"Catalog import: {result['inserted_records']} of {result['input_records']} records added.")
        print(f"Database: {args.db}")
    elif args.action == "diff":
        report = compare_snapshots(args.db, args.from_snapshot, args.to_snapshot)
        if args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(render_diff(report))
        if report.get("error"):
            return 1
    else:
        rows = list_snapshots(args.db, args.model, latest=not args.all_snapshots)
        if args.format == "json":
            print(json.dumps({"snapshots": rows}, indent=2, ensure_ascii=False))
        else:
            print(render(rows))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(2)
