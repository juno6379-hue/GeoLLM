# B0–B4 비교 프로토콜 v2 (2026-10-30, 연구 전용)

## 범위와 고정 조건

원본 18개 DRAFT 질의를 보존한다. 이번 제한된 파일럿은 Q1–Q6에서 한 사례씩 고른 PILOT_Q1_03, PILOT_Q2_03, PILOT_Q3_03, PILOT_Q4_01, PILOT_Q5_03, PILOT_Q6_03을 사용한다. 선택 이유는 범주별 실행 가능성과 예산이며 대표성이나 유리한 성능을 보장하지 않는다. 동일 질의·모델 digest·temperature·seed 정책·공통 plan JSON 출력 스키마를 모든 방법에 적용한다. 생성된 plan은 별도로 생산 QueryExecutionContext에 DRAFT로 캡처하며, 모델이 생산 QEC 자체를 직접 출력하거나 실행 승인받았다는 뜻은 아니다. 방법마다 K=3, 6×5×3=90개 방법 결과를 수집한다. B4 추가 검토18회를 합쳐 총108회 모델 호출이다. 실제 성공/실패/timeout을 모두 보존한다.

문맥 상한은 8192, 총 생성 상한은 방법별768 tokens다. B0–B3은 단일768, B4는 초안384+검토384로 나눈다. 남은 예산을 몰래 추가하거나 검토가 실패하면 초안을 성공답으로 대체하지 않는다. 공통 근거 상한은6000 Unicode characters다. 문자 수는 토큰 수와 다르므로 동일 token 입력량을 주장하지 않는다. 실측 입력/출력 tokens, prompt 원문·해시, 근거 packet 해시, 총 지연을 기록한다. 원천이 없는 방법에 의미 없는 padding을 하지 않는다. 호출횟수와 검토초안 재입력 때문에 B4 입력비용이 다를 수 있으며 별도 보고한다. 반복과 방법 실행순서를 기록하고 latency는 warm-up/cache 영향을 포함해 해석한다.

## 방법별 정보 접근

| 방법 | 제공 정보 | 이번 실행의 한계 |
|---|---|---|
| B0 | 질의와 공통 출력계약, 원천 근거 없음 | 직접 계획 생성, 실행하지 않음 |
| B1 | 같은 질의 + FC 원문 record/binding/attribute 발췌 | 결정론 lexical retrieval 기반 Text RAG; vector RAG 또는 전체 문서검색으로 표현하지 않음 |
| B2 | 같은 질의 + 실제 KG edge 및 양끝 node | 저장된 명시관계만; deterministic 실행validator 사용 없음 |
| B3 | 같은 질의 + generic typed tool definitions | source evidence는 비움; 실제 도구호출 agent가 아닌 typed plan-only 파일럿 |
| B4 | B2와 같은 packet + 초안 생성 + LLM 검토 | 검토 결과는 독립 정답이 아님; 동일총생성예산 내2회 호출 |

B0–B4 전체를 계획생성 비교로 명시한다. 현재 생산 full P 또는 실제 GIS 실행 비교가 아니다. QEC schema 통과는 구문적 적합성이고 의미·공간 정답이 아니다. 전체 생산 adapter, 실제 GIS, 독립 gold, recovery와 evidence 검증은 다음 단계다. deterministic validator를 무력화하는 운영 옵션은 만들지 않는다.

## 근거 패킷

`baselines/evidence_packets.py`의 `build_packet(query, method, max_chars=6000)`를 사용한다. 지원method는 B0/B1/B2이며 B3에는 B0 empty, B4에는 B2 packet을 동일하게 사용한다. 반환값은 sources, evidence/evidence_text, evidence_sha256/hash, packet_sha256, retrieval_trace, errors, status, matched_records/omitted_records다. 같은 원천과 질의·예산이면 같은 결과를 반환한다.

기존 marine_term_dictionary 및 s101_feature_dictionary의 label/alias/candidate feature는 검색후보 확장에만 사용한다. 모호한 후보를 정답으로 선택하지 않으며 해당 registry row/sha256를 retrieval_trace에 보존한다. 키워드 일치가 운영 route·실행허가를 변경하지 않는다. B1은 parsed S-101 FC의 실제 feature·binding·attribute record를 보존한다. B2는 기존 kg_edges_v2.jsonl의 실제 관계와 양끝 실제 node만 보존한다. 관계추론·가상edge 생성·좌표창작을 하지 않는다. KG 원천 자체의 미검수·추론 상태는 원문에 유지하며 관계 존재가 ontology 정확성의 증명은 아니다.

완전한 JSON record 단위로 예산에 들어가는 근거만 수록한다. 초과·누락 수를 기록한다. 공간 위치나 적합근거가 없으면 EVIDENCE_UNAVAILABLE, record가 있지만 예산에 전혀 들어가지 않으면 EVIDENCE_BUDGET_EXHAUSTED다. B0은 NO_EVIDENCE_BY_DESIGN이다. 파일없음/파싱실패는 errors에 남기고 일반 지식을 원천인 듯 채우지 않는다. 원본 path/sha256/locator와 KG nodes hash를 포함한다. 6000자 예산의 truncation 편향을 한계로 보고한다.

## 해석과 보고 금지사항

18개 전체에 대해 B0/B1/B2 packet을 생성하여 검색 coverage와 실패를 보존하고, 모델호출은 위6개로 제한한다. 원래 실험run을 덮어쓰지 않는다. GOLD는0이며 plan·답변 정확도, 개선율, 통계적 우월성은 보고하지 않는다. 자동 후보나 LLM검토를 GOLD로 바꾸지 않는다. 반복3회를 독립표본으로 간주하지 않는다. paired통계와 본실험 K5는 독립 expert semantic/QEC/spatial/evidence annotation 및 holdout 동결 후 수행한다. 이번에는 반환/timeout, parse/schema 성공, 근거 가용성, 실제 tokens/latency 및 보존된 실패사례만 보고한다.
