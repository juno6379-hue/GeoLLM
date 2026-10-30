"""Offline research readiness audit. No DB connections, model calls or scores."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def audit(config, root):
    root = Path(root).resolve()
    checks = []
    hashes = {}
    def add(category, key, status, reason, **details):
        checks.append(dict(category=category, key=key, status=status, reason_ko=reason, **details))
    def resolve(value):
        p = Path(value)
        return p if p.is_absolute() else root / p
    def artifact(key, spec):
        if not isinstance(spec, dict) or not spec.get('path'):
            add('DATA_PROVENANCE', key, 'UNKNOWN', '파일 경로 및 기대 해시가 제공되지 않았습니다.')
            return None
        path = resolve(spec['path'])
        if not path.is_file():
            add('ENVIRONMENT', key, 'BLOCKED', '선언된 로컬 파일이 없습니다.', path=str(path))
            return None
        cache_key = str(path.resolve())
        if cache_key not in hashes:
            hashes[cache_key] = sha256(path)
        actual = hashes[cache_key]
        expected = spec.get('sha256')
        add('DATA_PROVENANCE', key, 'PASS' if expected == actual else 'BLOCKED' if expected else 'UNKNOWN',
            '기대 해시와 파일을 대조했습니다.' if expected else '현재 해시만 관측했으며 원래 캡처와의 일치는 미확정입니다.',
            path=str(path), observed_sha256=actual, expected_sha256=expected)
        return path
    snapshot_spec = config.get('snapshot_manifest')
    snapshot_path = artifact('snapshot_manifest', snapshot_spec)
    snapshot = {}
    if snapshot_path:
        try:
            snapshot = json.loads(snapshot_path.read_text(encoding='utf-8'))
        except (ValueError, UnicodeError):
            add('DATA_PROVENANCE', 'snapshot_json', 'BLOCKED', 'manifest JSON을 읽을 수 없습니다.')
    sources = config.get('source_files', snapshot.get('files', []))
    if not sources:
        add('DATA_PROVENANCE', 'source_files', 'UNKNOWN', '원천 파일 목록이 없습니다.')
    for i, spec in enumerate(sources):
        artifact(f'source_file:{i}', spec)
    observations = []
    for spec in config.get('observations', []):
        kind = spec['kind']
        observed_path = artifact(kind + ':manifest', spec.get('manifest'))
        if not observed_path:
            continue
        observed = json.loads(observed_path.read_text(encoding='utf-8'))
        binding = observed.get('snapshot_manifest_sha256', observed.get('snapshot_sha256', (observed.get('snapshot_manifest') or {}).get('sha256')))
        add('OBSERVATION_BINDING', kind, 'PASS' if binding and binding == (snapshot_spec or {}).get('sha256') else 'BLOCKED',
            '별도 실행 관측이 같은 snapshot manifest를 참조하는지 검사합니다.')
        summary = {'kind': kind, 'scope': observed.get('scope', observed.get('method')), 'accuracy_inferred': False}
        if kind == 'DB_PROBE':
            for item in observed.get('observations', []):
                for suffix, hash_key in (('.sql', 'sql_sha256'), ('.json', 'result_sha256')):
                    artifact('DB_PROBE:' + item['probe'] + suffix,
                        {'path': str(observed_path.parent/(item['probe'] + suffix)), 'sha256': item.get(hash_key)})
            summary.update(probes=len(observed.get('observations', [])), model_calls=observed.get('model_calls'), database_writes=observed.get('database_writes'))
        rows_path = artifact(kind + ':rows', spec.get('rows')) if spec.get('rows') else None
        if rows_path:
            records = [json.loads(line) for line in rows_path.read_text(encoding='utf-8').splitlines() if line.strip()]
            summary.update(rows=len(records), status_counts=dict(Counter(r.get('graph_status', r.get('status', 'UNRECORDED')) for r in records)))
            if kind == 'RETRIEVAL_COMPONENT':
                add('OBSERVATION_BINDING', kind + ':rows', 'PASS' if observed.get('rows_sha256') == sha256(rows_path) and observed.get('rows') == len(records) else 'BLOCKED', '검색 manifest에 기록된 행 수와 원시 결과 해시를 대조했습니다.')
                summary.update(embedding_calls=observed.get('embedding_calls'), model=observed.get('model'),
                    model_digest_unchanged=observed.get('model_digest_unchanged'), stored_embedding_model_profile_verified=observed.get('stored_embedding_model_profile_verified'),
                    returned_candidate_counts=[r.get('result_count') for r in records])
                add('MODEL_PROFILE', kind, 'PASS' if observed.get('stored_embedding_model_profile_verified') is True else 'UNKNOWN',
                    '질의 임베딩 호출과 저장 벡터 모델의 동일성은 별도 조건입니다. 후보 반환을 근거 정확도로 승격하지 않습니다.')
        if kind == 'GRAPH_NO_LLM':
            integrity_path = artifact(kind + ':integrity_after', spec.get('integrity_after'))
            integrity = json.loads(integrity_path.read_text(encoding='utf-8')) if integrity_path else {}
            add('OBSERVATION_BINDING', kind + ':integrity', 'PASS' if integrity.get('verified') is True else 'UNKNOWN',
                '격리 graph 실행 후 원천 무변경 관측을 참조합니다. graph 반환과 실행 성공을 동일시하지 않습니다.')
            summary['differences_from_model_baselines'] = observed.get('differences_from_model_baselines')
        observations.append(summary)
    if snapshot:
        identity = snapshot.get('db_identity') or {}
        expected_identity = config.get('expected_db_identity')
        identity_ok = (expected_identity is not None and identity == expected_identity
            and identity.get('container') == 'marine-scie-pilot-db'
            and identity.get('database') in {'scie_pilot', 'scie_binding_v2'})
        add('EXECUTION_PROFILE', 'research_db_identity', 'PASS' if identity_ok else 'BLOCKED' if expected_identity else 'UNKNOWN',
            '명시적 연구 DB 식별자와 snapshot 대상의 일치를 검사합니다.', observed_identity=identity)
        source = config.get('snapshot_data_file')
        if source or not snapshot.get('relations'):
            artifact('snapshot_data', {'path': source, 'sha256': snapshot.get('source_sha256')} if source else None)
        metadata = ('captured_at', 'source_transaction')
        missing = [key for key in metadata if snapshot.get(key) is None]
        add('DATA_PROVENANCE', 'snapshot_capture', 'UNKNOWN' if missing else 'PASS',
            '캡처 시각·트랜잭션·행 수 기록 검사입니다. DB 현재 상태를 증명하지 않습니다.', missing=missing)
    relations = snapshot.get('relations') or ([{'name': snapshot.get('source_relation'), 'columns': snapshot.get('columns', [])}] if snapshot else [])
    relation_map = {r.get('name', r.get('relation')): r for r in relations}
    loaded = {r.get('relation'): r for r in snapshot.get('loaded_verification', [])}
    required = config.get('required_relations', {})
    if not required:
        add('RELATION_SCHEMA', 'required_relations', 'UNKNOWN', '실험에 필요한 관계·열 계약이 없습니다.')
    for name, columns in required.items():
        relation = relation_map.get(name)
        declared = (relation or {}).get('columns', [])
        names = {c if isinstance(c, str) else c.get('name') if isinstance(c, dict) else c[0] for c in declared}
        missing = sorted(set(columns) - names)
        add('RELATION_SCHEMA', name, 'PASS' if relation and not missing else 'BLOCKED',
            'manifest 선언과 필수 관계·열을 대조했습니다. 실제 DB 존재 여부는 별도 관측이 필요합니다.', missing_columns=missing)
        if relation:
            count = relation.get('rows', snapshot.get('subset_rows'))
            add('DATA_PROVENANCE', name + ':row_count', 'PASS' if type(count) is int and count >= 0 else 'UNKNOWN',
                '원천 행 수 선언 검사이며 DB 적재 행 수와 구분합니다.', declared_rows=count)
            if relation.get('csv_path'):
                csv_path = Path(relation['csv_path'])
                if not csv_path.is_absolute():
                    csv_path = snapshot_path.parent / csv_path
                artifact(name + ':csv', {'path': str(csv_path), 'sha256': relation.get('sha256')})
            observed = loaded.get(name)
            if observed:
                matches = (snapshot.get('status') == 'LOADED_VERIFIED' and observed.get('content_match') is True
                    and type(count) is int and observed.get('rows') == count
                    and bool(relation.get('sha256')) and observed.get('roundtrip_sha256') == relation.get('sha256'))
                add('DATABASE_LOAD_OBSERVATION', name, 'PASS' if matches else 'BLOCKED',
                    '별도 로더가 기록한 COPY 재출력 해시·행 수와 원천을 대조했습니다. 현재 DB를 재접속한 결과는 아닙니다.',
                    observed_rows=observed.get('rows'), roundtrip_sha256=observed.get('roundtrip_sha256'))
            else:
                add('DATABASE_LOAD_OBSERVATION', name, 'UNKNOWN', 'DB 적재 후 행 수·내용 재검증 관측이 없습니다.')
    env = config.get('environment_observation', {})
    probe_path = artifact('environment_probe', env.get('artifact')) if env.get('artifact') else None
    probe_verified = probe_path is not None and sha256(probe_path) == env['artifact'].get('sha256')
    add('ENVIRONMENT', 'runtime_probe', 'PASS' if env.get('status') == 'AVAILABLE' and env.get('observed_at') and probe_verified else 'BLOCKED' if env.get('status') == 'UNAVAILABLE' else 'UNKNOWN',
        '환경 관측 결과이며 모델 오류 또는 정상 질의 차단으로 분류하지 않습니다.', observed_at=env.get('observed_at'), timestamp_kind=env.get('timestamp_kind', 'UNSPECIFIED'))
    profile = config.get('profile', {})
    add('EXECUTION_PROFILE', 'embedding', 'BLOCKED' if profile.get('embedding_required') is True and profile.get('embedding_enabled') is False else 'PASS' if profile.get('embedding_required') is False and profile.get('embedding_enabled') is False else 'UNKNOWN',
        '임베딩 호출 비활성은 명시적 프로파일 제약입니다. 모델 오류로 간주하지 않습니다.',
        embedding_required=profile.get('embedding_required'), embedding_enabled=profile.get('embedding_enabled'))
    refs_path = artifact('references', config.get('references'))
    references = {}
    if refs_path:
        try:
            records = [json.loads(line) for line in refs_path.read_text(encoding='utf-8').splitlines() if line.strip()]
            references = {r['case_id']: r for r in records}
            if len(references) != len(records):
                add('REFERENCE_APPROVAL', 'duplicate_case_ids', 'BLOCKED', '중복 사례 ID가 있습니다.')
        except (ValueError, KeyError, TypeError):
            add('REFERENCE_APPROVAL', 'references_format', 'BLOCKED', '참조 JSONL 구조가 유효하지 않습니다.')
    cases = config.get('cases', [])
    if not cases:
        add('INPUT_CONTRACT', 'case_selection', 'UNKNOWN', '검사할 사례와 필수 평가 구성요소가 지정되지 않았습니다.')
    for case in cases:
        cid = case['case_id']; ref = references.get(cid, {})
        approved = ref.get('human_approval') is True and ref.get('annotation_status') == 'GOLD' and ref.get('adjudication_status') == 'APPROVED' and ref.get('review_kind') != 'AI_PRE_REVIEW'
        add('REFERENCE_APPROVAL', cid, 'PASS' if approved else 'BLOCKED',
            '사용자 승인과 독립 전문가 검수는 구분합니다. 승인은 완전한 계약을 뜻하지 않습니다.',
            review_kind=ref.get('review_kind'), independent_expert_review=ref.get('independent_expert_review') is True)
        if not case.get('required_components'):
            add('EVALUATION_CONTRACT', cid + ':required_components', 'UNKNOWN', '이 실험에서 평가할 필수 구성요소가 지정되지 않았습니다.')
        for component in case.get('required_components', []):
            complete = {'semantic': (ref.get('semantics') or {}).get('label_set_is_complete_semantic_contract') is True,
                'qec': ref.get('qec_reference_is_complete_execution_contract') is True,
                'spatial': isinstance((ref.get('spatial') or {}).get('object_ids'), list) and bool((ref.get('spatial') or {}).get('dataset_snapshot_sha256')) and bool((ref.get('spatial') or {}).get('oracle_sha256')),
                'evidence': (ref.get('evidence') or {}).get('complete_claim_support_contract') is True}.get(component, False)
            add('EVALUATION_CONTRACT', f'{cid}:{component}', 'PASS' if complete and approved else 'BLOCKED', '필수 평가계약의 명시적 완결성을 검사합니다. 점수는 계산하지 않습니다.')
        if ref.get('evaluation_enabled') is False:
            add('EVALUATION_CONTRACT', cid + ':enabled', 'BLOCKED', '새 의무분해 계약은 평가 활성화되지 않았습니다. 원래 참조의 승인을 전이하지 않습니다.')
        if case.get('requires_spatial_input') is True:
            aoi = case.get('aoi_bbox_epsg4326'); bounds = snapshot.get('bbox_epsg4326')
            valid = lambda b: isinstance(b, list) and len(b) == 4 and all(isinstance(v, (float, int)) and not isinstance(v, bool) for v in b) and -180 <= b[0] <= b[2] <= 180 and -90 <= b[1] <= b[3] <= 90
            if not valid(aoi):
                aoi_ref = case.get('aoi_reference')
                aoi_path = artifact(cid + ':aoi_reference', aoi_ref) if aoi_ref else None
                aoi_verified = aoi_path is not None and sha256(aoi_path) == aoi_ref.get('sha256')
                add('INPUT_CONTRACT', cid + ':aoi', 'PASS' if aoi_verified else 'UNKNOWN',
                    '명시적 AOI 계약 artifact를 참조합니다. bbox 포함 검사는 별도 미측정입니다.' if aoi_verified else '이 검사 입력에 검색영역이 제공되지 않았습니다. 기준점만으로 반경·AOI를 생성하지 않습니다.')
                if aoi_verified:
                    add('COVERAGE', cid + ':bbox', 'UNKNOWN', 'AOI 계약은 제공됐지만 bbox coverage는 이 검사에서 대조하지 않았습니다.')
            elif not valid(bounds):
                add('COVERAGE', cid, 'UNKNOWN', 'snapshot 공간 범위가 명시되지 않았습니다.')
            else:
                contained = bounds[0] <= aoi[0] and bounds[1] <= aoi[1] and bounds[2] >= aoi[2] and bounds[3] >= aoi[3]
                add('COVERAGE', cid + ':bbox', 'PASS' if contained else 'BLOCKED', '공간 범위 포함 검사이며 의미적·시간적 자료 완전성을 증명하지 않습니다.')
            add('COVERAGE', cid + ':completeness', 'PASS' if case.get('coverage_verified') is True and case.get('coverage_evidence_sha256') else 'UNKNOWN',
                '객체군·시간·원천 coverage 검증 근거가 별도로 필요합니다.')
    return {'schema_version': 'research.preflight.v1', 'recorded_at': datetime.now(timezone.utc).isoformat(),
        'scope': 'OFFLINE_DECLARATIONS_AND_LOCAL_ARTIFACTS_ONLY', 'status': 'READY' if checks and all(c['status'] == 'PASS' for c in checks) else 'NOT_READY',
        'scientific_scores_generated': False, 'model_errors_inferred': False, 'production_database_writes': False,
        'observations': observations, 'checks': checks}


def run(config_path, output_dir, root='.'):
    output = Path(output_dir)
    if output.exists():
        raise FileExistsError('기존 검사를 보존하려면 새 출력 경로를 사용하세요.')
    config_path = Path(config_path)
    result = audit(json.loads(config_path.read_text(encoding='utf-8')), root)
    result['config_sha256'] = sha256(config_path)
    output.mkdir(parents=True)
    (output/'preflight.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 연구 실행 준비 검사', '', f'상태: **{result["status"]}**. 논문 점수·모델 오류 판정이 아닙니다.', '',
        'manifest 관계·열은 선언 검사이며 현재 DB 접근 관측과 구분합니다. 기존 Results를 변경하지 않습니다.', '',
        '| 분류 | 검사 | 상태 | 설명 |', '| --- | --- | --- | --- |']
    lines += [f'| {c["category"]} | {c["key"]} | {c["status"]} | {c["reason_ko"]} |' for c in result['checks']]
    if result['observations']:
        lines += ['', '## 별도 실행 관측', '', '서로 다른 실행 범위를 합쳐 Full P 또는 의미·근거 정확도로 표현하지 않습니다.', '',
            '```json', json.dumps(result['observations'], ensure_ascii=False, indent=2), '```']
    (output/'preflight_KR.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True); parser.add_argument('--output-dir', required=True)
    parser.add_argument('--root', default='.')
    args = parser.parse_args()
    result = run(args.config, args.output_dir, args.root)
    print(json.dumps({'status': result['status'], 'checks': len(result['checks'])}))
