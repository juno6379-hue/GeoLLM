# RQ1 개발 18문항 GOLD grounding atom 작성 결과

18문항의 GOLD 원자 주석 작성과 원천 연결 검증을 완료했다. **RQ1 Semantic F1·Strict Match·CI 측정은 아직 완료되지 않았다.** 코드/주석/예측 추출/측정을 각각 구분한다.

## 완성한 주석

- [사례별 한글 주석표](../../research/marine_geollm_scie/benchmark/grounding_atoms_20261102_v1/annotation_KR.md)
- [기계판독 GOLD 원자](../../research/marine_geollm_scie/benchmark/grounding_atoms_20261102_v1/gold_atoms.jsonl)
- [주석 계약](../../research/marine_geollm_scie/benchmark/grounding_atoms_20261102_v1/schema.json)
- [manifest](../../research/marine_geollm_scie/benchmark/grounding_atoms_20261102_v1/manifest.json)

총 18문항, 필수 172원자·선택 5원자. 기존 승인 GOLD v2에서 직접 파생한 값, 계약 투영, AI 정규화 제안을 구분했다. 새 원자 표현에 대한 인간 검수를 대신 서명하거나 승인하지 않았다. 기존 GOLD 승인은 그대로 참조한다.

과업·Feature·속성 소유·연산·기준 위치·거리·CRS·출처 연결을 명시했다. Q5의 등대/침선 및 정박지/제한구역은 서로 다른 task로 나누어 거리·기준·연산이 한 과업에서 다른 과업의 정답으로 사용되지 않도록 했다. Q5_01 선택적 문서 대안 5원자는 필수 F1 분모와 분리한다. Q3_03의 selected_geometry 필수 조건, Q6의 FC 원천 해시·locator도 포함한다.

5000m/5km는 정수 미터, CRS는 EPSG:4326, 공간 연산은 covers/dwithin/nearest/intersects로 정규화한다. Q5_02의 polygon-area minimum geodesic distance와 Q4의 점 기준 거리는 별도 원자로 보존한다. 없는 필드·CRS·기준 위치를 평가기가 추론해서 보충하지 않는다. object 결과 ID·실제 GIS 실행·실세계 완전성은 RQ1 의미 원자와 별도 평가한다.

## 검증

별도 주석 작성/검증·UI/답변 원문 감사 에이전트를 사용했다. 부모는 복합 task 결합, 선택 문서와 필수 작업 분리, 출처 연결, 수치형 정규화의 누락을 확인하고 수정 후 재검증했다. 원천 JSON 포인터·해시·18개 질의 일치·원자 고유성·직접 파생값·manifest 검증을 통과했다. 실제 FC XML 해시와 27개 feature locator의 유일 노드를 별도로 확인했다.

`outputs/rq1_annotation_parent_20261102/final_validation.json`에 최종 검증과 기존 GOLD/v6 506파일 보존 결과를 기록한다. UI는 http://localhost:8001/research/scie-results 의 RQ1 메뉴에 작성18/검증18/원자172를 표시하며 실제 F1·Strict Match·CI는 null이다. HTTP 데이터 검증이며 브라우저 렌더링 검증과 구분한다.

## 아직 수치를 낼 수 없는 이유와 다음 순서

기존 B1/B2 36개 답변의 source hash 및 원문을 따로 감사했다. 완료형식25/INVALID_RESPONSE11(절단1 포함), 본문35개에서 직접 span146·구조화 필드155를 사전 주석했다. GOLD를 보고 모델 답변을 보충하지 않았다. 결과는 `outputs/rq1_prediction_audit_20261102_v1/사전주석_검증결과_KR.md`와 `prediction_preannotations.jsonl`이다.

1. 실제 답변의 구조화 필드와 본문 간 상충·중복, 별칭, 과업 연결, 잘린 JSON/실패 처리 규칙을 하나의 추출계약으로 고정한다. 현재 36개는 literal/span 사전주석이며 canonical prediction_atoms는 null이다.
2. 모든 36개 답변의 완전한 예측 원자 주석을 만들고 FP 대상 추가 주장까지 검토한다. 부분 feature 배열 점수를 전체 Semantic F1로 대체하지 않는다.
3. 동일 case/query/GOLD/contract/raw hash를 연결해 조건별 micro F1·Strict Match·paired cluster CI를 계산한다. 사후 개발셋 분석임을 표시하고 UNSEEN N=0·소수 동등군의 한계를 유지한다.
4. 운영 변경 후 새 시스템 비교는 새 동결 8방법 전체 실행으로 수행한다. 이번 주석을 과거 v6 원본에 덮어쓰거나 새 모델 결과로 재사용하지 않는다. 홀드아웃은 이번 작업에 사용하지 않았다.
