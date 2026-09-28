# 웹 질의의 의도 해석 오류와 실행 미지원 구분

검사일: 2026-09-28. 소스 기준 커밋: `d803208`. 아래 분류는 원문·API trace·코드를 대조한 AI 검토 의견이며 독립 human gold나 정확도 측정이 아니다. 운영 라우팅·모델·registry는 변경하지 않았다.

## 실행 범위

- 실제 `http://localhost:8000/` 페이지의 샘플 100개를 추출해 웹과 같은 `/api/v1/tasks/stream`으로 순차 실행했다. 페이지 SHA-256: `858f03b2a236b5fd95a34177f9da6f75cfc165773a44bd6a07011183f2ed6c59`.
- 100/100 완료 이벤트 수신, 관측 오류 0. 서비스 상태는 COMPLETED 9 / PARTIAL 14 / NEEDS_CLARIFICATION 69 / BLOCKED 8. 이 분포는 정확도가 아니다.
- Browser 연결 도구가 두 번 `Transport closed`를 반환했다. 화면 클릭·지도 이동·렌더링은 검증하지 못했다. 기본 100개에는 관측하지 못한 지도/대화 문맥을 넣지 않았다. 따라서 실제 사용자의 화면 문맥과 조건이 다를 수 있다.
- 추가로 실제 DB 객체를 사용한 선택 객체 API 5/5, S-101 속성·부정·복합 계약 API 10/10을 확인했다. 계약 통과는 기능 완성이나 의미 정답을 뜻하지 않는다.
- 별도 대조 질의 401–404는 원래 100개에 섞지 않았다. 402/403의 geometry는 속성 검색 검사 201의 실제 S-101 객체 기준점을 재사용했으며 브라우저에서 선택한 것처럼 표현하지 않는다.
- 신규 Qwen 추론·융합 평가·학습은 하지 않았다. 이번 결과는 현재 서비스 기준선이며 Qwen의 오류율이나 개선율이 아니다.

## 구분 기준

1. **의도/작업 해석 오류**: 요청 행위·대상·조건을 다른 작업으로 바꾸거나, 요청과 관계없는 필수 입력을 요구한다. route 이름의 차이만으로 판정하지 않는다.
2. **실행 기능 미지원**: 요청과 입력을 인식했지만 해당 연산이나 검증된 산출물을 만들 수 없다.
3. **원천/기간/매핑 부족**: 연산 존재 여부와 별도로 필요한 데이터나 권위 매핑이 없다. Qwen 학습으로 실제 데이터를 대체할 수 없다.
4. **입력·문맥 부족 또는 후보 확인**: 위치·선택 객체·반경·검토 대상 task가 없어 후속 실행이 관측되지 않았다. 전체 의미가 정확하다고도, 기능이 없다고도 단정하지 않는다.
5. **근거 선택·답변·완료 판정 문제**: 관련 자료는 찾았지만 요청한 설명·처리 이력·전체 범위를 충족하지 못한다. 상위 의도 오분류와 구분한다.
6. **슬롯 기본값 정책 불일치**: 명시 입력 없이 실행 범위를 보완하는 동작. 기능 미지원과 다르다.

한 질의에 여러 문제가 공존할 수 있다. 아래 대표 사례의 분류를 서로 배타적인 100개 정답 라벨로 사용하지 않는다.

## 확인된 의도/작업 해석 오류 6건

|샘플|사용자 요구|실제 경로·결과|판단 근거|
|---|---|---|---|
|37|창원 정비불량 **사건**을 찾아줘|`place_lookup`, `location_text=창원 정비불량 사건`, LOCATION_UNCONFIRMED|사건·원인 표현을 지명에 포함했다. 대조 401에서 **사고**로만 바꾸면 `accident_event_lookup`으로 실제 59건을 반환한다. 실행 기능 부재로 설명할 수 없다.|
|51|무창포 바다갈라짐 **시간**을 알려줘|`feature_search_by_radius`, DISTANCE_REQUIRED|시간/예측 조회 대신 반경을 요구한다. 날짜나 공식 예측 자료의 가용성을 확인하는 작업과 다르다.|
|52|진도 모도 바다갈라짐 **예측**을 보여줘|`place_lookup`, `location_text=진도 모도 바다갈라짐 예측`|예측 요구까지 지명 문자열로 넘긴다. 이후 공식 원천 부족이 존재하더라도 앞선 해석 오류는 별개다.|
|56|인천항VTS표시|`place_lookup`, `location_text=인천항VTS표시`, EXTERNAL_PLACE_CANDIDATES|VTS 구역 표시를 지명 조회로 바꾼다. 풀어 쓴 55번은 구역 공간 검색 경로에 들어간 뒤 위치 후보 확인을 요구한다.|
|72|신항만예정지역을 지도에 표시해줘|`place_lookup`, “신항의 기준 위치를 확인했습니다”, COMPLETED|예정지역 경계/레이어 대신 항만 기준점으로 완료한다.|
|73|부산 신항만예정지역을 찾아줘|`place_lookup`, “부산 신항의 기준 위치를 확인했습니다”, COMPLETED|신항만예정지역과 기존 항만 위치를 구분하지 않는다. 72/73은 S3 완료 판정의 잔여 문제도 함께 드러낸다.|

이는 관측한 6건의 근거 기반 오류 판단이며 **전체 오류가 6건뿐이라는 뜻이나 정확도 94%라는 뜻이 아니다.**

코드 근거: `fast_path_policy.instant_place_navigation_decision()`은 registry 억제 조건 이후 `place_navigation_target()` 결과를 허용한다. 후자는 `찾아줘/보여줘/표시해줘` 앞 표현을 장소로 잘라낼 수 있다. `graph.check_intent_parsed()`에서는 공간 레이어 실행 경로가 일부 차단 경로보다 앞선다. `graph.py`에는 별도의 `sea_parting_prediction_lookup`, `planned_port_overlay` 준비 부족 처리가 있지만 위 입력의 실제 경로는 다르다. 단일 키워드를 추가하는 수선보다 대상 타입·요청 산출물·후보·슬롯을 함께 검증해야 한다.

## 실제 실행 미지원과 원천 부족

|검사|관측|구분|
|---|---|---|
|선택 객체 301 / 심볼 추가 302|실제 동일 객체 조회 COMPLETED. 심볼 매칭 추가 시 PARTIAL / OUTPUT_OBLIGATIONS_UNMET, `official_rule_executed=false`|객체 조회는 실행 가능. 공식 portrayal rule/symbol binding 근거는 미완성.|
|속성 검색 201/202|실제 DB 기준점에서 잠제/수중방파제 조건 검색 성공, 실행 ID·속성·근거 연결 검사 통과|지원되는 실행의 대조군. 이 제한된 속성 매핑을 전체 용어 의미의 human gold로 간주하지 않는다.|
|206/209|NEGATION_EXECUTION_NOT_SUPPORTED, NOT_RUN|부정/제외를 감지했으나 실제 제외 연산은 미지원. 의도를 무시하고 실행한 경우와 구분.|
|207/210|COMPOUND_MAPPING_REQUIRED, NOT_RUN|복수 대상 입력을 감지했으나 복합 실행 계약 미지원.|
|203–205 물양장·예선·선유장|TERM_MAPPING_UNRESOLVED, NOT_RUN|권위 Feature/속성 매핑 부족. 단순 의도 라벨 오류로 계산하지 않는다.|
|31/32 최근 12개월 통항량|AIS/V-PASS·항만·P12M을 유지하고 TRAFFIC_PERIOD_NOT_COVERED|요청 월 2025-10~2026-09 미적재. 29번은 실제 적재가 2023년 12개월임을 반환. 연산 자체의 부재와 다르다.|
|대조 404 최신 적재 월 AIS|실제 2023-12 격자 합 6,847,473건, COMPLETED|같은 통항 실행 경로의 지원 대조군. 격자·월 합계이며 고유 선박 수나 현재 통항량이 아니다.|
|69–71 와류|`eddy_hazard_lookup`, BLOCKED_DATA|검증된 와류 레이어/실행 바인딩 미준비. 상위 도메인은 맞지만 모든 위치 슬롯의 정확도까지 검증된 것은 아니다.|
|97/98 파고 예보·대조기 일정|공식 `marine_weather` / `khoa_tide_prediction` 원천 연결 필요, BLOCKED_DATA|공식 시계열 원천 미연결. 날짜·연도·지점 해석은 별도 확인 필요.|
|66 국가유산 보호구역 보조 근거|NO_AUTHORITATIVE_EVIDENCE|권위 근거 미확보 및 앞선 대화 문맥 부재. 대상과 외부 검색 범위의 추가 검수 필요.|

## 입력 부족·검색 근거·정책 문제

- **문맥 확인:** 4번 인천항 이동에는 실제 두 위치 후보가 있다. 47/48은 선택 객체 미제공, 80/82/83은 검토할 원래 task 미제공이다. 추가 입력 요청을 곧바로 의도 오류나 미지원으로 분류하지 않는다. 28/30은 위치를 요구하며 나머지 집계 요건은 후속 검증이 남는다.
- **해소/사전 문제:** 2/34/35/91은 독도를 해소하지 못했다. 장소/사고 작업 선택은 관측되지만 원천 후보·별칭 coverage를 조사해야 하며 Qwen 오분류로 집계하지 않는다.
- **불명확한 표현·후속 검수:** 33번은 클릭 시 표시할 정보의 설명인지 실제 셀 조회인지, 46번은 일반 symbol 매핑 설명인지 특정 객체 매칭인지 사람 검수가 필요하다. 49/50, 60–62/68은 공간 레이어/시간 요구 또는 대상 타입이 적절히 보존됐는지 추가 대조가 필요하다.
- **복합 작업은 판정 유보:** 36/87/88/89/90은 첫 위치 확인에서 멈췄다. 하나의 공간 route라는 이유로 오분류로 확정하지 않지만, 위치 확정 뒤 모든 작업·산출물 보존 여부는 확인해야 한다.
- **근거 선택/범위 문제:** 19/20/76은 특정 항로표지 CSV나 바다갈라짐 ZIP을 요청했으나 사고 등 다른 자료가 주요 결과에 섞인다. `graph._query_dataset_evidence_sources()`의 OR 부분 문자열 검색과 source 선택을 점검해야 한다. 9/23/24/54/74/77/78은 문서 청크 조회가 실제 전체 적재·처리 이력 검증을 대신하지 못해 PARTIAL이다.
- **설명·완료 판정 문제:** 45번 렌더링 규칙 설명은 올바른 `Obstruction.lua`를 찾았지만 답변이 머리말/require 발췌 수준인데 COMPLETED다. 잘못된 의도라기보다 규칙 조건 설명과 완료 기준의 부족이다. `required_outputs()`는 모든 요청을 포괄하지 않아 S3 전체 완성으로 볼 수 없다.
- **기본 반경 정책 불일치:** 10/13/89/93/99/100에는 명시 반경 없이 `distance_m=3000`이 기록됐다. 대조 402는 실제 geometry만 제공한 “위험객체”에 3km/140건을 실행했고, 403은 명시 1km/49건을 실행했다. `s101_radius_execution.parse_distance()`의 `DEFAULT_NEARBY_RADIUS_M=3000.0` 적용이며 응답에도 기본값 적용을 알린다. 모델의 숫자 생성은 아니지만 로드맵의 근거 없는 반경 제거 정책과 불일치한다. 정책 승인/확인 계약을 정리할 P0이며 이 검토에서는 운영 코드를 변경하지 않았다.
- **제한된 적합 사례:** 21은 AnchorageArea 식별, 43/44는 정의와 FC/DCEG 참조, 40은 포항 기관손상 51건 조회, 75/79/81은 실제 DB/registry 관측과 한계 표시다. 전체 자료 의미 정확도·독립 근거 검수까지 완료됐다는 뜻은 아니다.

## Qwen 비교에 반영할 순서

1. 위 6건을 우선 검수 후보로 삼아 원문·허용 작업 조합·필수 슬롯·금지된 대체 결과를 사람이 확인한다. 사건/사고, 축약 VTS/풀어 쓴 표현, 구역/항만 기준점의 대조쌍을 같은 묶음으로 관리한다.
2. 규칙이 만든 동일 후보를 Qwen에 전달한다. 올바른 작업이 후보에서 빠졌으면 `candidate_gap`으로 기록하고 정답 강제 선택을 시키지 않는다. 장소 fast path는 후보 trace가 생기기 전에 끝날 수 있어 별도 관측이 필요하다.
3. 의도·슬롯·근거 선택 결과와 실제 실행 가능 여부를 별도 열로 둔다. 미적재 월·공식 원천 부재·portrayal 미구현은 Qwen 의도 오류의 분모/분자에 자동 포함하지 않는다.
4. 72/73의 잘못된 완료와 기본 반경 정책을 P0로 기록하되, 사용자가 지정한 한국어/Qwen 비교 흐름을 유지한다. S4 소규모 원문 선택·지연 검증 → 동일 후보 전체 비교 → 독립 gold/calibration 순서다. QLoRA는 DEFER다.

## 재현과 원본

원본 디렉터리: `outputs/web-intent-audit/`. runtime 결과는 소스 커밋과 구분한다.

- `20260928-v1/live_page.html`, `manifest.json`, `responses.jsonl`, `summary.json`: 웹 샘플 100개.
- `20260928-selected-feature.jsonl`: 실제 선택 객체 301–305.
- `20260928-marine-mapping.jsonl`: 실제 기준점 기반 속성/미지원 계약 201–210.
- `20260928-probes.jsonl`: 대조 질의 401–404. 초기 실행은 로컬 검토 스크립트에서 기존 `observe()`를 사용했고, 동일 질의/문맥을 재현하는 스크립트를 아래에 제공한다.

```powershell
python scripts/check_geollm_web_samples.py --output outputs/web-intent-audit/new-baseline --workers 1
docker exec geollm_backend python -m scripts.check_selected_feature_runtime --output outputs/web-intent-audit/new-selected.jsonl
docker exec geollm_backend python -m scripts.check_marine_mapping_runtime --output outputs/web-intent-audit/new-mapping.jsonl
python -m scripts.check_web_intent_disambiguation --anchor-run outputs/web-intent-audit/new-mapping.jsonl --output outputs/web-intent-audit/new-probes.jsonl
```

새 출력 경로를 사용한다. 사전/데이터/날짜가 바뀌면 결과 행 수와 기간도 달라질 수 있다. 본 검수 의견은 학습용 human gold로 자동 승격하지 않는다.
