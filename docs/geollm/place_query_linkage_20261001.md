# 지명 해석→위치 검증→검색 응답 연결 (2026-10-01)

## 실제 원인

사용자 요청 `울릉도 주변 지명을 찾아줘`의 task `67d5d42d-5a7d-4ee5-a9e3-1341fce60aa0`를 확인했다. Qwen shadow는 location=울릉도로 추출했고 실제 route도 공간 지명 검색으로 분류했다. 그러나 별도 위치 해소기에 `울릉도`만 직접 요청해도 LOCATION_UNCONFIRMED였다. 실제 원천 catalog 2,058개, unavailable_sources=[]이며 울릉항·울릉분지 등은 있으나 울릉도 기준점은 해소되지 않았다. 원천 전체에 울릉도가 없다는 주장으로 확대하지 않는다.

추가 대조 질의 `울릉항 반경 5km 지명을 찾아줘`는 위치가 확인돼도 실행 Gate에서 차단됐다. DB layer_id=marine_gazetteer_mof를 registry key로 전달했으나 registry key는 marine_gazetteer였다. 이는 Qwen 해석 문제가 아닌 실행 연결 오류다.

## 변경

- 요청에서 추출한 기준 지명·대상 레이어·반경을 query_interpretation으로 보존한다. Qwen을 실행 권위로 승격하지 않는다.
- 위치 미확인 시 이해한 위치와 검색 NOT_RUN을 설명한다. 검색 0건과 구분하고 기준 좌표와 누락 반경을 요청한다. 외부 후보/원천 장애는 기존 별도 사유를 유지한다.
- 반경 누락 시 이미 확인한 위치·geometry·출처를 버리지 않는다. 위치 확인은 검색 승인이 아니며 READY는 부여하지 않는다.
- marine_gazetteer의 registry_id와 실제 DB 필터 layer_id를 구분한다. DB 조회 조건은 기존 layer_id를 유지한다.
- 레이어 반경 binding은 overlay/intersects 대신 postgis.dwithin을 사용한다. 미등록 레이어는 계속 차단한다. 최종 승인은 ExecutionValidator만 부여한다.

## 재현과 검증

단위: `docker exec geollm_backend python -m pytest tests/unit/test_layer_clarification_context.py tests/unit/test_execution_authority.py tests/unit/test_execution_validator.py tests/unit/test_execution_gate_regressions.py -q --disable-warnings`.

실제 API: `docker exec geollm_backend python -m scripts.check_layer_clarification_runtime --output outputs/web-intent-audit/<새 파일>.jsonl`. 울릉도 위치 미확인, 울릉항 반경 누락, 울릉항 5km 지명 검색을 확인한다. 울릉항은 대조 질의이며 울릉도를 자동 치환한 것이 아니다.

초기 지명/권한 단위 6개 통과. 함께 실행한 기존 request_output_obligations에서 사고 조회 2개가 ACCIDENT_FILTERS_REQUIRED 대신 EXECUTION_GATE를 받아 실패했다(19 passed/2 failed에서 중단). 해당 사고 경로는 이번에 변경하지 않았으며 별도 P0 계약 정합성 점검으로 남긴다. API v1은 재시작 준비 전 연결 실패로 0/3, 준비 대기를 추가한 v2는 2/3으로 위 registry ID 오류를 발견했다. 실패 원본을 보존한다.

최종 관련 단위 **88 passed, 4 warnings**. backend 재시작 후 실제 HTTP API v3 **3/3 통과**: 울릉도 위치 미확인/NOT_RUN, 울릉항 위치 확인·반경 누락/NOT_RUN, 울릉항 5km 지명 검색 COMPLETED/**5건** 및 ExecutionValidator receipt. 원본 `outputs/web-intent-audit/20261001-layer-clarification-v3.jsonl`. 이번 검증은 HTTP이며 신규 브라우저 조작 검증은 아니다.

## 남은 범위

울릉도 자체의 근거 있는 기준 geometry 연결은 미완료다. 울릉항 좌표나 모델 추정 좌표로 대신하지 않는다. 현재는 사용자가 지도 기준점/좌표와 반경을 명시하는 경로 또는 원천에 등록된 지명 검색을 사용한다. authoritative 지명 원천 보강, 사용자 확인 후 재조회 UI, 일반 RAG 오경로, 기존 사고 Gate 상태 정합성을 이어 점검한다. Qwen shadow/calibration UNFITTED/QLoRA DEFER 유지.
