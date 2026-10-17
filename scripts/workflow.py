#!/usr/bin/env python3
"""Offline QA-dataset contracts, section checks, progress, merging and grouped splits."""
import argparse, collections, csv, hashlib, json, random, re, sys, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FACT_COLUMNS=['fact_id','chunk_id','source_pages','source_quote','category','intent','entity','attribute','answer','review_status','review_note']
QUESTION_COLUMNS=['qa_id','fact_id','question','question_style']
NEG_COLUMNS=['question','category','intent','answerability','reason']
STYLES={'direct','paraphrase','contextual','short'}
STATUSES={'draft','needs_review','human_approved'}
OUT_SCOPE={'not_in_catalog','live_data_needed'}
PLAN_LOCK=ROOT/'data'/'plan'/'labels.lock.sha256'
CATALOG_URL='https://www.rhu.edu.lb/Library/Assets/Gallery/Files/RHU_Undegraduate_Catalog_2026-2027.pdf'

def read_csv(path,fields,optional=False):
    if not path.exists():
        if optional:return [],[f'Missing file: {path.relative_to(ROOT)}']
        return [],[f'Missing file: {path.relative_to(ROOT)}']
    with path.open('r',encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        headers=reader.fieldnames or []
        errs=[] if headers==fields else [f'{path.relative_to(ROOT)} incorrect headers: expected {fields}, got {headers}']
        rows=list(reader)
        if any(None in r for r in rows): errs.append(f'{path}: malformed CSV column count')
        return rows,errs

def write_csv(path,fields,rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=fields, extrasaction='ignore');w.writeheader();w.writerows(rows)

def slug(s): return re.sub(r'[^a-z0-9]+','_',unicodedata.normalize('NFKC',s).lower()).strip('_')
def norm(s):
    return ' '.join(unicodedata.normalize('NFKC',s).replace('\u00ad','').split()).casefold()
def qnorm(s):
    return re.sub(r'[^\w]+',' ',norm(s)).strip()

def manifest():
    return json.loads((ROOT/'config'/'manifest.json').read_text(encoding='utf-8'))

def taxonomy():
    path=ROOT/'data'/'plan'/'labels.json'
    if not path.exists():return None, ['Missing data/plan/labels.json. Run planner first.']
    if PLAN_LOCK.exists():
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if PLAN_LOCK.read_text(encoding='utf-8').strip()!=actual:
            return None,['Taxonomy changed after processing began. Revert labels.json, or restart ALL section outputs with a new plan.']
    try: data=json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:return None,[f'Invalid labels.json: {exc}']
    errs=[]
    if not isinstance(data,dict):return None,['labels.json must be an object']
    cats=data.get('categories',[]);intents=data.get('intents',[])
    if not isinstance(cats,list) or not isinstance(intents,list):return None,['labels must contain category and intent lists']
    cids=set(); imap={}
    for x in cats:
        if not isinstance(x,dict) or not re.fullmatch(r'[a-z][a-z0-9_]*',str(x.get('id',''))): errs.append(f'Invalid category: {x}');continue
        if not str(x.get('description','')).strip():errs.append(f'Missing category description: {x}')
        if x['id'] in cids:errs.append(f'Duplicate category: {x["id"]}')
        cids.add(x['id'])
    for x in intents:
        if not isinstance(x,dict) or not re.fullmatch(r'[a-z][a-z0-9_]*',str(x.get('id',''))):errs.append(f'Invalid intent: {x}');continue
        if x['id'] in imap: errs.append(f'Duplicate intent: {x["id"]}')
        if x.get('category') not in cids:errs.append(f'Intent {x["id"]} maps to unknown category')
        if not str(x.get('description','')).strip():errs.append(f'Missing intent description: {x}')
        imap[x['id']]=x.get('category')
    if not cids: errs.append('No categories')
    if not imap: errs.append('No intents')
    if 'out_of_scope' not in cids:errs.append('Reserved category out_of_scope is required')
    for reserve in ['not_in_catalog','live_data_needed']:
        if imap.get(reserve)!='out_of_scope':errs.append(f'Reserved intent {reserve} must map to out_of_scope')
    return {'categories':cids,'intents':imap,'raw':data},errs

def page_texts(ident):
    path=ROOT/'chunks'/ident/'source.txt'
    text=path.read_text(encoding='utf-8')
    parts=re.split(r'^========== ORIGINAL PDF PAGE (\d+) ==========\s*$',text,flags=re.MULTILINE)
    return {int(parts[i]):parts[i+1] for i in range(1,len(parts)-1,2)}

def section_validate(record,tax,need_question_min=2):
    ident=record['chunk_id']; base=ROOT/'data'/'sections'/ident
    facts,errs=read_csv(base/'facts.csv',FACT_COLUMNS)
    qs,errs2=read_csv(base/'questions.csv',QUESTION_COLUMNS)
    errs+=errs2
    if errs:return facts,qs,errs,[]
    warnings=[]; fids=set();qids=set(); qcount=collections.Counter(); question_keys=set()
    src_path=ROOT/'chunks'/ident/'source.txt'
    if hashlib.sha256(src_path.read_bytes()).hexdigest()!=record['sha256_text']:
        return facts,qs,[f'{ident}: source text hash differs from manifest; stop and investigate'],[]
    src=page_texts(ident)
    first,last=record['original_start'],record['original_end']
    fact_map={}
    for ix,f in enumerate(facts,2):
        pre=f'{ident} facts.csv row {ix}'
        fid=f['fact_id']
        if not re.fullmatch(re.escape(ident)+r'_F\d{4,}',fid):errs.append(f'{pre}: invalid fact_id {fid}')
        if fid in fids:errs.append(f'{pre}: duplicate fact_id {fid}')
        fids.add(fid); fact_map[fid]=f
        if f['chunk_id']!=ident:errs.append(f'{pre}: incorrect chunk_id')
        if f['category'] not in tax['categories']:errs.append(f'{pre}: unknown category')
        if tax['intents'].get(f['intent'])!=f['category']:errs.append(f'{pre}: wrong intent/category mapping')
        if f['review_status'] not in STATUSES:errs.append(f'{pre}: invalid review_status')
        if f['review_status']=='needs_review' and not f['review_note'].strip():errs.append(f'{pre}: needs_review requires review_note')
        for key in ['source_pages','source_quote','entity','attribute','answer']:
            if not f[key].strip():errs.append(f'{pre}: missing {key}')
        if len(f['source_quote'])>420:errs.append(f'{pre}: source_quote over 420 chars')
        if len(f['source_quote'])<10:errs.append(f'{pre}: source_quote too short')
        if not re.fullmatch(r'\d+(;\d+)*',f['source_pages']):
            errs.append(f'{pre}: source_pages must be semicolon-separated original PDF page numbers')
        else:
            pages=[int(x) for x in f['source_pages'].split(';')]
            if len(set(pages))!=len(pages):errs.append(f'{pre}: duplicate source pages')
            if not all(first<=p<=last for p in pages):errs.append(f'{pre}: source_pages outside {first}-{last}')
            if not any(norm(f['source_quote']) in norm(src.get(p,'')) for p in pages):
                errs.append(f'{pre}: SOURCE QUOTE NOT FOUND in its cited PDF page text (check actual PDF and quote)')
        if f['review_status']=='human_approved':warnings.append(f'{pre}: ensure a HUMAN (not Claude) approved this')
    for ix,q in enumerate(qs,2):
        pre=f'{ident} questions.csv row {ix}'
        qid=q['qa_id'];fid=q['fact_id']
        if not re.fullmatch(re.escape(ident)+r'_Q\d{4,}',qid):errs.append(f'{pre}: invalid qa_id')
        if qid in qids:errs.append(f'{pre}: duplicate qa_id')
        qids.add(qid)
        if fid not in fact_map:errs.append(f'{pre}: unknown fact_id {fid}')
        if fid in fact_map:qcount[fid]+=1
        if q['question_style'] not in STYLES:errs.append(f'{pre}: invalid question_style')
        if not q['question'].strip() or len(q['question'].strip())<12:errs.append(f'{pre}: question too short')
        if len(q['question'])>300:errs.append(f'{pre}: question too long')
        normalized=qnorm(q['question'])
        if normalized in question_keys:errs.append(f'{pre}: repeated question')
        question_keys.add(normalized)
        if q['question'].lstrip().startswith(('=','+','@')):errs.append(f'{pre}: unsafe spreadsheet formula prefix')
    for fid in fact_map:
        if qcount[fid]<need_question_min:warnings.append(f'{ident} fact {fid}: only {qcount[fid]} question(s), expected 2-4')
        if qcount[fid]>5:warnings.append(f'{ident} fact {fid}: {qcount[fid]} questions; 2-4 preferred to limit cost')
    if not facts: warnings.append(f'{ident} has zero facts; check that no useful source information was skipped')
    return facts,qs,errs,warnings

def sections_state(tax):
    return [(r, *(section_validate(r,tax) if (ROOT/'data'/'sections'/r['chunk_id']/'facts.csv').exists() or (ROOT/'data'/'sections'/r['chunk_id']/'questions.csv').exists() else ([],[],['NOT_STARTED'],[]))) for r in manifest()]

def get_partition(ids, key):
    buckets=collections.defaultdict(list)
    for ident in ids:buckets[key[ident]].append(ident)
    result={}
    for label,items in buckets.items():
        items.sort(key=lambda item: hashlib.sha256(('rhu_2026_2027_v1_'+item).encode()).hexdigest())
        n=len(items)
        if n<7: test_n=val_n=0
        else:
            val_n=max(1, round(n*0.15));test_n=max(1,round(n*0.15))
            if n-val_n-test_n<1: val_n,test_n=0,0
        for i,ident in enumerate(items):result[ident]='test' if i<test_n else 'validation' if i<test_n+val_n else 'train'
    return result

def retrieval_rows():
    for record in manifest():
        ident=record['chunk_id']
        for pn,tx in sorted(page_texts(ident).items()):
            text=re.sub(r'\s+',' ',tx).strip()
            sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z0-9])',text)
            current='';num=0
            for sentence in sentences:
                if current and len(current)+len(sentence)>1150:
                    num+=1
                    yield {'passage_id':f'{ident}_P{pn:03d}_{num:02d}','chunk_id':ident,'source_page':pn,
                           'topic':record['topic'],'passage_text':current.strip(),'source_url':CATALOG_URL}
                    current=''
                current=(current+' '+sentence).strip()
            if current:
                num+=1
                yield {'passage_id':f'{ident}_P{pn:03d}_{num:02d}','chunk_id':ident,'source_page':pn,
                       'topic':record['topic'],'passage_text':current.strip(),'source_url':CATALOG_URL}

def cmd_status(args,tax):
    states=sections_state(tax)
    totals=collections.Counter('not_started' if e==['NOT_STARTED'] else 'invalid' if e else 'valid' for r,f,q,e,w in states)
    print('Chunks:',len(states),dict(totals))
    for r,f,q,e,w in states:
        if args.all or e and e!=['NOT_STARTED']:
            print(r['chunk_id'],f'pages {r["original_start"]}-{r["original_end"]}',
                  'VALID' if not e else 'NOT_STARTED' if e==['NOT_STARTED'] else f'INVALID ({len(e)} errors)',
                  f'facts={len(f)}, questions={len(q)}',r['topic'])
    for r,f,q,e,w in states:
        if e:print('NEXT:',r['chunk_id'],r['topic'], ' | ',r['txt_path']);break
    else:print('NEXT: all chunks complete. Run finalize.')

def cmd_validate(args,tax):
    rec=next((x for x in manifest() if x['chunk_id']==args.section),None)
    if not rec:raise SystemExit(f'Unknown section {args.section}')
    facts,qs,errors,warnings=section_validate(rec,tax)
    print(f'{args.section}: {len(facts)} facts; {len(qs)} questions; {len(errors)} errors; {len(warnings)} warnings')
    for x in errors[:35]:print('ERROR',x)
    if len(errors)>35:print(f'... {len(errors)-35} additional errors')
    for x in warnings[:20]:print('WARN ',x)
    if errors:sys.exit(1)

def cmd_final(args,tax):
    states=sections_state(tax)
    errors=[f'{r["chunk_id"]}: {e[:4]}' for r,f,q,e,w in states if e]
    if errors:
        print('Cannot finalize. Missing or invalid chunks:',len(errors))
        for err in errors[:15]:print(' ',err)
        sys.exit(1)
    facts=[x for r,f,q,e,w in states for x in f]
    questions=[x for r,f,q,e,w in states for x in q]
    fact_map={x['fact_id']:x for x in facts}
    if len(fact_map)!=len(facts):raise SystemExit('Repeated fact ID across sections')
    normalized_questions=[qnorm(q['question']) for q in questions]
    duplicates=[key for key,n in collections.Counter(normalized_questions).items() if n>1]
    if duplicates:
        print('Cannot finalize: duplicate question strings across chunks, examples:',duplicates[:12]);sys.exit(1)
    negatives=[]
    negatives_path=ROOT/'data'/'plan'/'negative_questions.csv'
    if negatives_path.exists():
        negatives,errors=read_csv(negatives_path,NEG_COLUMNS)
        if errors:raise SystemExit('\n'.join(errors))
        for row in negatives:
            if row['category']!='out_of_scope' or tax['intents'].get(row['intent'])!='out_of_scope':
                raise SystemExit('negative_questions.csv has invalid category or intent')
            if row['intent']!=row['answerability'] or row['answerability'] not in OUT_SCOPE:
                raise SystemExit('Negative question intent must match answerability')
            if not row['reason'].strip() or not row['question'].strip():raise SystemExit('Negative question missing reason/text')
        all_keys=normalized_questions+[qnorm(q['question']) for q in negatives]
        if len(all_keys)!=len(set(all_keys)):raise SystemExit('Duplicate positive or negative question')
    # Keep repeated semantic facts together even if they occur on multiple pages/chunks.
    # Manual review is still needed for near-duplicates with different answer wording.
    group_of_fact={fid:'|'.join([f['intent'],qnorm(f['entity']),qnorm(f['attribute']),qnorm(f['answer'])])
                   for fid,f in fact_map.items()}
    group_intents={group_of_fact[fid]:f['intent'] for fid,f in fact_map.items()}
    split_by_group=get_partition(list(group_intents),group_intents)
    split_by_fact={fid:split_by_group[group_of_fact[fid]] for fid in fact_map}
    output=[]
    fields=['qa_id','fact_id','chunk_id','question','answer','category','intent','entity','attribute','source_pages','source_url','question_style','answerability','review_status','split','training_eligible']
    for q in questions:
        f=fact_map[q['fact_id']]
        output.append(dict(qa_id=q['qa_id'],fact_id=q['fact_id'],chunk_id=f['chunk_id'],question=q['question'],
                           answer=f['answer'],category=f['category'],intent=f['intent'],entity=f['entity'],attribute=f['attribute'],
                           source_pages=f['source_pages'],source_url=CATALOG_URL,question_style=q['question_style'],
                           answerability='in_catalog',review_status=f['review_status'],split=split_by_fact[q['fact_id']],
                           training_eligible='yes' if f['review_status']!='needs_review' else 'no'))
    for index,n in enumerate(negatives,1):
        ident='NEG_'+str(index).zfill(5)
        h=hashlib.sha256(qnorm(n['question']).encode('utf-8')).digest()[0]
        split='train' if h<179 else 'validation' if h<217 else 'test'
        output.append(dict(qa_id=ident, fact_id='',chunk_id='',question=n['question'],answer='',category=n['category'],
                           intent=n['intent'],entity='',attribute='',source_pages='',source_url=CATALOG_URL,
                           question_style='negative',answerability=n['answerability'],review_status='draft',
                           split=split,training_eligible='yes'))
    dest=ROOT/'data'/'final'
    write_csv(dest/'RHU_QA_ALL.csv',fields,output)
    write_csv(dest/'RHU_FACTS.csv',FACT_COLUMNS,facts)
    eligible=[r for r in output if r['training_eligible']=='yes']
    for split in ('train','validation','test'):
        write_csv(dest/f'RHU_QA_{split.upper()}.csv',fields,[r for r in eligible if r['split']==split])
    passages=list(retrieval_rows())
    write_csv(dest/'RHU_RETRIEVAL_PASSAGES.csv',list(passages[0]) if passages else
              ['passage_id','chunk_id','source_page','topic','passage_text','source_url'],passages)
    report={'pdf_pages':429,'chunks':len(states),'facts':len(facts),'qa_all':len(output),'qa_eligible':len(eligible),
            'needs_review_facts':sum(f['review_status']=='needs_review' for f in facts),
            'distinct_exact_semantic_groups':len(group_intents),
            'review_status_counts':dict(collections.Counter(f['review_status'] for f in facts)),
            'split_eligible':dict(collections.Counter(r['split'] for r in eligible)),
            'categories':dict(collections.Counter(f['category'] for f in facts)),
            'intents':dict(collections.Counter(f['intent'] for f in facts)),
            'retrieval_passages':len(passages),
            'intent_split_gaps':{intent:sorted({'train','validation','test'}-{r['split'] for r in output if r['intent']==intent and r['training_eligible']=='yes'})
                                 for intent in sorted({r['intent'] for r in output})
                                 if {'train','validation','test'}-{r['split'] for r in output if r['intent']==intent and r['training_eligible']=='yes'}},
            'note':'Quote matching is automated; semantic correctness and generated paraphrases still need human review.'}
    (dest/'QUALITY_REPORT.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('FINALIZED: facts',len(facts),'QA',len(output),'eligible',len(eligible),'passages',len(passages))
    print('Output:',dest)

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    sub=ap.add_subparsers(dest='action',required=True)
    sub.add_parser('check-plan')
    sub.add_parser('lock-plan')
    p=sub.add_parser('status');p.add_argument('--all',action='store_true')
    p=sub.add_parser('validate');p.add_argument('section')
    sub.add_parser('finalize')
    args=ap.parse_args()
    tx,errors=taxonomy()
    if errors:
        for e in errors:print('ERROR',e)
        sys.exit(1)
    if args.action=='check-plan':
        if not (ROOT/'data'/'plan'/'plan.md').exists():raise SystemExit('Missing data/plan/plan.md')
        print('Planning files valid:',len(tx['categories']),'categories,',len(tx['intents']),'intents')
    elif args.action=='lock-plan':
        lock=hashlib.sha256((ROOT/'data'/'plan'/'labels.json').read_bytes()).hexdigest()
        PLAN_LOCK.write_text(lock+'\n',encoding='utf-8')
        print('Locked taxonomy for all section runs')
    elif args.action=='status':cmd_status(args,tx)
    elif args.action=='validate':cmd_validate(args,tx)
    elif args.action=='finalize':cmd_final(args,tx)
if __name__=='__main__':main()
