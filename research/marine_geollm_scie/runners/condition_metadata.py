"""Post-hoc descriptive RQ1 conditions, stored separately from protected GOLD."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

FROZEN_BENCHMARK_SHA256 = 'e0a98769f5bc0375272aa976bba4cb97bdf2a2c8a0e3c43c20910881935023e9'
# Query-language descriptions only. No model performance or gold answer enters this map.
LABELS = {
 'PILOT_Q1_01': (['DOMAIN_KOREAN'], ['SINGLE_CONCEPT'], 'NONE', ['SEMANTIC_AMBIGUITY'], '등대는 구조물과 등화의 의미 범위가 갈릴 수 있다.'),
 'PILOT_Q1_02': (['DOMAIN_KOREAN','COLLOQUIAL'], ['SINGLE_CONCEPT'], 'NONE', ['SEMANTIC_AMBIGUITY'], '정박지라는 도메인 용어와 어떤 객체야라는 구어 표현이며 특정 정박 위치와 수역 구분이 필요하다.'),
 'PILOT_Q1_03': (['OFFICIAL_TERM'], ['SINGLE_CONCEPT'], 'NONE', ['UNAMBIGUOUS'], '영문 Wreck 정의 질문이다. 비공간 설명 과업이다.'),
 'PILOT_Q2_01': (['DOMAIN_KOREAN'], ['SINGLE_CONCEPT'], 'NONE', ['ATTRIBUTE_AMBIGUITY','SEMANTIC_AMBIGUITY'], '색상이 구조물 색인지 발광 색인지 구분해야 한다.'),
 'PILOT_Q2_02': (['DOMAIN_KOREAN','COLLOQUIAL'], ['SINGLE_CONCEPT'], 'NONE', ['ATTRIBUTE_AMBIGUITY'], '제한 종류는 행위 restriction과 구역 분류를 혼동할 수 있다.'),
 'PILOT_Q2_03': (['OFFICIAL_TERM'], ['SINGLE_CONCEPT'], 'NONE', ['UNAMBIGUOUS'], 'Wreck의 속성 스키마를 설명하는 질문이다.'),
 'PILOT_Q3_01': (['DOMAIN_KOREAN'], ['SINGLE_SPATIAL_OPERATOR'], 'NEAREST', ['SEMANTIC_AMBIGUITY'], '등대 대상 범위와 기준 위치 해소 후 최근접 연산을 요청한다.'),
 'PILOT_Q3_02': (['DOMAIN_KOREAN'], ['SINGLE_SPATIAL_OPERATOR'], 'WITHIN', ['LOCATION_AMBIGUITY'], '부산항 영역의 경계를 정해야 한다.'),
 'PILOT_Q3_03': (['OFFICIAL_TERM'], ['SINGLE_SPATIAL_OPERATOR'], 'INTERSECTS', ['UNAMBIGUOUS'], '문장 의도는 명확하지만 입력 spatial_context에는 선택 영역 geometry가 없다.'),
 'PILOT_Q4_01': (['DOMAIN_KOREAN'], ['SINGLE_SPATIAL_OPERATOR'], 'DWITHIN_RADIUS', ['SEMANTIC_AMBIGUITY'], '해양지명의 범위·원천은 별도 확인이 필요하며 5km는 명시돼 있다.'),
 'PILOT_Q4_02': (['DOMAIN_KOREAN'], ['SINGLE_SPATIAL_OPERATOR'], 'DWITHIN_RADIUS', ['SEMANTIC_AMBIGUITY'], '5000m 표현이며 다른 Q4 두 문항과 같은 동등표현 그룹이다.'),
 'PILOT_Q4_03': ([], ['SINGLE_SPATIAL_OPERATOR'], 'DWITHIN_RADIUS', ['SEMANTIC_AMBIGUITY'], '영문 일반표현 marine place names를 고유 FC 공식용어로 단정하지 않는다. 제시된 용어 조건 중 확정 가능한 라벨이 없어 미분류로 남겼다.'),
 'PILOT_Q5_01': (['DOMAIN_KOREAN'], ['COMPOSITE_MULTI_TASK'], 'DWITHIN_RADIUS', ['SEMANTIC_AMBIGUITY'], '등대와 난파선 두 대상 검색과 근거 설명을 함께 요구한다. MULTI_SOURCE 여부는 실제 binding 전에는 알 수 없다.'),
 'PILOT_Q5_02': (['DOMAIN_KOREAN'], ['COMPOSITE_MULTI_TASK'], 'DWITHIN_RADIUS', ['LOCATION_AMBIGUITY'], '항만 기준 거리와 두 종류 객체 검색·비교가 결합돼 있다.'),
 'PILOT_Q5_03': (['OFFICIAL_TERM'], ['COMPOSITE_MULTI_TASK'], 'DWITHIN_RADIUS', ['UNAMBIGUOUS'], 'Wreck 반경 검색과 속성 설명이라는 두 과업이다.'),
 'PILOT_Q6_01': (['OFFICIAL_TERM','MIXED_KO_EN'], ['SINGLE_CONCEPT'], 'NONE', ['UNAMBIGUOUS'], '한글 문장에 Wreck/Feature Catalogue 용어가 함께 나온다.'),
 'PILOT_Q6_02': (['DOMAIN_KOREAN'], ['COMPOSITE_MULTI_TASK'], 'NONE', ['SEMANTIC_AMBIGUITY'], '등대와 부표의 구분 설명이며 유형 범위의 검토가 필요하다.'),
 'PILOT_Q6_03': (['OFFICIAL_TERM'], ['SINGLE_CONCEPT'], 'NONE', ['UNAMBIGUOUS'], '정확한 FC 식별자 AnchorageArea의 정의 출처 질문이다.'),
}


def build_metadata(benchmark_path):
    data = Path(benchmark_path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != FROZEN_BENCHMARK_SHA256:
        raise ValueError('Benchmark changed; descriptive condition labels require a new reviewed version')
    cases = [json.loads(line) for line in data.decode('utf-8').splitlines() if line.strip()]
    if {c['case_id'] for c in cases} != set(LABELS) or len(cases) != len(LABELS):
        raise ValueError('Unexpected case IDs')
    rows = []
    for case in cases:
        terms, complexity, operator, ambiguity, rationale = LABELS[case['case_id']]
        missing_area = case['case_id'] == 'PILOT_Q3_03' and not case.get('spatial_context')
        rows.append({'case_id': case['case_id'], 'query_sha256': hashlib.sha256(case['query'].encode()).hexdigest(),
                     'equivalence_group': case['equivalence_group'], 'terminology_condition': terms,
                     'complexity': complexity, 'spatial_operator': operator,
                     'information_availability': ['REFERENCE_GEOMETRY_MISSING'] if missing_area else [],
                     'availability_status': 'INPUT_MISSING' if missing_area else 'NOT_MEASURED',
                     'ambiguity': ambiguity, 'annotation_status': 'DRAFT', 'review_kind': 'AI_CONDITION_METADATA',
                     'human_approval': False, 'post_hoc': True, 'exposed_pilot': True, 'holdout_eligible': False,
                     'source_benchmark_sha256': digest, 'condition_version': 'rq1_descriptive_posthoc.v1',
                     'rationale_ko': rationale,
                     'limitations_ko': '결과 노출 이후 작성된 사후 설명 분류다. 정확도 정답이나 사전등록 층화가 아니다. UNSEEN_SYNONYM은 훈련/검색 사전 동결 근거가 없어 부여하지 않았다. 정보 가용성 미측정을 DATA_COMPLETE로 채우지 않았다.'})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--benchmark', type=Path, default=Path('research/marine_geollm_scie/benchmark/query_cases_v1.jsonl'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = build_metadata(args.benchmark)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as file:
        file.write(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in rows))
    print(json.dumps({'cases': len(rows), 'post_hoc': True, 'gold_modified': False}))


if __name__ == '__main__':
    main()
