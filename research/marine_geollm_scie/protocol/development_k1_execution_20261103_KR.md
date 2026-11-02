# RQ1–RQ5 Development K1 실행계약

## 순서와 분리

운영 source-bound 조회 수정 이후 연구용 측정계약을 동결하고 새 K1을 실행한다. 기존 v6와 GOLD v2 및 데이터 snapshot은 보존한다. 운영 서비스의 authority 설정을 연구용으로 승격하지 않는다. 홀드아웃 내용은 열람·개발·주석·실행하지 않으며 최종 시스템 동결 후에만 평가한다.

1. 현재 코드·측정계약·모델 digest·입력·예산을 동결한다. 연구 DB 6관계를 실제 재추출하여 부모 데이터 SHA/행/열과 대조한다.
2. 동일 GOLD v2의 개발 18질의에 B0/B1/B2/B3/B4/P0/H/P1을 새로 실행한다(144개). B3 최초 계획과 B4/H 검토를 각각 공유하며 P0 변환은 lossless이다.
3. 별도 69개 통제 입력에 B4/P0/H를 실행한다(207개). 정상 clarification은 실행 가능한 정상 요청의 False Block 분모에서 제외한다. 실패·미관측은 삭제하지 않는다.
4. 별도 실제 SQL 진단 8개를 실행한다. 정상 2개와 실행 가능한 공간 오답 6개이며 8방법의 오류 방어 성능으로 합산하지 않는다.
5. 새 B1/B2 원문 36개를 고정 RQ1 추출계약으로 AI 검토한다. 이전 답변 주석을 옮겨 쓰지 않는다. 답변 주장 witness·원문 SHA 검증 후 GOLD atom과 채점한다.
6. 원문·source hash·동일 분모·공유 계획·완료 gate 및 파생 보고서를 재검증한다. 개발 K1 결과를 검토한 뒤 K5(기본 720관측)를 별도로 진행한다.

## 계약별 연결

- 총괄: `development_k1_rq_contract_20261103.json`.
- RQ1: `rq1_prediction_review_contract_20261103_KR.md`. Semantic F1/Strict Match/B2−B1/paired cluster CI. AI atom 주석은 독립 인간 의미 정확도가 아니다. 개발셋에 없는 조건은 N=0·미측정이다.
- RQ2/RQ4: `rq2_rq4_expanded_20261103_KR.md`, `fixtures/rq2_rq4_expanded_20261103_v3`. Binary와 target-code 검출, 정상 오차단, non-empty 객체 복원과 task tuple 의미 보존. 독립 원천 base는 3개다.
- RQ3: `rq3_execution_faults_20261103_KR.md`, `evaluation/rq3_contract.py`. 공통 GOLD 적격 문항의 ESR, raw spatial, joint spatial, conditional correctness(CGE), SSFR, ESR−joint 격차를 구분한다. 성공 분모 0이면 CGE/SSFR은 null이다.
- RQ5: `rq5_telemetry_20261103_KR.md`. 실제 지연/토큰/모델·SQL·도구 호출/재시도/인간 escalation, 고유 비용과 공유 비용을 구분한다. 출처 존재율은 증거의 진실성이나 전체 provenance 정확성이 아니다.

P1은 운영 graph entry를 격리된 연구 컨테이너에서 실행하고 동일 frozen corpus를 source adapter에 연결한다. 실행 source의 실제 행/열/SHA와 READ ONLY REPEATABLE READ를 확인한다. 이 조건은 운영 원천 범위 승인이나 실세계 완전성 승격이 아니다. `source_scope_install.json`, graph manifest에 별도 기록한다. 모델 budget은 기존 방법별 정책을 유지하므로 equal-compute 실험으로 주장하지 않는다.

## 실행 명령

아래 출력 경로가 없고 기존 worker가 없을 때만 시작한다. 자동 supervisor는 lock을 독점하며 실패/중단 후에는 잔존 자식·컨테이너 확인 없이 lock을 지우지 않는다.

```powershell
.venv/Scripts/python.exe -u -X utf8 -m research.marine_geollm_scie.runners.supervise_development_k1 --output research/marine_geollm_scie/runs/20261103_development_k1_rq_v1 --snapshot-output outputs/scie_development_k1_rq_20261103_v1
```

수집 뒤 `rq1_review_template/reviews_REQUIRED.jsonl`을 새 답변 원문에 근거하여 작성한다. 검토는 AI 측정주석으로 표시한다. 실제 사람이 수행하지 않은 새 답변 채점을 인간 검수로 기록하지 않는다.

```powershell
.venv/Scripts/python.exe -X utf8 -m research.marine_geollm_scie.runners.finalize_development_k1 --run research/marine_geollm_scie/runs/20261103_development_k1_rq_v1 --reviews <새36답변_AI검토.jsonl> --output <새최종보고서폴더>
```

## 완료의 범위

개발 K1 측정 완료는 새 원문·정해진 측정·완료 gate의 충족이다. 모든 모델이 정답이라는 뜻이 아니다. 새로운 144개 답변의 독립 인간 의미·근거 채점이 없으면 전체 EVQSR은 null로 남는다. 기존 답변의 사람 채점을 새 원문에 재사용하지 않는다. Safe abstention의 행동 로그가 없으면 native 차단만으로 정답 행동을 만들지 않는다. 실제 오류·미측정·소수 cluster와 권위 경로 차이를 함께 보고한다.

Table 13 ablation, K5 변동성, 새로운 독립 인간 답변 평가, 최종 untouched holdout은 별도 단계다. 이 K1을 논문 전체 또는 시스템 전체 완료로 표시하지 않는다. 실행 중 소스·계약·입력·모델·예산이 바뀌면 원본을 보존하고 새 동결 전체 run으로 다시 시작한다. 운영 UI/PDF 작업 등 무관한 변경을 덮어쓰지 않는다.
