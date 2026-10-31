# 새 동결 실행에서 관측한 후속 수정 계획

2026-11-01. 이 문서는 **읽기 전용 진단·수정 제안**이다. 실행 중인 `20261101_gold_v2_eight_k1_v1`의 동결 소스·profile·GOLD·raw output은 변경하지 않았다. API/DB/모델 호출도 추가하지 않았다.

원본: `research/marine_geollm_scie/runs/20261101_gold_v2_eight_k1_v1/graph/production_rows.jsonl`. 아래는 P1의 실제 final_dict/QEC/실행 관측과 현재 코드 경로를 대조한 결과이며 모델 전체 우열이나 RQ 전체 결론이 아니다.

## 관측과 원인 분리

| 문항 | 실제 관측 | 코드상 원인 | 분류 |
|---|---|---|---|
| Q3-01 독도 최근접 등대 | NEEDS_CLARIFICATION / DISTANCE_REQUIRED. 독도 POINT는 확인했으나 place_lookup QEC, distance=null | `_nearest_target_features_from_query`는 Anchorage/Mooring만 지원한다(graph.py:384). 항로표지 레이어 요청은 `fast_requested_spatial_layer_execute_node`로 들어가 명시 nearest도 radius 필수 검사를 받는다(4893~4941) | 명시 공간연산을 반경 조회로 축약하는 routing/계약 오류. 등대 시설·등화 대상 해소와 source coverage는 별도 잔여 |
| Q3-02 부산항 영역 안 정박지 | LOCATION_UNCONFIRMED. 해석 위치에 '부산항 영역 안'이 남고 target_layers=anchorage_area/anchorage_point | generic layer 후보가 S-101 AnchorageArea 계약보다 앞선다. anchor extraction이 영역 연산을 슬롯으로 분리하지 못하고, handler는 점+radius 계약뿐이다(graph.py:1991,2057,4893) | operator/target source 선택 오류 + polygon registry 인터페이스 미구현 |
| Q5-02 부산항 주변2km 정박지+제한구역 비교 | LOCATION_UNCONFIRMED. distance2000은 추출했으나 target_layers에 정박지2개만 있고 RestrictedArea와 비교 산출물은 없다 | generic layer 부분 후보로 바로 fast path 선택(`_should_fast_execute_requested_spatial_layer`는 후보가 하나라도 있으면 true). 두 대상/비교 obligation을 만족하는지 검사 없이 진입 | 복합과업 누락 + polygon registry 인터페이스 미구현 |

세 사례 모두 관측 범위 내 `execution_attempted=false`, `execution_started=false`, `tool_called=false`, `sql_executed=false`였다. 따라서 잘못된 GIS 결과를 생성한 사례로 세면 안 된다. 다만 요청과 무관한 반경/위치 확인을 요구하므로 올바른 safe abstention으로 자동 채점할 수도 없다. 연구 GOLD의 독도 범위 밖 행동과 현재 DISTANCE_REQUIRED는 다른 이유다.

## canonical polygon이 전달됐는데 사용되지 않은 이유

공통 입력에는 `spatial_context.reference_geometries.canonical_busan_port_boundary`가 있다. 그러나 실제 입력의 `geometry_ref`나 `geometry`는 없다. 이는 사용할 수 있는 참조 레지스트리를 전달한 것이며 특정 geometry를 사용자 선택으로 전달한 것과 다르다.

현재 `place_resolver.resolve_location`은 `place_id/place_version` 또는 `geometry`를 처리하며 `reference_geometries`/`geometry_ref`를 읽지 않는다(`services/spatial_analysis_agent/place_resolver.py:269`). `geometry`도 `_point`로 검증한다. 따라서 polygon을 그 필드에 강제로 넣는 것만으로 해결되지 않는다. 연구 adapter는 명시 geometry_ref를 지원하지만 production P1은 같은 인터페이스를 아직 지원하지 않는다는 차이를 보고해야 한다. 입력의 레지스트리를 무조건 첫 항목으로 선택하거나 centroid로 바꾸면 안 된다.

## 최소 일반 수정 순서 — 현재 run 종료 후

1. **연산·산출물 계약을 fast path 앞에서 확정한다.** 명시 nearest/within/covers/intersects/dwithin, 다중 Feature, 비교/설명 산출물을 구조화한다. generic radius fast path는 해당 연산·모든 하위작업을 지원할 때만 선택한다. 단일 키워드 우선순위 변경으로 끝내지 않는다.
2. **공통 참조 geometry 인터페이스를 정의한다.** point navigation과 polygon analysis를 분리하고, 명시 geometry_ref 또는 등록명에 유일하게 결합된 참조를 hash/version/CRS/출처와 함께 검증한다. 후보 복수·충돌·출처 미확인은 clarification/config block. 연구 reference를 운영 법적 항계로 승격하지 않는다.
3. **조회 대상과 source identity를 유지한다.** AnchorageArea 요구를 정박지 점/면 Dataset 두 레이어로 자동 치환하지 않는다. 대체 원천을 허용하려면 target mapping·의미범위·coverage가 명시적으로 검증돼야 한다. RestrictedArea subset도 전체 제한구역으로 취급하지 않는다.
4. **연산별 실행기를 연결한다.** nearest는 최대반경 없이 top_k/시설 dedup/source scope를 검사한다. area는 승인 polygon과 사전 고정 predicate, polygon 주변거리는 geometry-to-geometry geodesic distance를 사용한다. 지원되지 않으면 '반경 누락'이 아니라 정확한 unsupported/config/data 이유로 중단한다.
5. **coverage는 서버에서 검증한다.** profile에 전달된 source_coverage를 임의 클라이언트 플래그처럼 신뢰하지 않는다. 연구 실행에는 동결 snapshot identity에 연결된 서버 adapter 계약을 제공하고 운영에는 실제 source scope를 별도로 확보한다. 독도라는 이름별 분기는 금지한다.
6. **복합 결과를 하위작업별로 합친다.** 정박지 집합/제한구역 집합/각각 근거/비교 기준/상호 source scope가 모두 있어야 full success. 하나만 있으면 PARTIAL이며 누락을 명시한다.

## 수정 후 검증 기준

- 서로 다른 지명·영문/국문·공간 연산을 사용한 일반 단위 회귀. nearest를 dwithin으로 바꾸거나 radius를 요구하지 않는지 검사.
- ref 누락/복수/잘못된 hash·CRS/point↔polygon 불일치/범위 밖/허용 source 없음에서 GIS 미실행을 관측.
- 두 하위대상 중 하나가 없거나 비교 결과가 없으면 COMPLETED를 금지.
- 실제 API 정상/부정 사례와 independent SQL/GIS 결과 대조. fixture 통과로 production 완성을 선언하지 않는다.
- 동결 중에는 적용하지 않는다. 변경 이후에는 새 source/profile/input hash의 전체8방법 재실행을 수행한다. 기존 raw 실패를 교정된 답안으로 덮어쓰지 않는다.

연구 공통 입력에 '명시 선택 geometry_ref'를 새로 추가해야 한다면, 이는 단순 코드 수정이 아니라 입력 조건 변경이다. 8방법 모두 같은 새 입력을 받고 별도 input version을 기록해야 한다. 특정 문항 ID에만 geometry를 주입하는 방식은 금지한다.
