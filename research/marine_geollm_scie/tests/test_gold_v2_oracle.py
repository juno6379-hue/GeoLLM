from research.marine_geollm_scie.runners.gold_v2_gate import comparison_gate, replay_decision, METHODS
from research.marine_geollm_scie.runners.gold_v2_oracle_audit import instance_links
from research.marine_geollm_scie.runners.extract_fc_reference_candidates import catalogue


def test_instance_value_link_is_not_fc_definition_only():
    result=instance_links({'waterLevelEffect':'3','unknownTestAttribute':'7'},'Wreck',catalogue())
    link=next(x for x in result['linked'] if x['attribute']=='waterLevelEffect')
    assert link['object_value']=='3'
    assert link['definition'] and link['fc_locator'] and link['fc_sha256']
    assert link['listed_value']['value']=='3'
    assert result['unresolved'][0]['attribute']=='unknownTestAttribute'


def test_empty_objects_cannot_supply_attribute_values():
    assert instance_links({},'Wreck',catalogue()) == {'linked':[],'unresolved':[]}


def valid_gate_input():
    cases=[{'case_id':f'PILOT_Q{g}_{c:02}','oracle_status':'VERIFIED','scope_frozen':True}
           for g in range(1,7) for c in range(1,4)]
    methods={name:{'adapter_validated':True,'gold_manifest_sha256':'a'*64,
             'input_condition_sha256':'same','domain_tools_enabled':name!='B0',
             'execution_observation_validated':True} for name in METHODS}
    return cases,methods


def test_gate_rejects_unready_oracle_tool_using_direct_llm_and_missing_method():
    cases,methods=valid_gate_input()
    assert comparison_gate(cases,methods,'a'*64)['ready']
    cases[0]['oracle_status']='CANDIDATE'
    methods['B0']['domain_tools_enabled']=True
    del methods['H']
    result=comparison_gate(cases,methods,'a'*64)
    assert not result['ready']
    assert {'EIGHT_DISTINCT_METHODS_REQUIRED','B0_IS_NOT_DIRECT_LLM','ORACLE_NOT_READY:PILOT_Q1_01'} <= set(result['errors'])


def test_only_rubric_changes_allow_replay_and_missing_logs_remain_unknown():
    identity={k:'frozen' for k in ('system_source_sha256','adapter_sha256','model_profile_sha256',
        'source_snapshot_sha256','benchmark_inputs_sha256','method_definitions_sha256')}
    assert replay_decision(identity,dict(identity,gold='v2'),required_observations_present=True)['action']=='RESCORE_IMMUTABLE_RAW'
    assert replay_decision(identity,identity,required_observations_present=False)['action']=='NEW_OBSERVATIONS_REQUIRED'
    assert replay_decision(identity,dict(identity,system_source_sha256='new'),required_observations_present=True)['action']=='FULL_BENCHMARK_RERUN'
