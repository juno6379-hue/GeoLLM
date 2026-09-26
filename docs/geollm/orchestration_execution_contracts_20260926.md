# 공통 오케스트레이터 실행 계약 확장

작성일: 2026-09-26. 적용 범위: GeoLLM 공통 S-101 선택 객체 조회와 해양 용어 속성 검색. UPort 전용 계획 시스템과 구분한다.

## 1. 목적과 이번 변경의 범위

사용자는 semantic router, context resolver, QueryExecutionContext, route planner, execution validator, Evidence builder를 최우선으로 지정했다. 이번 단계는 이 구성요소의 이름을 trace에 추가하는 데 그치지 않고, 실제 S-101 검색 한 경로가 공통 실행 계약을 사용하도록 바꾸는 작업이다.

직전 커밋 `f845a96`은 선택 객체 조회를 RoutePlanner, typed QueryExecutionContext, SchemaBindingAdapter, execution validator, EvidenceBuilder에 연결했다. 이전 `da09b99`는 해양 용어의 S-101 속성 검색과 반경 누락·제외·복합 입력 검사를 구현했다. 이번 변경은 속성 검색도 같은 공통 구성요소를 사용하도록 확장한다.

일반 semantic router와 ContextResolver 전체를 재구현하거나 모든 legacy 실행 경로를 통합한 것은 아니다. 실제 처리 순서와 아직 분리된 경로는 아래 표에 구분한다.

## 2. 발견한 문제와 수정 결과

기존 `marine_mapping_execution.execute`는 검증된 용어 매핑으로 PostGIS 검색을 수행했지만, 실행 계획과 QEC를 자체 dict로 만들었다. 결과의 `readiness=EXECUTION_READY`도 조회 성공 후 직접 넣었고, 공간 근거와 매핑 근거를 별도 dict 형식으로 구성했다. 검색 입력에 대한 자체 검사는 있었지만, 공통 검증기가 이 작업 유형을 검증하는 구조는 아니었다.

이번에는 `source_attribute_search`를 공통 operation으로 등록했다. RoutePlanner가 필요한 도구·데이터·출력을 계획하고, typed QEC가 입력·원천 버전을 보존하며, 공통 검증기가 DB 스키마와 입력 매핑을 재확인한 뒤 조회를 허용한다. 결과는 EvidenceBuilder를 통해 공통 EvidenceBundle로 구성한다.

특히 입력 슬롯의 `attribute_filters`를 그대로 신뢰하지 않는다. 원문으로 다시 얻은 registry 매핑과 비교해 속성 조건 누락, 다른 Feature, 오래된 mapping/FC hash를 차단한다. 이 검사는 registry 의미 해석 자체를 human gold로 승인하는 것은 아니다.

## 3. 단계별 책임과 현재 연결 상태

| 단계 | 실제 구성요소 | 이번 경로에서의 역할 | 제한 |
|---|---|---|---|
| 원문·제약 해석 | `korean_query_analysis` | 거리 수량, 부정/제외, 선택 객체 필수 조건 검사 | 모든 한국어 복합 표현을 지원하지 않음 |
| 의도·기능 후보 | `query_candidate_broker`, `semantic_slot_binding` | 정규화 원문에 대한 후보 trace, Feature·KG·capability 연결 기록 | 후보 순위는 실행 권한이나 의미 정확도 점수가 아님 |
| 문맥 해소 | `resolve_reference` → 기존 place resolver | 명시 지명·지도 문맥을 기준점과 해소 근거로 변환 | 일반 `ContextResolver`의 모든 경로를 이 단계로 통합하지 않음 |
| 실행 계획 | `RoutePlanner` | `source_attribute_search`, `postgis.dwithin`, 실제 serving 원천, 출력 종류 결정 | 계획의 ROUTED 상태만으로 실행 허용하지 않음 |
| 입력 계약 | `QueryExecutionContext`, `ExecutionSlots` | 원문, 기준 geometry, CRS, 반경, 객체, 속성 조건, snapshot hash 보존 | 기존 다른 경로의 QEC 사용 방식은 별도 감사 필요 |
| 원천 연결 | `SchemaBindingAdapter` | 실제 relation 존재·SELECT 권한·필수 컬럼 확인, 등록 도구 바인딩 | 스키마 검증과 실제 조회 사이 원천 변경 가능성은 조회 오류로 처리 |
| 실행 검증 | `validate_execution_context` | 반경·geometry·CRS·단일 매핑·속성 조건·snapshot 일치 검사 | 미지원 부정/복합 작업을 실행할 계획은 아직 없음 |
| 도구 실행 | `marine_mapping_execution` | 읽기 전용 PostGIS 거리/속성 검색 | 첫 100개 반환, 전체 count는 별도 보존 |
| 근거 구성 | `EvidenceBuilder` | 공간 행과 registry 매핑을 typed EvidenceBundle로 변환 | 변환은 자료의 진위·의미 정확도를 보증하지 않음 |
| 완료 판정 | graph의 `verify_output_obligations_node` | 필수 산출물 부족 시 PARTIAL 유지 | 모든 자연어 요구의 완전한 산출물 목록은 아직 미지원 |

## 4. 입력·원천 계약

### 4.1 지원하는 검색 의미

현재 잠제/수중방파제 검색은 다음 조건의 교집합이다.

```text
feature_type_name = ShorelineConstruction
categoryOfShorelineConstruction = 1
waterLevelEffect = 3
distance from verified reference point <= explicit radius
```

이는 S-101에서 항상 수중으로 부호화된 방파제 부분집합이다. 실제 세계의 모든 잠제를 포괄하지 않으며, 속성 미입력 객체를 포함하지 않는다. 물양장·예선·선유장은 의미 매핑이 미해결 상태이므로 계속 차단한다. 원문과 순화어의 관계만으로 임의 Feature를 확정하지 않는다.

### 4.2 QEC에 보존하는 슬롯

`slots.analysis_type`, `reference_geometry`, `crs`, `distance_m`, `target_features`와 `filters.attribute_filters`가 실제 SQL 입력을 설명한다. `filters.mapping_registry_sha256`와 `filters.fc_sha256`는 적용한 매핑/FC snapshot을 식별한다. 동일 hash를 `snapshot_versions`에도 기록해 평가·추적 시 명시적으로 확인할 수 있다.

`context.location_resolution`에는 기존 기준점 해소 결과를 보존하고 `semantic_resolution.source_mappings`에는 원문 구간과 매핑 provenance를 남긴다. 임의 좌표·기본 반경을 새로 만들지 않는다.

### 4.3 공통 검증 조건

- 실제 `projection.s101_feature_valid`가 존재하고 SELECT 권한이 있어야 한다.
- `feature_instance_id`, `feature_type_name`, `attributes`, `geometry` 컬럼이 있어야 한다.
- 등록된 `postgis.dwithin` 도구가 바인딩되어야 한다.
- 반경은 유한한 양수이며 기존 최대 반경 정책을 충족해야 한다.
- geometry는 유효한 geographic Point이고 경도/위도 범위를 충족해야 한다. CRS는 EPSG:4326이어야 한다.
- 원문 매핑은 실행 가능한 단일 매핑이어야 하며, Feature와 모든 속성 조건·hash가 슬롯과 같아야 한다.
- 명시 부정 조건은 공통 검증에서도 차단한다. 지도 exclusions와 복합 대상 검사는 실행 함수의 선행 검사도 유지한다.

SchemaBindingAdapter의 스키마 확인은 읽기 전용 진단이다. `execution_status=NOT_RUN`은 대상 Feature 검색 도구를 실행하지 않았다는 뜻이며 모든 메타데이터 조회가 없었다는 뜻은 아니다.

## 5. 계획·실행·근거 추적

### 5.1 계획 식별

`plan_hash`는 실행 검증 전 계획과 정규화 슬롯을 정렬 직렬화해 계산한다. 검증 이후 readiness와 결과 status는 달라질 수 있으므로 응답의 mutable route_plan 전체를 다시 hash한 값과 동일하다고 가정하면 안 된다. 이 hash는 입력 계획 식별용이며 서명이나 권한 토큰이 아니다.

### 5.2 실행 기록

`provenance.execution`에는 다음을 기록한다.

| 필드 | 의미 |
|---|---|
| `query_execution_id` | 실제 성공한 조회 실행 식별자 |
| `tool_id` | `postgis.dwithin` |
| `statement_sha256` | 사용한 SQL 템플릿 식별자 |
| `parameters` | 검증된 기준점·반경·대상·속성 조건 슬롯 |
| `result_sha256` | 전체 count와 반환 행 직렬화 결과의 hash |
| `total_count` | 조건을 만족한 DB 행 수 |
| `returned_count` | 실제 응답에 포함한 행 수 |

SQL 값은 파라미터로 전달한다. 고정된 serving relation을 사용하며 사용자 입력을 테이블 이름으로 삽입하지 않는다. 연결 제한은 5초, SQL statement 제한은 15초다. API 전체 지연 제한과는 다른 범위다.

### 5.3 근거 연결

각 공간 evidence의 ID와 data는 같은 query_execution_id를 참조한다. structured_result의 query_execution_id도 같아야 한다. registry 매핑은 `source_mapping` 타입의 typed item으로 보존하고 `human_gold=false` 상태를 유지한다. 근거 저장 위치가 `kg_provenance`라는 이유로 신규 KG 사실이 확정되었다고 해석하지 않는다.

결과 0건은 실제 조회가 성공한 경우에만 COMPLETED와 total_count=0으로 표현한다. SQL 연결/실행 장애는 FAILED 실행 기록과 DB_EXECUTION_FAILED로 반환하고 0건을 만들어 넣지 않는다. result hash는 조회 응답 재현용 식별자이며 raw→정제→serving 전체 lineage는 아니다.

## 6. 상태와 오류 계약

| 상황 | 응답 상태/코드 | 대상 검색 실행 |
|---|---|---|
| 명시 반경 없음 | NEEDS_CLARIFICATION / RADIUS_REQUIRED | NOT_RUN |
| 미해결 용어 | BLOCKED / TERM_MAPPING_UNRESOLVED | NOT_RUN |
| 미지원 제외 조건 | BLOCKED / NEGATION_EXECUTION_NOT_SUPPORTED | NOT_RUN |
| 다른 객체를 포함한 복합 요청 | BLOCKED / COMPOUND_MAPPING_REQUIRED | NOT_RUN |
| 공통 원천/매핑 검증 실패 | BLOCKED / SOURCE_ATTRIBUTE_EXECUTION_BLOCKED | NOT_RUN |
| DB 조회 장애 | BLOCKED / DB_EXECUTION_FAILED | FAILED |
| 성공한 조회, 0건 포함 | COMPLETED | EXECUTED |
| 별도 필수 산출물 누락 | 공통 output audit에 따라 PARTIAL | 수행된 도구 기록 유지 |

QEC readiness는 사전 검증 결과이고 execution_status는 실제 실행 결과다. 따라서 원천이 검증된 뒤 SQL이 실패하면 readiness가 EXECUTION_READY였다는 기록과 execution_status=FAILED가 함께 존재할 수 있다. 응답의 최종 상태와 plan.execution_ready는 실패에 맞게 처리한다. downstream은 readiness 하나만으로 성공을 판단하면 안 된다.

## 7. 검증과 재현

단위 테스트는 host Python의 의존성 차이를 피하기 위해 실행 backend 이미지에서 수행한다. mock 행은 tests 안에서만 사용하고 실제 API 기준점은 DB 객체에서 얻는다.

```powershell
docker exec geollm_backend python -m pytest tests/unit/test_attribute_execution_contract.py tests/unit/test_s101_source_mapping.py tests/unit/test_selected_feature_evidence.py tests/unit/test_execution_validator.py tests/unit/test_evidence_builder.py -q
docker exec geollm_backend python -m scripts.check_marine_mapping_runtime --output outputs/marine-mapping/orchestration-v1.jsonl
docker exec geollm_backend python -m scripts.check_selected_feature_runtime --output outputs/selected-feature/orchestration-v1.jsonl
```

출력 경로가 이미 있으면 새 run 이름을 사용한다. 수집 스크립트는 기존 관측 파일을 덮어쓰지 않는다. API readiness를 기다린 뒤 질의를 실행한다. timeout은 실제 task 실패와 구분해서 원본 관측에 남긴다.

관련 단위 62개가 통과했다. 새 테스트는 정상/빈 결과의 typed 계약, 근거 ID 연결, 원천 스키마 장애의 SQL 차단, DB 장애의 FAILED 상태, 조건·snapshot·Feature·geometry·반경 변조를 검사한다. Starlette multipart import deprecation 경고 1건이 있으며 테스트 실패는 아니다.

실제 서비스에서 속성 검색 **10/10**, 선택 객체 조회 **5/5**, 웹·DB **11/11**이 통과했다. 속성 검색 원본은 `outputs/marine-mapping/orchestration-v1.jsonl`, 선택 객체 원본은 `outputs/selected-feature/orchestration-v1.jsonl`이다. 첫 속성 검색은 10.722초, 이후 해당 run의 질의는 1.132~1.736초였으며 cold/warm 조건이 다른 단일 개발 환경 관측이다. 이전 run보다 성능이 향상되었다는 비교 실험 결과로 해석하지 않는다.

단위/계약 통과는 독립 human gold 의미 정확도·F1 측정이나 전체 저장소 테스트 통과를 뜻하지 않는다. 실제 브라우저 클릭·지도 렌더링은 이번 범위에서 검증하지 않았다.

`docker exec geollm_backend python scripts/check_navigation_runtime.py`도 **7/7** 통과했다. 부산/인천 문맥과 명시 지명 우선 적용은 PARTIAL, 위치 없음/먼 기준점/미등록 항만은 NEEDS_CLARIFICATION, 정의 요청은 COMPLETED로 기존 계약을 유지했다.

## 8. 모델·shadow 정책

Qwen은 모델이고 Ollama는 해당 모델을 실행하는 프로그램이다. 이번 변경은 모델 결합이나 모델 교체 작업이 아니다. 규칙·슬롯·registry와 Qwen 후보 평가의 결합은 기존 shadow 정책을 유지한다. 신규 Ollama 추론·calibration·QLoRA 학습은 수행하지 않았다.

모델 평가가 제안한 슬롯을 운영 도구 실행에 자동 반영하지 않는다. registry exact hit 역시 답변 정확도 100%가 아니다. 향후 승격에는 독립 human gold, holdout, calibration, 오류 분석, 자원/지연 검증이 필요하다.

## 9. 남은 P0와 후속 순서

1. 동일 계획/실행/근거 식별 계약을 사고·통항·기타 legacy 경로에 확대하고, semantic router와 ContextResolver의 실제 결정/생략 사유를 통합 감사한다.
2. 공식 PC 규칙 실행 trace를 선택 객체와 연결한다. 현재 Python portrayal 후보만으로 공식 rule/symbol binding 완료를 주장하지 않는다.
3. raw→표준화→serving의 실제 처리 lineage를 보강한다. 행 hash만으로 전체 lineage를 대신하지 않는다.
4. 복합 작업의 작업별 계획과 결과를 구성하고 미지원 부정/제외의 실제 실행 의미를 구현한다.
5. 독립 gold와 동일 후보 shadow 비교를 준비한 뒤 calibration과 지연 개선 효과를 측정한다.

## 10. 전달·변경 관리

관련 코드, registry, 테스트, 이 문서와 remaining_work_roadmap을 함께 커밋한다. `data/feedback/query_quality_issues.jsonl`의 기존 사용자 변경과 outputs 실행 원본은 제외한다. 사용자가 요청한 origin/main push에는 기존 미푸시 `da09b99`, `f845a96`도 함께 포함한다.

문제 발생 시 먼저 해당 실행 ID와 blockers, snapshot hash를 확인한다. 소스 되돌리기가 필요하면 공유 이력을 재작성하지 않고 해당 변경의 revert 커밋으로 처리한 뒤 backend를 재기동하고 단위·실제 API를 재검증한다. DB schema/data migration은 이번 변경에 포함되지 않는다.
