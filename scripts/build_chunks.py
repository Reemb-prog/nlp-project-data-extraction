#!/usr/bin/env python3
"""Rebuild independent PDF/text chunks with original-page citations. Requires PyMuPDF."""
import argparse, csv, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASES = ROOT / 'config' / 'sections.json'
MANIFEST_FIELDS = ['chunk_id','topic','original_start','original_end','page_count','approx_input_tokens','text_chars','txt_path','pdf_path','sha256_text']

def safe_slug(s):
    return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')[:48]

def get_intervals(pdf, cap_chars, cap_pages):
    ranges = json.loads(BASES.read_text(encoding='utf-8'))
    assert ranges[0][0] == 1 and ranges[-1][1] == len(pdf)
    assert all(ranges[i][1] + 1 == ranges[i + 1][0] for i in range(len(ranges)-1))
    texts = [pg.get_text('text', sort=True).strip() for pg in pdf]
    intervals = []
    for first, last, heading in ranges:
        start, total = first, 0
        for page_num in range(first, last + 1):
            length = len(texts[page_num - 1])
            if page_num > start and (total + length > cap_chars or page_num - start >= cap_pages):
                intervals.append((start, page_num - 1, heading))
                start, total = page_num, 0
            total += length
        intervals.append((start, last, heading))
    return intervals, texts

def build(source, cap_chars=22000, cap_pages=10):
    import fitz
    doc=fitz.open(source)
    intervals, texts = get_intervals(doc, cap_chars, cap_pages)
    chunk_root = ROOT/'chunks'
    chunk_root.mkdir(parents=True,exist_ok=True)
    rows=[]
    for index,(first,last,topic) in enumerate(intervals,1):
        ident=f'S{index:03d}'
        base=chunk_root/ident
        base.mkdir(exist_ok=True)
        banner=(f'RHU UNDERGRADUATE CATALOG 2026-2027\nSECTION: {ident} | {topic}\n'
                f'ORIGINAL PDF PAGES: {first} to {last} (inclusive)\n'
                f'ONLY extract facts whose source page is between {first} and {last}.\n'
                'The text is a machine extraction; check chunk.pdf for tables or unclear layouts.\n\n')
        contents = banner + '\n\n'.join(f'========== ORIGINAL PDF PAGE {n} ==========\n{texts[n-1]}' for n in range(first,last+1))+'\n'
        (base/'source.txt').write_text(contents, encoding='utf-8')
        small = fitz.open()
        small.insert_pdf(doc, from_page=first-1,to_page=last-1)
        small.save(base/'chunk.pdf', garbage=4, deflate=True)
        small.close()
        # Boundary help prevents missing an entry continued from adjacent page;
        # the neighboring content is not part of this chunk's extraction scope.
        borders=[]
        if first > 1:
            borders.append(f'PREVIOUS PAGE {first-1} (reference only; do not make a fact for this page):\n{texts[first-2]}')
        if last < len(texts):
            borders.append(f'NEXT PAGE {last+1} (reference only; do not make a fact for this page):\n{texts[last]}')
        (base/'boundary_context.txt').write_text('\n\n'.join(borders)+'\n',encoding='utf-8')
        digest=hashlib.sha256(contents.encode('utf-8')).hexdigest()
        rows.append(dict(chunk_id=ident, topic=topic,original_start=first,original_end=last,
                         page_count=last-first+1,approx_input_tokens=(len(contents)+3)//4,
                         text_chars=len(contents),txt_path=f'chunks/{ident}/source.txt',
                         pdf_path=f'chunks/{ident}/chunk.pdf',sha256_text=digest))
    with (ROOT/'config'/'manifest.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=MANIFEST_FIELDS);w.writeheader();w.writerows(rows)
    (ROOT/'config'/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'Built {len(rows)} complete nonoverlapping chunks, {len(doc)} PDF pages, '+
          f'~{sum(r["approx_input_tokens"] for r in rows):,} input tokens total (rough text estimate).')
    doc.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--pdf',default=str(ROOT/'source'/'RHU_Undergraduate_Catalog_2026-2027.pdf'))
    p.add_argument('--max-chars',type=int,default=22000)
    p.add_argument('--max-pages',type=int,default=10)
    args=p.parse_args()
    build(Path(args.pdf), args.max_chars,args.max_pages)
if __name__=='__main__':main()
