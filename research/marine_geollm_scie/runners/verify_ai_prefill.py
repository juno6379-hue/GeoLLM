"""Read-only verification of AI review JSONL and exported XLSX source preservation."""
import hashlib
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'research/marine_geollm_scie/benchmark/review_exports/20261030_ai_prefill'
OUT=ROOT/'outputs/scie_annotation_ai_prefill_20261030'


def verify():
    benchmark=[json.loads(s) for s in (ROOT/'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl').read_text(encoding='utf-8').splitlines()]
    queries={r['case_id']:r['query'] for r in benchmark}
    report=[]
    files=[('검수자A',BASE/'reviewer_A/annotations_DRAFT.jsonl'),('검수자B',BASE/'reviewer_B/annotations_DRAFT.jsonl'),('합의검토',BASE/'adjudication_DRAFT.jsonl')]
    for label,path in files:
        text=path.read_text(encoding='utf-8'); assert '\ufffd' not in text
        rows=[json.loads(s) for s in text.splitlines() if s.strip()]
        assert len(rows)==18 and {r['case_id']:r['query'] for r in rows}==queries
        assert all(r['annotation_status']=='DRAFT' and r['review_kind']=='AI_PRE_REVIEW' and r['human_approval'] is False for r in rows)
        for r in rows:
            for material in r.get('source_materials',[]):
                assert hashlib.sha256(material['source_text'].encode('utf-8')).hexdigest()==material['source_text_sha256']
        if label=='합의검토':
            for r in rows:
                if r['category']=='Q2':
                    assert r['resolution']['source_checked_feature_records']
                    assert all(f['attribute_bindings'] for f in r['resolution']['source_checked_feature_records'])
                assert r['resolution']['spatial_oracle']['expected_object_ids'] is None
                assert r['resolution']['spatial_oracle']['expected_count'] is None
        workbook=OUT/f'{label}_18사례_AI사전검토.xlsx'
        with zipfile.ZipFile(workbook) as archive:
            strings=[]; formulas=0; sheets=[]
            for name in archive.namelist():
                if name=='xl/sharedStrings.xml' or (name.startswith('xl/worksheets/sheet') and name.endswith('.xml')):
                    root=ET.fromstring(archive.read(name))
                    formulas+=sum(e.tag.rsplit('}',1)[-1]=='f' for e in root.iter())
                    strings += [''.join(e.itertext()) for e in root.iter() if e.tag.rsplit('}',1)[-1] in ('t','v')]
                if name=='xl/workbook.xml':
                    sheets=[e.attrib['name'] for e in ET.fromstring(archive.read(name)).iter() if e.tag.rsplit('}',1)[-1]=='sheet']
            assert formulas==0
            combined='\n'.join(strings)
            assert '\ufffd' not in combined
            assert all(q in strings for q in queries.values())
            assert 'AI 사전검토 · 사용자 승인 대기 · GOLD 아님' in strings
            assert '입력필드전체' in sheets and '근거' in sheets
            assert hashlib.sha256(path.read_bytes()).hexdigest() in strings
        report.append({'assignment':label,'cases':18,'utf8_replacement_characters':0,'formulas':formulas,
                       'original_queries_preserved':True,'input_hash_present':True,'sheets':sheets,
                       'workbook_sha256':hashlib.sha256(workbook.read_bytes()).hexdigest()})
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__': verify()
