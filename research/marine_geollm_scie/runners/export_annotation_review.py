"""Export blinded DRAFT expert-review forms; never writes or promotes GOLD."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def export_review(cases_path: Path, packets_path: Path, output: Path) -> dict:
    """Create a new directory; reviewers receive raw evidence, never model answers."""
    cases_path, packets_path, output = map(Path, (cases_path, packets_path, output))
    cases, packets = _read(cases_path), _read(packets_path)
    identifiers = [case['case_id'] for case in cases]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError('Duplicate case IDs')
    lookup = {}
    for packet in packets:
        key = (packet['case_id'], packet['method'])
        if packet['method'] not in {'B1', 'B2'}:
            continue
        if key in lookup:
            raise ValueError('Duplicate evidence packet')
        evidence = packet.get('evidence', '')
        if hashlib.sha256(evidence.encode('utf-8')).hexdigest() != packet['evidence_sha256']:
            raise ValueError('Evidence hash mismatch')
        for source in packet['sources']:
            if not source.get('path') or not source.get('sha256'):
                raise ValueError('Source provenance missing')
        lookup[key] = packet
    # Fail before creating a partial export if any query lacks its packet pair.
    if any((case_id, method) not in lookup for case_id in identifiers for method in ('B1', 'B2')):
        raise ValueError('Missing B1/B2 evidence packet')
    provenance = {'benchmark_path': str(cases_path), 'benchmark_sha256': _digest(cases_path),
                  'source_packet_path': str(packets_path), 'source_packet_sha256': _digest(packets_path),
                  'exporter_sha256': _digest(Path(__file__)),
                  'source_role': 'retrieval_material_not_gold', 'model_answers_included': False}
    forms = []
    for case in cases:
        evidence = []
        for method in ('B1', 'B2'):
            packet = lookup[(case['case_id'], method)]
            # Deliberate allow-list: no expected behavior, model output, rankings,
            # retrieval trace or suggested annotation is exported.
            evidence.append({'material_type': 'FC_TEXT' if method == 'B1' else 'KG_EXPLICIT_RELATIONS',
                             'sources': packet['sources'], 'source_text': packet.get('evidence', ''),
                             'source_text_sha256': packet['evidence_sha256']})
        forms.append({'case_id': case['case_id'], 'query': case['query'],
                      'category': case['category'], 'equivalence_group': case['equivalence_group'],
                      'annotation_status': 'DRAFT', 'annotator_id': None, 'reviewed_at': None,
                      'split_eligibility': 'PILOT_EXPOSED_NOT_HOLDOUT',
                      'semantics': None, 'qec_fields': None, 'spatial_oracle': None,
                      'required_evidence': None, 'expected_execution_behavior': None,
                      'acceptable_alternatives': None, 'uncertainties': None, 'review_notes': None,
                      'source_materials': evidence, 'provenance': provenance})
    output.mkdir(parents=True, exist_ok=False)
    for reviewer in ('reviewer_A', 'reviewer_B'):
        folder = output / reviewer
        folder.mkdir()
        (folder / 'annotations_DRAFT.jsonl').write_text(
            ''.join(json.dumps({**row, 'reviewer_assignment': reviewer}, ensure_ascii=False) + '\n'
                    for row in forms), encoding='utf-8')
    adjudication = [{'case_id': row['case_id'], 'annotation_status': 'DRAFT',
                     'adjudicator_id': None, 'reviewer_A_annotation_hash': None,
                     'reviewer_B_annotation_hash': None, 'disagreement_fields': None,
                     'resolution': None, 'resolution_sources': None, 'adjudication_status': None,
                     'adjudicated_at': None, 'provenance': provenance} for row in forms]
    (output / 'adjudication_DRAFT.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in adjudication), encoding='utf-8')
    manifest = {'cases': len(forms), 'reviewer_files': 2, 'annotation_status': 'DRAFT',
                'gold_written': False, 'holdout_eligible': False, 'provenance': provenance}
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / '검수안내_KR.md').write_text(GUIDE, encoding='utf-8')
    return manifest


GUIDE = '''# 독립 전문가 검수 안내 — 18개 노출된 파일럿 질의

이 자료는 전문가 정답을 수집하기 위한 빈 DRAFT 양식입니다. 자동 정답이나 모델 답변을 포함하지 않습니다. 기존18개 질의는 이미 파일럿 실험에 노출됐으므로 향후 독립 holdout으로 재사용할 수 없습니다. 새 holdout은 항만·원질의·동등표현 그룹을 분리하여 별도로 작성해야 합니다.

검수자A는 reviewer_A 파일만, 검수자B는 reviewer_B 파일만 받아 서로의 주석과 모델 결과를 보지 않고 작성합니다. 공통 원문 근거를 제공하므로 독립성이란 주석 판단의 독립성입니다. 제출 전에 담당자가 파일 접근을 분리해야 하며 폴더 분리가 접근통제를 보장하지는 않습니다.

각 행에 본인 식별자·검수시각을 기록하고 semantics에는 의도·개념·feature·속성·코드·공간관계·단위·CRS를, qec_fields에는 생산 QEC의 필요한 필드와 허용 대안을 기록합니다. 단일 intent 이름만으로 맞고 틀림을 결정하지 않습니다. 필요한 작업·실행계약·근거를 함께 판단합니다. expected_execution_behavior에는 실행·추가입력·지원불가 등 기대 행동을 독립적으로 작성합니다. 불확실하거나 검증하지 못한 필드는 null로 남기고 사유를 uncertainties에 기록합니다.

source_materials에는 기존 FC 문서와 실제 KG 관계의 원문·원천경로·SHA256만 첨부했습니다. 원천 검색은 불완전할 수 있으며 빈 근거는 관련 표준이나 사실이 존재하지 않는다는 뜻이 아닙니다. 제공된 후보를 정답으로 간주하지 말고 필요하면 독립적인 공식 출처를 추가하고 문서판·원문위치·해시를 기록하십시오. KG에 관계가 존재하는 것과 그 관계가 의미적으로 타당한 것은 다릅니다. 예산 때문에 일부 record가 제공되지 않을 수 있습니다.

spatial_oracle는 별도 동결된 실제 공간 원본과 독립 reference query로 검증할 때만 작성합니다. 제공된 FC/KG 텍스트만으로 객체 ID·좌표·거리 정답을 만들지 않습니다. 정상 빈 결과도 독립 검증이 필요합니다. required_evidence에는 원문참조와 결과→도구→QEC→개념→원천 추적 요건을 기록합니다.

두 사람이 독립 제출한 원본을 보존하고 해시를 계산한 후 별도 adjudication_DRAFT.jsonl에서 불일치·합의근거·제3검토자를 기록합니다. 실제 독립 주석을 확보하기 전에 일치도나 정확도를 계산하지 않습니다. 이 exporter는 GOLD 파일을 수정하거나 자동 승격하지 않습니다. 검수자가 파일의 DRAFT를 바꾸는 것만으로 논문 GOLD 승인이 완료되는 것도 아닙니다. 공식 검수·합의·출처확인이 완료된 뒤 별도 승인 절차로 반영해야 합니다.
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=ROOT / 'research/marine_geollm_scie/benchmark/query_cases_v1.jsonl')
    parser.add_argument('--packets', type=Path, default=ROOT / 'research/marine_geollm_scie/runs/20261030_comparison_v2/evidence_packets/packets.jsonl')
    parser.add_argument('--output', type=Path, default=ROOT / 'research/marine_geollm_scie/benchmark/review_exports/20261030_pilot18')
    args = parser.parse_args()
    result = export_review(args.cases, args.packets, args.output)
    print(json.dumps({'cases': result['cases'], 'gold_written': False, 'output': str(args.output)}))


if __name__ == '__main__':
    main()
