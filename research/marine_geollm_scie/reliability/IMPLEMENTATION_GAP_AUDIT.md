# 운영 구현 감사와 논문 평가 분리

감사 기준 Git `08e03dbcae6aa52c60fdb78cb290bbe1725b9ae8` + dirty 작업트리, 2026-11-01. 정적 코드 감사이며 운영 전체 완료 또는 논문 실험 결과가 아니다. 아래 IMPLEMENTED도 지정한 경로의 구현 상태다. 실제 API 검증은 통합 책임자가 별도 기록한다.

## 실제 수정 범위

최우선 위험은 coverage를 검증하지 않고 SQL 0행을 SUCCESS_EMPTY/COMPLETED로 확정한 radius/bbox 경로다. 최소 수정으로 관측 0행은 보존하되 PARTIAL/NO_EVIDENCE, coverage UNKNOWN, count/total_count=null, observed_count/observed_total_count=0을 반환한다. query_execution_succeeded=true는 이미 수행된 조회의 사실이며 spatial correctness가 아니다. 후처리이므로 GIS 미실행을 주장하지 않는다. 임의 client/provenance VERIFIED flag는 신뢰하지 않는다. 실제 coverage 원천이 없으므로 검증된 빈 결과를 허용하는 분기를 가짜로 만들지 않았다. 다른 executor와 실행 전 coverage gate는 남았다.

이번 추가 fixture 단위검증 7 passed. 이후 execution validator/agent execution/KG ontology 회귀를 합친 실행은 57 passed, 34 warnings, 24.36초(7개 포함; 합산 금지). 실제 API/재기동/모델 실행은 이 감사 에이전트가 하지 않았다. 수정으로 production hash가 바뀌므로 GOLD v2 신규 8방법 전체 실행이 필요하고 기존 K5 결과는 재사용하지 않는다.

## 사례별 구현 상태

| ID | 상태 | 코드 근거 | 확인/잔여 |
|---|---|---|---|
| R-A1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:138` | 승인된 target 집합·명시 제외어 검사와 모호한 등대 차단은 존재. 일반 자연어 의미 일치 및 시설 단위 해소는 미완료. |
| R-A2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:138` | 승인된 target 집합·명시 제외어 검사와 모호한 등대 차단은 존재. 일반 자연어 의미 일치 및 시설 단위 해소는 미완료. |
| R-A3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:138` | 승인된 target 집합·명시 제외어 검사와 모호한 등대 차단은 존재. 일반 자연어 의미 일치 및 시설 단위 해소는 미완료. |
| R-B1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:501` | nearest gate는 반경 필수 아님. 모든 라우터에서 explicit nearest 우선 및 실제 최근접 executor까지 보장되지 않음. |
| R-B2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:90` | 이 radius 경로는 명시거리 없으면 clarification. _distance_policy는 명시입력 기록하나 통합 policy_id/version/출처 구분은 부족. 문서의 1km 예시는 운영 default가 아님. |
| R-B3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:489` | AOI 필수 gate와 query contract 있음. 전 경로 GIS 미실행 계측은 연구 observer에 한정되고 외부도구 관측은 미완료. |
| R-B4 | PARTIALLY_IMPLEMENTED | `services/orchestrator/context_resolver.py:109` | 문맥/레이어 해소 존재. 연구 polygon1137770은 운영 canonical 정책이 아님. geometry 종류·경계 predicate의 전 경로 정책 통일 미완료. |
| R-B5 | PARTIALLY_IMPLEMENTED | `services/orchestrator/context_resolver.py:109` | 문맥/레이어 해소 존재. 연구 polygon1137770은 운영 canonical 정책이 아님. geometry 종류·경계 predicate의 전 경로 정책 통일 미완료. |
| R-B6 | PARTIALLY_IMPLEMENTED | `data/query_template_registry.yaml:31` | radius SQL geography 거리 계산 존재. 모든 polygon 경로가 minimum geometry distance를 보존하는지는 종단 검증 필요. |
| R-C1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:655` | 이번 radius/bbox 후처리에서 coverage 미검증 0행은 PARTIAL/NO_EVIDENCE와 실제 observed_count=0 분리. 실제 coverage 검증 전 gate/검증된 SUCCESS_EMPTY 경로 및 다른 executor는 미완료. |
| R-C2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/schema_binding_adapter.py:330` | metadata_only/미적재 차단 및 시간자료 전용 계약은 존재. 일반 공간/문서의 대상별 부분범위·최신성 증명 gate는 없음. |
| R-C3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/schema_binding_adapter.py:330` | metadata_only/미적재 차단 및 시간자료 전용 계약은 존재. 일반 공간/문서의 대상별 부분범위·최신성 증명 gate는 없음. |
| R-D1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:461` | source_attribute_search는 실제 mapping/filters/FC hash 일치를 다시 검사. 모든 generic plan의 FC feature/attribute/codelist 의미 검증을 뜻하지 않음. KG validator는 node/edge 구조·provenance 검사이지 사용자 의도 정답검사 아님. |
| R-D2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:461` | source_attribute_search는 실제 mapping/filters/FC hash 일치를 다시 검사. 모든 generic plan의 FC feature/attribute/codelist 의미 검증을 뜻하지 않음. KG validator는 node/edge 구조·provenance 검사이지 사용자 의도 정답검사 아님. |
| R-D3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:461` | source_attribute_search는 실제 mapping/filters/FC hash 일치를 다시 검사. 모든 generic plan의 FC feature/attribute/codelist 의미 검증을 뜻하지 않음. KG validator는 node/edge 구조·provenance 검사이지 사용자 의도 정답검사 아님. |
| R-D4 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:973` | 실제 attributes와 객체ID/버전/근거는 반환됨. 모든 객체 실제 값 ↔ FC definition/code locator 결합은 운영 종단 미완료. |
| R-E1 | IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:90` | 확인한 radius 경로의 단위 파싱/비유한·음수·충돌·상한 검사 존재. 이 상태는 해당 경로 코드 범위이며 전체 서비스 정확도 아님. |
| R-E2 | IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:90` | 확인한 radius 경로의 단위 파싱/비유한·음수·충돌·상한 검사 존재. 이 상태는 해당 경로 코드 범위이며 전체 서비스 정확도 아님. |
| R-E3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:485` | source attribute 검색 및 radius 준비에서 EPSG:4326 검사. 일반 validator의 전체 binding SRID와 geometry CRS/변환 사슬 검증은 부족. |
| R-F1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/schema_binding_adapter.py:312` | 등록 도구/template 및 relation/geometry/code column/SELECT 권한 gate 존재. 실제 도구 liveness와 실행 직전 schema drift 및 전 경로 security 검증은 별도 필요. |
| R-F2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/schema_binding_adapter.py:312` | 등록 도구/template 및 relation/geometry/code column/SELECT 권한 gate 존재. 실제 도구 liveness와 실행 직전 schema drift 및 전 경로 security 검증은 별도 필요. |
| R-F3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/schema_binding_adapter.py:312` | 등록 도구/template 및 relation/geometry/code column/SELECT 권한 gate 존재. 실제 도구 liveness와 실행 직전 schema drift 및 전 경로 security 검증은 별도 필요. |
| R-F4 | PARTIALLY_IMPLEMENTED | `services/orchestrator/schema_binding_adapter.py:312` | 등록 도구/template 및 relation/geometry/code column/SELECT 권한 gate 존재. 실제 도구 liveness와 실행 직전 schema drift 및 전 경로 security 검증은 별도 필요. |
| R-G1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:21` | slots/spatial/data/tool 변경 hash 무효화, merge_slot_patch 승인 제거 존재. semantic_resolution/feature_bindings/snapshot_versions/provenance의 정책변경은 현재 hash 대상 아님. |
| R-H1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/request_obligations.py:134` | 출력 obligation 감사와 PARTIAL 강등 존재. spatial/evidence별 완전성·비교 공통범위·객체 oracle까지 전면 검사하지 않음. |
| R-H2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/request_obligations.py:134` | 출력 obligation 감사와 PARTIAL 강등 존재. spatial/evidence별 완전성·비교 공통범위·객체 oracle까지 전면 검사하지 않음. |
| R-H3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/request_obligations.py:134` | 출력 obligation 감사와 PARTIAL 강등 존재. spatial/evidence별 완전성·비교 공통범위·객체 oracle까지 전면 검사하지 않음. |
| R-I1 | NOT_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:978` | feature ID 중복검사만 있고 동일 실재 시설 across feature dedup의 고정 정책/근거는 없음. |
| R-J1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/evidence_builder.py:176` | 객체 source/version/evidence ID 및 KG/RAG 구분 존재. source 적합성/공식판/설명판 동등성은 모든 응답에 검사되지 않음. |
| R-J2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/evidence_builder.py:176` | 객체 source/version/evidence ID 및 KG/RAG 구분 존재. source 적합성/공식판/설명판 동등성은 모든 응답에 검사되지 않음. |
| R-J3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/evidence_builder.py:176` | 객체 source/version/evidence ID 및 KG/RAG 구분 존재. source 적합성/공식판/설명판 동등성은 모든 응답에 검사되지 않음. |
| R-K1 | PARTIALLY_IMPLEMENTED | `shared/schemas/agent.py:241` | slot patch 이력/재검증과 연구 lossless compiler 존재. bounded recovery 이후 의미보존 측정·권한/coverage 불변식의 공통 operational engine은 미완료. |
| R-K2 | PARTIALLY_IMPLEMENTED | `shared/schemas/agent.py:241` | slot patch 이력/재검증과 연구 lossless compiler 존재. bounded recovery 이후 의미보존 측정·권한/coverage 불변식의 공통 operational engine은 미완료. |
| R-K3 | PARTIALLY_IMPLEMENTED | `shared/schemas/agent.py:241` | slot patch 이력/재검증과 연구 lossless compiler 존재. bounded recovery 이후 의미보존 측정·권한/coverage 불변식의 공통 operational engine은 미완료. |
| R-K4 | PARTIALLY_IMPLEMENTED | `shared/schemas/agent.py:241` | slot patch 이력/재검증과 연구 lossless compiler 존재. bounded recovery 이후 의미보존 측정·권한/coverage 불변식의 공통 operational engine은 미완료. |
| R-L1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/schema_binding_adapter.py:330` | metadata_only/미적재 차단 및 시간자료 전용 계약은 존재. 일반 공간/문서의 대상별 부분범위·최신성 증명 gate는 없음. |
| R-L2 | PARTIALLY_IMPLEMENTED | `services/orchestrator/execution_validator.py:562` | traffic/time-series의 기간/원천 계약 존재. 전체 temporal operation의 required/default provenance 일관성 미완료. |
| R-M1 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:655` | 이번 radius/bbox 후처리에서 coverage 미검증 0행은 PARTIAL/NO_EVIDENCE와 실제 observed_count=0 분리. 실제 coverage 검증 전 gate/검증된 SUCCESS_EMPTY 경로 및 다른 executor는 미완료. |
| R-M2 | IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:981` | 확인한 radius/bbox 경로 count/returned/offset/truncated 분리와 반환수·중복 검증 존재. 전체 executor로 일반화한 완료 아님. |
| R-M3 | PARTIALLY_IMPLEMENTED | `services/orchestrator/s101_radius_execution.py:90` | 이 radius 경로는 명시거리 없으면 clarification. _distance_policy는 명시입력 기록하나 통합 policy_id/version/출처 구분은 부족. 문서의 1km 예시는 운영 default가 아님. |

## 12개 판단 질문의 답

1. 잘 통제되는 범위: 확인한 radius 경로의 명시거리 정규화·비유한/음수/상한 차단, 반환 객체 ID/건수 일관성, 승인 후 slot 변경 무효화.
2. 부분 구현: semantic binding, CRS, 시간/범위, evidence, composite completeness, 도구 runtime, recovery. 정적 존재와 실제 API 통과를 구분한다.
3. 가장 위험한 silent failure: 범위 미검증 0행을 실제 부재로 확정. 이번 최소수정은 radius/bbox 답변만 보완한다.
4. dataset coverage deterministic gate: 일반 공간 실행 전에는 아직 없다. 테이블 존재/적재상태는 공간 coverage가 아니다.
5. reference geometry: 연구 단일 부산 polygon 고정은 운영 전체 canonical policy가 아니다. 운영은 resolver/사용자 선택 문맥별이며 경계 선택 정책 통합이 필요하다.
6. default distance: 해당 radius는 명시거리 필수이며 provenance 일부 존재. 모든 경로의 policy_id/version/source 통일은 미완료. 문서 1km 예시를 바로 적용하지 않았다.
7. boundary/distance/dedup: SQL geography 거리 구현은 있으나 전체 정책 일관성과 시설 dedup 미완료.
8. composite: 출력 obligation 감사로 PARTIAL 가능하나 subtask별 spatial oracle+evidence+scope 완결 gate는 미완료.
9. empty 구분: TaskResultStatus에 SUCCESS_EMPTY 존재, 이번 두 경로 unknown 0은 NO_EVIDENCE. 실제 out-of-coverage 검출과 verified-empty 복귀는 미완료.
10. recovery: slot 변경 이력은 존재. 실제 recovery success와 semantic preservation의 통일된 운영 측정은 없다.
11. evidence: 일부 공간 경로 객체 ID/source/version/evidence 연결 가능. 전체 object attribute ↔ FC 판·정의·코드 원문 연결의 의미 정확도는 별도 검수.
12. RQ 측정: 연구 observer/metric 코드 일부 존재하나 8방법과 fault/recovery 동일조건 종단연결은 준비중. 운영 instrumentation만으로 논문 RQ 전체 결과가 이미 있다고 말할 수 없다.

## 스키마와 승격 정책

PlanStatus에는 PARTIAL 없음(실행준비 판단); AgentStatus에는 PARTIAL 존재(응답/작업 집계); TaskResultStatus에는 SUCCESS_EMPTY/NO_EVIDENCE/FAILED가 있음(개별 결과). 서로 다른 단계의 상태를 단일 enum으로 합치지 않는다. QEC 확장 전 provenance/spatial/snapshot_versions에 구조화하고 deterministic gate가 읽는 입력만 명시 계약으로 승격한다. 새로운 coverage/geometry/default 정책을 넣으면 authorization hash에도 해당 입력을 포함해야 한다.

## 다음 실행 및 수용 기준

1. 실제 API 정상 양성/관측 0/DB 실패/누락 geometry를 별도 운영 audit run에 저장하고 최종 본문·map·evidence 숫자 일치를 검증한다.
2. 권위 있는 원천 coverage(대상별·공간·시간·판)를 확보하고 SQL/GIS로 검증한 후 ExecutionValidator 전 gate를 추가한다. 모르면 UNKNOWN으로 둔다.
3. source/geometry/boundary/default/dedup 및 recovery 불변식을 일반 정책으로 고정한다. 특정 지명/문항 ID 분기 금지.
4. source hashes를 새 동결 run에 기록한 뒤 RQ별 동일 fault와 8방법을 실행한다. 연구 정책을 production에 자동 배포하지 않는다.
5. 전 taxonomy의 status와 runtime 검증 evidence가 닫히기 전 완성된 시스템이라고 선언하지 않는다.
