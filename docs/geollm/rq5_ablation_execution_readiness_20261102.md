# RQ5 비용·신뢰성과 모듈 제거 실험 준비 상태

작성: 2026-11-02. 상태: **기존 결과 확인 및 새 실험 계약 준비**. 이 작업에서 모델 호출, DB 변경, 새 실험 실행은 하지 않았다. 운영 SourceCorpus 보완과 진행 중인 재임베딩이 완료되기 전에는 추가 Ollama 실험을 시작하지 않는다.

## 확인한 기존 결과

기준 run은 `research/marine_geollm_scie/runs/20261102_gold_v2_eight_k1_v6`이다. 아래 값은 그 run의 `report_with_faults/summary.json`, `comparison/observations.jsonl`, `faults/rows.jsonl`을 직접 읽은 값이며, 이후 운영 수정의 성능을 나타내지 않는다. 8개 방법 각 18문항, K1이며 18문항은 16개 표현 동등 그룹이다.

| 방법 | p50 초 | p95 초 | 평균 입력 토큰 | 평균 출력 토큰 | 평균 tool calls |
|---|---:|---:|---:|---:|---:|
| B0 | 28.98 | 49.55 | 1326.50 | 121.78 | 0.00 |
| B1 | 41.34 | 83.67 | 2438.61 | 130.11 | 0.00 |
| B2 | 48.16 | 104.16 | 2651.67 | 163.50 | 0.00 |
| B3 | 40.86 | 85.67 | 2037.50 | 229.67 | 0.83 |
| B4 | 95.15 | 167.28 | 4139.89 | 501.11 | 1.17 |
| P0 | 41.08 | 85.86 | 2037.50 | 229.67 | 0.11 |
| H | 95.20 | 167.35 | 4139.89 | 501.11 | 0.17 |
| P1 | 10.09 | 33.34 | 112.67 | 39.28 | 미측정 |

지연·토큰은 각 18/18 계측이다. P1 tool calls는 0/18 계측이며 0회라는 뜻이 아니다. 모든 방법의 요약 SQL/model calls도 미측정이다. B4/H는 검토 응답을 공유하므로 표의 논리적 방법별 비용을 합해 실제 전체 소비량으로 보고하면 안 된다. P1의 짧은 지연을 신뢰성 향상으로 해석할 수 없다. 정상 공간 요청 차단에 따른 가용성 저하도 함께 측정해야 한다.

별도 통제 오류 집합(방법별 오류 8건+정상 1건)의 검토기 판정은 다음과 같다. 공통 실행 차단 정책 이전의 `predicted_invalid`를 사용한다.

| 방법 | Recall | False Ready | False Block |
|---|---:|---:|---:|
| B4 | 0/8 | 8/8 | 0/1 |
| P0 | 8/8 | 0/8 | 1/1 |
| H | 8/8 | 0/8 | 1/1 |

정상 대조군이 1건뿐이므로 전체 서비스 오차단율로 일반화하지 않는다. 18문항 비용과 9건 오류 집합의 분모를 합쳐 하나의 비용 대비 신뢰성 점수로 만들지 않는다. SourceCorpus의 문서 검색 정상 요청 오차단 개선은 **새 운영 검증 결과**로 별도 기록하며 위 v6 수치를 소급 변경하지 않는다. 문서 검색 허용이 공간 데이터 coverage 승인도 의미하지 않는다.

## 측정 가능한 것과 남은 것

- 기존 frozen 요약의 공통 ESR은 모든 방법 0/5이다. 공간 정확도는 방법마다 2/5 계측·3/5 결측으로 전체 값 null이다. SSFR은 실행 성공 분모가 0이어서 정의되지 않는다. 오류율 0%라는 뜻이 아니다.
- EVQSR은 `protocol/paper_metric_definitions.md` 및 `evaluation/metrics.py`의 정의가 이미 있다: EXECUTE 대상에서 `semantic_correct × plan_valid × execution_success × spatial_correct × evidence_correct`. 다섯 값 중 결측이 있으면 전체 값 null과 구성요소별 계측률을 보고한다. v6의 각 관측에 이 다섯 판정을 동일 답변 해시 기준으로 연결한 완료 자료는 위 frozen 요약에 없다. UI에서 임의로 기계계약 통과율을 EVQSR로 대체하지 않는다.
- 독립 답변 채점·승인 자료는 별도 lineage로 연결해야 한다. 이 문서는 v6 원본에 남은 `semantic_human_accuracy=null`만 확인했으며 이후 채점 자료가 없다고 단정하지 않는다. 채점 답변 SHA, 기준 GOLD SHA, 검수 provenance가 해당 관측과 일치하는지 확인 후 새 평가 산출물로 만든다.
- Human Escalation, evidence completeness, provenance completeness는 현재 Table14에서 미측정이다. raw 파일 SHA가 존재하는 것은 재현성 근거이지 답변의 모든 주장에 충분한 근거가 있다는 판정은 아니다.
- CGE는 `evaluation/rq_metrics.py::spatial_gap`에서 P(공간 정답|실행 성공)으로 정의되어 있음을 독립 확인했다. 동일 성공 집합의 공간 판정이 완전할 때만 1−SSFR이며, v6는 성공 분모 0으로 산출 불가이다. Table11은 관측 Spatial Correctness, 실행·공간 공동 성공, CGE, 기존 gap을 별도 열로 보존한다. 기존 gap은 ESR−공동 성공이며 raw 공간 정확도와의 차이가 아니다.

## 새 계측 계약: 동결 전에 구현·검증할 필드

아래는 신규 계약 요구사항이며 현재 모두 구현되었다는 뜻이 아니다.

| 대상 | 원시 필드와 검증 |
|---|---|
| 관측 식별 | run_id, method/configuration, case_id, repeat, equivalence_group, benchmark/GOLD/source/model/prompt hash, answer SHA, module_flags hash |
| EVQSR | expected_behavior, eligibility, 다섯 boolean 판정, 각 판정 oracle/reviewer·artifact SHA·결측 사유; PARTIAL/CLARIFY/ABSTAIN 별도 cohort |
| 지연 | monotonic 시작/종료, queue/warmup 여부, 단계별 시간, timeout 포함; 동일 시작·종료 경계로 end-to-end p50/p95/IQR |
| 모델 비용 | call_id, parent_call_id, stage, model digest, input/output tokens, 실제 시도·실패·재시도, shared_call_id 및 실제 비용 귀속 |
| 도구 비용 | tool_event_id, 도구명, 호출 시작/종료/오류, spatial 여부, SQL 실행 boolean/횟수, 재시도와 중복 제거 규칙 |
| Escalation | escalation_eligible, escalated boolean, reason, 대상 사람/단계, 요청·응답 event; 단순 NEEDS_USER_INPUT과 구분 |
| Evidence completeness | 사전 고정한 required claim/task IDs, answer claim IDs, claim→citation 연결, 실제 인용내용 지지 판정, supported/required 개수와 판정 출처 |
| Provenance trace | citation→chunk/object ID→source locator/page/span→원본 SHA→snapshot SHA 역추적, required/valid trace 개수, 중간 연결 누락 사유 |
| FR/FB | 독립 계획 적합성 label, raw detector 결정, 최종 실행 결정, coverage 상태/권위, 오류 유형, 정상군·오류군 분모 |

Escalation은 `metrics.py`의 `human_escalation`과 다른 경로의 `escalated`를 명시적으로 정규화한다. 결측을 false로 채우지 않는다. Evidence completeness와 provenance trace는 분모 정의·복합 작업 처리·지원 판정 방법을 고정한 후 산출하며, 단순 비어 있지 않은 citation 수를 성공으로 쓰지 않는다. 성공·실패·timeout 모두 비용 관측에 남긴다. P1 tool 계측도 B3와 같은 범위로 맞춘다.

## Table13 모듈 제거 실험

Full P1 및 w/o Ontology, w/o Bounded KG, w/o QEC, w/o Validator, w/o Post-validation Recovery의 6개 조건을 별도 configuration으로 실행한다. **B0/B1/B2/B3/B4/P0/H를 이 제거 조건으로 재명명하지 않는다.** 현재 이 다섯 제거 조건의 실행 원본은 Table13에 연결되어 있지 않아 모두 미측정이다.

모델·문항·GOLD·snapshot·예산·반복 수·평가계약을 같게 두고 한 번에 한 모듈만 제거한다. 제거된 기능을 다른 경로가 몰래 보충하지 않았음을 stage trace로 검증한다. 실제 실행 보호 장치는 모든 조건에 동일하게 유지하고 연구 read-only DB에서만 실행한다. Validator 제거 조건에서도 최종 안전 정책이 차단했다면 그 효과를 제거된 Validator 효과로 보고하지 않고 detector decision과 execution floor를 분리한다.

Semantic/Schema/Spatial/Runtime/Evidence 다섯 오류 분류는 raw 기계 실패 키에서 자동 추정하지 않는다. 각 범주의 정의, 중복 오류 집계 방식, 미측정 처리와 사례별 mapping을 실행 전에 동결한다. Full P1의 기존 실패 키는 원문 그대로 보존한다. EVQSR 및 공간 정확도의 Full 대비 paired delta는 동일 문항·반복끼리 계산하며 CI는 그룹 의존성과 반복 구조를 반영한 사전 지정 재표집법으로만 계산한다. 현재 K1 표에 가짜 CI를 붙이지 않는다.

## 실행 순서와 명령

1. 진행 중 운영 재임베딩의 완료/차원/model digest/원문 receipt를 검증하고 운영 SourceCorpus 대표 정상·부정 요청을 검증한다. 연구 snapshot을 운영 승인 coverage로 승격하지 않는다.
2. 위 공통 계측 및 제거 스위치, 오류 taxonomy 계약을 구현하고 단위·통합 검증한다. Holdout 문항/GOLD는 읽거나 개발에 사용하지 않는다.
3. 동결 전에 기존 supervisor 및 하위 runner의 source lists가 신규 계측 소스를 모두 포함하는지 확인한다. 새 run/snapshot 경로, 실제 worker/lock 부재, DB 실제 재추출 hash, 모델 digest, 원문 변경 lineage, 예산을 검증한다.
4. 전체 8방법과 통제 오류를 새 동결 조건으로 실행한다. 기존 v6 답변을 운영 수정 이후 결과로 재사용하지 않는다. 다음은 **현재 지원되는 8방법 supervisor 명령 형식**이며 아직 실행하지 않았다. `<NEW_RUN>`과 `<NEW_SNAPSHOT>`는 존재하지 않는 새 경로로 정하고 gate 완료 후 실행한다.

```powershell
.venv/Scripts/python.exe -u -m research.marine_geollm_scie.runners.supervise_eight --output research/marine_geollm_scie/runs/<NEW_RUN> --snapshot-output outputs/<NEW_SNAPSHOT> --include-faults
```

5. `supervise_eight.py`의 현재 CLI에는 `--output`, `--snapshot-output`, `--include-faults`만 있으며 ablation 실행 스위치는 없다. 따라서 위 명령만으로 Table13이 완료되지 않는다. 제거 조건 manifest/runner 및 각 조건 trace 검증을 구현·동결한 뒤 별도 실행 명령을 이 문서에 추가한다. 지원하지 않는 명령을 제시하지 않는다.
6. raw hash, 동일 GOLD, B3 공유 계획/B4-H 공유 검토/P0 lossless, 계측 결측률·분모, 성공과 공간 정답의 분리를 검증한 후 Table10~14를 새 run 선택으로 연결한다. 최종 시스템 동결 후 holdout 평가를 별도로 실시한다.

## UI 반영 및 확인

`tools/scie_results_ui/static/app.js`에서 Table10/11/12/14를 RQ2/3/4/5 맨 앞에 표시하고 기존 기계표는 보조 진단으로 접었다. Table13은 RQ4 다음 신뢰성 모듈 비교 메뉴에 둔다. 8개 방법을 유지하고 B4/H 추가 비교를 표시한다. 측정 0, 미측정, 분모 0을 구분하며 근거 경로·SHA와 결측 사유를 표시한다. Table9 기존 구현은 보존했다. UI Node 회귀검사 20/20 통과. 실제 서버 재시작·브라우저 검증은 부모 통합 작업에서 수행한다.

참조: `tools/scie_results_ui/paper_tables.py`, `research/marine_geollm_scie/protocol/paper_metric_definitions.md`, `research/marine_geollm_scie/evaluation/metrics.py`, `research/marine_geollm_scie/protocol/eight_execution_v6_20261102_KR.md`.
