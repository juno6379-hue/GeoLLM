# GOLD v2 Oracle 검증과 동일 초기 계획 비교

최신 참조는 `benchmark/gold_v2_20261031_r2/manifest.json`이다. 이전 GOLD·K5 원본은 보존했다. 본 문서는 **정답 참조와 실험 분기 준비 결과**이며 8개 방법 재실험 결과가 아니다. 사용자 승인 범위와 독립 전문가 검수를 구분하며 독립 검수 결과는 아직 수령하지 않았다.

## 승인한 평가 구분

| 사례 | 새 평가 기준 | 현재 검증 |
|---|---|---|
| Q3-01 독도 최근접 등대 | DATA_OUT_OF_SCOPE, 공간 객체 GOLD 없음 | 부산청 항로표지 원천·연구 snapshot 범위 확인 |
| Q3-02 부산항 안 정박지 | 고정 항계 polygon이 대상 전체 형상을 덮는 ST_Covers | 지정 polygon 기준 0개. 부산항 전체 정박지 0개라는 의미 아님 |
| Q3-03 선택 영역 없는 교차 검색 | NEEDS_USER_INPUT, 실행 시도 false | 별도 실제 graph 무모델 진단 7/7, 과거 K5는 소급 통과로 바꾸지 않음 |
| Q5-01 독도 등대+Wreck | 두 공간 하위작업 모두 BLOCKED_DATA, 표준 근거는 선택적 PARTIAL_RESPONSE | 공간 정답 집합은 null. 빈 목록을 GOLD로 사용하지 않음 |
| Q5-02 부산항 주변 2km | 단일 항계 polygon과 대상 형상 사이 최소 지오데식 거리 ≤2,000m | 정박지 3개·제한구역 21개, 객체 ID·형상·거리·원천 저장 |
| Q5-03 독도 Wreck+속성 | 공간 BLOCKED_DATA, FC 속성 설명은 별도 문서 과제 | 독도 실제 객체 값은 생성하지 않음 |

독도 세 문항은 Spatial Correctness와 Execution–Correctness Gap의 공간 정답 분모에서 제외하고 Safe Abstention으로 평가한다. 실제 속성 값↔FC 정의 연결은 별도 부산권 보충 사례에 적용한다. 원래 독도 문항을 부산 문항으로 덮어쓰지 않으며 보충 사례는 기존 18개와 별도 cohort로 관리한다. 사용자가 구성하겠다고 한 보충 질의는 아직 최종 입력 집합에 추가하지 않았다.

## 단일 항계와 독립 검산

- 연구 기준 객체 **1137770**, dataset/version **540/540**, dataset_name **101KR00658D00.000**, layer **projection.s101_feature_current / HarbourAreaAdministrative**, CRS **EPSG:4326**.
- `min_scale=16`, `max_scale=18`, 속성 `scaleMinimum=17999`. 이 필드들의 의미를 서로 바꿔 부르지 않는다.
- 선택 정책: 정확한 부산항 명칭·유효 polygon → snapshot 2km 범위를 충족 → 최대 상세 단계 → 면적 내림차순·ID 오름차순. 법적 항계 증빙은 별도 확인되지 않았으므로 **연구 snapshot의 명시적 항계 객체**로만 고정한다. 전체 부산항의 법적 경계라고 주장하지 않는다.
- snapshot bbox 내부이며 경계까지 최소거리 4,561.66668103m. 상세 단계에서 면적이 더 큰 1152961·1153280은 snapshot 밖/경계 접촉으로 2km 평가 범위를 보장하지 못해 선택하지 않았다. 결과 객체 개수를 보고 기준점을 고른 것이 아니다.
- 원본 EWKB SHA256, 데이터 snapshot hash, 전체 EWKB와 dataset/version/축척 필드는 `canonical_busan_boundary.json`에 기록했다. 내부/겹침 대상은 polygon 면과 거리 0이며, 항계 테두리 선과의 거리가 아니다.
- 실제 DB의 항로표지·S-101 전체 COPY를 재추출해 동결 CSV SHA256과 각각 일치 확인. 독립 READ ONLY SQL과 Shapely에서 단일 경계의 covers/intersects를 대조했고, ST_DWithin과 ST_Distance≤2000의 집합도 대조했다. 최종 v3의 정박지·제한구역 **109개 기록 검사 전부 일치**. Shapely/PostGIS가 GEOS를 공유하므로 완전히 독립적인 수치 알고리즘 검증이라고 과장하지 않는다.
- Q5-02 비교 기준은 유형별 개수, 유형별 최소·최대 거리(허용 오차 0.01m), 서로 다른 FC 객체 정의 근거, 원천/기준 영역 공개로 고정했다. 이 기준을 실행 결과를 본 뒤 바꾸지 않는다.
- 부산권 Wreck 172개에서 실제 값 **805개**를 FC 2.0.0의 해당 Feature 바인딩·정의·locator/hash에 연결했다. 그중 열거 코드 의미 연결 362개, 원시 값+정의 연결 443개. 이는 805개 값의 측정 정확도·현행성 검증을 뜻하지 않는다. 독도 속성 GOLD로 사용하지 않는다.

원본 위치: `outputs/gold_v2_oracle_audit_20261031_v3`. 최초 v1은 독립 SQL 60초 timeout으로 실패했으며 SQL/실패 기록을 보존했다. v2의 여러 축척 항계 union에서는 RestrictedArea 1181349의 covers 판정이 SQL과 Shapely에서 달랐다. EWKB로 다시 검사해도 차이가 유지되어 GeoJSON 반올림 탓으로 확정하지 않았다. union/연산 순서·엔진 차이 원인은 미확정이며 해당 union을 GOLD로 채택하지 않았다. 사용자 승인에 따른 단일 polygon v3의 전수 대조는 일치한다.

## B3·B4·P0·H의 동일 초기 계획

사용자 승인 설계:

```text
B3 Tool Agent → Frozen Initial Plan / plan_hash
  B3: 그대로 실행
  B4: LLM Review 후 실행
  P0: lossless QEC compilation → Deterministic Validator
  H : LLM Review → lossless QEC compilation → 같은 Validator
```

`matched_branches.py`가 원본 계획 파일·hash를 고정하고 분기별 deep copy, 검토 후 hash, 실패 원본을 보존한다. B4/H는 검토 결과도 한 번 생성해 공유하므로 Validator 유무 외 검토 출력 변동을 제거한다. 원본 계획 변조/덮어쓰기는 거절한다. 초기 생성·검토 비용은 공유 비용과 각 방법을 단독 실행할 때의 비용을 구분해 보고해야 한다.

P0/H 분기는 실제 공통 `is_execution_authorized`를 사용한다. 모든 하위 QEC의 승인 없이는 전체 계획 실행 callback을 호출하지 않는 정책이다. 부분 계획을 재작성해 실행하지 않는다. 실제 model/reviewer/DB adapter는 아직 연결·통합 검증하지 않았다. callback을 호출했다는 사실을 SQL 성공 또는 execution_attempted의 대체 증거로 사용하지 않는다.

P1은 독립적인 전체 GeoLLM 경로이며 동일 입력·원천·GOLD를 적용한다. B0/B1/B2는 각각 Direct LLM/Text RAG/Ontology-KG로 분리한다. 기존 K5에서는 B0도 도구 호출을 허용했으므로 이를 새 B0로 이름만 바꿔 재사용하지 않는다. 기존 P도 P0/H/P1 세 조건으로 분할 복제하지 않는다.

## P0 무손실 컴파일

`baselines/lossless_qec.py`는 순수 구조 변환이다. lookup/LLM 호출 없이 원문 계획 전체와 hash, 필드별 원본 경로, MISSING 목록을 보존한다.

- 허용: 명시적 `5 km → 5000m`, literal 필드명 변환, 단일 feature를 길이 1 목록으로 변환.
- 금지: 누락 CRS/형상 추론, Feature 오타 수정, dataset 자동 선택/재선택, 다른 하위작업·상위 계획의 생략 필드 보충, 새로운 분석 작업 선택.
- 누락은 typed QEC에서 null, trace에서는 MISSING. 음수 거리·잘못된 feature/dataset/CRS는 고치지 않고 Validator 입력으로 유지한다. 단위 불명·명시 값 충돌·스키마 불일치는 원본을 보존하고 컴파일 오류로 분리한다.
- Validator 호출 뒤 semantic slots가 바뀌거나 누락 dataset이 채워지거나 명시 dataset이 달라지면 branch error로 차단한다. 실행 승인 토큰을 컴파일러에서 만들지 않는다.
- **주의:** 운영 SchemaBindingAdapter는 source binding을 자동 생성할 수 있으므로 실제 P0 adapter에서 이 규칙을 통과하는지 아직 확인해야 한다. 컴파일러 단위 통과를 P0 실제 실행 완료로 표현하지 않는다.

최종 관련 테스트 **33 passed**. 실제 모델 생성/8조건 DB 실행은 미수행이다. Q3-03의 이전 31개와 중복되므로 합산하지 않는다.

## 재채점과 새 실행의 구분·다음 단계

GOLD만 바뀌고 시스템·adapter·모델 profile·snapshot·입력·방법 정의가 같으며 필요한 관측이 모두 존재하면 원본 raw를 새 폴더에서 재채점한다. 빠진 로그는 null이며 새 로그를 옛 응답에 붙이지 않는다.

이번에는 운영 코드와 observer가 바뀌었고 B0 방법 정의 및 P0/H 분기까지 달라졌으므로 **새 동결 전체 실행이 필요**하다. 현재 참조 manifest는 `model_comparison_ready=false`다.

다음 필수 작업:

1. 보충 부산권 질의가 확정되면 별도 cohort에 object-level GOLD를 계산한다. 원래 18개를 조용히 치환하지 않는다.
2. 동일 source/profile의 B0/B1/B2 어댑터, 공통 B3 초기 계획 생성, B4/P0/H 실 reviewer·Validator·executor를 연결하고 정상/차단 사례로 검증한다. P1의 단일 기준 polygon 전달과 실제 결과 어댑터도 검증한다.
3. GIS 실행과 문서/metadata SQL을 구분하는 공통 관측을 8개 방법에 적용한다. 기존 Q3 observer의 전체 SQL 보수 관측을 그대로 문서 PARTIAL 과제의 GIS 시도로 오판하지 않도록 한다.
4. 공통 v2 evaluator를 실제 출력/실행 기록에 연결한다. 현재 순수 채점 함수·gate·분기 단위 검사는 구현했지만 전체 어댑터 통합은 미완료다. 의미 설명의 독립 검수와 기계 검사를 분리한다.
5. 새 snapshot lineage/profile/소스/GOLD hash를 고정하고 사전 gate 통과 후 K1 전체8조건 → 실패 분석 → 변경 없을 때 K5를 실행한다. 실패를 제거하거나 완료 gate를 우회하지 않는다.
