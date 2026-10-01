# 질의창 예제 100개와 단계별 설명 검증 (2026-10-01)

## 범위와 실제 결과

웹에서 제공하는 예제 100개를 추출해 실제 `/api/v1` SSE 요청으로 검증했다. 직접 API 검증과 브라우저 렌더링 검증은 구분한다. 초기 100건 모두 completed 이벤트를 받았고 FAILED/응답 유실은 없었다. 상태 분포는 COMPLETED 11, PARTIAL 14, NEEDS_CLARIFICATION 67, BLOCKED 8이다. 이는 의미 정확도나 기능 완성도를 뜻하지 않는다.

수정 후 오경로 대표 15건을 재검증했다. 15/15 응답에 6단계 설명이 포함됐다. 창원 정비불량 사건은 지명 검색 대신 사고 59건으로 연결됐다. 시간 예측은 반경 질문 대신 원천 미연결 BLOCKED_DATA, 위치 없는 레이어 요청은 LOCATION_REQUIRED, 최근 사고는 ACCIDENT_FILTERS_REQUIRED로 구분한다. 부산 신항만예정지역을 항만 중심점으로 표시하던 경로를 실제 계획구역 레이어 요청으로 수정했다. 주변 질의의 대상 단어가 지명에 붙던 오류도 수정했다.

## 변경

- 새 요청 시 이전 비교 패널을 초기화하고 지연된 이전 비교 응답도 무시한다. 질의/비교 ID 일치 여부를 검증한다.
- 모든 최종 응답에 질의 해석 → 위치·조건 → 실행 승인 → 도구 실행 → 근거 → 결과·다음 입력 설명을 추가했다. 실행 승인은 ExecutionValidator 영수증으로만 판단한다.
- 비교 결과와 실행 완료를 구분한다. 도구 실행 기록이 없으면 성공을 추정하지 않는다. 미실행/근거 없음/검색 0건을 구분한다.
- 기존 trace의 무조건적인 쿼리 완료·가짜 실행시간·undefined 계획 필드 표시를 제거했다.
- 근거→근처 오타 교정, 일반 근거 문서 요청의 적재 메타데이터 오분기, 근거 단어만으로 법령 경로에 보내는 오류를 수정했다.
- 렌더링 규칙 요구는 객체 정의만으로 완료될 수 없도록 필수 출력 검사를 추가했다. 실제 사고 조회에는 성공/실패 실행 기록을 남기고 trace 반경 누락을 0으로 바꾸지 않도록 수정했다.
- 해운대 해수욕장/울릉도는 현재 원천에서 검증 좌표를 찾지 못한 것임을 설명한다. 장소 자체가 없다고 단정하지 않으며 모델/seed 좌표를 승격하지 않는다.

## 검증

Python 배치 68 passed, 후속 공간/반경 회귀 59 passed, 최종 설명·의미 회귀 11 passed (중복 포함이므로 합산 고유 건수로 표시하지 않는다). Node UI 13 passed. git diff --check 및 JS 구문 검사 통과.

재시작 초기화 중 ConnectionRefused/ERR_EMPTY_RESPONSE가 발생한 시도는 검증 성공에 포함하지 않았다. 준비 완료 후 15건을 다시 실행했다. Qwen shadow 큐가 밀릴 수 있으며 비교 완료와 실제 응답 완료는 독립이다.

## 남은 P0/P1 및 다음 순서

1. P0: 울릉도·해운대 해수욕장 authoritative 기준 geometry와 동명항 선택을 확보/확인해야 한다. 현재는 위치 확인 안내가 올바른 차단이며 실제 검색 완료가 아니다.
2. P0: 일반 문서 및 특정 CSV 적재 근거의 검색 관련성, AIS 셀 설명 요청, S-101 portrayal 규칙 요청의 최종 근거 완결성은 별도 검증이 필요하다. PARTIAL이나 단순 응답 완료를 해결로 간주하지 않는다.
3. P0: 사고+보호구역/사고+지명/VTS+통항량 복합 요청은 위치 확인 후 모든 필수 출력이 충족되는지 양성 대조가 필요하다. 이번 검증은 미확인 위치에서의 차단까지다.
4. P1: legacy 실행의 상세 도구 receipt 누락을 보강한다. 단계 설명의 UNRECORDED는 미실행 확정이 아니라 기록 부재다. trace의 기존 null→0 반경 표시는 이번 수정에서 제거했다.
5. P1: 바다갈라짐 시간 예측 및 와류/기상 실제 원천 adapter, 최신 AIS 기간, Qwen 큐 지연/SLO. Qwen shadow/calibration 미완료 및 QLoRA 보류 유지.

## 재현

```powershell
docker exec geollm_backend python -m scripts.check_geollm_web_samples --output outputs/web-intent-audit/NEW-all --workers 2 --socket-timeout 180
docker exec geollm_backend python -m scripts.check_geollm_web_samples --output outputs/web-intent-audit/NEW-fixes --workers 2 --socket-timeout 180 --ids 37 41 49 50 56 61 63 64 68 72 73 85 87 88 95
node --test tests/unit/test_intent_comparison_ui.js tests/unit/test_query_summary.js tests/unit/test_radius_ui.js
```

원본 응답/manifest는 outputs/web-intent-audit/20261001-presets-all-v1 및 20261001-presets-fixes-v2이며 런타임 산출물로 커밋하지 않는다.

## 예제별 관측 상태

아래 상태는 기능/정답 판정이 아니다. 수정 후 공란은 재실행하지 않았다는 뜻이다.

|번호|질의|초기 상태|수정 후 상태/코드|
|---|---|---|---|
|1|해운대구로 이동|COMPLETED| |
|2|독도를 찾아줘|NEEDS_CLARIFICATION| |
|3|부산항 입구로 이동|NEEDS_CLARIFICATION| |
|4|인천항으로 이동|NEEDS_CLARIFICATION| |
|5|울릉도 주변 지명을 찾아줘|NEEDS_CLARIFICATION| |
|6|독도 부근 지명을 찾아줘|NEEDS_CLARIFICATION| |
|7|독도 부근 해저지명을 찾아줘|NEEDS_CLARIFICATION| |
|8|독도구근해저지명|NEEDS_CLARIFICATION| |
|9|해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘|PARTIAL| |
|10|위험객체|NEEDS_CLARIFICATION| |
|11|부산항 입구 3km 이내 위험객체를 찾아줘|NEEDS_CLARIFICATION| |
|12|부산항입구3km위험객체|NEEDS_CLARIFICATION| |
|13|부산항 입구 위험객체|NEEDS_CLARIFICATION| |
|14|부산항 입구 1km 이내 침선을 찾아줘|NEEDS_CLARIFICATION| |
|15|부산항 입구 5km 이내 암초와 간출암을 표시해줘|NEEDS_CLARIFICATION| |
|16|부산항 입구 3km 이내 부표와 위험표지를 같이 보여줘|NEEDS_CLARIFICATION| |
|17|울산항 3km 이내 장애물을 찾아줘|NEEDS_CLARIFICATION| |
|18|목포항 주변 항로표지를 보여줘|NEEDS_CLARIFICATION| |
|19|항로표지정보_20250623.csv 파싱/표준화/공간 적재 근거를 보여줘|PARTIAL| |
|20|Dataset 폴더의 해양수산부 항로표지 CSV는 embedding 대상인지 확인해줘|PARTIAL| |
|21|정박지는 S-101에서 어떤 Feature야?|COMPLETED| |
|22|부산항 입구 주변 정박지와 항로표지를 같이 조회해줘|NEEDS_CLARIFICATION| |
|23|정박지/일반항로/통항분리 레이어가 적재되어 있는지 확인해줘|PARTIAL| |
|24|진입제한구역과 속도제한구역 레이어가 적재되어 있는지 확인해줘|PARTIAL| |
|25|인천항 주변 통항분리구역을 표시해줘|NEEDS_CLARIFICATION| |
|26|부산항 주변 일반항로를 보여줘|NEEDS_CLARIFICATION| |
|27|여수항 주변 정박지를 보여줘|NEEDS_CLARIFICATION| |
|28|최근 1년간 AIS/V-PASS 통항량을 분석해줘|NEEDS_CLARIFICATION| |
|29|AIS와 V-PASS 데이터는 어느 기간까지 적재되어 있어?|COMPLETED| |
|30|최근 1년 통항량이 가장 높은 격자와 월을 알려줘|NEEDS_CLARIFICATION| |
|31|부산항 최근 12개월 AIS 통항량을 구역별로 요약해줘|BLOCKED| |
|32|인천항 최근 12개월 V-PASS 통항량을 월별로 보여줘|BLOCKED| |
|33|통항량 지도 셀을 클릭했을 때 보여줄 AIS/V-PASS 세부정보를 설명해줘|NEEDS_CLARIFICATION| |
|34|독도 부근 사고 이력|NEEDS_CLARIFICATION| |
|35|독도 사고 이력|NEEDS_CLARIFICATION| |
|36|독도 주변 10km 이내 사고와 위험객체를 같이 비교해줘|NEEDS_CLARIFICATION| |
|37|창원 정비불량 사건을 찾아줘|NEEDS_CLARIFICATION|COMPLETED |
|38|해양경찰청 해상조난사고 데이터는 임베딩되었나?|PARTIAL| |
|39|부산 앞바다 충돌 사고 이력을 찾아줘|COMPLETED| |
|40|포항 기관손상 사고 사례를 찾아줘|COMPLETED| |
|41|최근 사고 이력|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION ACCIDENT_FILTERS_REQUIRED|
|42|사고 찾아줘|NEEDS_CLARIFICATION| |
|43|S-101 2.0 Obstruction 정의와 DCEG 근거를 알려줘|COMPLETED| |
|44|Wreck 정의와 S-101 근거를 알려줘|COMPLETED| |
|45|Obstruction 렌더링 규칙 설명해줘|COMPLETED| |
|46|S-101 portrayal symbol과 장애물 아이콘 매칭 근거를 보여줘|NEEDS_CLARIFICATION| |
|47|지도에서 빨간 폴리곤이 무엇인지 설명 가능한 정보로 보여줘|NEEDS_CLARIFICATION| |
|48|위험객체 지도 클릭 시 feature 정보와 근거를 같이 보여줘|NEEDS_CLARIFICATION| |
|49|제부도 바닷길 예측 정보를 알려줘|NEEDS_CLARIFICATION|BLOCKED BLOCKED_DATA|
|50|제부도바닷길예측정보|NEEDS_CLARIFICATION|BLOCKED BLOCKED_DATA|
|51|무창포 바다갈라짐 시간을 알려줘|NEEDS_CLARIFICATION| |
|52|진도 모도 바다갈라짐 예측을 보여줘|NEEDS_CLARIFICATION| |
|53|바다갈라짐 알려줘|NEEDS_CLARIFICATION| |
|54|바다갈라짐 예측정보 데이터는 공간 적재되었나?|PARTIAL| |
|55|인천항 주변 선박안전교통관제구역을 표시해줘|NEEDS_CLARIFICATION| |
|56|인천항VTS표시|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION LOCATION_UNCONFIRMED|
|57|부산항 주변 선박안전교통관제구역을 찾아줘|NEEDS_CLARIFICATION| |
|58|선박안전교통관제구역 보여줘|NEEDS_CLARIFICATION| |
|59|부산항 주변 투기장을 찾아줘|NEEDS_CLARIFICATION| |
|60|부산항 산업폐기물투기구역 찾아줘|NEEDS_CLARIFICATION| |
|61|산업폐기물투기구역찾아줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION LOCATION_REQUIRED|
|62|투기장 보여줘|NEEDS_CLARIFICATION| |
|63|독도 주변 보호수역을 찾아줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION LOCATION_UNCONFIRMED|
|64|해운대구 주변 천연보호구역을 찾아줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION EXTERNAL_PLACE_CANDIDATES|
|65|독도 부근 천연보호구역을 찾아줘|NEEDS_CLARIFICATION| |
|66|전자해도에 없으면 국가유산 보호구역 근거도 찾아줘|BLOCKED| |
|67|OSM에서 해운대구 지명과 주소 후보를 보완해줘|NEEDS_CLARIFICATION| |
|68|보호수역 찾아줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION LOCATION_REQUIRED|
|69|포항 주변 와류 위험구역을 보여줘|BLOCKED| |
|70|울산 주변 와류 발생 위험을 찾아줘|BLOCKED| |
|71|와류 위험구역 보여줘|BLOCKED| |
|72|신항만예정지역을 지도에 표시해줘|COMPLETED|NEEDS_CLARIFICATION LOCATION_REQUIRED|
|73|부산 신항만예정지역을 찾아줘|COMPLETED|NEEDS_CLARIFICATION LOCATION_UNCONFIRMED|
|74|Dataset 폴더 안의 공간 적재 완료 현황을 요약해줘|PARTIAL| |
|75|Dataset 폴더 안의 embedding 완료 현황을 요약해줘|PARTIAL| |
|76|해양수산부 바다갈라짐 ZIP은 어떤 방식으로 좌표를 보완했어?|PARTIAL| |
|77|공간 적재되지 않은 Dataset 항목이 남아 있는지 알려줘|PARTIAL| |
|78|법령/사고/표준 문서 embedding 산출물이 live knowledge.document_chunks에 병합되었는지 확인해줘|PARTIAL| |
|79|capability_embeddings 테이블과 pgvector top-k가 동작하는지 확인해줘|PARTIAL| |
|80|질의를 multi-label route로 분류한 근거를 보여줘|NEEDS_CLARIFICATION| |
|81|Resolver Registry에서 사용 가능한 해양 resolver 목록을 보여줘|PARTIAL| |
|82|Ontology/KG validator가 후보를 제거한 이유를 설명해줘|NEEDS_CLARIFICATION| |
|83|ExecutionValidator가 이 질의를 실행 가능한지 판단한 근거를 보여줘|NEEDS_CLARIFICATION| |
|84|위치 없이 부근 사고를 찾아줘|NEEDS_CLARIFICATION| |
|85|부근 해저지명 찾아줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION LOCATION_REQUIRED|
|86|3km 이내 위험객체를 찾아줘|NEEDS_CLARIFICATION| |
|87|해운대구 근처 사고와 보호구역을 같이 찾아줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION EXTERNAL_PLACE_CANDIDATES|
|88|독도 주변 해저지명과 사고 이력을 같이 보여줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION LOCATION_UNCONFIRMED|
|89|부산항 주변 항로표지와 위험객체를 같이 보여줘|NEEDS_CLARIFICATION| |
|90|인천항 주변 VTS와 통항량을 같이 분석해줘|NEEDS_CLARIFICATION| |
|91|독도부근사고이력|NEEDS_CLARIFICATION| |
|92|해운대구로이동|COMPLETED| |
|93|부산항입구위험객체|NEEDS_CLARIFICATION| |
|94|Dokdo nearby marine gazetteer|NEEDS_CLARIFICATION| |
|95|해운대 해수욕장을 찾아줘|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION LOCATION_UNCONFIRMED|
|96|부산항 obstruction 3km|NEEDS_CLARIFICATION| |
|97|내일 인천 앞바다 파고 예보를 알려줘|BLOCKED| |
|98|9월 인천 대조기 일정을 알려줘|BLOCKED| |
|99|없는항구 주변 위험객체를 찾아줘|NEEDS_CLARIFICATION| |
|100|asdfasdf 위험객체|NEEDS_CLARIFICATION| |

## 추가 대조 및 브라우저

실제 브라우저에서 울릉도 → 해운대 해수욕장 연속 입력을 실행했다. 새 입력 직후 이전 비교 패널이 비워지고 완료 후 해운대 비교 1개와 현재 질의의 6단계 설명만 남는 것을 확인했다. 울릉도/해운대의 미승인·미실행과 위치 확인 안내를 확인했다. 증빙: outputs/web-intent-audit/20261001-processing-steps.png.

정상 대조 `울릉항 반경 5km 지명을 찾아줘`: COMPLETED, ExecutionValidator 승인, 실제 실행, 지명 5건과 레이어 근거 1건, 6단계 확인. 일반 문서 대조에서는 무관한 항만 고시 4건의 잘못된 완료를 발견하여 법령 판별 조건을 추가 수정했다. 추가 테스트 27 passed 및 렌더링 필수 출력 포함 20 passed. 기존 지명/법령 graph fixture는 금지한 DB 접속이 발생해 teardown 1 error(본문 1 passed)로 중단됐다. pgvector 비활성화만으로 해소되지 않아 해당 임시 fixture 변경은 되돌렸다. 전체 graph integration 통과로 보고하지 않는다. 명시적 법령의 원천 일치 테스트를 별도로 추가했다.

최종 법령/의미 양성·음성 회귀: 10 passed (3 warnings). 기존 graph fixture 실패는 미해소 항목으로 남긴다.

최종 재시작 후 추가 3건 실제 API: 일반 수로 품질 문서 Standard RAG 2건(COMPLETED, DCEG Quality of Survey 등), Obstruction 렌더링 PARTIAL/OUTPUT_OBLIGATIONS_UNMET, 창원 사고 59건 COMPLETED. 모두 6단계 반환. 원본 20261001-final-additional.jsonl. 문서 검색 관련성의 전체 정답 평가가 아니라 기존 항만 고시 오경로 해소 대조다.
