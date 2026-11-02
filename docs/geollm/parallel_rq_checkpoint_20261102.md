# RQ1–RQ5 병렬 개발 체크포인트

2026-11-02. 사용자 요청에 따른 GitHub 게시 시점 기록이다. 기존 v6 결과를 표시·검증하는 작업과 새 실험 계측 개발을 구분한다.

| 담당 | 범위 | 현재 결과 |
|---|---|---|
| entity_verify | RQ1 grounding / RQ3 실행·공간 정확성 | 조건별 Table 9, 새 명시 관측 평가 모듈 및 합성 검사 |
| locator_verify | RQ2 오류 탐지 / RQ4 복구 | Table 10–14 원본 연동, 오류/복구 분모 확인, 다음 실행 계약; 새 RQ2/RQ4 evaluator 미작성 |
| pdf_verify | RQ5 비용 / ablation | 비용·모듈 제거 실험 계획, 새 명시 관측 evaluator 및 합성 검사 |
| 부모 | 통합·실제 원본 대조 | UI 연결, 누락값/분모/실험 출처 확인, 운영 Dataset 작업과 분리 |

## 실제 결과와 미측정

현재 인용 가능한 완료 실행은 `research/marine_geollm_scie/runs/20261102_gold_v2_eight_k1_v6`의 144개 답변과 27개 통제 관측이다. 새 모델 비교를 실행한 것은 아니다. Table 9의 Semantic F1/Strict Match/CI는 정답 atom 계약과 관측이 없어 미측정이다. 실제 모듈 제거 실험과 paired CI도 미실행이다.

통제 오류 8개에 대해 B4 검토기는 모두 정상으로 판정했고 P0/H는 모두 차단했다. 정상 대조 1개는 P0/H가 차단했다. 이진 차단율은 정확한 오류 원인을 모두 식별했다는 뜻이 아니다. 공통 coverage 미승인이 함께 작용하므로 오류별 blocker와 정상 오차단을 같이 해석해야 한다.

P1 ESR은 0/5, 원래 Spatial Correctness는 2/5만 측정되어 전체 값 null이다. 공동 실행·공간 성공 0/5를 원래 공간 정확성으로 바꾸지 않는다. CGE는 성공 조건부 공간 정확성이고 성공 분모 0에서 미정의다. EVQSR에 필요한 관측이 없으면 다른 이진 점수로 대신하지 않는다.

## 운영 Dataset 작업

- 원문 재대조에서 추가 literal 확인 142개, XLSX 저장 XML을 셀 본문으로 사용한 99개는 불일치 격리 대상으로 구분했다.
- FC 302개는 원본 XML 필드를 보완하고 bge-m3 고정 digest·1024차원으로 재임베딩 후 운영 DB에 적용했다. 이전 행·벡터를 보존했다. 본문 literal 확인과 파생 필드 검증은 별개다.
- PDF 2,215개는 숫자 표기를 보존하는 원문 span 후보로 준비했고 재임베딩 중이다. 완료·운영 적용으로 간주하지 않는다. 409개는 수치 차이/정렬 실패로 보류한다.
- FC 적용 후 receipt의 최초 게시 시도는 snapshot provenance gate에서 거부되었다. 생성기 보완과 새 산출물 검증을 진행했다. 실제 current 게시 및 서비스 재시작/API 검증은 별도 확인해야 한다.
- 작업 파일·checkpoint는 `C:/Users/최준오/.codex/geollm-audit/20261102/`, 감사 요약은 `outputs/dataset_unverified_followup_20261102/`에 있다. 런타임 파일은 GitHub 소스 커밋과 분리한다.

## 재개 순서

1. 실제 PDF worker/PID/checkpoint와 pinned 모델 digest를 확인한다. 중복 worker를 띄우지 않는다. 완료 후 원문·벡터·기존 DB CAS를 검증하고 새 revision으로 적용한다.
2. 새 source receipt provenance를 검증·게시하고 운영 대표/부정 질의에서 실제 본문 활용을 확인한다. XLSX/DOCX와 실제 지명·좌표 대상 연결의 남은 문제를 보완한다.
3. RQ1 atom/GOLD 계약, RQ2/RQ4 계측, RQ3 분모, RQ5 비용 귀속을 고정한다. 새 모듈 합성 검사는 실제 시스템 실험이 아니다.
4. 안정된 운영 소스·데이터·모델·예산을 새로 동결한 뒤 8방법 전체 비교와 별도 fault/recovery/ablation을 실행한다. 과거 raw를 새 실행으로 재사용하지 않는다.
5. 홀드아웃은 개발에 사용하지 않고 최종 동결 후 별도 gate로 평가한다. 기존 GOLD 승인과 독립 인간 답변 의미 채점의 provenance를 구분한다.

세부 계획: [RQ1·RQ3](rq1_rq3_execution_readiness_20261102.md), [RQ2·RQ4](rq2_rq4_execution_readiness_20261102.md), [RQ5·ablation](rq5_ablation_execution_readiness_20261102.md).

## 체크포인트 검증

운영 후속 통합 90개, UI Python 66개, UI Node 20개 검사가 통과했다. 새 RQ1/RQ3·RQ5와 receipt 게시 통합 검사는 합쳐 40개가 통과했다. 부분 실행 결과와 중복 합산하지 않는다. 실제 새 API 검증과 새 모델 비교는 완료하지 않았다. FC v5 receipt는 재생성 검증됐지만 current 게시를 아직 수행하지 않았다.

[v6 오류 8건·정상 1건의 상세 원인](v6_fault_detection_explanation_20261102.md)에는 LLM 초기 판정과 무보고 수정, compiler/native 검출 근거, 연구 범위와 운영 coverage 권한의 차이를 기록했다.
