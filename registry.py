#!/usr/bin/env python3
"""Local, metadata-only Pollinations model test registry."""
from __future__ import annotations
import argparse, json, sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_DB = ROOT / "data" / "model_tests.sqlite3"
SCHEMA = """
CREATE TABLE IF NOT EXISTS model_tests (
 test_id TEXT PRIMARY KEY, tested_at TEXT NOT NULL,
 requested_model TEXT NOT NULL, actual_model TEXT, provider TEXT,
 endpoint TEXT NOT NULL,
 key_policy TEXT NOT NULL CHECK(key_policy IN ('quest_only','unknown')),
 http_status INTEGER,
 outcome TEXT NOT NULL CHECK(outcome IN ('pass','quality_fail','error','inconclusive')),
 prompt_tokens INTEGER, completion_tokens INTEGER, total_tokens INTEGER,
 latency_ms REAL, error_code TEXT, notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_tests_model_time ON model_tests(requested_model,tested_at DESC);
"""

def connect(path=DEFAULT_DB):
    db=Path(path); db.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(str(db)); conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL'); conn.executescript(SCHEMA)
    return conn

def import_jsonl(path, db_path=DEFAULT_DB):
    rows=[]
    with open(path,encoding='utf-8') as f:
        for line_no,line in enumerate(f,1):
            if not line.strip(): continue
            item=json.loads(line)
            required=('test_id','tested_at','requested_model','endpoint','key_policy','outcome')
            missing=[k for k in required if not item.get(k)]
            if missing: raise ValueError(f'Line {line_no}: missing {", ".join(missing)}')
            rows.append(item)
    allowed={'test_id','tested_at','requested_model','actual_model','provider','endpoint','key_policy','http_status','outcome','prompt_tokens','completion_tokens','total_tokens','latency_ms','error_code','notes'}
    conn=connect(db_path)
    try:
        before=conn.total_changes
        for item in rows:
            extra=set(item)-allowed
            if extra: raise ValueError(f'Unsupported fields: {sorted(extra)}')
            cols=list(item)
            conn.execute('INSERT OR IGNORE INTO model_tests ('+','.join(cols)+') VALUES ('+','.join('?' for _ in cols)+')',[item[k] for k in cols])
        conn.commit()
        return {'status':'ok','input_records':len(rows),'inserted_records':conn.total_changes-before,'database':str(db_path)}
    finally: conn.close()

def list_tests(db_path=DEFAULT_DB, model=None, limit=100):
    conn=connect(db_path)
    try:
        if model:
            rows=conn.execute('SELECT * FROM model_tests WHERE requested_model LIKE ? ORDER BY tested_at DESC LIMIT ?',('%'+model+'%',max(1,min(limit,1000)))).fetchall()
        else:
            rows=conn.execute('SELECT * FROM model_tests ORDER BY tested_at DESC,test_id LIMIT ?', (max(1,min(limit,1000)),)).fetchall()
        return [dict(r) for r in rows]
    finally: conn.close()

def summary(db_path=DEFAULT_DB):
    conn=connect(db_path)
    try:
        rows=conn.execute("""SELECT requested_model,MAX(actual_model) actual_model,COUNT(*) attempts,
          SUM(outcome='pass') passes,SUM(outcome='quality_fail') quality_fails,
          SUM(outcome='error') errors,SUM(outcome='inconclusive') inconclusive,
          MAX(tested_at) last_test FROM model_tests GROUP BY requested_model ORDER BY requested_model""").fetchall()
        return [dict(r) for r in rows]
    finally: conn.close()

def display_value(value):
    return "—" if value is None or value == "" else str(value)

def render_summary(models):
    if not models: return "MODEL REGISTRY\nNo test records found yet."
    lines=["POLLINATIONS MODEL REGISTRY","="*76]
    for index,m in enumerate(models,1):
        lines += [
            f"{index}. {m['requested_model']}",
            f"   Actual routed model : {display_value(m['actual_model'])}",
            f"   Attempts            : {m['attempts']}",
            f"   Passed              : {m['passes'] or 0}",
            f"   Quality failures    : {m['quality_fails'] or 0}",
            f"   Errors              : {m['errors'] or 0}",
            f"   Inconclusive        : {m['inconclusive'] or 0}",
            f"   Last tested         : {display_value(m['last_test'])}",
            "-"*76
        ]
    return "\n".join(lines)

def render_tests(rows):
    if not rows: return "TEST HISTORY\nNo matching test records found."
    lines=["POLLINATIONS TEST HISTORY","="*76]
    for i,r in enumerate(rows,1):
        lines += [
            f"{i}. {r['requested_model']}  [{str(r['outcome']).upper()}]",
            f"   Tested          : {display_value(r['tested_at'])}",
            f"   Actual model    : {display_value(r['actual_model'])}",
            f"   Provider        : {display_value(r['provider'])}",
            f"   HTTP status     : {display_value(r['http_status'])}",
            f"   Key policy      : {display_value(r['key_policy'])}",
            f"   Token usage     : prompt {display_value(r['prompt_tokens'])} | completion {display_value(r['completion_tokens'])} | total {display_value(r['total_tokens'])}",
            f"   Latency         : {display_value(r['latency_ms'])} ms",
            f"   Error           : {display_value(r['error_code'])}",
            f"   Notes           : {display_value(r['notes'])}",
            "-"*76
        ]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser(description='Pollinations Model Intelligence Registry')
    sub=p.add_subparsers(dest='action',required=True)
    init=sub.add_parser('init'); init.add_argument('--db',default=str(DEFAULT_DB)); init.add_argument('--format',choices=('text','json'),default='text')
    imp=sub.add_parser('import-jsonl'); imp.add_argument('source'); imp.add_argument('--db',default=str(DEFAULT_DB)); imp.add_argument('--format',choices=('text','json'),default='text')
    ls=sub.add_parser('list'); ls.add_argument('--db',default=str(DEFAULT_DB)); ls.add_argument('--model'); ls.add_argument('--limit',type=int,default=100); ls.add_argument('--format',choices=('text','json'),default='text')
    sm=sub.add_parser('summary'); sm.add_argument('--db',default=str(DEFAULT_DB)); sm.add_argument('--format',choices=('text','json'),default='text')
    ex=sub.add_parser('export-jsonl'); ex.add_argument('source',nargs='?'); ex.add_argument('--db',default=str(DEFAULT_DB))
    a=p.parse_args()
    if a.action=='init':
        c=connect(a.db); c.close(); out={'status':'ok','database':a.db}
    elif a.action=='import-jsonl': out=import_jsonl(a.source,a.db)
    elif a.action=='list':
        rows=list_tests(a.db,a.model,a.limit); out={'tests':rows}
        if a.format=='text': print(render_tests(rows)); return 0
    elif a.action=='summary':
        rows=summary(a.db); out={'models':rows}
        if a.format=='text': print(render_summary(rows)); return 0
    else:
        records=list_tests(a.db,limit=1000)
        with open(a.source or '-', 'w',encoding='utf-8') if a.source else __import__('sys').stdout as f:
            for row in records: f.write(json.dumps(row,ensure_ascii=False)+'\n')
        return 0
    if a.format=='json': print(json.dumps(out,ensure_ascii=False,indent=2))
    else:
        print("Registry initialized: " + out['database'] if a.action=='init' else
              f"Import complete: {out['inserted_records']} of {out['input_records']} records added.\nDatabase: {out['database']}")
    return 0

if __name__=='__main__': raise SystemExit(main())
