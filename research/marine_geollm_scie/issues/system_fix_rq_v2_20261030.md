# RQ v2 시스템 수정 감사와 실제 API 재현

## 확인된 오류와 최소 수정

실제 `/api/v1/tasks` 경로에서 아래 세 질의를 실행했다. 모두 독도 반경5km 침선 검색이고, 두 번째와 세 번째는 속성 설명도 요청했다.

1. `Find wrecks within 5 km of Dokdo.`
2. `Find wrecks within 5 km of Dokdo and explain their S-101 attributes.`
3. `독도 주변 5km의 침선을 찾고 S-101 속성을 설명해줘.`

수정 전 세 응답 모두 공간검색0건 summary와 `COMPLETED`였고 속성 설명 근거나 출력의무 기록이 없었다. 0건 자체는 오류로 판정하지 않았다. 확인된 오류는 **추가로 요청한 설명을 제공하지 않았는데 전체 완료로 표시한 것**이다. GOLD는 읽거나 runtime 수정에 이용하지 않았다.

운영 변경은 `services/orchestrator/request_obligations.py` 한 파일이다. 조회 동사와 명시적인 속성 설명 요구가 함께 있을 때만 별도 출력의무를 기록한다. 속성 필터를 가진 단순 검색, 독립 정의 질문, 설명하지 말라는 요청은 구분한다. 설명이 있어도 구조화된 출처·대상 feature·속성·설명 필드가 없으면 의무를 충족했다고 표시하지 않는다. 이 근거의 존재 판정은 의미정확도나 출처 진위를100% 보장하지 않으며 기존 방식대로 `EVIDENCE_PRESENT_REVIEW_REQUIRED`다.

누락된 복합 출력은 `PARTIAL`과 구체적 미충족 설명으로 표시한다. 기존 공간 실행의 `SUCCESS_EMPTY`는 `execution_result_status`에 보존하며0건을 실패로 바꾸지 않는다. 반환된 객체가 없어 실제 객체 속성값을 설명할 수 없다는 점과, FC에 허용된 속성의 설명은 별도 카탈로그 근거가 필요한 작업이라는 점을 사용자 응답에서 구분한다. **FC 설명을 새로 생성하는 기능까지 구현한 것은 아니다.** 이후 원천 기반 속성설명 producer를 연결하면 같은 의무 계약으로 완료 여부를 검증할 수 있다.

## 기존 validator 후보의 운영 재현

합성 explicit point에서 정상 반경/잘못된 feature/잘못된 CRS/operator context충돌을 실제 API로 비교했다.

|요청|수정 전|첫 수정 후 준비완료 상태|
|---|---|---|
|정상 반경|COMPLETED|COMPLETED|
|미등록 feature 문자열|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION|
|잘못된 CRS 문자열|NEEDS_CLARIFICATION|NEEDS_CLARIFICATION|
|radius 원문과 within context 필드 충돌|COMPLETED|COMPLETED|

앞서 발견한 generic validator 독립 입력 공백은 실제 radius 전처리에서 feature/CRS가 차단되므로 이 경로의 unsafe 실행으로 재현되지 않았다. operator는 원문 자체가 radius 요청이고 쓰이지 않는 context 필드만 변형한 경우이므로 의미 계약 감사 후보로 유지하며 임의로 운영 validator를 강화하지 않았다.

## 테스트·배포 범위

- 신규 `tests/unit/test_composite_attribute_obligations.py`: 한/영 복합 요구, 단순 검색/필터/정의/부정 표현, 출처 없는 설명,0건, 기존 차단 상태, 출처 연결된 설명을 검증.
- 관련 검사: **29 passed, 4 deselected**, 기존 multipart deprecation 경고1건. 제외한4건은 이번 출력의무와 무관한 graph helper 테스트이며 전체 regression 통과를 주장하지 않는다.
- 기존 services bind mount로 변경 모듈만 반영한다. uvicorn이 reload 없이 실행 중이므로 `geollm_backend`만 재시작했다. 이미지 재빌드·다른 파일 copy·UI 수정은 하지 않았다. 사용자의 기존 static UI·feedback·test_place_graph_integration 변경은 편집하지 않았다. 일반 API 요청의 task/관측 이력은 서버의 기존 정책대로 생성될 수 있다.
- 첫 재시작 준비기간의 transport 실패3건도 보존했으며 준비 이후 결과와 분리했다. 준비 이후 첫 재검증에서는 단순 조회 `COMPLETED`, 두 복합 요청 `PARTIAL`, 모든 count0 및 복합 요청의 `execution_result_status=SUCCESS_EMPTY`를 확인했다.

## 증거 위치

- `runs/20261030_system_audit_rq_v2_before/`: 기존 validator 후보 실제 API4건
- `runs/20261030_composite_audit_rq_v2_before/`: 복합 누락 실제 API3건
- `runs/20261030_composite_audit_rq_v2_after/`: 첫 재시작 준비 중 transport 오류3건
- `runs/20261030_composite_audit_rq_v2_after_ready/`: 첫 준비완료 후 실제 API3건
- `runs/20261030_system_audit_rq_v2_after_ready/`: 정상/부정 실제 API4건

각 raw에는 요청·task ID·응답·소스 해시를 보존했다. 원본 모델실험과 smoke 결과는 수정하지 않았다. 최종 부정 표현 범위 보완 후 재시작한 검증은 별도 final run으로 추가하며 이 문서 하단에 결과를 기록한다.

## 최종 소스의 실제 API 검증 완료

최종 부정 표현 범위를 보완한 소스를 기존 bind mount로 적용하고 backend 재시작/HTTP200 확인 후 다시 검증했다.

- `runs/20261030_composite_audit_rq_v2_after_final/`: 단순 영어조회 COMPLETED, 영어복합 PARTIAL, 한국어복합 PARTIAL. 두 복합 응답 모두 count0과 `execution_result_status=SUCCESS_EMPTY` 보존 및 속성설명 미충족 기록 확인.
- `runs/20261030_system_audit_rq_v2_after_final/`: 정상 COMPLETED, invalid feature/CRS NEEDS_CLARIFICATION, operator context변형 COMPLETED. 기존과 동일.
- **7/7 실제 API에서 기대한 계약 상태 확인**. 이는 개발 재현의 계약검증이며 GOLD 정확도나 논문7건 성공률이 아니다.
- 최종 복합 raw3행에 저장된 source hash가 현재 request_obligations.py와 일치하는지 검증했다. 새 코드에 맞춰 GOLD/원본 모델예측/기존 run을 수정하지 않았다.
