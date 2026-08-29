# S-101 GeoLLM 자연어 공간조회 개발 문서

## 1. 목적

이 문서 세트는 PostgreSQL/PostGIS 기반 S-101 ENC 데이터에 대해 자연어 질문을 안정적으로 해석하고, 검증된 공간 SQL을 자동 생성·실행하기 위한 개발 기준을 정의한다.

현재 시스템의 주요 문제는 질문이 변경될 때 다음 상태로 중단되는 것이다.

- `Intent = N/A`
- `Derived Concept = None`
- `Target Agent = None`
- `Route Plan Status = UNKNOWN`

이를 해결하기 위해 LLM 직접 SQL 생성 방식 대신 다음 파이프라인을 적용한다.

```text
자연어 질문
→ 질의 정규화
→ 해양 객체 개념 해석
→ 위치 해석
→ 의도 및 공간관계 판별
→ 에이전트 라우팅
→ QueryPlan 생성
→ SQL Template Compiler
→ Schema/SRID 검증
→ PostGIS 실행
→ GeoJSON/지도/보고서 출력
```

## 2. 문서 구성

| 파일 | 내용 |
|---|---|
| `01_schema_registry.md` | 실제 테이블·뷰·컬럼·조인 규칙 |
| `02_query_normalization_rules.md` | 자연어 슬롯 추출 및 정규화 규칙 |
| `03_marine_concept_dictionary.md` | 해양 객체 개념·동의어·코드 매핑 사전 |
| `04_place_resolution_rules.md` | 부산항 등 장소명·영역·중심점 해석 규칙 |
| `05_intent_agent_routing_rules.md` | Intent 결정, fallback, Agent 라우팅 |
| `06_query_plan_sql_compiler.md` | QueryPlan JSON 및 SQL 템플릿 컴파일 규칙 |
| `07_error_codes_tests.md` | 오류코드, 로그, 테스트 및 완료 기준 |

## 3. 핵심 원칙

1. `public.feature`는 물리 테이블로 유지한다.
2. 사람이 읽을 수 있는 조회용 뷰는 `public.v_feature_readable`로 별도 생성한다.
3. `feature.nftc`는 정수 코드이며 자연어 문자열과 직접 비교하지 않는다.
4. 자연어 객체명은 `codeinformation.name` 또는 `v_feature_readable.feature_name`에서 검색한다.
5. 객체명과 NFTC 코드는 데이터베이스 조회로 결정하며 임의 하드코딩하지 않는다.
6. LLM은 QueryPlan을 생성하고, SQL은 허용된 템플릿으로 컴파일한다.
7. 모든 동적 값은 bind parameter로 전달한다.
8. SRID 확인 없이 `geom::geography`를 사용하지 않는다.
9. 미해결 슬롯이 있으면 `READY` 상태가 될 수 없다.
10. 실패는 `UNKNOWN`이 아니라 명시적인 오류코드로 반환한다.
