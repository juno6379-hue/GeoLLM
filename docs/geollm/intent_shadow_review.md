# GeoLLM 공통 의도 해석: 근거 기반 파일럿 검토

검토자: Codex. 상태: **AI의 사후 검토 의견, 사람 미검수, 학습용 gold 아님**.
대상: `outputs/intent-shadow/qwen-pilot-v1/raw_rows.jsonl`의 C01–C06, E01–E10. 각 행의 `case`, `candidates`, `shadow.request`, `shadow.raw_response`, `execution`을 대조했다. 평가에 사용한 capability는 `data/capability_registry.yaml`에 선언된 계약이며 실제 기능 완성이나 데이터 가용성을 보장하지 않는다.

## 판정 원칙

1. **의미 관계**: 직접 관련, 하위 작업, 복합 작업의 일부인지 구분한다. route 이름 불일치는 오분류 판정 근거가 아니다.
2. **기능 충족**: 요청한 대상·행위·범위·출력을 해당 capability 또는 조합이 제공하는지 본다. 관련 기능이지만 필수 작업을 누락하면 부분 적합이다.
3. **실행 근거**: 입력 슬롯, 데이터·도구, 관측 산출물을 확인한다. `COMPLETED` 문자열만으로 요청 완료라고 판단하지 않는다.
4. **의견과 사실 구분**: 아래 적합/부분 적합/부적합/유보는 AI 의견이다. 원문, capability 출력 계약, 모델 응답, API 상태는 관측 근거로 구분한다. 계약 검증 실패는 의미 판단 실패와 별도다.
5. 기존 API는 기존 router를 실행했으며 **Ollama가 고른 후보를 실행한 것이 아니다**. API 실패를 Ollama 후보 실패로 귀속하지 않는다. 향후 사람 검수 시 허용 가능한 복수 capability 조합을 포함하고, 모델 예측을 보지 않은 독립 annotation과 대조해야 한다.

## 사용자가 지적한 두 사례

### C02: 부산항 반경 3km 이내 침선을 찾아줘

- 필수 작업: 부산항 기준 위치 확인 → 침선 객체 식별 → 3,000m 이내 공간 필터 → 위치·거리·출처를 갖춘 결과.
- Ollama 선택은 `ACCIDENT_ANALYSIS`. 연결된 `tool.accident_spatial_history_lookup`은 반경 내 사고 사건, 거리, GeoJSON을 출력한다. 따라서 **공간 검색과 사고 정보라는 실질적 관련성**이 있다. 사고 이력에 침선 위치와 검증된 연결 관계가 있다면 보조 기능으로 사용할 수 있다.
- 다만 이 계약만으로 현존 침선 객체 필터를 수행한다고 확인할 수 없다. 사고 발생 지점과 침선 객체 위치를 동일시해서도 안 된다. 판단 의견은 **관련 있음 / 단독 충족 여부 유보**이며, 이 차이만으로 오분류로 확정하지 않는다. `resolver.place_registry` + `tool.spatial_radius_search` + 침선 feature 식별도 허용 가능한 조합 후보다.
- 별도 관측: 모델 설명 `查找距离釜山港3公里内的游船`에는 원문의 침선 대신 `游船`이 등장한다. 대상 보존에 문제가 있다는 근거이며, `analysis_type=definition`도 실행 요청과 맞지 않는다. 이는 route 이름 비교와 독립된 **응답 의미의 불일치**다.
- 실험 한계: v1 입력 축약에서 공간 후보의 세 번째 capability인 `tool.spatial_radius_search` 설명을 모델에 전달하지 않았다. 제공 정보가 불완전했으므로 결과를 모델 성능으로만 귀속할 수 없다. v2에서 준비한 세 capability를 모두 전달하도록 수정했다.
- 기존 API 관측: `BLOCKED / GAZETTEER_UNAVAILABLE`. 실제 침선 검색 완료는 확인되지 않았다. Ollama 후보를 실행한 결과가 아니다.

### C03: 인천항 위치를 지도에서 보여줘

- 필수 작업: 인천항 엔터티 해소 → 권위 있는 geometry·출처 확인 → 지도 표시.
- Ollama의 `SPATIAL_ANALYSIS`와 잠정 라벨 `PLACE_LOOKUP`에 제공된 capability 목록은 실제로 동일했다: `resolver.place_registry`, `resolver.marine_gazetteer_spatial`, `resolver.poi_beach_place`.
- 따라서 두 route 이름만으로 전자를 잘못된 선택이라고 판정할 수 없다. geometry를 제공하는 place resolver와 지도 표시 기능을 연결할 수 있다면 **적합 가능한 대안**이다. 지도 출력까지 실제 연결되는지 확인하기 전에는 요청 완료를 주장하지 않는다.
- 모델 설명의 장소명이 원문의 `인천항`과 일치하는지 추가 검토가 필요하다. `analysis_type=definition`은 지도 표시 요청과 구별해 점검할 항목이다.
- 기존 API 관측은 `BLOCKED / GAZETTEER_UNAVAILABLE`. 의미상 타당한 후보 선택과 실행 데이터 부재를 분리한다.

## 전체 문항 검토

| 사례 | 요구 결과·판단 근거 | AI 검토 의견 | 별도 실행 관측 |
|---|---|---|---|
| C01 S-101 Feature 정의 | `STANDARD_RAG`에는 feature dictionary와 graph-scoped RAG 계약이 있다. 정의와 출처가 핵심이며 지도 검색은 필수가 아니다. | 의미·기능상 적합 후보. 모든 후보에 같은 1.0을 주고 `composite`로 기술한 이유는 근거 부족. 답변 내용 정확도는 별도 검수 필요. | COMPLETED |
| C02 부산항 3km 침선 | 위 상세 검토. 사고 정보는 연관되지만 침선 객체·반경 결과 충족 여부가 필요하다. | 관련 있음, 단독 충족 유보. 대상 변형은 별도 불일치. 입력 설명 누락도 원인 후보. | BLOCKED / GAZETTEER_UNAVAILABLE |
| C03 인천항 지도 위치 | 위 상세 검토. 두 route가 동일한 place resolver 계약을 공유한다. | 적합 가능한 대안. 지도 출력 연결·장소 보존은 추가 확인. | BLOCKED / GAZETTEER_UNAVAILABLE |
| C04 월별 AIS 비교 | 항만 범위·월별 시간축·동일 지표 집계·비교가 필요하다. `tool.dynamic_traffic_aggregation`은 관련 계약이다. | Ollama 후보별 평가 누락으로 선택 유보. 기간·집계 단위·비교 산출물 충족 여부를 독립 검수해야 한다. | COMPLETED이지만 그 자체로 완결성 증명은 아님 |
| C05 사고 데이터 출처·적재 건수 | 선택한 graph-scoped RAG는 출처 문서 검색과 관련된다. 현재 적재 건수는 데이터셋 registry/DB 관측 시점과 연결돼야 한다. | 출처 검색에는 적합 가능, 최신 적재 건수까지 단독 충족하는지는 유보. `resolver.dataset_provenance_registry` 조합을 비교할 가치가 있다. | COMPLETED |
| C06 인천항 규칙 고시 근거 | 적용 고시·조항·문서 인용이 필요하다. `STANDARD_RAG` 이름은 있으나 공급 후보의 capability 설명이 비어 있다. | 점수 범위 위반으로 선택 유보. 빈 설명을 모델의 도메인 무지로 해석하지 않는다. 후보 구성의 누락을 먼저 확인해야 한다. | COMPLETED |
| E01 독도 부근 사고 이력 | 사고 공간 이력 도구가 실제 사건·거리·근거를 반환하도록 선언돼 있다. | `ACCIDENT_ANALYSIS`는 의미·기능상 적합 후보. `definition` 표기는 실행 작업과 불일치. 기준 위치/검색 범위와 실제 결과는 별도 확인. | BLOCKED / GAZETTEER_UNAVAILABLE |
| E02 위치를 찾지 말고 침선 정의만 | 명시적 부정에 따라 위치 검색을 실행하지 않고 정의·근거를 제공해야 한다. 공간 계열 agent라도 정의만 처리하면 허용 가능하다. | 점수 범위 위반으로 유보. 라벨 이름 대신 불필요한 공간 실행 여부를 검수해야 한다. | COMPLETED |
| E03 여기서 가까운 장애물 | 지도 중심은 주어졌다. 장애물 feature 식별과 거리 기반 검색이 필요하다. place lookup은 위치 해소라는 하위 작업일 수 있다. | 선택한 place resolver만으로 장애물 검색 충족을 입증할 수 없어 부분 적합/조합 검토. capability 설명에 가까운 객체 검색이 빠진 것도 확인 대상. | BLOCKED / GAZETTEER_UNAVAILABLE |
| E04 여기서 가까운 위험객체, 문맥 없음 | `여기`를 해소할 지도·대화 위치가 없다. 위치 clarification이 선행돼야 한다. | 계약 오류로 Ollama 의미 판단은 유보. 기존 서비스도 단순 원천 장애보다 누락 위치를 명확히 안내하는지 개선 검토 필요. | BLOCKED / GAZETTEER_UNAVAILABLE |
| E05 통항위험을 사고·수심까지 설명 | 위치, 통항, 사고, 수심을 같은 시공간 범위로 결합하고 근거·누락을 밝혀야 한다. 사고 검색/위치 해소는 하위 작업으로 적합할 수 있다. | 계약 오류로 선택 유보. NAVIGATION_RISK_ANALYSIS라는 이름이 없다는 사실만으로 수행 불가 판정 금지. 공급 계약에서 통항·수심 결합이 충분히 표현됐는지 검토. | PARTIAL |
| E06 내일 인천항 만조 시각 | 항만과 날짜 해소는 하위 작업. 필수 최종 출력은 공식 조석 자료의 만조 시각·시간대·기준일·출처다. | PLACE_LOOKUP 자체는 하위 작업으로 관련. 그러나 모델 설명은 `天气情况`(날씨)로 바뀌었고 공급 계약에서 만조 시각 출력을 확인할 수 없어 전체 요청 충족은 부적합/근거 부족 의견. | COMPLETED와 BLOCKED_DATA가 함께 관측됨. 완료 표기 정합성은 P0 후속 점검 |
| E07 아이콘·범례 불일치 검증 | 같은 feature의 심볼/범례/portrayal 규칙을 대조하고 차이와 근거를 제시해야 한다. 레이어 검사는 합리적인 하위 작업이다. | 후보별 평가 누락으로 유보. QUALITY_REVIEW의 빈 capability 설명과 실제 비교 기능 계약을 보완해야 한다. | API 관측 timeout; 작업 실패로 단정 불가 |
| E08 선택 레이어 상세정보 | 선택 layer ID 해소와 속성·출처 표시가 필요하다. PLACE_LOOKUP 쪽에도 `agent.spatial_analysis`가 연결돼 있어 이름만으로 배제할 수 없다. | 관련 기능의 조합 가능성은 있으나 실제 선택 레이어를 소비하는지 유보. v1 모델 입력에는 해당 agent 설명이 생략돼 있었다. | NEEDS_CLARIFICATION. API 관측기는 selected_layer_id를 전달하지 않았으므로 공정 비교 불가 |
| E09 조석예보 정의 | 예보를 실행하는 것이 아니라 개념·출처를 설명해야 한다. | 점수 범위 위반으로 선택 유보. 실행/정의 구별을 검수하고 날짜나 예측값을 임의 생성하지 않아야 한다. | COMPLETED |
| E10 그 항만 통항량 비교 | 대화 속 인천항을 해소하고 비교 기준·기간·통항 지표를 유지해야 한다. 통항 aggregation은 관련 기능이다. | TRAFFIC_ANALYSIS는 적합 가능한 후보. 모델 설명의 처리량/통항량 차이와 항만 문맥 보존을 추가 검수해야 한다. | COMPLETED. API에는 대화 문맥이 전달되지 않았으므로 모델과 동등 조건이 아님 |

## 합의해야 할 평가 단위

추가로 `outputs/intent-shadow/qwen-rationale-v2/raw_rows.jsonl`을 검토했다. C02는 SPATIAL_ANALYSIS와 실제 `tool.spatial_radius_search`를 인용했지만 그 기능으로 선박 위치를 찾을 수 없다고 설명했고, 침선을 일반 선박으로 표현했다. **잠정 라벨이 일치해도 의미 문제가 해결됐다는 뜻은 아니다.** C03은 LAYER_INSPECTION에 제공되지 않은 place resolver를 그 후보의 근거로 인용해 거부됐다. registry 어딘가에 기능이 있는 것과 해당 후보에 연결된 것은 구분해야 한다. 반복 reason code도 독립 근거 수로 세지 않는다. 현재 경량 모델을 운영 분류 권위로 승격할 근거는 없다.

단일 intent 정답 대신 문항별 필수 작업 집합, 허용 capability 조합, 반드시 유지할 대상·시간·공간 슬롯, 금지된 부가 실행, 근거 요구, clarification 조건을 검수한다. 서로 다른 경로라도 이 계약을 충족하면 허용한다. 같은 route를 골라도 대상을 바꾸거나 필수 작업을 빠뜨리면 적합 판정을 주지 않는다.

현재는 정량적 task-coverage 정확도를 계산할 gold가 없다. 이 사후 AI 의견을 모델 선택 정답으로 재사용하거나, 라벨을 결과에 맞춰 바꾼 뒤 holdout 성능 향상이라고 보고하지 않는다. QLoRA는 아직 적용하지 않는다.
