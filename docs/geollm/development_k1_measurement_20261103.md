# RQ1–RQ5 측정계약과 Development K1 인계

사용자 요청: RQ1–RQ5 측정계약을 병렬 완성·검증한 뒤 새 동결 개발 K1 실행. 운영 수정과 논문 실험은 분리하고 최종 동결 전 홀드아웃 사용 금지.

## 완료한 준비

- RQ1: 개발 18질의의 기존 B1/B2 원문 36개를 AI가 전부 검토해 190개 예측 atom과 11개 INVALID 응답을 보존했다. 새 추출계약·원문 witness/SHA 검증 CLI를 작성했다. 이 사후 개발 분석은 새 K1 또는 독립 인간 의미 정확도가 아니다. 새 K1의 36답변은 다시 검토한다.
- RQ2: 서로 다른 원천 Wreck 기준점 3개, 오류 11종×3와 정상 대조 36개를 고정했다. B4/P0/H 총207관측이며 정상 clarification 6개×3은 binary/False Block 분모와 분리한다. 목표 fault code와 최초 invalid 판정을 별도로 측정한다. v1/v2 준비 원본을 보존하고 단일 unit fault를 교정한 v3를 사용한다.
- RQ3: 실제 SQL이 성공하면서 공간 정답은 틀리는 6개 반례와 정상2개를 확인했다. 새 run의 snapshot/profile로 계약을 다시 작성한다. 방법별 Table11은 실제144개 원문·GOLD·채점을 재검증하여 생성하며 별도 SQL 진단을 합산하지 않는다. CGE는 성공 실행에 조건부인 공간 정답률이며 ESR−joint gap과 별개다. 성공0이면 CGE/SSFR null이다.
- RQ4: 비어 있지 않은 실제 Oracle 4/5/4개를 독립 SQL로 확인했다. 복구 실행, 객체 집합 복원, 고정 task tuple 의미 보존을 각각 기록한다. scripted clean 복원은 모델 recovery 성능으로 보지 않는다.
- RQ5: 공유 모델 호출의 고유/독립 실행/배분 비용, P1 모델·논리 도구·SQL·retry·인간 escalation을 계측한다. 출처 존재와 내용 진실성은 구분하며 새 답변의 의미/근거 판정 없이는 전체 EVQSR를 만들지 않는다.
- P1 연구 격리 프로세스에 동일 finite frozen corpus를 연결했다. 실제 개발 probe v2는 Q4/정상control 승인 및 범위밖 DATA_OUT_OF_SCOPE 차단을 확인했다. 운영 registry 또는 원천을 연구APPROVED로 바꾸지 않았다.

## 교차검증에서 발견한 결함

- supervisor 중단 시 살아 있는 자식 작업을 남기고 lock을 삭제하는 결함을 재현했다. 비정상/중단 때는 lock·PID·잔존 컨테이너 가능성을 보존하고 정상 수집 완료 때만 해제하도록 수정했다.
- RQ5 event ID 생성이 case ID 없는 mock/helper 호출에서 실패해 검토 실패 receipt 저장을 건너뛰던 회귀를 수정했다. 실제 cohort에는 case ID가 있으며 helper의 미관측 ID는 null이다.
- snapshot freeze의 무관한 protocol 문서 포함 문제를 발견하여 명시적 개발 계약 목록만 동결하도록 수정했다. 부모 데이터 6관계는 변경을 허용하지 않는다. 현재 execution source 변경은 새 manifest에 이전/현재 SHA를 공개하며 옛 결과를 재사용하지 않는다.
- finalizer는 새 source/profile/GOLD identity, 공유 계획, raw 행, 실제 SQL 진단 및 새 RQ1 annotation을 재검증한다. 수집 개수만으로 전체 완료를 선언하지 않는다.

검증 자료는 `outputs/development_contract_20261103_v1`, `outputs/rq1_prediction_complete_20261103_v2/freeze_candidate`, `outputs/rq3_execution_faults_20261103_v4`, `outputs/rq3_methods_bridge_20261103_v2`, `outputs/rq5_integration_probe_20261103_v1`에 보존했다. 초기 실패 probe도 덮어쓰지 않았다.

## 실행·완료 확인

통합 연구 테스트625개가 통과했다(136.55초). 별도 finalizer34개와 freeze/telemetry12개 검사는 중복합산하지 않는다. 소스 커밋은 a5f7147이다.

실행 명령·측정 범위·후속 순서는 [실행계약](../../research/marine_geollm_scie/protocol/development_k1_execution_20261103_KR.md)을 따른다. 새 실행은 `research/marine_geollm_scie/runs/20261103_development_k1_rq_v1`, 새 snapshot은 `outputs/scie_development_k1_rq_20261103_v1`이다. 2026-11-03 08:39 KST에 실제 시작했다(launcher7340/supervisor25104). 실제 연구DB6관계와337개 source 동결 LOADED_VERIFIED를 확인했으며 전체 실험은 아직 진행 중이다. 해당 `status.json`과 부모/자식 PID, graph/comparison/fault raw를 확인한다.

실행 중 동결 소스·입력·계약·모델·예산을 변경하거나 추가 Ollama/API 부하를 주지 않는다. 실패 시 원본 보존, 원인 재현, 별도 수정·테스트 후 새 전체 frozen run을 사용한다. lock은 자식/컨테이너 부재를 실제 확인하기 전 삭제하지 않는다.

K1 다음은 오류 검토와 K5이며 ablation과 새 답변 인간 의미 평가는 별도 남은 단계다. 홀드아웃은 최종 시스템 동결 뒤 평가한다. 기존 GOLD/답변 인간 승인 기록은 보존하되 새로 생성된 답변의 인간 채점으로 이전하지 않는다.
