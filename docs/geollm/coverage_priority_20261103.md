# Coverage 우선 정리와 RQ 동결 순서

2026-11-03. 사용자 지정 순서: **Coverage/source authority → RQ1–RQ5 측정계약 동결 → Development K1 → K5 → 최종 시스템 동결 후 untouched holdout**. 항만 사진 등 기능 추가보다 이 순서를 우선한다.

## 실제 수정과 검증

운영 Q4는 이미 정상화돼 있었지만 연구 `ResearchBindingAdapter`는 테이블 존재만 검사하고 원천 scope를 공통 Validator에 연결하지 않았다. 연구의 명시 source ID `marine_places`를 운영 ID로 바꾸는 방법은 P0의 lossless 조건에 위배되므로 사용하지 않았다.

- 원래 source/슬롯을 보존하고, 명시 snapshot manifest SHA·CSV SHA·현재 연구 DB 전체 행과 열 순서·고정 DB identity를 검증한다.
- S101 연구 bbox는 `RESEARCH_SNAPSHOT_DOMAIN`이다. 운영 승인 지리 범위나 실세계 완전성으로 승격하지 않는다. 해양지명은 frozen corpus 한정 조회다.
- 실제 공간 SQL과 원천 해시 재검사는 동일 `READ ONLY REPEATABLE READ` transaction에서 수행한다. 불일치하면 공간 SELECT 전에 차단한다. 검사 metadata SQL을 공간 실행으로 집계하지 않는다.
- 실제 DB executor의 snapshot pin 누락을 거부한다. 공통 executor도 profile의 범위 확대를 거부해 B3/B4와 P0/H의 공통 안전 조건을 맞춘다.
- 확실한 사전 차단의 `sql_executed=false`를 `null`로 바꾸던 계측 결함을 수정했다. 통신 실패의 불확실성은 계속 `null`이다.
- COPY와 동일한 boolean t/f 직렬화 및 현재 열 목록 일치 검사를 추가했다.

독립 데이터 감사: 기존 연구 DB 6개 관계의 전체 CSV가 v6 snapshot 해시와 모두 일치했다. 운영 DB와 연구 DB를 합치거나 원본 데이터를 다시 적재하지 않았다.

최종 연구/운영 coverage 통합 회귀 **639개 통과**. 이후 추가 RQ1 추출계약 전용 14개도 통과했으며 서로 다른 검사 범위로 기록하고 중복 합산하지 않는다.

| 실제 연구 Validator 개발 점검 | 결과 |
|---|---|
| 독도 5km 해양지명 Q4 | 승인·실행, 11개 |
| 범위 내 정상 Wreck CONTROL | 승인·실행, 해당 원천에서 0개 |
| 독도 S101 범위 밖 | 차단, count=null |
| 연구 범위와 부분 겹침 | 차단, count=null |
| 실세계 전체 지명 요구 | 차단, count=null |
| 기준 geometry 누락 | 실행하지 않음 |
| 잘못된 CRS | 실행하지 않음 |

운영 서비스 재기동 후 실제 SSE도 Q4 COMPLETED/11개, 실세계 전체성 요구 BLOCKED/count=null을 확인했다. 이는 개발 검증이며 v6 P1 0/5나 예전 144개 답안을 새 점수로 덮어쓰지 않는다. 정상 CONTROL 0개는 원천 내 결과이고 실제 해역의 침선 부재 보증이 아니다.

근거는 `outputs/coverage_priority_20261103_v1/`의 `독립검증_KR.md`, `independent_db/verification.json`, `native_probe_v3/`, `operational_api_v1/validation.json`이다. 초기 probe/audit도 보존한다. 감사에서 발견한 bbox·boolean·열 목록 결함은 후속 수정했으므로 초기 감사의 ‘남음’은 발견 시점 상태다.

## 측정계약에 반영할 필수 미완료

1. RQ1: GOLD atoms 18개와 canonical prediction은 별개다. 36개 원문의 task/owner/근거 연결·FP 주장·상충 처리 주석과 추출계약이 완료되기 전 Semantic F1/Strict Match/CI를 생성하지 않는다.
2. RQ2: 기존 단일 정상 계획의 8개 변형에서 독립 fault/정상 대조를 확대하고 `expected_fault_codes`를 사전에 고정한다. binary Recall과 target-code Recall을 분리한다.
3. RQ3: 정상 실행 복구에 이어 실제 wrong-but-executable fault를 방법별 executor에 연결한다. 직접 SQL의 정상 24개/centroid 0개 반례는 모델 성능이 아니다. 실행 성공 분모 0이면 CGE/SSFR=null이다.
4. RQ4: 빈 Oracle가 복구 성공으로 집계되던 결함은 이번에 수정했다. 새 계약은 빈 Oracle를 제외, 누락 Oracle를 미측정으로 구분한다. **실제 비어 있지 않은 객체집합 복구 사례 구성·실행은 남아 있다.**
5. RQ5: P1 전체 tool/SQL/model/retry/escalation·근거/provenance 관측을 완성하고 공유 비용 배분을 고정한다.
6. 실제 독립 ablation configuration과 실행 trace, 8방법 K5 runner를 완성한다. 기존 반복 runner는 6방법 540관측이며 새 8방법 K5의 기본 720관측을 대신하지 않는다.

이번 RQ1 후속 준비: `protocol/rq1_prediction_extraction_20261103_KR.md`와 `evaluation/prediction_contract_v1.py`를 추가했다. 원본 36개 SHA, 301개 witness(필드155/span146)를 검증하고 canonical 후보166개/개별 처리 검토135개를 보존했다. 후보도 task·상충·중복·전체 주장 검토 전이므로 36개 `prediction_atoms`는 아직 null이다. 이 숫자는 정확도나 오류 개수가 아니다. 산출물은 `outputs/rq1_prediction_contract_20261103_v1/`이다.

`measurement_readiness_KR.md`는 수정 전 감사 기록이다. 이번 Coverage와 RQ4 계측 수정은 위에서 갱신했지만 나머지 미완료를 자동 완료로 처리하지 않는다.

## 다음 실행 gate

- 위 계약·개발 자산·계측을 완성하고 코드/모델 digest/embedding/snapshot/GOLD/입력/예산을 새로 동결한다.
- 기존 `supervise_eight --include-faults`는 144+27만 수집하므로 새 전체 RQ 완료로 사용하지 않는다. RQ별 관측·분모·raw hash·공유 계획·P0 lossless까지 확인하는 새 실행 절차가 필요하다.
- Development K1은 코드 결함만 수정한다. 코드가 바뀌면 원본을 보존하고 새 동결 전체 실행을 한다. 낮은 점수 자체를 이유로 조건을 바꾸지 않는다.
- K1 gate 통과 후 같은 계약으로 K5를 수행한다. 반복 관측은 독립 사례가 아니다.
- 최종 시스템 동결 후에만 untouched holdout을 평가한다. 이번 작업은 홀드아웃 문항·GOLD 본문을 읽거나 개발에 사용하지 않았다.

현재 새 모델 비교/K5/홀드아웃은 실행하지 않았다. Coverage 개발 검증 통과와 전체 논문 측정 완료를 구분한다.
