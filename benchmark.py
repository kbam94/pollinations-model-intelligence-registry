#!/usr/bin/env python3
"""Offline benchmark planner and scorer. Makes NO network/API calls."""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DEFAULT_CASES=ROOT/'benchmarks'/'cases.json'

def load_cases(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data,list): raise ValueError('Cases file must contain a JSON array')
    ids=set()
    for c in data:
        for k in ('id','category','type','prompt','expected'):
            if k not in c: raise ValueError(f'Case missing field: {k}')
        if c['id'] in ids: raise ValueError(f'Duplicate case id: {c["id"]}')
        ids.add(c['id'])
    return data

def plan(cases, model):
    for c in cases:
        print(json.dumps({'case_id':c['id'],'category':c['category'],'model':model,'prompt':c['prompt']},ensure_ascii=False))

def evaluate(case, response):
    text=response.strip(); kind=case['type']; expected=case['expected']
    if kind=='exact':
        ok=text==str(expected)
        return ok, 'exact_match' if ok else 'not_exact_match'
    if kind=='json_object':
        try: parsed=json.loads(text)
        except Exception: return False,'invalid_json'
        ok=isinstance(parsed,dict) and parsed==expected
        return ok,'json_matches_expected_object' if ok else 'json_object_mismatch'
    if kind=='contains_all':
        missing=[part for part in expected if part not in text]
        return not missing, ('required_fragments_present' if not missing else 'missing_fragments:'+','.join(missing))
    raise ValueError(f'Unknown evaluator type: {kind}')

def score(cases, input_path, output_path=None, output_format='text'):
    by_id={c['id']:c for c in cases}; results=[]; seen=set()
    with open(input_path,encoding='utf-8') as f:
        for n,line in enumerate(f,1):
            if not line.strip(): continue
            item=json.loads(line); cid=item.get('case_id'); model=item.get('model'); response=item.get('response')
            if cid not in by_id: raise ValueError(f'Line {n}: unknown case_id {cid!r}')
            if not model or not isinstance(response,str): raise ValueError(f'Line {n}: model and string response are required')
            key=(model,cid)
            if key in seen: raise ValueError(f'Line {n}: duplicate response for {model}/{cid}')
            seen.add(key); case=by_id[cid]
            passed,reason=evaluate(case,response)
            results.append({'model':model,'case_id':cid,'category':case['category'],'passed':passed,'reason':reason,'manual_review_recommended':bool(case.get('manual_review',False)),'prompt_tokens':item.get('prompt_tokens'),'completion_tokens':item.get('completion_tokens'),'total_tokens':item.get('total_tokens')})
    groups=defaultdict(list)
    for r in results: groups[r['model']].append(r)
    summaries=[]
    for model, rows in sorted(groups.items()):
        passed=sum(r['passed'] for r in rows); total=len(rows); cats=defaultdict(lambda:{'passed':0,'total':0})
        for r in rows:
            cats[r['category']]['total']+=1; cats[r['category']]['passed']+=int(r['passed'])
        summaries.append({'model':model,'passed':passed,'tested':total,'accuracy_percent':round(100*passed/total,2) if total else 0,'manual_reviews':sum(r['manual_review_recommended'] for r in rows),'categories':dict(cats)})
    report={'created_at':datetime.now(timezone.utc).isoformat(),'mode':'offline_scoring_no_api_calls','response_records':len(results),'summaries':summaries,'results':results}
    rendered=json.dumps(report,ensure_ascii=False,indent=2)+'\n'
    if output_path: Path(output_path).write_text(rendered,encoding='utf-8')
    if output_format=='json': print(rendered,end='')
    else: print(render_text(report))
    return report

def render_text(report):
    lines=["OFFLINE BENCHMARK REPORT","="*72,
           f"Created       : {report['created_at']}",
           f"Response rows : {report['response_records']}",
           "Mode          : Offline scoring; no API calls were made.",""]
    if not report['summaries']: lines.append("No response records to score.")
    for s in report['summaries']:
        lines += [f"MODEL: {s['model']}",
                  f"Overall score : {s['passed']} / {s['tested']} passed ({s['accuracy_percent']}%)",
                  f"Manual reviews: {s['manual_reviews']}"]
        for category,counts in s['categories'].items():
            lines.append(f"  {category.replace('_',' ').title():24} {counts['passed']} / {counts['total']} passed")
        lines.append("")
    lines += ["INDIVIDUAL RESULTS","-"*72]
    for r in report['results']:
        status="PASS" if r['passed'] else "FAIL"
        lines.append(f"[{status}] {r['model']} | {r['case_id']} | {r['category']}")
        lines.append(f"       Result: {r['reason']}")
        if r['manual_review_recommended']: lines.append("       Note  : Manual review recommended")
    return "\n".join(lines)

def render_cases(cases):
    lines=["BENCHMARK CASES","="*72]
    for c in cases:
        lines.append(f"{c['id']} | {c['category'].replace('_',' ').title()} | {c['type']}")
        lines.append(f"  Prompt: {c['prompt']}")
        if c.get('manual_review'): lines.append("  Note  : Manual review recommended")
    lines.append(f"\nTotal cases: {len(cases)}")
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser(description='Offline Pollinations benchmark planner/scorer; never calls model APIs')
    p.add_argument('--cases',default=str(DEFAULT_CASES))
    sub=p.add_subparsers(dest='command',required=True)
    pl=sub.add_parser('plan',help='Export prompts as JSONL; no model call'); pl.add_argument('--model',required=True)
    sc=sub.add_parser('score',help='Score a JSONL file of model responses'); sc.add_argument('responses'); sc.add_argument('--output'); sc.add_argument('--format',choices=('text','json'),default='text')
    ls=sub.add_parser('list-cases',help='List benchmark cases'); ls.add_argument('--format',choices=('text','json'),default='text')
    a=p.parse_args(); cases=load_cases(a.cases)
    if a.command=='plan': plan(cases,a.model)
    elif a.command=='score': score(cases,a.responses,a.output,a.format)
    elif a.format=='json': print(json.dumps([{'id':c['id'],'category':c['category'],'type':c['type'],'manual_review':bool(c.get('manual_review',False))} for c in cases],indent=2))
    else: print(render_cases(cases))

if __name__=='__main__':
    try: main()
    except Exception as e: print(f'ERROR: {e}',file=sys.stderr); raise SystemExit(2)
