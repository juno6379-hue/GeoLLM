import copy
from pathlib import Path
from zipfile import ZipFile

import pytest

from research.marine_geollm_scie.runners.import_review_workbooks import read_workbook
from research.marine_geollm_scie.runners.review_v2_diagnostics import index_cases, plan_checks, validate_sources


def test_xlsx_read_preserves_inline_shared_and_formula_without_execution(tmp_path):
    path = tmp_path / 'review.xlsx'
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    with ZipFile(path, 'w') as z:
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="검토" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', '<Relationships><Relationship Id="rId1" Target="/xl/worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/sharedStrings.xml', f'<sst xmlns="{ns}"><si><r><t>독도</t></r><r><t> 근처</t></r></si></sst>')
        z.writestr('xl/worksheets/sheet1.xml', f'<worksheet xmlns="{ns}"><sheetData><row r="1"><c r="A1" t="s"><v>0</v></c><c r="B1" t="inlineStr"><is><t>DRAFT</t></is></c><c r="C1"><f>1+1</f><v>2</v></c></row></sheetData></worksheet>')
    result = read_workbook(path)
    row = result['sheets']['검토'][0]
    assert row['A1']['value'] == '독도 근처'
    assert row['B1']['value'] == 'DRAFT'
    assert row['C1'] == {'value': '2', 'formula': '1+1'}
    assert result['import_grants_gold'] is False


def test_diagnostics_keep_missing_and_explicit_zero_distinct():
    assert plan_checks('PILOT_Q4_01', None)[0]['status'] == 'UNAVAILABLE'
    checks = plan_checks('PILOT_Q4_01', {'radius_m': 0, 'spatial_relation': 'dwithin'})
    assert checks[1]['status'] == 'REVIEW_REQUIRED'
    checks = plan_checks('PILOT_Q1_03', {'spatial_relation': 'none', 'radius_m': None, 'location_text': None})
    assert all(c['status'] == 'MATCH' for c in checks)
    assert plan_checks('PILOT_Q1_03', {})[0]['status'] == 'REVIEW_REQUIRED'
    # A matching narrow slot check is never a semantic/execution success flag.
    assert all('semantic_correct' not in c for c in checks)


def test_duplicate_case_rejected():
    with pytest.raises(ValueError, match='Duplicate'):
        index_cases([{'사례 ID': 'x'}, {'사례 ID': 'x'}])


def test_source_hash_query_and_approval_validation():
    def workbook(name, headers, rows, digest):
        def cells(values, n):
            return {f'{chr(65+i)}{n}': {'value': value, 'formula': None} for i, value in enumerate(values)}
        return {'sha256': digest, 'sheets': {name: [cells(headers, 1)] + [cells(r, i+2) for i, r in enumerate(rows)]}}
    rows = [[str(i), f'질문{i}'] for i in range(18)]
    a = workbook('검수작성', ['사례 ID', '원문 질의'], rows, 'A')
    b = workbook('AI 검토안', ['사례 ID', '원문 질의'], rows, 'B')
    c = workbook('합의작성', ['사례 ID', '원문 질의', 'A 제출파일 SHA256', 'B 제출파일 SHA256', '상태(유지)', '수동 승인 기록'],
                 [r + ['A', 'B', 'DRAFT', 'human_approval=false'] for r in rows], 'C')
    cases = {r[0]: {'query': r[1]} for r in rows}
    assert len(validate_sources(c, a, b, cases)[0]) == 18
    wrong = copy.deepcopy(a)
    wrong['sha256'] = 'wrong'
    with pytest.raises(ValueError, match='hash mismatch'):
        validate_sources(c, wrong, b, cases)
    wrong_cases = copy.deepcopy(cases)
    wrong_cases['0']['query'] = 'changed'
    with pytest.raises(ValueError, match='query mismatch'):
        validate_sources(c, a, b, wrong_cases)
    c['sheets']['합의작성'][1]['E2']['value'] = 'GOLD'
    with pytest.raises(ValueError, match='Approval changed'):
        validate_sources(c, a, b, cases)
