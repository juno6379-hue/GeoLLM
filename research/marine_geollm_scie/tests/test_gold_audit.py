import json

from research.marine_geollm_scie.runners.gold_audit import audit, approval_eligible, component_coverage


def approved():
    return {'case_id':'x','annotation_status':'GOLD','annotator_ids':['human_a','human_b'],
            'adjudication_status':'APPROVED','human_approval':True}


def test_ai_or_draft_never_approved():
    row=approved()
    assert approval_eligible(row)
    for changes in ({'annotation_status':'DRAFT'},{'human_approval':False},
                    {'review_kind':'AI_PRE_REVIEW'},{'annotator_ids':['AI_REVIEWER_A']}):
        assert not approval_eligible({**row,**changes})
    del row['human_approval']
    assert not approval_eligible(row)


def test_valid_empty_requires_snapshot_and_independent_oracle():
    row={'spatial_oracle':{'expected_object_ids':[],'snapshot_sha256':'sourcehash','reference_query':'reviewed SQL'}}
    assert component_coverage(row)['spatial']
    del row['spatial_oracle']['reference_query']
    assert not component_coverage(row)['spatial']
    row['spatial_oracle']['expected_object_ids']=None
    assert not component_coverage(row)['spatial']


def test_audit_preserves_source_and_deduplicates_cases(tmp_path):
    row={**approved(),'semantics':{'intent':'definition'},'qec_fields':{'slots':{'operation':'definition_lookup'}}}
    p=tmp_path/'gold_semantics.jsonl';p.write_text(json.dumps(row)+'\n',encoding='utf-8')
    q=tmp_path/'annotations_copy.jsonl';q.write_bytes(p.read_bytes())
    before=p.read_bytes()
    result=audit([tmp_path])
    assert p.read_bytes()==before
    assert result['components']['semantic']['eligible_unique_cases']==1
    assert result['components']['spatial']['eligible_unique_cases']==0
    assert result['gold_modified'] is False


def test_empty_files_and_malformed_are_not_ready(tmp_path):
    (tmp_path/'gold_empty.jsonl').write_text('',encoding='utf-8')
    (tmp_path/'gold_bad.jsonl').write_text('{broken',encoding='utf-8')
    result=audit([tmp_path])
    assert all(c['eligible_unique_cases']==0 for c in result['components'].values())
    assert any(f['status']=='UNREADABLE' for f in result['files'])


def test_rq_evaluator_schema_compatibility():
    from research.marine_geollm_scie.evaluation.rq_metrics import derive
    gold={**approved(), 'gold_sha256':'fixture',
          'semantics':{'labels':['Wreck'],'label_set_is_complete_semantic_contract':False},
          'qec_fields':{'slots.distance_m':5000},
          'spatial':{'object_ids':[],'dataset_snapshot_sha256':'snapshot','oracle_sha256':'oracle'},
          'evidence':{'required_refs':['fc#Wreck']}}
    assert all(component_coverage(gold)[key] for key in ('semantic','qec','spatial','evidence'))
    result=derive({'predicted_semantics':{'labels':['Wreck']},'predicted_qec':{'slots':{'distance_m':5000}},
                   'returned_object_ids':[],'dataset_snapshot_sha256':'snapshot','verified_evidence_refs':['fc#Wreck']},gold)
    assert result['semantic_label_exact'] and result['spatial_correct']
    assert result['semantic_correct'] is None


def test_user_approval_does_not_become_independent_expert(tmp_path):
    row={**approved(),'review_kind':'USER_APPROVED_AI_ASSISTED','independent_expert_review':False,
         'annotator_ids':['USER_APPROVAL'],'qec_fields':{'slots.distance_m':5000}}
    (tmp_path/'annotations_approved.jsonl').write_text(json.dumps(row)+'\n',encoding='utf-8')
    result=audit([tmp_path])
    assert result['approval_cohorts_unique_cases']['user_approved_ai_assisted']==1
    assert result['approval_cohorts_unique_cases']['independent_expert_explicit']==0
