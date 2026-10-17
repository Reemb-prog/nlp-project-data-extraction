#!/usr/bin/env python3
"""Run Claude Code in short isolated sessions with a safe tool allow-list.

Requires Claude Code CLI installed/authenticated. Does not use ANTHROPIC_API_KEY or store credentials.
"""
import argparse, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def call(prompt,max_turns=18,dry_run=False):
    # New CLI process = independent context. Only file read/write tooling; Bash and Web disabled.
    cmd=['claude','-p',prompt,'--allowedTools','Read,Write,Edit,Glob,Grep','--max-turns',str(max_turns)]
    if dry_run:
        print('DRY RUN: claude -p <phase prompt> --allowedTools Read,Write,Edit,Glob,Grep --max-turns',max_turns)
        print('PROMPT:',prompt[:1000]);return 0
    if not shutil.which('claude'):
        print('Claude Code CLI not found. Install/authenticate Claude Code, or use manual instructions in docs/RUNBOOK.md.')
        return 2
    return subprocess.call(cmd,cwd=ROOT)

def check_plan():return subprocess.call([sys.executable,str(ROOT/'scripts'/'workflow.py'),'check-plan'],cwd=ROOT)==0

def get_next():
    for r in json.loads((ROOT/'config'/'manifest.json').read_text(encoding='utf-8')):
        folder=ROOT/'data'/'sections'/r['chunk_id']
        if not (folder/'facts.csv').exists() or not (folder/'questions.csv').exists():return r
        result=subprocess.run([sys.executable,str(ROOT/'scripts'/'workflow.py'),'validate',r['chunk_id']],
                              cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        if result.returncode:return r
    return None

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sp=ap.add_subparsers(dest='mode',required=True)
    sp.add_parser('plan')
    sp.add_parser('next')
    s=sp.add_parser('section');s.add_argument('section_id')
    s=sp.add_parser('batch');s.add_argument('--count',type=int,default=2)
    sp.add_parser('negatives')
    ap.add_argument('--dry-run',action='store_true')
    args=ap.parse_args()
    rows=json.loads((ROOT/'config'/'manifest.json').read_text(encoding='utf-8'))
    by_id={r['chunk_id']:r for r in rows}
    if args.mode=='plan':
        p=(ROOT/'prompts'/'PLAN.md').read_text(encoding='utf-8')
        code=call(p,15,args.dry_run)
        if code:sys.exit(code)
        if not args.dry_run and not check_plan():sys.exit(1)
        return
    if not args.dry_run and not check_plan():sys.exit(1)
    if args.mode=='negatives':
        code=call((ROOT/'prompts'/'NEGATIVES.md').read_text(encoding='utf-8'),10,args.dry_run)
        sys.exit(code)
    if args.mode=='section':
        if args.section_id not in by_id:raise SystemExit('Invalid section ID')
        selected=[by_id[args.section_id]]
    elif args.mode=='next':
        nxt=get_next() if not args.dry_run else rows[0]
        selected=[nxt] if nxt else []
    else:
        if args.count<1 or args.count>10:raise SystemExit('--count must be 1 to 10 (token/cost safety limit)')
        selected=[]
        # Process dynamically: next() is recalculated after each validated completed chunk.
        for i in range(args.count):
            nxt=get_next() if not args.dry_run else rows[i]
            if not nxt:break
            selected.append(nxt)
            if not args.dry_run:
                rc=execute(nxt,args.dry_run)
                if rc:sys.exit(rc)
        if not args.dry_run:
            print('Batch finished:',len(selected),'chunks')
        return
    if not selected:
        print('All chunks passed validation. You can generate negatives and finalize.')
        return
    sys.exit(execute(selected[0],args.dry_run))

def execute(rec,dry_run):
    if not dry_run:
        (ROOT/'data'/'sections'/rec['chunk_id']).mkdir(parents=True,exist_ok=True)
        rc=subprocess.call([sys.executable,str(ROOT/'scripts'/'workflow.py'),'lock-plan'],cwd=ROOT)
        if rc:return rc
    prompt=(ROOT/'prompts'/'EXTRACT.md').read_text(encoding='utf-8').format(**rec)
    print(f'Processing {rec["chunk_id"]} / PDF original pages {rec["original_start"]}-{rec["original_end"]} / {rec["topic"]}',flush=True)
    rc=call(prompt,22,dry_run)
    if rc:return rc
    if dry_run:return 0
    rc=subprocess.call([sys.executable,str(ROOT/'scripts'/'workflow.py'),'validate',rec['chunk_id']],cwd=ROOT)
    if rc:print('Correct ONLY this section using section',rec['chunk_id'])
    return rc

if __name__=='__main__':main()
