import csv, hashlib, json, re, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import workflow

class HarnessTests(unittest.TestCase):
    def test_all_429_pages_once(self):
        manifest=json.loads((ROOT/'config'/'manifest.json').read_text())
        pages=[p for r in manifest for p in range(r['original_start'],r['original_end']+1)]
        self.assertEqual(pages,list(range(1,430)))
        self.assertEqual(len(manifest),68)
        for r in manifest:
            base=ROOT/'chunks'/r['chunk_id']
            self.assertTrue((base/'chunk.pdf').exists())
            self.assertTrue((base/'boundary_context.txt').exists())
            content=(base/'source.txt').read_bytes()
            self.assertEqual(hashlib.sha256(content).hexdigest(),r['sha256_text'])
            self.assertEqual(len(re.findall(r'^========== ORIGINAL PDF PAGE \d+ ==========\s*$',
                                            content.decode('utf-8'),flags=re.M)),r['page_count'])

    def test_original_pdf_and_chunks_exist(self):
        self.assertTrue((ROOT/'source'/'RHU_Undergraduate_Catalog_2026-2027.pdf').exists())
        import fitz
        d=fitz.open(ROOT/'source'/'RHU_Undergraduate_Catalog_2026-2027.pdf')
        self.assertEqual(len(d),429)
        for r in json.loads((ROOT/'config'/'manifest.json').read_text())[:3]:
            s=fitz.open(ROOT/r['pdf_path'])
            self.assertEqual(len(s),r['page_count'])
            s.close()
        d.close()

    def test_taxonomy_parser_and_quote_guard(self):
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td); (tmp/'chunks'/'S001').mkdir(parents=True);(tmp/'data'/'sections'/'S001').mkdir(parents=True)
            source='========== ORIGINAL PDF PAGE 28 ==========\nThe RHU Computer Science bachelor degree requires 93 credits.\n'
            (tmp/'chunks'/'S001'/'source.txt').write_text(source)
            record={'chunk_id':'S001','original_start':28,'original_end':28,'sha256_text':hashlib.sha256(source.encode()).hexdigest()}
            f={'fact_id':'S001_F0001','chunk_id':'S001','source_pages':'28','source_quote':'requires 93 credits',
               'category':'programs','intent':'degree_credits','entity':'Computer Science','attribute':'credits',
               'answer':'The BS in Computer Science requires 93 credits.','review_status':'draft','review_note':''}
            q=[{'qa_id':'S001_Q0001','fact_id':'S001_F0001','question':'How many credits does RHU Computer Science need?', 'question_style':'direct'},
               {'qa_id':'S001_Q0002','fact_id':'S001_F0001','question':'What is the credit requirement for the RHU CS degree?', 'question_style':'paraphrase'}]
            workflow.write_csv(tmp/'data'/'sections'/'S001'/'facts.csv',workflow.FACT_COLUMNS,[f])
            workflow.write_csv(tmp/'data'/'sections'/'S001'/'questions.csv',workflow.QUESTION_COLUMNS,q)
            original=workflow.ROOT
            try:
                workflow.ROOT=tmp
                tax={'categories':{'programs'},'intents':{'degree_credits':'programs'}}
                facts,qs,errors,warns=workflow.section_validate(record,tax)
                self.assertFalse(errors,errors)
                self.assertEqual(len(qs),2)
                f['source_quote']='clearly fabricated sentence'
                workflow.write_csv(tmp/'data'/'sections'/'S001'/'facts.csv',workflow.FACT_COLUMNS,[f])
                self.assertTrue(any('SOURCE QUOTE' in e for e in workflow.section_validate(record,tax)[2]))
            finally:workflow.ROOT=original

    def test_group_split(self):
        keys={f'fact{i}':'academics' for i in range(30)}
        d=workflow.get_partition(list(keys),keys)
        self.assertEqual(len(d),30)
        self.assertEqual(set(d.values()),{'train','validation','test'})
        self.assertEqual(d,workflow.get_partition(list(keys),keys))

    def test_end_to_end_one_chunk_mock(self):
        with tempfile.TemporaryDirectory() as td:
            tmp=Path(td)
            for folder in ['chunks/S001','config','data/sections/S001','data/plan','data/final']:
                (tmp/folder).mkdir(parents=True,exist_ok=True)
            source='========== ORIGINAL PDF PAGE 28 ==========\nThe RHU Computer Science bachelor degree requires 93 credits.\n'
            (tmp/'chunks/S001/source.txt').write_text(source,encoding='utf-8')
            rec={'chunk_id':'S001','original_start':28,'original_end':28,'topic':'Degrees','sha256_text':hashlib.sha256(source.encode()).hexdigest()}
            (tmp/'config/manifest.json').write_text(json.dumps([rec]))
            f={'fact_id':'S001_F0001','chunk_id':'S001','source_pages':'28','source_quote':'requires 93 credits',
               'category':'programs','intent':'degree_credits','entity':'Computer Science','attribute':'credits',
               'answer':'The BS in Computer Science requires 93 credits.','review_status':'draft','review_note':''}
            q=[{'qa_id':'S001_Q0001','fact_id':'S001_F0001','question':'How many credits does RHU Computer Science need?', 'question_style':'direct'},
               {'qa_id':'S001_Q0002','fact_id':'S001_F0001','question':'What is the credit requirement for the RHU CS degree?', 'question_style':'paraphrase'}]
            workflow.write_csv(tmp/'data/sections/S001/facts.csv',workflow.FACT_COLUMNS,[f])
            workflow.write_csv(tmp/'data/sections/S001/questions.csv',workflow.QUESTION_COLUMNS,q)
            taxonomy={'categories':{'programs'},'intents':{'degree_credits':'programs'}}
            original=workflow.ROOT
            try:
                workflow.ROOT=tmp
                workflow.cmd_final(None,taxonomy)
                with (tmp/'data/final/RHU_QA_ALL.csv').open(encoding='utf-8-sig') as file:
                    qa=list(csv.DictReader(file))
                self.assertEqual(len(qa),2)
                self.assertEqual({x['split'] for x in qa},{'train'})
                self.assertEqual({x['source_pages'] for x in qa},{'28'})
                self.assertTrue((tmp/'data/final/RHU_RETRIEVAL_PASSAGES.csv').exists())
            finally:workflow.ROOT=original

    def test_code_syntax(self):
        import py_compile
        for p in (ROOT/'scripts').glob('*.py'):py_compile.compile(str(p),doraise=True)

if __name__=='__main__':unittest.main()
