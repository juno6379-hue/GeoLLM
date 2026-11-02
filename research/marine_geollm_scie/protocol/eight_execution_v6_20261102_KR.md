# GOLD v2 8방법 v6 — 운영 범위 차단 보완 후 새 전체 비교

상태: 준비. 실제 시작·완료는 새 run의 status.json, 부모/자식 PID 및 단계 로그로 확인한다. 이 문서는 실행 완료 증거가 아니다.

## 변경 목적과 운영·연구 경계

v5의 Q5-03은 coverage UNKNOWN/required=false에서 공간 SQL을 실행했다. 이번 운영 수정은 요청자가 coverage 필수 여부를 낮춰 미검증 공간 검색을 허용하지 못하도록 서버 정책을 보완하는 작업이다. 연구 runner가 운영 답변을 대체하거나 GOLD를 실행 판단에 주입하지 않는다.

기존 common input에는 부산 연구 snapshot의 범위 선언과 전체 2022 지명 corpus의 범위가 모든 방법에 동일하게 제공된다. 그러나 이는 실세계 완전성을 보증하지 않는 연구 입력이다. B3/B4/P0/H의 공통 V2Executor는 이 연구 범위를 검사하고, native Validator 및 P1은 운영 서버 registry의 계약을 검사한다. 같은 입력을 받더라도 권위 판단 경로는 같지 않다는 제한을 유지한다.

이번 v6에는 연구 bbox를 운영 APPROVED coverage로 승격하거나 native Validator에 연구 전용 승인 overlay를 넣지 않는다. 따라서 운영의 UNKNOWN 차단 강화로 기존 정상 통제 계획까지 차단될 수 있다. 이를 통제 오류 검출 개선으로 계산하지 않고 정상 사례의 False Block으로 그대로 보고한다. 승인 coverage가 없는 운영 상태와 검증기 의미 오류를 구분한다.

같은 영향은 Q4의 독도 주변 지명 세 표현에도 적용된다. 공통 입력에 전체 동결 지명 corpus가 명시돼 있어도 운영 registry의 승인된 공간 범위 계약이 없으면 P1은 UNKNOWN으로 차단할 수 있다. v5에서 공간 성공으로 측정한 Q4 세 관측이 v6에서 줄어들 가능성을 가용성 비용으로 별도 보고한다. 이는 원본 지명 데이터 소실이나 GOLD 변경이 아니라, 실행 승인에 필요한 범위 근거 미등록의 영향이다. 안전한 중단 증가만으로 전체 신뢰성 개선을 선언하지 않으며 동일 공간 분모 5와 정상 요청의 실패·False Block을 유지한다.

## 고정 조건

- 새 run: `research/marine_geollm_scie/runs/20261102_gold_v2_eight_k1_v6`
- 새 snapshot: `outputs/scie_gold_v2_eight_snapshot_20261102_v6`
- 불변 GOLD: `benchmark/gold_v2_immutable_20261101_v1`, manifest SHA256 `feb9ef9851553fe53c12b0733b1747d3c238fb64c7b6bffd2ae848a35e6b1c5c`.
- 동일 18개 질문과 8방법 144관측, 별도 통제 9개 × 3방법 27관측. 기존 원시 답변 재사용 없음.
- v5의 Qwen2.5:1.5b/bge-m3 digest, 모델 예산, typed B3와 structured_review_v2, eight_execution_contract_v4, spatial_execution_semantics_v3 유지.
- B3/B4/P0/H 동일 초기 계획, B4/H 동일 검토 원본, P0 lossless compilation 유지. 누락 슬롯·CRS·source 자동 보완 금지.
- 실제 연구 DB 6관계를 다시 추출하여 부모 snapshot과 hash 대조 후 새로운 운영·연구 소스를 동결한다.
- 운영 수정·단위/실제 API 검증이 끝난 후 실행한다. 실행 중 소스·GOLD·입력·모델·예산 변경과 추가 모델/API 호출을 금지한다.

v5 원본 495파일, 불변 GOLD 10파일, v5 snapshot 7파일의 보존 hash는 `outputs/eight_v6_prechange_preservation_20261102.json`에 기록했다. 기존 run을 수정하거나 실패를 제외하지 않는다. 신규 coverage JSON 자산이 추가된다면 YAML 참조뿐 아니라 해당 자산 자체도 freeze에 포함되는지 먼저 점검해야 한다. 현재 준비 단계에는 신규 자산을 추가하지 않았다.

연구 준비 검증: 전체 연구 테스트 384개 통과(66.87초). 기존 단위 fixture의 누락된 review initial_checks와 coverage 전제, 오래된 invalid feature 허용 기대값을 현재 계약에 맞췄다. coverage fixture는 세 단위 테스트 모듈 안에서만 `UNIT_TEST_ONLY_SYNTHETIC_COVERAGE`로 표시하며 실제 연구 runner나 운영 registry에는 주입하지 않는다. 실행·채점 코드를 변경하거나 기존 실패 결과를 재채점하지 않았다. 원본 512파일은 `outputs/eight_v6_prechange_preservation_verified_20261102.json`에서 전부 불변으로 재검증했다.

## 실행 순서와 재현 명령

부모 검증자가 실제 서비스와 독립 회귀를 확인한 뒤 아래 명령을 한 번만 실행한다. 출력 두 경로가 없어야 하고 `outputs/eight_comparison_active.lock` 및 실제 연구 프로세스·컨테이너가 없어야 한다. stale lock을 확인 없이 삭제하지 않는다.

```powershell
.venv/Scripts/python.exe -u -m research.marine_geollm_scie.runners.supervise_eight --output research/marine_geollm_scie/runs/20261102_gold_v2_eight_k1_v6 --snapshot-output outputs/scie_gold_v2_eight_snapshot_20261102_v6 --include-faults
```

supervisor는 freeze → profiles → P1 graph → 나머지 7방법 → report → faults → fault_report → report_with_faults 순서로 실행한다. 별도로 freeze를 먼저 만들어 두면 새 경로 전용 gate가 중단하므로 supervisor가 동결까지 수행하게 한다.

최종 확인: 144+27행, 모델 digest 사후 검사, 6관계/source/raw hash, 공유 계획·검토, lossless compilation, 공통 공간 분모 5, 관측 완료 gate. 범위 밖 3문항은 공간 ESR과 별도로 비실행·범위 설명·문서 부분응답을 검사한다. 정상 통제 False Block, 미측정 및 실패를 숨기지 않는다.

독립 인간 GOLD 미수령, K1, 개발에 사용한 동일 질문이라는 제한을 유지한다. 이번 관측 완료가 전체 시스템 완성·인간 정확도·일반화 또는 RQ1–RQ5 완료를 의미하지 않는다. 코드 결함이 발생하면 원본을 보존하고 수정·검증 후 새 동결 run에서 전체를 다시 실행한다.
