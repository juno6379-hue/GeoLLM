# RQ 중심 v2 GOLD 입력 감사와 사후 조건 메타데이터

## 문서 전제와 실제 자료의 불일치

`CODEX_Marine_GeoLLM_SCIE_Results_실험프롬프트_v2_RQ중심_KR.md`는 GOLD가 이미 제공됐다고 명시한다. 그러나 2026-10-30 현재 이 저장소에서 확인한 v2 합의 자료는 **18개 AI DRAFT, human_approval=false**이며 승인된 공간 객체 ID도 없다. 이 불일치를 완료나 승인으로 간주하지 않는다. 사용자 전달 문구를 근거로 파일의 DRAFT를 GOLD로 바꾸지 않았다.

`research/`와 `outputs/`에서 이름에 gold/annotation/adjudication/승인/검수/합의가 포함된 JSON·JSONL·CSV·XLSX를 읽기 전용으로 탐색했다. 개인 설정·환경파일·DB 접속정보를 읽지 않았고 symlink/junction 및 node_modules를 따라가지 않았다. 파일명 제한 검색이므로 이름이 다른 외부 파일까지 존재하지 않는다는 주장은 아니다. 실제 별도 승인 파일이 제공되면 경로와 해시를 추가 확인해야 한다.

결과: [gold_audit.json](../../../outputs/scie_rq_v2_audit_20261030/gold_audit.json). 초기 workbook 집계가 근거 분할행도 세던 것은 독립 audit 출력에서 바로잡았으며, 초기 파일은 `gold_audit_initial_counting.json`으로 보존했다. 재검사에서는 원문 질의와 사례 ID를 함께 가진 검수행만 센다. 두 검사 모두 승인 가능 사례는 0이었다.

## 승인 입력 상태

| 구성요소 | 승인된 고유 사례 | 상태 | 남은 요건 |
|---|---:|---|---|
| Semantic GOLD | 0 | NOT_READY | 독립 전문가 개념·속성·관계 및 허용 대안 승인 |
| QEC GOLD | 0 | NOT_READY | 필수 슬롯·binding·기대 행동의 명시적 승인 |
| Spatial Result GOLD | 0 | NOT_READY | 동결 snapshot, 독립 oracle/query, 실제 객체집합·geometry·허용오차 |
| Evidence GOLD | 0 | NOT_READY | 원문 참조와 주장 지지·역추적 요건 승인 |
| Fault/Error GOLD | 0 | NOT_READY | 정상/오류 여부·유형에 대한 독립 승인 |

기존 `gold_semantics_v1.jsonl`, `gold_qec_v1.jsonl`, `gold_spatial_results_v1.jsonl`, `gold_evidence_v1.jsonl`은 모두 0 bytes이며 SHA256는 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`다. fault 승인 파일도 탐색 범위에서는 확보되지 않았다. 연구 fixture의 주입 오류는 독립 전문가 GOLD가 아니다.

실제 지정된 v2 workbook의 SHA256:

| 파일 (outputs/scie_annotation_ai_prefill_20261030/) | SHA256 |
|---|---|
| 검수자A_18사례_AI사전검토_Dataset근거_v2.xlsx | `298e56ee5f401620c29d18908c031da467b362ae76326978ef8ecda1f1014a61` |
| 검수자B_18사례_AI사전검토_v2.xlsx | `feb4b38125c9ae17af790ef70b18bdd0610b1553db4d8705dd3ebabca4d8db9b` |
| 합의검토_18사례_AI합의수정본_v2.xlsx | `97ee97567ddf224a65ed592c4f09bb4cfb47e60700d656984b2a76ad3d0c95c3` |

감사기는 기존 `evaluation.metrics.is_gold`의 승인 조건을 재사용하되, 추가로 **human_approval가 boolean true로 명시**되어 있어야 한다. GOLD 라벨·annotator_ids·APPROVED 합의 조건이 필요하며 AI_PRE_REVIEW 또는 human_approval=false/누락은 거부한다. AI 식별자만 있는 행도 독립 사람 검수로 세지 않는다. 이 엄격한 감사 gate는 기존 평가함수의 동작을 바꾸지 않는다. 이 조건을 충족하더라도 내용의 정확성을 자동 보증하지 않고 `CANDIDATES_REQUIRE_REVIEW`로 보고한다. XLSX는 관측·해시만 보존하며 명시적 승인 import 없이 GOLD로 매핑하지 않는다.

Spatial은 빈 목록 `[]`도 유효한 정답 후보가 될 수 있다. 다만 snapshot과 독립 reference query/oracle가 함께 있어야 하며 `null` 객체집합은 미확정이다. 의미·QEC·근거의 구조적 필드 존재와 실제 정답 적합성은 분리한다.

## RQ1 조건은 GOLD 외부에 보관

[condition_metadata.jsonl](../../../outputs/scie_rq_v2_audit_20261030/condition_metadata.jsonl)에 18개 기존 질의의 설명용 조건 라벨을 별도로 기록했다. 각 행은 다음 상태를 명시한다.

```text
annotation_status=DRAFT
review_kind=AI_CONDITION_METADATA
human_approval=false
post_hoc=true
exposed_pilot=true
holdout_eligible=false
```

용어·복잡도·공간연산·정보 가용성·모호성 축은 RQ1 표 생성용이다. 동일 사례가 복수 라벨을 가질 수 있어 축별 행 수를 합쳐 전체 사례 수로 보지 않는다. 결과 노출 뒤 붙인 라벨이므로 사전등록 조건이나 confirmatory interaction 근거로 표현하지 않는다. 결과값이나 모델 예측은 이 분류의 입력에 넣지 않았다.

실제 데이터 가용성은 대부분 미측정이며 빈 목록과 `NOT_MEASURED`로 남겼다. 선택 영역 입력이 없는 Q3_03만 `REFERENCE_GEOMETRY_MISSING`이다. 이 라벨을 원천 데이터 전체가 없다는 뜻으로 확대하지 않는다. 훈련 사전·holdout 자료의 동결 근거가 없어 UNSEEN_SYNONYM은 부여하지 않았다. 영문 일반표현인 Q4_03을 정확한 FC 공식용어로 단정하지 않고 용어축 미분류로 남겼다.

benchmark SHA256를 `e0a98769f5bc0375272aa976bba4cb97bdf2a2c8a0e3c43c20910881935023e9`로 고정했다. 질의 파일이 바뀌면 라벨을 자동 재사용하지 않고 실패한다. GOLD 원문·원본 benchmark·기존 run·운영 코드는 수정하지 않았다. 기존 planning 비교 프로토콜의 표현만 공통 plan JSON schema와 생산 QEC DRAFT capture가 별개임을 명확히 했다. 실험 설정은 바꾸지 않았다.

## 재현 및 검증

```text
.venv/Scripts/python.exe -m pytest research/marine_geollm_scie/tests/test_gold_audit.py research/marine_geollm_scie/tests/test_condition_metadata.py -q
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.gold_audit --output outputs/<새디렉터리>/gold_audit.json
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.condition_metadata --output outputs/<새디렉터리>/condition_metadata.jsonl
```

검증 결과 6 passed. AI/DRAFT 거부, 정상 빈 집합의 oracle 요건, 중복 case 집계, 원본 불변, 손상·빈 GOLD 입력, 사후 메타데이터 및 benchmark 변경 거부를 확인했다. 실제 audit와 18행 metadata 생성 완료. 모델 호출·DB 실행·GOLD 승격은 수행하지 않았다.

따라서 현재 RQ1–RQ5의 독립 GOLD 정확도·CI·우월성은 계산할 수 없다. 관측 가능한 실행/형식/비용 진단은 별도 cohort로 진행할 수 있지만 이를 GOLD 기반 논문 Results 완료로 표시해서는 안 된다.
