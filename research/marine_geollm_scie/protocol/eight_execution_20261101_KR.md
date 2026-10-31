# GOLD v2 8방법 신규 실행 조건

운영 수정 커밋 `7c7f9ff`, 연구 실행 코드 `7c8fefc`. 기존 K5 결과를 재사용하지 않는다. 이번 K1 실행은 `runs/20261101_gold_v2_eight_k1_v1/status.json`과 실제 프로세스·하위 manifest를 기준으로 확인한다. 완료·실패 상태는 실행 뒤 보고서로 갱신한다.

## 동결과 공통 입력

- 기존 immutable GOLD v2 18문항의 질문·답안계약·원본은 불변이다.
- 연구 DB `scie_model_v3`의 6개 관계를 READ ONLY COPY로 재추출하여 부모 snapshot과 전체 바이트 SHA256 일치를 검사했다. 새 snapshot은 `outputs/scie_gold_v2_eight_snapshot_20261101_v1`이다.
- 운영 Python·연구 adapter/평가/runner·registry 등272개 실행 소스를 추가로 고정했다. 모델은 Qwen2.5:1.5b와 bge-m3 digest를 이전 승인 조건과 대조한다.
- `profiles/common_inputs.jsonl`은 모든 방법에 동일한 원문과 source registry/coverage 선언을 제공한다. 특정 문항의 geometry 슬롯을 자동 채우지 않는다. 선택 영역이 없는 Q3-03은 그대로 없다.
- 승인된 단일 부산 항계 참조는 실제 연구DB의 EWKB와 동결 입력 해시를 대조하여 공개 입력 registry로 제공한다. 대상 정박지·제한구역 정답 집합은 모델에게 주지 않는다. 연구 참조를 운영 canonical 정책으로 등록하지 않는다.
- P1이 이 참조 registry 인터페이스를 활용하지 못하면 그 실패를 그대로 기록한다. 같은 자료 가용성과 각 시스템의 실제 활용 능력을 구분한다.

## 방법별 실행

| 방법 | 신규 실행 경로 |
|---|---|
| B0 | 모델 직접 응답, domain tools 없음 |
| B1 | 고정 Text 근거 packet + 모델, domain tools 없음 |
| B2 | 고정 KG 근거 packet + 모델, domain tools 없음 |
| B3 | 모델 최초 계획 동결 → 공통 읽기전용 executor |
| B4 | 같은 B3 계획 → LLM 검토 1회 → 공통 executor |
| P0 | 같은 B3 계획 → 무손실 QEC 컴파일 → 실제 ExecutionValidator → 공통 executor |
| H | B4와 동일 검토안 → 무손실 QEC 컴파일 → 실제 ExecutionValidator → 공통 executor |
| P1 | 격리된 실제 production graph, 동일 연구DB·모델·입력 |

명시된 geometry_ref를 소스 registry에서 역참조하는 것은 binding 검사이며 누락 ref/CRS/원천을 선택하는 추론은 허용하지 않는다. B3/B4/P0/H의 공통 executor는 읽기전용 SQL·명시 원천 범위 검사라는 공통 하한을 갖는다. 이 공통 차단 효과를 P0 Validator 효과로 귀속하지 않는다. 도구 실행 결과의 최종 구조화 답변은 공통 결정론 projector가 실제 receipt만으로 만든다. 모델의 선행 후보 설명은 검증된 실행 답변으로 승격하지 않는다.

생성은768 output token 상한, seed42, temperature0.2, context8192이며 공유 최초계획/검토의 비용을 각 분기 독립사용 비용과 구분한다. P1은 실제 내부 prompt·호출 예산을 유지하므로 동일 연산량 대조가 아니다. 전체 tool call 수를 알 수 없는 P1은 null이며 관측된 공간 도구 수만 따로 보고한다.

## 계측·평가

실제 SQLAlchemy와 psycopg2의 공간 SQL을 문서/metadata SQL과 구분한다. 외부 GIS·미계측 드라이버는 관측 범위 밖이고, 누락을 false로 채우지 않는다. 성공한 SQL은 공간 정답을 뜻하지 않는다. 모델/도구 실패도 기대 관측 집합에서 제거하지 않는다.

RQ1/3/5는 `report/comparison_KR.md`, 이후 통제 실험을 결합한 보고서는 `report_with_faults/comparison_KR.md`에 생성한다. 문항·조건·오류 유형별 분모와 결측을 보존한다. 자유문 응답을 근거 없이 구조화 정답으로 추정하지 않으므로 일부 항목은 미측정으로 남는다. 독립 인간 GOLD 검수나 의미 정확도 완료를 주장하지 않는다.

RQ2/4는 [통제 오류 프로토콜](matched_fault_recovery_v2_20261101_KR.md)의 별도9사례×3방법27관측을 실행한다. 추가 오류 사례를 원래18문항에 섞지 않는다. 의미 보존은 명시 계약 tuple 및 실제 독립 SQL 객체집합으로 검사하는 제한된 진단이며 자연어 의미 전반의 인간 검수 대체가 아니다.

## 변경·실패 처리

원본 run은 보존한다. source/model/snapshot/input hash 변경이나 완료 gate 실패 시 supervisor가 멈춘다. 실패 원인 수정으로 코드가 바뀌면 새 run ID로 전체 비교를 다시 실행한다. 실행 중 발견한 운영 결함을 동일 run 소스에 즉시 반영하지 않는다. 운영 UI·기존 feedback의 무관한 변경은 분리 유지한다.

## v1 중단 기록

P1 18건 후 comparison 10행에서 source=list 응답을 projector가 dict key로 사용하여 TypeError로 중단했다. v1 원본은 보존한다. 768-token 종료 INVALID_RESPONSE는 별도 실제 모델 실패이며 중단 원인과 다르다. harness 수정 및 운영 gate 검증 후 새 동결 v2에서 P1을 포함한 전체 비교를 다시 실행한다. v1 결과를 완성된 비교로 보고하지 않는다.

## v2 준비 검증

연구 수정 커밋 `27445e6`: malformed source/target/연산/응답 구조를 보정하지 않고 실패 관측으로 보존한다. 예상하지 못한 projector 예외도 별도 실패로 기록한다. 새 공통 V2 응답 schema는 실행기가 지원하는 `covers`를 허용하며 NaN/Infinity/overflow를 거절한다. GOLD·모델 토큰 예산은 변경하지 않았다. 주검증자가 관련 통합121개 테스트를 통과했고, 운영 guard 범위 축소 후 관련40개를 재검증했다(중복을 합산하지 않음). 보존된 v1 59파일 SHA가 모두 동일하며 immutable GOLD 8파일 검증을 통과했다. v1 P1 18행은 새 채점기의 구조 처리 smoke 검증만 수행했으며 새로운 최종 실험결과로 재사용하지 않는다.

## 최신 v2 실행

운영 `6508224`와 연구 `27445e6`을 포함한 신규 동결 v2를 시작했다. 현재 run은 `runs/20261101_gold_v2_eight_k1_v2`, snapshot은 `outputs/scie_gold_v2_eight_snapshot_20261101_v2`다. P1 포함 전체 재실행이며 최종 완료 여부는 실제 status/보고서 gate를 따른다. 운영 revision 전달 및 shadow selection/score mismatch는 미해결 제한이다.
