# 다음 접속: 정상 오차단·검토 모순 보완 후 GOLD v2 8방법 새 동결

> 2026-11-03 우선순위 갱신: 이 문서의 과거 재개 명령을 바로 실행하지 않는다. Coverage 연구 연결은 보완했고 새 실제 검증은 `docs/geollm/coverage_priority_20261103.md`를 참조한다. PDF 이전 진행 숫자와 런타임 차단 기록은 역사적 상태다. 사용자가 Coverage → RQ1–RQ5 측정계약 동결 → 개발 K1 → **8방법 K5** → 최종 untouched holdout 순서를 지정했다. 아래 144+27 수집기는 아직 확장 RQ·non-empty recovery·ablation·K5 전체 실행을 구현하지 않으므로, 측정계약/자산/runner gate 완성 후 새 protocol로 재개한다.

작성일: 2026-11-02 (KST). **현재 상태: PREPARATION_BLOCKED_RUNTIME. 실행하지 않음.** 사용자는 이번 접속에서 수정·검증을 진행하고 전체 비교는 다음 접속에서 시작하도록 요청했다. 이 문서는 시작 승인이나 완료 증거를 대체하지 않는다.

## 먼저 읽을 파일

- `docs/geollm/remaining_work_roadmap.md` 최신 인계
- `docs/geollm/normal_request_review_repair_20261102.md`
- `research/marine_geollm_scie/protocol/review_consistency_repair_20261102_KR.md`
- `docs/geollm/v6_fault_detection_explanation_20261102.md`

## 시작 전 필수 순서

1. Docker Desktop과 운영 DB/백엔드는 후속 세션에서 복구됐고 실제 API 검증을 수행했다. 재개 시 실제 상태를 다시 확인한다. 과거 socket 삭제 차단을 우회하지 않았다.
2. PDF 임베딩 worker가 실제로 없는지 명령행으로 확인한다. 마지막 독립 검증은 2,215개 중 948개 checkpoint 정상, 1,267개 남음, 최종 embedded.json 없음이다. stale lock은 검증 없이 삭제하지 않는다. 안전 재개·완료 후 원문/hash/vector/CAS/새 receipt/API를 검증한다. 기록은 `outputs/coverage_review_repair_20261102_independent/pdf_checkpoint_validation.json`이다.
3. 운영 부산 원본 cell의 DataCoverage 및 Wreck 전체 4,339행 identity 검증을 등록했다. Q4 11건과 부산 source-bound 정상 요청을 실제 API로 확인했다. 최신 근거는 docs/geollm/source_bound_execution_20261102.md 참조. 원천 존재/공간 범위/실세계 완전성을 분리하며, 연구 bbox를 운영 APPROVED로 승격하지 않는다. 각 Wreck 원문 geometry 전수 검증은 미완료다.
4. 연구 `ResearchBindingAdapter`가 사용하는 source scope와 운영 Validator의 권위 경로를 조정·검증한다. 현재 v6의 연구 CONTROL은 운영 coverage 미등록으로 차단됐다. 운영 generic 지원만으로 연구 CONTROL이 자동 통과하지 않는다. 같은 공개 연구 입력을 모든 방법에 제공하고, 연구 snapshot의 범위·hash를 검증한 별도 연구 경로와 운영 원천 권위를 분리한다. GOLD에서 실행 허용을 주입하지 않는다.
5. 초기 판정 false + 계약 필드 변경 응답은 사용 불가로 남기는 새 검토 계약을 확인한다. raw false를 true로 바꾸지 않는다. 이 모순 차단은 LLM 의미 오류 검출 개선과 다르다. 기존 v6 읽기 재현과 별도로 개발 probe 4건을 실행했다. 초기 오류 Recall 0/3, 모순 수정 거부 2/4로 의미 오류 탐지는 여전히 미완료다. 개발 결과를 논문 성능으로 재사용하지 않는다.
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
