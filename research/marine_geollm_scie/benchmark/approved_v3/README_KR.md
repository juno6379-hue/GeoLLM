# 사용자 승인 AI 보조 검토 v3

사용자가 기존 AI 검토 내용을 명시적으로 승인한 새 참조 버전이다. 독립 전문가 2인의 GOLD나 holdout이 아니다. 원본 DRAFT/XLSX와 기존 GOLD 파일은 그대로 보존했다.

evaluation_references.jsonl의 상위 human_approval=true 및 GOLD는 사용자 승인을 기록한다. approved_source_record의 DRAFT/false 문구는 승인 이전 원본으로 변경하지 않았다. 후보 Feature·모호성·미확정 사항을 승인에 편승하여 확정하지 않았다.

공통 평가 스키마의 semantics.labels/evidence.required_refs는 서술형 자료를 강제 집합으로 새로 해석하지 않아 null이다. QEC는 원문의 명시적 위치·거리만 전사했다. 공간 객체 ID는 별도 사용자 승인 범위와 검증된 실제 oracle manifest가 있을 때만 결합한다. 없는 geometry/coverage/객체 ID는 null이다.

승인 문구 원문·기록시각·원천/출력 해시는 approval_manifest.json을 따른다. 이벤트 발생시각이 제공되지 않았으므로 기록시각과 혼동하지 않는다. 평가기는 reference 파일 SHA256를 gold_sha256로 주입하고 USER_APPROVED_AI_ASSISTED cohort로 구분한다. 이 자료를 모델 prompt나 runtime rule 수정에 사용하지 않는다.

## 이번 승인본의 실제 범위

- 사용자 승인 AI 보조 참조 18건, 독립 전문가 검수 0건이다.
- 원문에서 명시적으로 전사한 QEC 위치/거리 필드가 있는 사례는 8건이다. 전체 계획 타당성을 채점하는 완전 계약은 아니다.
- Q4_01/02/03에만 고정된 동도 기준점·2022 해양지명 CSV의 공간 결과를 결합했다. 각 사례의 객체 ID는 `mof_marine_names_20221231:44`부터 `:54`까지 11개다. 이 셋은 동일 질의의 표현 변형이므로 33개의 독립 객체 또는 세 독립 검증 사례로 세지 않는다.
- CSV 1,146행의 좌표 처리와 두 거리 알고리즘 결과를 대조하고 원본 CSV·anchor·reference SQL 해시, 5km 포함 여부를 확인했다. 실제 원천의 세계 전체 완전성이나 공식 수직/수평 기준판 승인을 뜻하지 않는다. WGS84는 oracle에 명시한 실험 CRS 해석을 따른다.
- 다른 공간 6사례는 선택영역·대상 범위·자료 coverage 등이 미확정이므로 객체 ID를 null로 남겼다. 비공간 9사례도 공간 정답을 만들지 않았다.
- Q3_03은 선택 영역 없는 실제 입력과 원문 조건에 따라 NEEDS_USER_INPUT이다. Q4 세 사례만 승인된 고정 원천 실행 과업으로 표시했다.
- 평가 가능한 semantic label 집합과 evidence 필수 참조 집합은 원문만으로 확정하지 않았다. 따라서 해당 정답 지표는 자동으로 채워지지 않는다.

승인 후 감사는 `outputs/scie_rq_v3_approval_20261030/gold_audit_v3.json`이다. 승인 전 `outputs/scie_rq_v2_audit_20261030/`의 0건 결과와 다른 시점·버전이며 이전 산출물을 덮어쓰지 않았다. `generation_source_snapshot.py`는 실제 생성 당시 코드의 보존 사본으로 approval_manifest.code_sha256와 일치한다. 재사용 생성기는 `runners/approve_review_v2.py`에 있다.
