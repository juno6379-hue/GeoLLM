# 오류코드, 로그 및 테스트 규칙

## 1. 오류코드

| 코드 | 의미 | 처리 |
|---|---|---|
| `CONCEPT_NOT_RESOLVED` | 객체 개념 미해석 | 동의어·코드 후보 재검색 |
| `FEATURE_CODE_NOT_FOUND` | 실제 NFTC 코드 없음 | DB 후보 표시 |
| `MULTIPLE_FEATURE_CODES` | 코드 후보 다수 | 문맥·지오메트리로 재평가 |
| `LOCATION_NOT_RESOLVED` | 장소 해석 실패 | 후보 또는 지도 위치 요청 |
| `MULTIPLE_LOCATION_CANDIDATES` | 장소 후보 다수 | 전체/북항/신항 선택 |
| `SRID_UNKNOWN` | SRID 0 또는 미확인 | 공간 거리 실행 차단 |
| `SRID_MISMATCH` | 서로 다른 SRID | 변환 정책 적용 |
| `INVALID_GEOMETRY` | 유효하지 않은 geometry | 오류 반환 또는 보정 후보 |
| `SQL_SCHEMA_VALIDATION_FAILED` | 없는 컬럼/테이블 | 실행 차단 |
| `SQL_TEMPLATE_NOT_FOUND` | 템플릿 미지원 | 지원 Intent로 재분류 |
| `SQL_EXECUTION_FAILED` | DB 실행 실패 | SQLSTATE 포함 로그 |
| `EMPTY_RESULT` | 결과 0건 | 정상 완료, 범위 확장 제안 가능 |
| `UNRESOLVED_SLOTS` | 필수 슬롯 누락 | ClarificationAgent 호출 |

## 2. 로그 구조

```json
{
  "query_id": "Q-20260731-001",
  "original_query": "부산항 반경 1km 내 선석을 찾아줘",
  "normalization": {},
  "concept_resolution": {},
  "place_resolution": {},
  "intent_resolution": {},
  "query_plan": {},
  "sql_template_id": "feature_dwithin",
  "bind_parameters": {
    "place_id": "BUSAN_PORT",
    "nftc_codes": [153],
    "distance_m": 1000,
    "result_limit": 100
  },
  "srid_check": {
    "source_srid": 4326,
    "transform_applied": false
  },
  "execution_time_ms": 83,
  "result_count": 12,
  "status": "COMPLETED",
  "error_code": null
}
```

## 3. 단위 테스트

- 선석 → `MARINE_BERTH`
- 방파제 → `MARINE_BREAKWATER`
- `Land Area` → `%Land%Area%`
- `Depth Contour` → `%Depth%Contour%`
- 부산항 장소 해석
- 부산항 북항/신항 모호성 처리
- km→m 변환
- Intent fallback
- Agent routing
- unresolved slot 차단
- SRID 4326 허용
- 비4326 변환
- SRID 0 차단
- SELECT-only 검증
- LIMIT 강제

## 4. 통합 테스트 질문

1. 부산항 반경 1km 내 선석을 찾아줘.
2. 부산항에 있는 방파제를 보여줘.
3. 부산항에서 가장 가까운 등대는 어디인가?
4. 부산항 내 정박지는 몇 개인가?
5. 부산항의 선석과 항로가 교차하는 구간을 찾아줘.
6. 반경 500m 이내의 Land Area를 찾아줘.
7. 북항 주변의 Depth Contour를 보여줘.
8. 부산항을 찾아줘.
9. 선석을 찾아줘.
10. 부산항 신항 주변 시설을 찾아줘.

각 테스트는 다음을 검증한다.

```text
normalization
concept resolution
place resolution
intent
agent
QueryPlan
SQL template
bind parameters
SRID policy
result schema
failure code
```

## 5. 완료 기준

- 동일 질문 10회 반복 시 동일한 Intent와 Agent 선택
- 자연어 객체명과 `feature.nftc` 직접 비교 없음
- `public.feature`와 동일 이름의 뷰 생성 없음
- 모든 SQL이 Schema Registry 검증 통과
- 모든 동적 값이 bind parameter로 전달
- SRID 0에서 geography 연산 차단
- unresolved slot 존재 시 `READY` 금지
- 실패 시 `UNKNOWN` 대신 명시적 오류코드 반환
- 부산항 선석 질문이 `SpatialQueryAgent`로 정상 실행
- 결과에 `id`, `nftc_code`, `feature_name`, `geometry_type`, `geojson`, `distance_m` 포함
