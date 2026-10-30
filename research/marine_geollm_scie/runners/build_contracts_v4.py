"""Build reviewable task contracts from approved prose; never promote new interpretations."""
import argparse
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'research/marine_geollm_scie'
REFERENCE = BASE / 'benchmark/approved_v3/evaluation_references.jsonl'
REGISTRY = ROOT / 'data/capability_registry.yaml'

# Explicit case-level proposals, not production keyword routing or model predictions.
SPECS = {
 'Q1_01': ('표준 유형·정의 설명', ['explain_structure_and_light_distinction', 'explain_conditional_feature_mapping'], 'document'),
 'Q1_02': ('정박구역 표준 정의', ['explain_anchorage_area_definition'], 'document'),
 'Q1_03': ('난파선 표준 정의', ['explain_wreck_definition'], 'document'),
 'Q2_01': ('등대 색상과 허용값', ['distinguish_structure_and_light_colour', 'explain_feature_bound_permitted_values'], 'document'),
 'Q2_02': ('제한 종류 코드', ['distinguish_restriction_and_area_category', 'explain_restriction_codes'], 'document'),
 'Q2_03': ('난파선 속성', ['explain_wreck_attribute_bindings'], 'document'),
 'Q3_01': ('가장 가까운 등대', ['resolve_reference', 'resolve_lighthouse_target_conditions', 'verify_coverage', 'find_nearest', 'report_objects_or_unresolved_reason'], 'nearest'),
 'Q3_02': ('부산항 영역 내 정박지', ['resolve_official_port_polygon', 'verify_coverage', 'search_within_polygon', 'report_objects_or_unresolved_reason'], 'polygon'),
 'Q3_03': ('선택 영역과 교차하는 난파선', ['require_selected_aoi', 'verify_coverage', 'search_intersections_if_aoi_available', 'request_aoi_when_missing'], 'intersection'),
 'Q4_01': ('독도 5km 해양지명', ['resolve_approved_anchor', 'search_fixed_gazetteer_5000m', 'report_source_bound_objects'], 'gazetteer'),
 'Q4_02': ('독도 5000m 해양지명', ['resolve_approved_anchor', 'search_fixed_gazetteer_5000m', 'report_source_bound_objects'], 'gazetteer'),
 'Q4_03': ('독도 5km 해양지명 영어', ['resolve_approved_anchor', 'search_fixed_gazetteer_5000m', 'report_source_bound_objects'], 'gazetteer'),
 'Q5_01': ('등대·난파선 복합조회와 근거', ['resolve_reference', 'resolve_lighthouse_target_conditions', 'verify_both_target_coverages', 'search_both_targets_5000m', 'provide_per_target_evidence', 'separate_partial_document_answer'], 'composite'),
 'Q5_02': ('정박지·제한구역 복합조회와 비교', ['resolve_reference', 'verify_both_target_coverages', 'search_both_targets_2000m', 'compare_target_results', 'disclose_subset_limitations'], 'composite'),
 'Q5_03': ('난파선 조회와 표준 속성 설명', ['resolve_reference', 'verify_coverage', 'search_wrecks_5000m', 'explain_s101_attributes', 'distinguish_object_values_from_standard_attributes', 'separate_partial_document_answer'], 'composite'),
 'Q6_01': ('난파선 원문·출처', ['provide_wreck_definition_text', 'cite_catalogue_edition_and_locator'], 'document'),
 'Q6_02': ('등대·부표 표준 비교근거', ['compare_fixed_structure_and_floating_aid_models', 'cite_comparison_evidence'], 'document'),
 'Q6_03': ('정박구역 정의 출처', ['provide_anchorage_definition_source', 'cite_catalogue_edition_and_locator'], 'document'),
}
COMBINATIONS = {
 'document': [['resolver.s101_feature_dictionary', 'tool.graph_scoped_rag']],
 'nearest': [['resolver.place_registry', 'resolver.s101_feature_dictionary', 'agent.spatial_analysis']],
 'polygon': [['resolver.place_registry', 'resolver.s101_feature_dictionary', 'agent.spatial_analysis']],
 'intersection': [['resolver.s101_feature_dictionary', 'agent.spatial_analysis']],
 'gazetteer': [['resolver.place_registry', 'resolver.marine_gazetteer_spatial', 'tool.spatial_radius_search']],
 'composite': [['resolver.place_registry', 'resolver.s101_feature_dictionary', 'tool.spatial_radius_search', 'tool.graph_scoped_rag']],
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def provenance(path, digest, case_id, pointer, value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)
    return {'source_path': str(path), 'source_sha256': digest, 'case_id': case_id,
            'json_pointer': pointer, 'exact_text': text, 'text_sha256': sha(text.encode('utf-8')),
            'span_start': 0, 'span_end': len(text), 'span_unit': 'unicode_code_points',
            'serialization': 'original_string' if isinstance(value, str) else 'json_sorted_keys'}


def build(reference_path=REFERENCE, registry_path=REGISTRY):
    raw = reference_path.read_bytes(); digest = sha(raw)
    refs = [json.loads(s) for s in raw.decode('utf-8').splitlines() if s.strip()]
    registry_raw = registry_path.read_bytes(); registry = yaml.safe_load(registry_raw)
    caps = {c['capability_id']: (i, c) for i, c in enumerate(registry['capabilities'])}
    rows = []
    for ref in refs:
        cid = ref['case_id']; key = cid.removeprefix('PILOT_')
        title, tasks, kind = SPECS[key]
        if ref.get('human_approval') is not True or ref.get('annotation_status') != 'GOLD':
            raise ValueError('Approved input required; new output remains DRAFT')
        def p(pointer, value): return provenance(reference_path, digest, cid, pointer, value)
        source = {
            'query': p('/query', ref['query']),
            'semantics': p('/semantics/approved_reference_text', ref['semantics']['approved_reference_text']),
            'qec_original_text': p('/qec_original_text', ref['qec_original_text']),
            'qec_fields': p('/qec_fields', ref['qec_fields']),
            'evidence': p('/evidence/approved_reference_text', ref['evidence']['approved_reference_text']),
            'behavior': p('/expected_behavior_reference_text', ref['expected_behavior_reference_text']),
            'uncertainty': p('/uncertainties_preserved', ref['uncertainties_preserved']),
            'spatial': p('/spatial', ref['spatial']),
        }
        proposals = []
        for ids in COMBINATIONS[kind]:
            entries = []
            for cap_id in ids:
                index, c = caps[cap_id]
                entries.append({'capability_id': cap_id, 'registry_status': c.get('status'),
                                'runtime_availability': 'NOT_VERIFIED',
                                'provenance': provenance(registry_path, sha(registry_raw), cid,
                                                         f'/capabilities/{index}/description', c['description'])})
            proposals.append({'status': 'PROPOSED_NOT_APPROVED', 'all_of': entries,
                              'sufficient_for_execution': False})
        rows.append({
            'contract_version': 'v4_DRAFT', 'case_id': cid, 'query': ref['query'],
            'category': ref['category'], 'equivalence_group': ref['equivalence_group'],
            'title_ko': title, 'annotation_status': 'DRAFT', 'human_approval': False,
            'source_reference_version': 'user_approved_v3', 'source_human_approval': True,
            'post_hoc': True, 'holdout_eligible': False, 'evaluation_enabled': False,
            'source_provenance': source,
            'transcribed_approved_values': {
                'qec_fields': ref['qec_fields'], 'spatial': ref['spatial'],
                'expected_behavior': ref['expected_behavior'],
                'semantics_text': ref['semantics']['approved_reference_text'],
                'evidence_text': ref['evidence']['approved_reference_text'],
                'qec_original_text': ref['qec_original_text'],
                'transcription_policy': 'EXACT_COPY_NO_NEW_INTERPRETATION',
            },
            'task_obligations': [
                {'obligation_id': t, 'status': 'PROPOSED_INTERPRETATION',
                 'required_if_contract_approved': True, 'supporting_sources': ['query', 'semantics', 'behavior', 'qec_original_text'],
                 'automatic_pass_rule': None} for t in tasks
            ],
            'acceptable_capability_combinations': proposals,
            'capability_policy': {'exhaustive': False, 'exact_sequence_required': False,
                                  'equivalent_implementations_allowed_in_principle': True,
                                  'approval_required_for_automatic_scoring': True,
                                  'single_intent_equality_is_not_correctness': True},
            'evidence_contract': {'approved_prose': ref['evidence']['approved_reference_text'],
                                  'required_refs': ref['evidence']['required_refs'],
                                  'proposed_checks': ['source_file_and_version', 'source_locator', 'claim_supported_by_source'],
                                  'check_status': 'PROPOSED_INTERPRETATION', 'automatic_pass_rule': None},
            'execution_guards': {'existing_expected_behavior': ref['expected_behavior'],
                                 'conditional_source_text': ref['expected_behavior_reference_text'],
                                 'do_not_invent_aoi_or_coverage': True,
                                 'new_default_geometry': None,
                                 'new_default_radius_m': None,
                                 'registry_candidate_is_execution_authority': False},
            'unresolved': {'source_notes': ref['uncertainties_preserved'],
                           'source_notes_are_historical': True,
                           'already_resolved_by_v3': ['Q4 anchor/source/5000m boundary and object IDs'] if ref['spatial'] else [],
                           'interpretation_approval_required': True,
                           'complete_semantic_pass_criteria': None,
                           'complete_evidence_pass_criteria': None,
                           'spatial_scope': 'EXISTING_APPROVED_Q4_ONLY' if ref['spatial'] else 'NOT_SUPPLIED_OR_NOT_APPLICABLE'},
        })
    validate(rows)
    return rows


def validate(rows):
    if {r['case_id'] for r in rows} != {'PILOT_' + k for k in SPECS} or len(rows) != 18:
        raise ValueError('Expected 18 unique original cases')
    for row in rows:
        if row['annotation_status'] != 'DRAFT' or row['human_approval'] is not False or row['evaluation_enabled'] is not False:
            raise ValueError('New interpretations cannot be automatically approved or scored')
        if row['holdout_eligible'] is not False or not row['task_obligations']:
            raise ValueError('Invalid pilot contract')
        for src in row['source_provenance'].values():
            if src['text_sha256'] != sha(src['exact_text'].encode('utf-8')) or src['span_end'] != len(src['exact_text']):
                raise ValueError('Source span/hash mismatch')
        for task in row['task_obligations']:
            if task['status'] != 'PROPOSED_INTERPRETATION' or task['automatic_pass_rule'] is not None:
                raise ValueError('Unapproved task interpretation')


def run(output):
    rows = build()
    output.mkdir(parents=True, exist_ok=False)
    target = output / 'task_contracts_DRAFT.jsonl'
    target.write_bytes((''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)).encode('utf-8'))
    manifest = {'status': 'DRAFT_REVIEW_REQUIRED', 'count': 18,
                'reference_sha256': sha(REFERENCE.read_bytes()), 'registry_sha256': sha(REGISTRY.read_bytes()),
                'contracts_sha256': sha(target.read_bytes()), 'generator_sha256': sha(Path(__file__).read_bytes()),
                'model_results_read': False, 'production_modified': False, 'approved_v3_modified': False}
    (output / 'manifest.json').write_bytes(json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8'))
    lines = ['# 18사례 평가계약 초안 v4', '', '기존 v3 사용자 승인은 보존한다. 아래 작업 분해·capability 조합은 새 해석이므로 DRAFT이며 자동 채점에 사용하지 않는다.', '',
             '| 사례 | 질의 | 작업 제안 | 승인 QEC 전사 | 공간 참조 | 미확정 원문 |', '|---|---|---|---|---|---|']
    for r in rows:
        values = r['transcribed_approved_values']; spatial = values['spatial']
        cells = [r['case_id'], r['query'], ', '.join(t['obligation_id'] for t in r['task_obligations']),
                 str(len(values['qec_fields'])) + '개 필드', '기존 Q4 11개 ID' if spatial else ('공간정답 미확정' if r['category'] in ('Q3','Q5') else '비공간 과업'),
                 '기준점·CSV·거리·ID는 v3에서 해소. 새 작업분해 승인 및 응답 완결성 기준 미확정.' if spatial else r['unresolved']['source_notes']]
        lines.append('| ' + ' | '.join(c.replace('|', '\\|').replace('\n', ' ') for c in cells) + ' |')
    (output / '현황_KR.md').write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    print(json.dumps(manifest, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    run(parser.parse_args().output)
