# 다음 접속: 정상 오차단·검토 모순 보완 후 GOLD v2 8방법 새 동결

작성일: 2026-11-02 (KST). **현재 상태: PREPARATION_BLOCKED_RUNTIME. 실행하지 않음.** 사용자는 이번 접속에서 수정·검증을 진행하고 전체 비교는 다음 접속에서 시작하도록 요청했다. 이 문서는 시작 승인이나 완료 증거를 대체하지 않는다.

## 먼저 읽을 파일

- `docs/geollm/remaining_work_roadmap.md` 최신 인계
- `docs/geollm/normal_request_review_repair_20261102.md`
- `research/marine_geollm_scie/protocol/review_consistency_repair_20261102_KR.md`
- `docs/geollm/v6_fault_detection_explanation_20261102.md`

## 시작 전 필수 순서

1. Docker Desktop 정상 기동과 운영 DB/연구 DB/백엔드 상태를 확인한다. 이번 기동은 `Docker/run/dockerInference` 소켓 접근 오류로 실패했다. 소켓 이동도 실패했고 삭제는 자동 승인 검토가 `blocked by policy`로 차단했다. 우회 삭제나 factory reset을 하지 않는다.
2. PDF 임베딩 worker가 실제로 없는지 명령행으로 확인한다. 마지막 독립 검증은 2,215개 중 948개 checkpoint 정상, 1,267개 남음, 최종 embedded.json 없음이다. stale lock은 검증 없이 삭제하지 않는다. 안전 재개·완료 후 원문/hash/vector/CAS/새 receipt/API를 검증한다. 기록은 `outputs/coverage_review_repair_20261102_independent/pdf_checkpoint_validation.json`이다.
3. 운영 S-101의 원천 DataCoverage와 전체 inventory/live identity를 실제 DB에서 검증한다. 구현된 generic 계약만으로 실제 registry 승인/정상 허용이 완료된 것은 아니다. 연구 bbox를 운영 원천 DataCoverage로 바꾸지 않는다. 정상 bounded 요청은 허용하고 범위 밖·전체성·geometry 누락·원천 변조는 실행 전에 차단되는지 실제 API와 SQL 실행 기록으로 확인한다.
4. 연구 `ResearchBindingAdapter`가 사용하는 source scope와 운영 Validator의 권위 경로를 조정·검증한다. 현재 v6의 연구 CONTROL은 운영 coverage 미등록으로 차단됐다. 운영 generic 지원만으로 연구 CONTROL이 자동 통과하지 않는다. 같은 공개 연구 입력을 모든 방법에 제공하고, 연구 snapshot의 범위·hash를 검증한 별도 연구 경로와 운영 원천 권위를 분리한다. GOLD에서 실행 허용을 주입하지 않는다.
5. 초기 판정 false + 계약 필드 변경 응답은 사용 불가로 남기는 새 검토 계약을 확인한다. raw false를 true로 바꾸지 않는다. 이 모순 차단은 LLM 의미 오류 검출 개선과 다르다. 기존 v6 3건 읽기 재현은 새 모델 실험이 아니다.
6. 최종 소스·데이터·모델·예산·review protocol을 확인한다. 신규 JSON/원천 inventory/coverage 자산도 freeze에 포함하고 실제 연구 6개 관계 재추출 hash를 대조한다. 현재 generic 운영 계약이 미등록이면 먼저 위 3~4단계를 완료한다. 미완료 gate를 우회해 새 실행을 시작하지 않는다.

## 새 실행 명령

아래는 위 gate가 모두 충족된 뒤 **다음 접속에서 한 번만** 실행한다. 기존 디렉터리가 있으면 재사용하지 않고 새 버전을 택한다. 먼저 `outputs/eight_comparison_active.lock` 및 실제 supervisor/model/embedding worker를 대조한다.

```powershell
.venv/Scripts/python.exe -u -m research.marine_geollm_scie.runners.supervise_eight --output research/marine_geollm_scie/runs/20261102_gold_v2_eight_k1_v7 --snapshot-output outputs/scie_gold_v2_eight_snapshot_20261102_v7 --include-faults
```

경로의 날짜는 준비 식별자다. 실제 시작일·시간은 status.json에 기록한다. supervisor가 freeze부터 수행하므로 snapshot 디렉터리를 사전에 만들지 않는다.

## 완료 확인

- B0/B1/B2/B3/B4/P0/H/P1 각 18개, 총 144개 + 통제 9×3=27개. 실패·미측정 포함.
- 공유 B3 초기 plan, B4/H review receipt, P0 lossless, raw hash, 모델 digest, 공통 spatial ESR 분모 확인.
- LLM raw verdict / consistency rejection / 수정 후 결과를 각각 집계한다. REVIEW_UNDECLARED_PLAN_CHANGE를 오류 Recall 성공으로 합산하지 않는다.
- 정상 CONTROL False Block과 데이터 범위 밖 비실행을 별도 보고한다. 잘못된 계획이 그대로인데 LLM false인 미검출도 남긴다.
- 최종 report_with_faults/comparison_KR.md 및 source hash를 확인하고 RESULTS_INDEX/UI를 갱신한다. K1/개발셋 한계와 미측정 RQ 지표를 공개한다.
- 홀드아웃은 개발·이번 수정 재현에 사용하지 않고 최종 시스템 동결 후 별도 gate로 평가한다.

새 모델 성능이나 전체 RQ 완료를 이번 코드 테스트로 주장하지 않는다. 실행 실패 시 원본 run을 보존하고 수정 후 새 동결 전체 실행을 사용한다.
