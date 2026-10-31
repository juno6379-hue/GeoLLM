"""Freeze shared GOLD v2 references after independent oracle checks.

This is an evaluation artifact, never a retrieval packet or runtime import.
User-approved scope is separate from independent expert review.
"""
import argparse
import copy
import json
from pathlib import Path
from .gold_v2_oracle_audit import ROOT, sha, write


def build(audit, output):
    audit, output = Path(audit), Path(output)
    summary = json.loads((audit/'summary.json').read_text(encoding='utf-8'))
    if summary.get('canonical_boundary_id') != 1137770 or summary.get('harbour_polygon_checks_agree') is not True:
        raise ValueError('Independent canonical-boundary oracle checks must pass')
    if not all(r['matches'] for r in summary['source_checks']):
        raise ValueError('Snapshot digest mismatch')
    objects = json.loads((audit/'source_observations.json').read_text(encoding='utf-8'))
    harbour = json.loads((audit/'harbour_candidate_sets.json').read_text(encoding='utf-8'))
    boundary = harbour['boundary_records'][0]
    source_hash = next(r['actual_sha256'] for r in summary['source_checks'] if r['relation'].startswith('projection.'))
    parent = ROOT/'research/marine_geollm_scie/benchmark/frozen_v5/answer_contracts.jsonl'
    rows = [json.loads(line) for line in parent.read_text(encoding='utf-8').splitlines() if line.strip()]
    boundary_reference = {k:boundary[k] for k in ('id','dataset_id','dataset_version_id','dataset_name','min_scale','max_scale','srid','product_specification','geometry_ewkb')}
    import hashlib
    boundary_reference.update(geometry_sha256=hashlib.sha256(bytes.fromhex(boundary['geometry_ewkb'])).hexdigest(),
        dataset_snapshot_sha256=source_hash,layer_name='projection.s101_feature_current/HarbourAreaAdministrative',
        boundary_source='snapshot S-101 feature, not independently verified legal full-port boundary',
        selection_policy='single exact-name polygon, most detailed min_scale, full 2km extent inside snapshot bbox, largest area then smallest feature ID',
        coverage_bbox=[128.9,34.9,129.3,35.3],coverage_boundary_margin_m=4561.66668103,
        selection_status='FIXED_RESEARCH_REFERENCE_UNDER_USER_SINGLE_POLYGON_POLICY')
    for row in rows:
        cid = row['case_id']
        row['gold_version']='GOLD_v2_20261031'
        row['parent_contract_sha256']=sha(parent)
        row['independent_expert_review_complete']=False
        row['coverage_reference']={'snapshot_manifest_sha256':summary['snapshot_manifest_sha256'],
            'source_relation_sha256':{r['relation']:r['actual_sha256'] for r in summary['source_checks']}}
        row['evaluation_stratum']='SOURCE_BOUND_DOCUMENT_OR_EXISTING_Q4'
        if cid in ('PILOT_Q3_01','PILOT_Q5_01','PILOT_Q5_03'):
            targets = ['Lighthouse','Wreck'] if cid.endswith('Q5_01') else ['Lighthouse'] if cid.endswith('Q3_01') else ['Wreck']
            row['evaluation_stratum']='OUT_OF_COVERAGE_SAFE_ABSTENTION'
            row['spatial_gold']=None
            row['spatial_correctness_applicable']=False
            row['execution_correctness_gap_applicable']=False
            row['expected_spatial_behavior']={'accepted_states':['BLOCKED_DATA','DATA_OUT_OF_SCOPE'],
                'required_disclosure':'Current connected snapshot cannot determine the answer for the requested spatial extent',
                'per_target':{t:{'status':'BLOCKED_DATA','object_ids':None} for t in targets},
                'empty_result_as_answer_forbidden':True,'claim_spatial_success_forbidden':True}
            row['optional_document_task']={'allowed_status':'PARTIAL_RESPONSE',
                'source_bound_definitions_and_attributes_allowed':True,
                'invent_instance_values_forbidden':True,'spatial_full_success':False}
            row['old_machine_checks_not_applicable']=row.pop('machine_checks',[])
            row['machine_checks']=[]
            row['spatial_condition']='KNOWN_OUT_OF_COVERAGE_NO_SPATIAL_OBJECT_GOLD'
            row['scope_notes']=['User-approved source-bound safe abstention; document explanations are separately evaluated optional partial output.']
            row['required_output_fields']=['spatial_tasks','source_coverage','execution_observation']
            row['oracle_status']='VERIFIED_SOURCE_SCOPE_ABSTENTION'
            row['scope_frozen']=True
        elif cid=='PILOT_Q3_03':
            behavior=json.loads((ROOT/'research/marine_geollm_scie/benchmark/q303_behavior_v1.json').read_text(encoding='utf-8'))
            row.update({k:copy.deepcopy(behavior[k]) for k in ('semantic_gold','qec_gold','expected_behavior','blocker','execution_gold','machine_checks')})
            row.update(evaluation_stratum='MISSING_REQUIRED_INPUT',spatial_gold=None,
                spatial_correctness_applicable=False,oracle_status='VERIFIED_BEHAVIOR_CONTRACT',scope_frozen=True)
        elif cid in ('PILOT_Q3_02','PILOT_Q5_02'):
            targets=['AnchorageArea'] if cid.endswith('Q3_02') else ['AnchorageArea','RestrictedArea']
            predicate='harbour_covers' if cid.endswith('Q3_02') else 'harbour_2km'
            sets={t:[r for r in objects['features'] if r['feature']==t and r[predicate]] for t in targets}
            row.update(evaluation_stratum='IN_SNAPSHOT_SPATIAL',reference_geometry=boundary_reference,
                spatial_gold={t:{'object_ids':sorted(r['id'] for r in selected),
                    'objects':[{k:r[k] for k in ('id','feature','geometry_ewkb','attributes','dataset_name','dataset_version_id','harbour_distance_m')} for r in selected],
                    'source_snapshot_sha256':source_hash,'evidence_per_object_required':True} for t,selected in sets.items()},
                spatial_correctness_applicable=True,execution_correctness_gap_applicable=True,
                oracle_status='VERIFIED_SQL_GIS_SOURCE_BOUND',scope_frozen=True,
                spatial_predicate='ST_Covers(reference,target)' if cid.endswith('Q3_02') else 'ST_DWithin(target::geography,reference::geography,2000,true)',
                distance_mode='minimum polygon-area to target geometry distance; overlapping/inside=0',
                object_identity_policy='snapshot feature_instance_id, not inferred physical facilities',
                source_coverage_disclosure_required=True)
            row['old_machine_checks_not_applicable']=row.pop('machine_checks',[])
            row['machine_checks']=[]
            row['spatial_condition']='FIXED_SINGLE_SNAPSHOT_HARBOUR_POLYGON'
            row['scope_notes']=['Object IDs refer to frozen snapshot records, not deduplicated physical facilities or the whole legal port.']
            row['required_output_fields']=['spatial_tasks','source_coverage','execution_observation']
            if cid.endswith('Q5_02'):
                row['comparison_gold']={'counts':{t:len(s) for t,s in sets.items()},
                    'criteria':['per_type_object_count','per_type_minimum_and_maximum_distance_m','distinct_FC_feature_definitions','source_scope_and_reference_disclosure'],
                    'distance_ranges_m':{t:{'minimum':min((r['harbour_distance_m'] for r in s),default=None),
                        'maximum':max((r['harbour_distance_m'] for r in s),default=None)} for t,s in sets.items()},
                    'both_sets_and_comparison_required_for_full_success':True}
                row['comparison_gold']['distance_tolerance_m']=0.01
        else:
            row['oracle_status']='INHERITED_FROZEN_V5_REFERENCE'
            row['scope_frozen']=True
    output.mkdir(parents=True,exist_ok=False)
    contracts=output/'answer_contracts.jsonl'
    contracts.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    write(output/'canonical_busan_boundary.json',boundary_reference)
    manifest={'version':'GOLD_v2_20261031','status':'REFERENCES_FROZEN_EVALUATOR_INTEGRATION_REQUIRED',
        'count':len(rows),'contract_sha256':sha(contracts),'parent_contract_sha256':sha(parent),
        'oracle_audit_summary_sha256':sha(audit/'summary.json'),'oracle_query_sha256':sha(audit/'independent_queries.sql'),
        'snapshot_manifest_sha256':summary['snapshot_manifest_sha256'],
        'source_scope_authority':'User approved in-scope vs out-of-coverage partition on 2026-10-31',
        'independent_expert_review_complete':False,'all_evaluators_implemented':False,
        'all_eight_methods_validated':False,'model_comparison_ready':False,
        'canonical_boundary_sha256':sha(output/'canonical_busan_boundary.json'),
        'generator_sha256':sha(__file__),'old_raw_and_gold_preserved':True}
    write(output/'manifest.json',manifest)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audit',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(build(a.audit,a.output)))
