"""Read-only operational evidence, separate from frozen research metrics."""
import hashlib
import json
import argparse
import re
from pathlib import Path

SUMMARY = 'operational/20261102_coverage_availability_v1/summary.json'
LATEST = 'operational/latest.json'


def read_verified(root: Path, source_folder='outputs/coverage_availability_20261102_v2'):
    """Recheck saved development receipts without HTTP, models or holdout reads."""
    from scripts.check_coverage_availability_20261102 import CASES, SOURCE_PATHS, inspect_case
    root = root.resolve()
    folder = (root / source_folder).resolve()
    if not folder.is_relative_to((root / 'outputs').resolve()):
        raise ValueError('Operational input must be within outputs')
    report = json.loads((folder / 'verification.json').read_text(encoding='utf-8'))
    rows = report['observations']
    if len(rows) != len(CASES) or {r['case'] for r in rows} != {c[0] for c in CASES}:
        raise ValueError('Incomplete operational cases')
    evidence = {}
    for name in ('verification.json', 'source_hashes.json'):
        path = folder / name
        evidence[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for case, _, _, expectation in CASES:
        item = next(r for r in rows if r['case'] == case)
        path = folder / (case + '.json')
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        check = inspect_case(json.loads(raw), expectation)
        if digest != item['raw_sha256'] or not check['passed'] or any(item[k] != v for k, v in check.items()):
            raise ValueError('Operational receipt mismatch: ' + case)
        evidence[path.relative_to(root).as_posix()] = digest
    sources = json.loads((folder / 'source_hashes.json').read_text())
    if set(sources) != set(SOURCE_PATHS):
        raise ValueError('Incomplete operational source hash set')
    for name, digest in sources.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('Operational source changed: ' + name)
    if not report['passed'] or not report['source_unchanged'] or report['paper_experiment'] or report['holdout_loaded']:
        raise ValueError('Unexpected verification scope')
    return rows, evidence, sources


def load_summary(adapter):
    """Only expose a hash-bound summary; original operational raw stays local."""
    summary_path = SUMMARY
    if (adapter.research / LATEST).exists():
        pointer = adapter.load(LATEST, {})
        manifest_path = pointer.get('manifest', '')
        if not isinstance(manifest_path, str) or not re.fullmatch(r'operational/[A-Za-z0-9_-]+/manifest\.json', manifest_path):
            return {'status': 'UNAVAILABLE_LOCAL_ARTIFACT'}
        manifest = adapter.load(manifest_path, {})
        key = (Path('research/marine_geollm_scie') / manifest_path).as_posix()
        if not manifest or adapter.sources.get(key, {}).get('source_sha256') != pointer.get('sha256'):
            return {'status': 'UNAVAILABLE_LOCAL_ARTIFACT'}
        summary_path = manifest_path.replace('manifest.json', 'summary.json')
    else:
        manifest = adapter.load(SUMMARY.replace('summary.json', 'manifest.json'), {})
    summary = adapter.load(summary_path, {})
    key = (Path('research/marine_geollm_scie') / summary_path).as_posix()
    if not summary or adapter.sources.get(key, {}).get('source_sha256') != manifest.get('summary_sha256'):
        return {'status': 'UNAVAILABLE_LOCAL_ARTIFACT'}
    if summary.get('paper_experiment') is not False or summary.get('holdout_evaluation_executed') is not False:
        return {'status': 'UNAVAILABLE_LOCAL_ARTIFACT'}
    # A subsequent operational fix does not erase the historical verification.
    changed, missing = [], []
    for name, digest in manifest.get('operational_source_sha256', {}).items():
        source = (adapter.root / name).resolve()
        if not source.is_relative_to(adapter.root) or not source.is_file():
            missing.append(name)
        elif hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            changed.append(name)
    return {**summary, 'historical_verification_valid': True,
            'summary_path': summary_path,
            'current_source_freshness': 'CHANGED' if changed else 'UNAVAILABLE' if missing else 'MATCHES' if manifest.get('operational_source_sha256') else 'UNVERIFIED',
            'changed_sources': changed, 'missing_sources': missing}


def generate(root, source_folder, version):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', version):
        raise ValueError('Invalid operational version')
    rows, evidence, sources = read_verified(root, source_folder)
    previous = root / 'outputs/coverage_availability_20261102_v1'
    for path in sorted(previous.glob('*.json')):
        evidence[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    summary = dict(
        version=version, status='DEVELOPMENT_VERIFIED',
        date='2026-11-02', paper_experiment=False, holdout_evaluation_executed=False,
        passed_cases=sum(r['passed'] for r in rows), total_cases=len(rows),
        source_unchanged_at_verification=True,
        corpus_row_count=1146, query_scope='SOURCE_CORPUS', geographic_coverage='UNKNOWN',
        absence_certified=False, dataset_coordinate_audit_complete=False,
        observations=[{k: r[k] for k in ('case', 'passed', 'status', 'count', 'raw_sha256')} for r in rows],
        limitations=[
            '운영 보완의 기존 개발 질의 검증이며 새 동결 논문 비교가 아닙니다. v6 ESR·FalseBlock 및 기존 연구 지표는 변경하지 않았습니다.',
            '검증된 2022 해양지명 CSV 1,146행과 DB의 exact identity에 한정합니다. 원천 수록 객체 조회만 허용하며 실제 해역의 전체 지명·부재를 보증하지 않습니다.',
            '부산 S-101 정상 가능 요청도 승인 coverage가 없어 여전히 차단됩니다. 정상 가용성 한계는 미해결입니다.',
            'Dataset 전체 지명·위치·좌표 전수 검증: 미완료. 문서 청크의 지명·좌표 추출 정확성 및 공간객체 연결 전수 검증은 임베딩 완료와 별개입니다.',
            '검사는 서버 receipt 기반이며 독립 SQL 계측이나 인간 의미 정확도 채점이 아닙니다. Q4 세 표현은 같은 개발 지리조건입니다.',
            '최초 v1 수집은 재시작 직후 transport 실패로 원본 보존했습니다. 성공 8건에 합산하지 않습니다.',
            '독립 홀드아웃은 최종 시스템 동결 후 평가 예정이며 미실행입니다. HUMAN_FINAL은 사람이 확인한 AI 보조 채점으로 유지합니다.',
        ], evidence_sha256=evidence)
    research = root / 'research/marine_geollm_scie'
    folder = research / 'operational' / version
    folder.mkdir(parents=True, exist_ok=False)
    target = folder / 'summary.json'
    target.write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    manifest = dict(version=summary['version'], summary_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                    input_sha256=evidence, operational_source_sha256=sources,
                    generator='tools/scie_results_ui/operational.py',
                    generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    original_research_modified=False, holdout_loaded=False)
    manifest_file = folder / 'manifest.json'
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    pointer = dict(manifest=manifest_file.relative_to(research).as_posix(),
                   sha256=hashlib.sha256(manifest_file.read_bytes()).hexdigest())
    temporary = research / 'operational/latest.json.tmp'
    temporary.write_text(json.dumps(pointer, indent=2)+'\n', encoding='utf-8')
    temporary.replace(research / LATEST)
    print('Verified 8 development receipts; created ' + str(folder))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-folder', default='outputs/coverage_availability_20261102_v2')
    parser.add_argument('--version', default='20261102_coverage_availability_v1')
    args = parser.parse_args()
    generate(Path(__file__).resolve().parents[2], args.source_folder, args.version)


if __name__ == '__main__':
    main()
