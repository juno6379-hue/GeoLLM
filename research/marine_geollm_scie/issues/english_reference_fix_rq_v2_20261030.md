# 영어 거리 조건의 기준위치 추출 수정

## 실제 API에서 확인한 문제

`Find marine place names within 5 km of Dokdo.`를 실제 API에 보냈을 때 기준위치가 `Find marine place names within`으로 추출되어 `NEEDS_CLARIFICATION`이 반환됐다. 원형 한국어5km/5000m 질의는 정상 검색됐다. 재현 원본은 `outputs/scie_q4_live_20261030_v1/api_rows.jsonl`이다. 이번 수정은 일반 영어 문법 계약을 바로잡으며 GOLD 파일을 읽거나 지명/정답 ID를 runtime에 추가하지 않았다.

## 호출 경로 감사와 실패 보존

첫 수정은 `semantic_router.DynamicSlotExtractor`의 거리 앞 추출을 보완했고 경량 단위검증은 통과했다. 그러나 실제 API7건은 여전히 동일 prefix 문제를 보였다. 이를 `runs/20261030_english_reference_rq_v2_after/`에 보존했다. 실제 해양지명 fast path가 `graph._requested_layer_anchor_query`의 별도 추출 함수를 사용하기 때문이다. 이 실패는 단위검증만으로 운영 수정 완료를 주장할 수 없다는 근거다.

최종 변경은 공통 `extract_english_radius_reference` helper를 두 경로가 사용하도록 연결했다. `within <수치><단위> of <장소>`에서 뒤의 장소 문자열을 후보로 취하며, 성공 여부와 후보 부재를 구분하는 handled 플래그로 'of/장소가 없음'을 legacy prefix 추출로 되돌리지 않는다. 복수 반경도 임의의 하나를 선택하지 않는다. 복수 장소 문자열은 보존하여 실제 지명 resolver가 모호성을 판단한다. 추출은 좌표·출처·실행 권한을 부여하지 않는다.

수정 파일은 `services/orchestrator/semantic_router.py`와 `services/orchestrator/graph.py`의 anchor 함수 연결이다. 앞선 복합 출력의무 수정은 유지한다. 독도·부산항 등의 literal 특례, GOLD ID 목록, 임의 좌표, 거리 clamp 변경은 없다.

## 검사

신규 `tests/unit/test_english_radius_reference.py`는 일반 영어 참조·복합 설명절·한국어 기존분기·없는 장소·복수 장소·거리구문/장소 누락을 검증한다. 실제 graph anchor 함수도 직접 호출하여 첫 수정에서 빠진 호출 경로를 검증한다. 신규18건과 기존 복합출력13건을 합쳐 **31 passed**(격리 Docker/network none,32.16초)다. 앞선 실제graph4건을 포함한 호스트 검사는28 passed였고, 이후 누락/multiple/Korean분기3건을 추가한31건을 최종 검사했다.

backend는 기존 services bind mount의 수정 Python 모듈을 다시 로드하도록 재시작했다. 이미지 재빌드·UI 변경·다른 source copy·업무 DB 변경은 하지 않았다. 실제 지명 원천이 확인되지 않거나 여러 기준점이면 실행하지 않아야 한다. 최종 실제 API7건은 `runs/20261030_english_reference_rq_v2_after_shared/`에 별도로 저장하며 결과를 아래에 추가한다.


## 추가 실제 실패와 최종 검증

`after_shared`의 7건 중 독도는 완료됐지만 `Dokdo and Ulleungdo`도 완료되는 결함이 드러났다. 전체 문자열을 유지해도 resolver가 자유문 중 알려진 부분 지명 하나만 선택했기 때문이다. 이 실패 원본도 보존했다. 영어 반경 문법에서 추출한 전체 이름을 명시 `location_text`로 넘겨 기존 resolver의 exact 비교를 사용하도록 최소 연결했다. 기존 명시 geometry/place_id/위치 문맥은 보존한다. `and`라는 단어 자체를 거부하지 않으며 synthetic `Trinidad and Tobago` 등록명 성공으로 확인했다.

최종 raw: `research/marine_geollm_scie/runs/20261030_english_reference_rq_v2_after_exact/`. `manifest.json`에 운영 모듈 3개 해시와 배포 범위를 저장했다. `api_rows.jsonl` 7건과 별도 `busan_alias.jsonl` 1건 모두 terminal이며 timeout은 없었다.

| 실제 질의 구분 | 최종 상태 | 해석 |
|---|---|---|
| Dokdo 5km | COMPLETED | 정상 실행. 독립 공간 정답 대조는 부모 연구 run에서 별도 수행 |
| BUSAN HANG 2km | COMPLETED | 실제 `serving.island_gazetteer_current`의 정확한 영어 별칭 사용; 독도 literal 특례 아님 |
| 부산항 2km | NEEDS_CLARIFICATION | 기준명 추출 정상. harbour:598357와 island:d2c4608aecb2e09b7cb7d0f7의 서로 다른 좌표 후보가 있어 선택 필요 |
| 울릉도 2km | NEEDS_CLARIFICATION | 기준명 추출 정상, 현재 resolver 원천 후보 0. 일반 지명이 존재하지 않는다는 뜻은 아님 |
| 장소 누락 | NEEDS_CLARIFICATION | 실행하지 않음 |
| Dokdo and Ulleungdo | NEEDS_CLARIFICATION | 알려진 첫 지명만 임의 선택하지 않음 |
| 미등록 합성 이름 | NEEDS_CLARIFICATION | 실행하지 않음 |
| Dokdo 60km | NEEDS_CLARIFICATION | 기존 최대50km 계약 유지 |

부산항·울릉도 확인 요청을 정상 검색 성공 수에 포함하지 않는다. 지명 공급원의 중복·범위 문제는 별도 데이터 후속 작업이며 이 수정에서 좌표를 창작하거나 후보를 승격하지 않았다.

최종 단위검사는 영어20건+복합의무13건 **33 passed**, Docker network none,33.99초다. 실제 fast execute node가 resolver에 전체 location_text를 전달하는지 검사했고 단일 고유명의 conjunction 허용 검사도 추가했다. 운영 수정은 graph와 semantic_router, 이전 복합의무 모듈에 한정한다. 사용자 UI·기존 place integration test·GOLD를 수정하지 않았다.

연구 관측기 3개는 terminal 미도달을 `OBSERVATION_TIMEOUT`으로 분리했다. 기존 raw 중 CAPTURED35건을 감사했을 때 비terminal은0건이었다. 기존 raw는 고치지 않았다. 이는 연구 어댑터 진실성 보완이며 운영 라우팅 변경과 구분한다.
