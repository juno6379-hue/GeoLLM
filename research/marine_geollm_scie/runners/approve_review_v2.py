"""Version explicit user approval of AI-assisted v2 references without altering sources."""
from __future__ import annotations

import argparse
import copy
import datetime
import hashlib
import json
import math
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8').splitlines() if line.strip()]


def explicit_slots(text):
    """Only literal scalar input constraints, never inferred semantic/feature sets."""
    result = {}
    for part in text.split(';'):
        key, sep, value = part.strip().partition('=')
        if not sep:
            continue
        value = value.strip()
        if key in {'location_text', 'location'} and value:
            result['slots.location_text'] = value
        if key == 'distance_m' and re.fullmatch(r'\d+(?:\.\d+)?', value):
            result['slots.distance_m'] = float(value)
    return result


def verified_spatial(manifest_path):
    """Optional explicit verified-oracle exchange; never inserts placeholder IDs."""
    if manifest_path is None:
        return {}, None
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('status') == 'COMPUTED_VERIFIED_REFERENCE':
        return computed_csv_spatial(manifest_path, manifest)
    if manifest.get('status') != 'VERIFIED' or manifest.get('mock') is True:
        raise ValueError('Spatial oracle is not verified actual source data')
    results = Path(manifest['results_path'])
    if not results.is_absolute():
        results = manifest_path.parent / results
    if sha(results) != manifest['results_sha256']:
        raise ValueError('Spatial results hash mismatch')
    if not manifest.get('dataset_snapshot_sha256') or not manifest.get('reference_geometry_source'):
        raise ValueError('Spatial snapshot/reference provenance missing')
    data = {}
    for row in load_rows(results):
        if row.get('status') != 'VERIFIED':
            continue
        if row['case_id'] not in {'PILOT_Q4_01', 'PILOT_Q4_02', 'PILOT_Q4_03'}:
            raise ValueError('Approval scope only permits the explicitly fixed Q4 oracle')
        if row['case_id'] in data:
            raise ValueError('Duplicate spatial case')
        if not isinstance(row.get('object_ids'), list) or any(not isinstance(x, (str, int)) or isinstance(x, bool) for x in row['object_ids']):
            raise ValueError('Actual object IDs required, including verified empty list')
        if len(set(row['object_ids'])) != len(row['object_ids']):
            raise ValueError('Duplicate spatial object IDs')
        data[row['case_id']] = {**copy.deepcopy(row), 'dataset_snapshot_sha256': manifest['dataset_snapshot_sha256'],
                               'oracle_sha256': sha(manifest_path), 'oracle_results_sha256': manifest['results_sha256'],
                               'reference_geometry_source': manifest['reference_geometry_source']}
    if set(data) != {'PILOT_Q4_01', 'PILOT_Q4_02', 'PILOT_Q4_03'}:
        raise ValueError('Expected all three equivalent Q4 oracle cases')
    sets = [set(row['object_ids']) for row in data.values()]
    if any(s != sets[0] for s in sets[1:]):
        raise ValueError('Equivalent Q4 cases have different oracle object sets')
    return data, {'path': str(manifest_path.resolve()), 'sha256': sha(manifest_path), 'results_path': str(results.resolve()),
                  'results_sha256': manifest['results_sha256']}


def computed_csv_spatial(path, manifest):
    """Verify the actual fixed-CSV dual-distance oracle supplied by the root run."""
    allowed = {'PILOT_Q4_01','PILOT_Q4_02','PILOT_Q4_03'}
    if set(manifest.get('case_ids', [])) != allowed or manifest.get('user_scope_approval') != '동도 기준점·2022 CSV로 고정':
        raise ValueError('Computed oracle scope differs from explicit user approval')
    snapshot = manifest['source_snapshot']
    if sha(snapshot['path']) != snapshot['sha256'] or snapshot['sha256'] != manifest['snapshot_sha256']:
        raise ValueError('Source CSV hash mismatch')
    if sha(manifest['reference_query']) != manifest['reference_query_sha256']:
        raise ValueError('Reference SQL hash mismatch')
    anchor_path = Path(__file__).resolve().parents[3] / 'data/public_place_anchors.json'
    if sha(anchor_path) != manifest['anchor_source_sha256']:
        raise ValueError('Anchor source hash mismatch')
    distances_path = path.parent / 'all_distances.jsonl'
    distances = load_rows(distances_path)
    if len(distances) != snapshot['row_count'] or manifest['parsed_rows'] != snapshot['row_count'] or manifest['parse_errors']:
        raise ValueError('Incomplete source coordinate coverage')
    if len({r['object_id'] for r in distances}) != len(distances):
        raise ValueError('Duplicate source objects in oracle distances')
    if manifest.get('radius_m') != 5000 or manifest.get('reference_crs') != 'EPSG:4326':
        raise ValueError('Unexpected fixed spatial contract')
    members = set()
    for row in distances:
        v, p = row['distance_vincenty_m'], row['distance_postgis_m']
        if not isinstance(v, (int, float)) or not isinstance(p, (int, float)) or not math.isfinite(v) or not math.isfinite(p) or min(v,p)<0 or abs(v-p)>0.01 or (v<=5000)!=(p<=5000):
            raise ValueError('Independent distance verification failed')
        if p <= 5000:
            members.add(row['object_id'])
    ids = manifest['object_ids']
    if not isinstance(ids, list) or len(set(ids)) != len(ids) or set(ids) != members:
        raise ValueError('Computed membership differs from oracle IDs')
    if {r['object_id'] for r in manifest['objects']} != members:
        raise ValueError('Object detail IDs differ from membership')
    common = {'object_ids': ids, 'objects': manifest['objects'], 'dataset_snapshot_sha256': manifest['snapshot_sha256'],
              'oracle_sha256': sha(path), 'oracle_path': str(path.resolve()),
              'reference_query_sha256': manifest['reference_query_sha256'],
              'all_distances_sha256': sha(distances_path), 'reference_geometry_source': manifest['anchor'],
              'reference_crs': manifest['reference_crs'], 'distance_policy': manifest['distance_policy'],
              'crs_policy': manifest['crs_policy'], 'scope': manifest['scope'],
              'independent_expert_review': False, 'calculation_verified': True}
    return {case: copy.deepcopy(common) for case in sorted(allowed)}, {
        'path': str(path.resolve()), 'sha256': sha(path), 'all_distances_path': str(distances_path.resolve()),
        'all_distances_sha256': sha(distances_path), 'source_csv_sha256': snapshot['sha256']}


def approve(source_path, benchmark_path, approval_event, output, spatial_manifest=None):
    source_path, benchmark_path, output = map(Path, (source_path, benchmark_path, output))
    if output.exists():
        raise FileExistsError('Choose a new immutable reference version directory')
    if approval_event.get('explicit_user_approval') is not True or not approval_event.get('verbatim_user_request'):
        raise ValueError('Explicit user approval event required')
    spatial, spatial_provenance = verified_spatial(spatial_manifest)
    if spatial and not approval_event.get('spatial_scope_approval', {}).get('verbatim_answer'):
        raise ValueError('Separate fixed spatial scope approval required')
    source_rows = load_rows(source_path)
    cases = {r['case_id']: r for r in load_rows(benchmark_path)}
    if len(source_rows) != 18 or len({r['case_id'] for r in source_rows}) != 18 or set(cases) != {r['case_id'] for r in source_rows}:
        raise ValueError('Expected original 18 cases')
    # Integrated v2 artifact has its own immutable source manifest and workbook hashes.
    source_manifest_path = source_path.parent / 'manifest.json'
    source_manifest = json.loads(source_manifest_path.read_text(encoding='utf-8'))
    if source_manifest.get('annotations_sha256') != sha(source_path):
        raise ValueError('Integrated v2 annotation hash mismatch')
    for item in source_manifest.get('sources', []):
        if sha(item['path']) != item['sha256']:
            raise ValueError('Original v2 workbook changed')
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    source_hash = sha(source_path)
    approved = []
    for original in source_rows:
        case_id = original['case_id']
        if original['query'] != cases[case_id]['query']:
            raise ValueError('Original query changed')
        a = original.get('reviewer_A', {})
        qec_text = a.get('필요 QEC 필드', '')
        expected = 'EXECUTE' if case_id in spatial else None
        if case_id == 'PILOT_Q3_03' and not cases[case_id].get('spatial_context') and 'NEEDS_USER_INPUT' in original.get('resolution', ''):
            expected = 'NEEDS_USER_INPUT'
        approved.append({'case_id': case_id, 'query': original['query'],
            'category': cases[case_id]['category'], 'equivalence_group': cases[case_id]['equivalence_group'],
            'annotation_status': 'GOLD', 'human_approval': True, 'adjudication_status': 'APPROVED',
            'review_kind': 'USER_APPROVED_AI_ASSISTED', 'reference_version': 'user_approved_v3',
            'annotator_ids': ['USER_APPROVAL'], 'approving_user_id': 'USER_IN_THIS_CHAT',
            'ai_author_ids': ['AI_REVIEWER_A','AI_REVIEWER_B','AI_SYNTHESIS'],
            'independent_expert_review': False, 'two_reviewers': False, 'holdout_eligible': False,
            'post_hoc': True, 'approved_at_recorded_utc': timestamp,
            'approval_scope': 'User approves existing AI-assisted review content; unresolved facts remain unresolved.',
            'semantics': {'labels': None, 'label_set_is_complete_semantic_contract': False,
                          'approved_reference_text': original.get('resolution'),
                          'unstructured_reason': '조건부 후보·서술형 합의를 필수 완전 정답집합으로 새로 해석하지 않았다.'},
            'qec_fields': explicit_slots(qec_text), 'qec_original_text': qec_text,
            'qec_field_provenance': 'reviewer_A/필요 QEC 필드의 명시적 location_text/location/distance_m만 기계적으로 전사. route/candidate/REQUIRED는 기대값으로 바꾸지 않음.',
            'spatial': spatial.get(case_id),
            'spatial_unresolved_reason': None if case_id in spatial else '공간 oracle 미제공 또는 비공간 과업. 선택영역·coverage·객체 ID·geometry를 승인 문구로 생성하지 않는다.',
            'evidence': {'required_refs': None, 'approved_reference_text': original.get('evidence'),
                         'unstructured_reason': '서술형·조건부 근거를 자동 필수 인용집합으로 변환하지 않았다.'},
            'expected_behavior': expected, 'expected_behavior_reference_text': a.get('기대 실행 행동'),
            'uncertainties_preserved': original.get('remaining_review'),
            'disagreements_preserved': original.get('disagreements'),
            'source_reference': {'path': str(source_path.resolve()), 'sha256': source_hash,
                                 'workbook_sha256': original.get('source_sha256'), 'locator': original.get('source_locator')},
            'approved_source_record': copy.deepcopy(original)})
    output.mkdir(parents=True, exist_ok=False)
    (output / 'generation_source_snapshot.py').write_bytes(Path(__file__).read_bytes())
    references = output / 'evaluation_references.jsonl'
    references.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in approved), encoding='utf-8')
    manifest = {'schema_version': 'user_approval_reference.v3', 'recorded_at_utc': timestamp,
                'approval_event': approval_event, 'event_timestamp_provided': approval_event.get('event_timestamp') is not None,
                'source_path': str(source_path.resolve()), 'source_sha256': source_hash,
                'source_manifest_sha256': sha(source_manifest_path), 'original_workbooks': source_manifest.get('sources', []),
                'benchmark_sha256': sha(benchmark_path), 'code_sha256': sha(__file__),
                'reference_path': str(references.resolve()), 'reference_sha256': sha(references), 'cases': len(approved),
                'human_approval': True, 'review_kind': 'USER_APPROVED_AI_ASSISTED',
                'independent_expert_review': False, 'two_reviewers': False, 'holdout_eligible': False,
                'spatial_cases_with_verified_oracle': len(spatial), 'spatial_oracle': spatial_provenance,
                'original_files_modified': False, 'model_calls': 0}
    (output / 'approval_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'README_KR.md').write_text('''# 사용자 승인 AI 보조 검토 v3

사용자가 기존 AI 검토 내용을 명시적으로 승인한 새 참조 버전이다. 독립 전문가 2인의 GOLD나 holdout이 아니다. 원본 DRAFT/XLSX와 기존 GOLD 파일은 그대로 보존했다.

evaluation_references.jsonl의 상위 human_approval=true 및 GOLD는 사용자 승인을 기록한다. approved_source_record의 DRAFT/false 문구는 승인 이전 원본으로 변경하지 않았다. 후보 Feature·모호성·미확정 사항을 승인에 편승하여 확정하지 않았다.

공통 평가 스키마의 semantics.labels/evidence.required_refs는 서술형 자료를 강제 집합으로 새로 해석하지 않아 null이다. QEC는 원문의 명시적 위치·거리만 전사했다. 공간 객체 ID는 별도 사용자 승인 범위와 검증된 실제 oracle manifest가 있을 때만 결합한다. 없는 geometry/coverage/객체 ID는 null이다.

승인 문구 원문·기록시각·원천/출력 해시는 approval_manifest.json을 따른다. 이벤트 발생시각이 제공되지 않았으므로 기록시각과 혼동하지 않는다. 평가기는 reference 파일 SHA256를 gold_sha256로 주입하고 USER_APPROVED_AI_ASSISTED cohort로 구분한다. 이 자료를 모델 prompt나 runtime rule 수정에 사용하지 않는다.
''', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('outputs/scie_review_v2_20261030/annotations_DRAFT.jsonl'))
    parser.add_argument('--benchmark', type=Path, default=Path('research/marine_geollm_scie/benchmark/query_cases_v1.jsonl'))
    parser.add_argument('--approval-event', type=Path, required=True)
    parser.add_argument('--spatial-manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    event = json.loads(args.approval_event.read_text(encoding='utf-8'))
    result = approve(args.source, args.benchmark, event, args.output, args.spatial_manifest)
    print(json.dumps({'cases': result['cases'], 'spatial_cases': result['spatial_cases_with_verified_oracle'],
                      'reference_sha256': result['reference_sha256'], 'independent_expert_review': False}))


if __name__ == '__main__':
    main()
