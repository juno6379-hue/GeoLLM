import copy
import pytest
from research.marine_geollm_scie.runners import report_rq3_methods as report

def fixture(monkeypatch):
    contracts=[{'case_id':cid,'equivalence_group':group,'evaluation_stratum':'IN_SNAPSHOT_SPATIAL','category':'fixture'}
               for cid,group in (('a','source-a'),('b','source-b'))]
    queries=[{'case_id':c['case_id'],'query':'query-'+c['case_id']} for c in contracts]
    rows=[];scores=[]
    for method in report.METHODS:
        for contract in contracts:
            cid=contract['case_id']
            rows.append({'method':method,'case_id':cid,'repeat':0,'query':'query-'+cid,'raw_artifact_sha256':'a'*64})
            scores.append({'method':method,'case_id':cid,'repeat':0,'equivalence_group':contract['equivalence_group'],
                'execution_correctness_gap_applicable':True,'execution_succeeded':False,'spatial_correctness':None,
                'checks':{},'stratum':'IN_SNAPSHOT_SPATIAL'})
    lookup={report.key(r):r for r in scores}
    monkeypatch.setattr(report,'score_row',lambda row,contract:lookup[report.key(row)])
    return rows,scores,contracts,queries

def test_zero_success_remains_null_in_table_and_ci(monkeypatch):
    rows,scores,contracts,queries=fixture(monkeypatch)
    result=report.build_cohort(rows,scores,contracts,queries,'b'*64,0)
    assert len(result['methods'])==8
    assert all(m['ESR']['value']==0 and m['ESR']['denominator']==2 for m in result['methods'].values())
    assert all(m['CGE']['value'] is None and m['SSFR']['value'] is None for m in result['methods'].values())
    assert result['paired_comparisons']['B3_vs_P1']['metrics']['SSFR']['ci95'] is None
    assert result['fault_diagnostic_rows_included']==0

def test_conditional_correctness_distinct_from_gap_and_shared_pairs(monkeypatch):
    rows,scores,contracts,queries=fixture(monkeypatch)
    for score in scores:
        if score['method'] in ('B3','P0','P1'):
            score.update(execution_succeeded=True,spatial_correctness=score['method']!='B3')
    result=report.build_cohort(rows,scores,contracts,queries,'b'*64,0)
    assert result['methods']['B3']['CGE']['value']==0
    assert result['methods']['B3']['execution_correctness_gap']==1
    assert result['methods']['P0']['CGE']['value']==1
    assert result['methods']['P0']['execution_correctness_gap']==0
    paired=result['paired_comparisons']['B3_vs_P0']['metrics']
    assert paired['Spatial_Correct']['difference_B_minus_A']==1 and paired['Spatial_Correct']['ci95']==[1,1]
    assert paired['execution_correctness_gap']['difference_B_minus_A']==-1

@pytest.mark.parametrize('mutation',['query','eligibility','equivalence','missing','duplicate'])
def test_common_identity_cannot_change_by_method(monkeypatch,mutation):
    rows,scores,contracts,queries=fixture(monkeypatch)
    if mutation=='query':rows[0]['query']='different'
    if mutation=='eligibility':scores[0]['execution_correctness_gap_applicable']=False
    if mutation=='equivalence':scores[0]['equivalence_group']='different'
    if mutation=='missing':rows.pop()
    if mutation=='duplicate':rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(ValueError):report.build_cohort(rows,scores,contracts,queries,'b'*64,0)

def test_scores_must_reproduce_from_raw(monkeypatch):
    rows,scores,contracts,queries=fixture(monkeypatch)
    old=report.score_row
    monkeypatch.setattr(report,'score_row',lambda row,contract:dict(old(row,contract),spatial_correctness=True))
    with pytest.raises(ValueError,match='not reproduced'):report.build_cohort(rows,scores,contracts,queries,'b'*64,0)
