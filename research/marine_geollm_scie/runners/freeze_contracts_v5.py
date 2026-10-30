"""Finalize bounded task/output contracts under user direction, without invented spatial truth."""
import argparse
import json
from pathlib import Path
from research.marine_geollm_scie.runners.build_contracts_v4 import ROOT, BASE, REFERENCE, sha

V4=BASE/'benchmark/contracts_v4'
STATUS='AGENT_FINALIZED_UNDER_USER_DIRECTION'
PRIMARY={
 'Q1_01':['Landmark','Building','LightAllAround','LightSectored'],
 'Q1_02':['AnchorageArea'],'Q1_03':['Wreck'],
 'Q2_01':['Landmark','Building','LightAllAround','LightSectored'],
 'Q2_02':['RestrictedArea'],'Q2_03':['Wreck'],
 'Q6_01':['Wreck'],
 'Q6_02':['Landmark','Building','LightAllAround','LightSectored','LateralBuoy'],
 'Q6_03':['AnchorageArea'],
 'Q5_01':['Landmark','Building','LightAllAround','LightSectored','Wreck'],
 'Q5_02':['AnchorageArea','RestrictedArea'], 'Q5_03':['Wreck'],
}


def load(path):return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]


def build():
    refs={r['case_id']:r for r in load(REFERENCE)}
    contracts=load(V4/'task_contracts_DRAFT.jsonl')
    evidence={r['case_id']:r for r in load(V4/'evidence_reference_candidates.jsonl')}
    manifest=json.loads((V4/'evidence_manifest.json').read_text(encoding='utf-8'))
    if sha((V4/'evidence_reference_candidates.jsonl').read_bytes())!=manifest['candidate_sha256']:
        raise ValueError('FC candidate bytes changed')
    first=next(iter(evidence.values()))
    if sha((ROOT/first['fc_metadata']['source']).read_bytes())!=first['xml_sha256']:
        raise ValueError('FC source changed since verification')
    output=[]
    for c in contracts:
        cid=c['case_id'];key=cid.removeprefix('PILOT_');r=refs[cid]
        obligations=[x['obligation_id'] for x in c['task_obligations']]
        row={'case_id':cid,'query':r['query'],'category':r['category'],'equivalence_group':r['equivalence_group'],
             'contract_version':'frozen_v5','finalization_status':STATUS,'annotation_status':'AGENT_FINALIZED',
             'human_approval':False,'independent_human_review':False,'independent_expert_review':False,
             'source_v3_user_approval':True,'holdout_eligible':False,'post_hoc':True,
             'required_task_obligations':obligations,'required_qec_fields':r['qec_fields'],
             'single_intent_match_is_sufficient':False,'acceptable_capability_combinations':c['acceptable_capability_combinations'],
             'capability_id_exact_match_required':False,
             'forbidden_substitutions':['intent_label_for_task_completion','registry_hit_for_factual_authority',
                 'plan_json_for_execution_result','unexecuted_search_for_zero_objects','partial_result_for_full_completion'],
             'machine_checks':[],'required_output_fields':[],
             'spatial_reference':r['spatial'],'spatial_object_scoring_enabled':r['spatial'] is not None,
             'source_provenance':{'approved_v3_sha256':sha(REFERENCE.read_bytes()),
                 'v4_contracts_sha256':sha((V4/'task_contracts_DRAFT.jsonl').read_bytes()),
                 'fc_candidates_sha256':manifest['candidate_sha256'],'v4_case_id':cid},
             'scope_notes':[], 'complete_semantic_accuracy_claim_allowed':False}
        for combination in row['acceptable_capability_combinations']:
            combination['status']='FINALIZED_ACCEPTABLE_CANDIDATE_NOT_EXECUTION_PROOF'
        row['capability_combination_policy']='Illustrative candidates; equivalent implementations satisfying task/output contracts are allowed. Runtime availability still requires verification.'
        if key in PRIMARY:
            e=evidence.get(cid,evidence['PILOT_Q2_03'])
            objects={o['code']:o for source in evidence.values() for o in source['source_backed_claims']}
            primary=[objects[code] for code in PRIMARY[key]]
            row['required_output_fields']+=['document_answer.features','document_answer.evidence']
            row['document_scope']={'selected_feature_codes':PRIMARY[key],
                 'features':[{'code':o['code'],'definition':o['definition'],
                              'permitted_primitives':o['permitted_primitives'],'locator':o['locator']} for o in primary],
                 'definition_policy':'Source-equivalent paraphrase accepted by substantive review; exact-text agreement is a separate transcription check, not semantic accuracy.',
                 'evidence_requirements':{'edition':e['fc_metadata']['versionNumber'],'source_sha256':e['xml_sha256'],
                     'source_path':e['fc_metadata']['source'],'locators':[o['locator'] for o in primary],
                     'claim_source_links_required':True,'DCEG_required':False},
                 'attribute_scope':None}
            row['machine_checks'] += [
                 {'id':'required_feature_codes','kind':'set_inclusion','expected':PRIMARY[key],'field':'document_answer.features[].code'},
                 {'id':'feature_geometry','kind':'per_feature_set_equality','expected':{o['code']:o['permitted_primitives'] for o in primary},'field':'document_answer.features[].permitted_primitives'},
                 {'id':'definitions_present','kind':'nonempty_per_feature','field':'document_answer.features[].definition','expected_codes':PRIMARY[key]},
                 {'id':'source_binding','kind':'edition_hash_locator_match','field':'document_answer.evidence','expected':row['document_scope']['evidence_requirements']}]
            if key.startswith('Q2') or key=='Q5_03':
                roots=PRIMARY[key]; wanted=None
                if key=='Q2_01':wanted={'colour','sectorCharacteristics','lightSector'}
                if key=='Q2_02':wanted={'restriction','categoryOfRestrictedArea'}
                entries=[];queue=list(roots);seen=set()
                while queue:
                    code=queue.pop(0)
                    if code in seen:continue
                    seen.add(code)
                    for b in objects[code]['bindings']:
                        for target in b['references']:
                            if target['type']!='attribute':continue
                            attr=target['ref']
                            if wanted is not None and attr not in wanted:continue
                            a=objects[attr]
                            entry={'owner':code,'attribute':attr,'lower':b['lower'],'upper':b['upper'],
                                   'unbounded':b['unbounded'],'permitted_values':b['permitted_values'],
                                   'attribute_definition':a['definition'],'global_listed_values':a['listed_values'],
                                   'owner_locator':objects[code]['locator'],'attribute_locator':a['locator']}
                            entries.append(entry)
                            if wanted is not None and a['bindings']:queue.append(attr)
                row['document_scope']['attribute_scope']={'mode':'FEATURE_DIRECT_BINDINGS' if key in ('Q2_03','Q5_03') else 'EXPLICIT_ATTRIBUTE_PATHS',
                    'bindings':entries,'global_enumeration_is_not_binding_permission':True,
                    'empty_permitted_values_means':'No explicit binding-level permitted-values restriction; not an empty global codelist.',
                    'object_instance_values_required':False}
                row['machine_checks'].append({'id':'attribute_binding_contract','kind':'exact_structured_bindings','field':'document_answer.attribute_bindings','expected':entries})
                row['required_output_fields'].append('document_answer.attribute_bindings')
            if key in ('Q1_01','Q2_01','Q6_02'):
                row['scope_notes'].append('Landmark/Building describe conditional structure alternatives; LightAllAround/LightSectored describe light alternatives. Listing these for explanation does not assert all must exist in one physical lighthouse.')
                row['forbidden_substitutions']+=['single_Lighthouse_feature_assertion','global_colour_codes_for_feature_binding']
            if key=='Q6_02':row['scope_notes'].append('Bounded comparison: LateralBuoy is the explicitly selected representative floating-aid feature; no claim to exhaustively describe every buoy class. Compare with conditional structure/light models.')
            if key=='Q6_01':row['machine_checks'].append({'id':'requested_verbatim_definition','kind':'exact_value','field':'document_answer.definition_quote','expected':objects['Wreck']['definition']})
            if key=='Q2_02':row['scope_notes'].append('Explain restriction codes separately from categoryOfRestrictedArea. RequiredArea alternatives from another FC edition are not substitutes for FC 2.0.0 RestrictedArea.')
        else:
            row['document_scope']=None
        if r['category'] in ('Q3','Q4','Q5'):
            row['required_output_fields']+=['spatial_status','source_coverage','execution_status']
            row['forbidden_substitutions']+=['invented_AOI','invented_snapshot_or_object_ID','unsupported_zero_object_claim']
            if r['spatial']:
                row['spatial_condition']='FIXED_USER_APPROVED_Q4_REFERENCE'
                row['required_output_fields']+=['returned_object_ids','dataset_snapshot_sha256','oracle_sha256']
                row['machine_checks'].append({'id':'spatial_objects','kind':'source_bound_set_equality',
                    'field':'returned_object_ids','expected':r['spatial']['object_ids'],
                    'dataset_snapshot_sha256':r['spatial']['dataset_snapshot_sha256'],'oracle_sha256':r['spatial']['oracle_sha256']})
            elif key=='Q3_03':
                row['spatial_condition']='SELECTED_AOI_NOT_SUPPLIED'
                row['machine_checks'] += [{'id':'request_missing_aoi','kind':'exact_value','field':'execution_status','expected':'NEEDS_USER_INPUT'},
                    {'id':'no_execution_without_aoi','kind':'exact_value','field':'search_executed','expected':False}]
                row['required_output_fields']+=['clarification_request','search_executed']
                row['scope_notes'].append('No selected geometry is provided by this benchmark input; an arbitrary viewport is not a substitute.')
            else:
                row['spatial_condition']='REFERENCE_GEOMETRY_OR_COVERAGE_UNVERIFIED'
                row['machine_checks'].append({'id':'unverified_scope_disclosed','kind':'required_structured_disclosure',
                    'field':'source_coverage','expected':{'benchmark_oracle_available':False,'unverified_conditions_must_be_listed':True}})
                row['scope_notes'].append('Evaluate disclosure/verification behavior separately; no expected object set exists. Runtime may establish geometry/coverage with verifiable evidence, but its returned IDs are not correctness GOLD.')
            if r['category']=='Q5':
                row['required_output_fields']+=['per_task_status','partial_completion_reasons']
                row['machine_checks'].append({'id':'composite_status_complete','kind':'per_obligation_status','field':'per_task_status','expected_obligations':obligations})
                row['scope_notes'].append('All requested tasks need separate status. Document explanation may be provided when spatial execution is blocked; this is partial completion.')
        row['score_reporting_policy']={'components_separate':True,'missing_field_is_failure_for_applicable_contract_check':True,
             'unsupported_metric_is_null':True,'text_presence_is_not_meaning_correctness':True,
             'no_spatial_oracle_means_no_spatial_accuracy':r['spatial'] is None,
             'no_aggregate_full_semantic_accuracy_without_substantive_review':True}
        output.append(row)
    validate(output)
    return output


def validate(rows):
    if len(rows)!=18 or len({r['case_id'] for r in rows})!=18:raise ValueError('18 unique cases required')
    for r in rows:
        if r['finalization_status']!=STATUS or r['human_approval'] or r['independent_human_review']:raise ValueError('Misrepresented authority')
        if r['spatial_object_scoring_enabled']!=(r['category']=='Q4'):raise ValueError('Only Q4 has verified spatial oracle')
        if not r['required_task_obligations'] or not r['machine_checks']:raise ValueError('Incomplete finalized contract')


def run(output):
    rows=build();output.mkdir(parents=True,exist_ok=False)
    data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows).encode('utf-8')
    (output/'answer_contracts.jsonl').write_bytes(data)
    manifest={'status':STATUS,'count':18,'independent_human_review':False,'source_v3_preserved':True,'source_v4_preserved':True,
        'contract_sha256':sha(data),'generator_sha256':sha(Path(__file__).read_bytes()),
        'reference_sha256':sha(REFERENCE.read_bytes()),'model_results_read':False,
        'authority':'User directed agent to finalize answer scope; this is not independent human GOLD.'}
    (output/'manifest.json').write_bytes(json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    lines=['# 사용자 지시 아래 확정한 답안 범위 v5','','상태: AGENT_FINALIZED_UNDER_USER_DIRECTION. 독립 인간 검수 아님. v3 사용자 승인 원문과 v4 초안은 보존한다. 단일 intent 일치를 정답으로 사용하지 않는다.','','| 사례 | 질의 | 문서 범위 | 공간 평가 범위 | 필수 작업 수 |','|---|---|---|---|---|']
    for r in rows:
        doc=r['document_scope'];fields=[r['case_id'],r['query'],', '.join(doc['selected_feature_codes']) if doc else '개별 과업 상태와 가용 근거',r.get('spatial_condition','비공간'),str(len(r['required_task_obligations']))]
        lines.append('| '+' | '.join(f.replace('|','\\|') for f in fields)+' |')
    lines+=['','정의: code·정의·허용기하, 속성: FC 직접 binding/명시 경로·다중도·binding 허용값, 인용: edition·원문 hash·locator. 설명의 존재와 의미 정확도를 구분한다. Q4만 실제 ID 정확도, Q3_03은 AOI 확인, 그 외 공간 질의는 미검증 조건 고지·검증 행동을 평가한다.','',
            'LateralBuoy는 부표 전체를 대신하는 완전 분류가 아니라 비교용 대표 Feature로 명시했다. 등대 구조/등화 후보의 설명 요구는 모든 유형이 한 시설에 존재해야 한다는 의미가 아니다. Q5는 공간 결과와 설명/비교/근거 과업의 상태를 각각 내야 한다.']
    (output/'답안범위_KR.md').write_bytes(('\n'.join(lines)+'\n').encode('utf-8'))
    (output/'.gitattributes').write_bytes(b'* -text -working-tree-encoding\n')
    print(json.dumps(manifest))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);run(p.parse_args().output)
