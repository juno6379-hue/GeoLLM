import json
from research.marine_geollm_scie.runners.comparison_report import summarize, report_comparison


def test_schema_missing_and_plan_object_are_different():
    result=summarize([{'case_id':'a','method':'B0','plan':{},'status':'error'},
                      {'case_id':'b','method':'B0','plan':None,'schema_valid':False,'status':'timeout'}])[0]
    assert result['plan_objects']==1
    assert result['schema_unmeasured']==1
    assert result['schema_pass_rate_all_rows'] is None
    assert result['error_rows']==1 and result['timeout_rows']==1
    assert result['accuracy'] is None and result['evqsr'] is None


def test_observable_metrics_keep_missingness_and_repeats():
    rows=[{'case_id':'a','method':'B4','model':'qwen','schema_valid':True,'plan':{'needs_clarification':False,'actions':['lookup']},'latency_ms':12,'input_tokens':None},
          {'case_id':'a','method':'B4','model':'qwen','schema_valid':True,'plan':{'needs_clarification':True,'actions':[{'action':'clarify'}]},'latency_ms':20,'input_tokens':10}]
    result=summarize(rows)[0]
    assert result['distinct_cases']==1 and result['rows']==2
    assert result['planned_llm_calls_per_trial']==2
    assert result['llm_call_count_measured']==0
    assert result['input_tokens_missing']==1
    assert result['latency_ms_p50']==16
    assert result['unique_emitted_actions']==2


def test_report_is_summary_only(tmp_path):
    (tmp_path/'manifest.json').write_text('{}')
    row={'case_id':'a','method':'B1','raw_response':'RAW_PRIVATE_SENTINEL','status':'COMPLETED','plan':None}
    (tmp_path/'comparison_rows.jsonl').write_text(json.dumps(row)+'\n')
    result=report_comparison(tmp_path,publish_latest=False)
    assert result['rows']==1
    for path in (tmp_path/'reports').iterdir():
        assert b'RAW_PRIVATE_SENTINEL' not in path.read_bytes()
    assert (tmp_path/'reports'/'comparison_report_KR.md').exists()


def test_actual_plan_schema_actions_and_tools():
    row={'method':'B3','case_id':'a','schema_valid':True,'plan':{'action':'search','tool_calls':[{'tool_id':'spatial.search','arguments':{}}]}}
    result=summarize([row])[0]
    assert result['clarify_false']==1
    assert result['unique_emitted_actions']==1
    assert result['unique_emitted_tool_ids']==1
    assert result['schema_pass_rate_all_rows']==1


def test_model_calls_alias():
    result=summarize([{'case_id':'a','method':'B4','model_calls':2}])[0]
    assert result['llm_call_count_mean']==2
    assert result['llm_call_count_measured']==1


def test_latest_only_completed_and_manifest_preserved(tmp_path,monkeypatch):
    import research.marine_geollm_scie.runners.comparison_report as module
    monkeypatch.setattr(module,'RESEARCH',tmp_path)
    run=tmp_path/'run'; run.mkdir()
    manifest={'status':'RUNNING','generation_budget':{'B4':{'calls':2}}}
    (run/'manifest.json').write_text(json.dumps(manifest))
    (run/'comparison_rows.jsonl').write_text(json.dumps({'case_id':'a','method':'B4','status':'error'})+'\n')
    result=module.report_comparison(run)
    assert not (tmp_path/'latest_comparison').exists()
    assert result['budget_notes']['declared_run_budget']==manifest['generation_budget']
    manifest['status']='COMPLETED'
    (run/'manifest.json').write_text(json.dumps(manifest))
    module.report_comparison(run)
    latest=tmp_path/'latest_comparison'
    assert json.loads((latest/'manifest.json').read_text())==manifest
    assert (latest/'D2_comparison_observables.png').exists()
    assert not (latest/'comparison_rows.jsonl').exists()


def test_query_candidate_report_is_not_gold(tmp_path):
    from research.marine_geollm_scie.runners.comparison_report import build_query_comparison
    rows=[{'case_id':'a','query':'예시 질의','method':'B4','repeat':0,'status':'COMPLETED',
        'first_plan':{'action':'clarify'},'plan':{'action':'search','answer':'abcdefghij','evidence_refs':['known','unknown']}}]
    build_query_comparison(tmp_path,rows,source_packet={'known':{}},answer_max_chars=3)
    text=(tmp_path/'query_comparison_KR.md').read_text(encoding='utf-8')
    assert '미검증 후보' in text and '처음 3자만' in text
    assert '식별자 연결 확인' in text and '확인하지 못함' in text
    assert '변경 필드' in text and 'action' in text
    assert 'abcdefghij' not in text


def test_coverage_and_prompt_trace_use_actual_inputs(tmp_path):
    import csv
    import hashlib
    from research.marine_geollm_scie.runners.comparison_report import sample_coverage, write_prompt_trace
    cases=[{'case_id':str(i),'language':'en' if i<5 else 'ko_formal','category':'Q'+str(i+1),'equivalence_group':str(i)} for i in range(6)]
    case_path=tmp_path/'cases.json'; case_path.write_text(json.dumps(cases))
    coverage=sample_coverage(case_path)
    assert coverage['language_counts']=={'en':5,'ko_formal':1}
    assert coverage['case_count']==6 and len(coverage['equivalence_group_counts'])==6
    rows=[{'case_id':'a','method':'B4','repeat':0,'calls':[{'prompt':'PRIVATE PROMPT'},{'prompt':None}]}]
    raw=tmp_path/'raw.jsonl'; raw.write_text(json.dumps(rows[0])+'\n')
    write_prompt_trace(tmp_path,rows,raw)
    index=tmp_path/'prompt_trace_index.csv'
    records=list(csv.DictReader(index.open(encoding='utf-8-sig')))
    assert records[0]['prompt_sha256']==hashlib.sha256(b'PRIVATE PROMPT').hexdigest()
    assert records[1]['trace_status']=='MISSING_PROMPT'
    assert records[0]['jsonl_record_number']=='1' and records[1]['call_index_zero_based']=='1'
    assert 'PRIVATE PROMPT' not in index.read_text(encoding='utf-8-sig')


def test_provenance_is_explicitly_post_hoc_and_packet_based(tmp_path,monkeypatch):
    import research.marine_geollm_scie.runners.comparison_report as module
    monkeypatch.setattr(module.subprocess,'check_output',lambda *a,**k:'current-branch\n')
    manifest={'status':'RUNNING','plan_output_schema':{'b':2,'a':1}}
    path=tmp_path/'manifest.json'; path.write_text(json.dumps(manifest))
    original=path.read_bytes()
    packets={'c':{'B2':{'sources':[{'path':'does-not-exist','sha256':'recorded-source','nodes_path':'also-missing','nodes_sha256':'recorded-node'}]}}}
    result=module.write_provenance_audit(tmp_path,manifest,packets,path)
    assert path.read_bytes()==original
    assert result['audit_type']=='POST_HOC_PROVENANCE_AUDIT'
    assert result['branch_recorded_at_run'] is None
    assert result['current_branch_observed_at_audit']=='current-branch'
    assert result['packet_recorded_sources'][0]['sha256_recorded_in_packet']=='recorded-source'
    assert result['prompt_template_hash_status']=='NOT_RECORDED_AT_RUN'
    assert result['embedding']['status']=='NOT_USED'
