# RQ 중심 v2 실행 인계 — 2026-10-30

## 먼저 확인할 현재 상태

사용자는 기존 AI 검토의 승인 전환과 공간 정답 ID 작성을 명시적으로 지시했고, Q4 조건으로 **독도 동도 기준점·2022 해양지명 CSV**를 선택했다. 이에 원본 DRAFT와 지정 v2 XLSX를 변경하지 않고 `benchmark/approved_v3/`에 새 참조 버전을 생성했다.

- 사용자 승인 AI 보조 참조 18건: `annotation_status=GOLD`, `human_approval=true`, `adjudication_status=APPROVED`.
- 독립 전문가 검수 0건: `independent_expert_review=false`, `two_reviewers=false`, `holdout_eligible=false`.
- QEC 부분 슬롯 8건: 원문의 위치·거리만 전사. 전체 계획의 정확도를 의미하지 않는다.
- Q4 세 표현에 실제 원본 ID44–54 각11개: 같은 동등표현 그룹·같은 객체집합이다.
- 미확정 의미 label 집합·근거 필수집합·다른 공간 과업은 자동으로 채우지 않았다.

[18개 승인 현황표](../benchmark/approved_v3/승인현황_KR.md), [승인 manifest](../benchmark/approved_v3/approval_manifest.json), [평가 참조 JSONL](../benchmark/approved_v3/evaluation_references.jsonl), [독립 재검증 기록](../benchmark/approved_v3/independent_verification_v3.json)을 읽는다. 참조 JSONL SHA256는 `a69cda7558eca74c8d869de6fc80653c51541ab2cc4a7cb628e3fd065b27558c`다.

## 승인 전후 자료의 구분

[GOLD 감사 문서](gold_audit_v2_KR.md)는 **승인 이전** 파일의 DRAFT·0건 상태를 기록한 것이다. 승인 후 최종 감사는 `outputs/scie_rq_v3_approval_20261030/gold_audit_v3.json`이다. 같은 폴더의 초기 `gold_audit.json`은 references 파일명 탐색 보완 전의 산출물이므로 최종 승인 감사로 사용하지 않는다.

사용자 승인 기록은 독립 전문가 둘이 서로 보지 않고 판정한 결과가 아니다. 기존 AI 작성자와 approving_user를 분리했고, 사용자 요청 원문과 조건 선택 원문을 manifest에 보존했다. 메시지 발생 timestamp는 제공되지 않아 기록시각과 별도로 null을 유지했다. 원본 source record 내부의 DRAFT/false는 승인 이전 역사 자료로 그대로 남겼다.

공통 schema는 `semantics.labels`, dotted-key `qec_fields`, `spatial.object_ids`와 snapshot/oracle hash, `evidence.required_refs`다. 표준화가 원문 재해석을 허용하는 것은 아니다. `semantics.labels`와 `evidence.required_refs`는 강제 집합으로 확정할 근거가 없어 null이며, 자동 정확도 값도 그 제한을 따라야 한다.

## 실제 공간 참조

[독도 공간 참조와 실제 지명·거리](dokdo_spatial_reference_v3_KR.md)를 따른다. 계산 자료는 `outputs/scie_dokdo_reference_20261030_v2/`의 `spatial_reference.json`, `all_distances.jsonl`, `reference_query.sql`이다.

2022 CSV 1,146행, 공개 동도 기준점, 5000m 이하 포함 조건을 고정했다. 좌표 문자열 파싱 trace와 WGS84 실험 해석을 보존했고 PostGIS geography와 Vincenty 거리·포함 여부를 검산했다. 참조 결합 시 CSV·anchor·SQL 해시와 전 행 검산·membership을 재확인했다. 이 ID는 S-101 Feature ID가 아니라 `mof_marine_names_20221231:<원본 ID>`이다.

선택 AOI가 없는 Q3_03은 NEEDS_USER_INPUT이며 객체집합을 만들지 않았다. 기존 부산권 연구 snapshot이 독도 Wreck 영역을 포함하지 않는다는 점을 고려해야 한다. 그 snapshot의 0건을 독도 난파선 정답으로 전용하지 않는다. 다른 공간 6사례는 geometry·원천 coverage·시설 의미 등이 확정될 때까지 null을 유지한다.

## 최신 RQ 결과와 생산 진단

- [최신 RQ 해석](../results/latest/reports/SCIE_RESULTS_INTERPRETATION.md)
- [최신 결과 요약](../results/latest/reports/final_results_summary.md)
- [최신 manifest](../results/latest/manifest.json)
- [RQ1 조건별 효과](../results/latest/reports/RQ1_condition_effectiveness.md)
- [RQ2 오류 탐지](../results/latest/reports/RQ2_error_detection.md)
- [RQ3 실행–공간정답 차이](../results/latest/reports/RQ3_execution_spatial_gap.md)
- [RQ4 복구와 의미 보존](../results/latest/reports/RQ4_recovery_semantic_preservation.md)
- [RQ5 신뢰성과 비용](../results/latest/reports/RQ5_reliability_cost.md)
- [격리 생산 graph 진단](rq_v2_graph_smoke_KR.md)
- [시스템 수정 기록](../issues/system_fix_rq_v2_20261030.md)
- [영어 위치 해석 수정 기록](../issues/english_reference_fix_rq_v2_20261030.md)

latest는 이후 재분석으로 바뀔 수 있으므로 manifest의 run_id·source hash·참조 승인종류를 기준으로 해석한다. 최종 확인된 latest는 `20261030_rq_v2_reanalysis_04_userapproved_before_after`이며 216개 기록을 실행 범위별로 분리한다. 이후 작업에서도 실제 manifest를 다시 확인해야 한다. 기존 B0–B4 90행은 planning-only다. 공통 plan JSON을 별도 생산 QEC DRAFT로 캡처했으며 생산 QEC가 모델 출력 계약 자체였다고 표현하지 않는다.

최종 API 검증은 `runs/20261030_english_reference_rq_v2_after_exact/`에 보존했다. 독도와 BUSAN HANG은 완료, 복수·누락·미등록·60km 요청은 확인 요청으로 차단됐다. 부산항은 서로 다른 원천 후보 2개, 울릉도는 후보 0개로 확인 요청을 유지했다. 단위검사 33건 통과. 속성 설명 누락의 PARTIAL 보완과 이 영어 위치 수정은 별도 운영 수정이며 모델 prompt에 승인 정답을 넣지 않았다.

루트가 원본 Q4 세 질의를 다시 실행한 `outputs/scie_q4_live_20261030_after_location_fix/api_rows.jsonl`은 세 건 모두 COMPLETED·11개 반환이다. raw SHA256 `3f8ac8a36cb3ef0a0d9315450c2144890b010f6dd98ab2bb3d923a9a510d6c26`. `outputs/scie_q4_score_20261030_after_fix/summary.json`에서 수집 manifest·원문·원천 hash·관측 전후 코드 불변을 확인했고, 객체집합 3/3 일치 및 거리 33객체 모두 0.01m 이내를 확인했다. 수정 전 `outputs/scie_q4_score_20261030_before_fix/`는 실행/객체집합 2/3이며 영어는 미실행이었다. 수정 전에는 production 전후 hash를 수집하지 않았다는 제한을 유지한다. 두 run을 서로 다른 cohort로 보고하며 세 질의는 독립 지리 표본 1그룹이다. 개발 코드 수정 후 재실행을 bounded recovery나 holdout 결과로 전용하지 않는다.

## 검증과 재현

```text
.venv/Scripts/python.exe -m pytest research/marine_geollm_scie/tests/test_approve_review_v2.py research/marine_geollm_scie/tests/test_gold_audit.py -q
```

승인 생성·원본 불변·oracle 해시와 거리 검산·공통 평가 schema 호환 테스트 11 passed. 추가 독립 검사에서 참조 JSONL, 원본 v2 합의 자료, A/B/합의 XLSX, Q4 oracle, 승인 후 audit의 원천 해시와 사례 수를 확인했다.

생성기 보존 사본에 Windows CRLF가 들어가 manifest의 생성 당시 코드 해시와 다른 문제가 있었다. **코드 사본만 원래 LF bytes로 복원**하여 manifest와 일치시켰다. 승인 manifest와 정답 JSONL은 변경하지 않았다. 전후 해시는 `independent_verification_v3.json`을 따른다.

재실행은 새 출력 디렉터리를 사용한다. 승인 생성기는 [approve_review_v2.py](../runners/approve_review_v2.py), 감사기는 [gold_audit.py](../runners/gold_audit.py), 조건 분류기는 [condition_metadata.py](../runners/condition_metadata.py)다. 조건 메타데이터는 GOLD 외 별도이며 `post_hoc=true`를 유지한다. source/oracle 입력을 확인하지 않은 채 승인 생성 명령을 다시 실행하거나 기존 버전을 덮어쓰지 않는다.

## 다음 순서

1. 다음 실행 전 latest manifest와 위 최종 Q4 run·운영 수정 이력을 먼저 확인한다. 정상/부정 재현은 새 run으로 보존한다.
2. 다른 공간 과업도 실제 source snapshot·ID namespace와 참조를 확인한 뒤 평가한다. source가 다르면 정확도 채점을 보류한다.
3. 남은 semantic/QEC/evidence 계약과 다른 공간 과업의 AOI·경계·coverage·시설 중복 정책을 검수하여 새 참조 버전을 만든다. 승인 자료를 유리하게 다시 쓰지 않는다.
4. 실행형 B3, 동일 조건 P0/P1/full P, post-validation·bounded recovery·ablation을 실제 동결 데이터로 연결한다.
5. 별도의 미노출 holdout과 독립 전문가 주석, K5와 paired/군집 통계로 본실험을 수행한다.

현재의 18건 사용자 승인, 일부 실제 공간 참조, RQ 표·그림 생성만으로 RQ1–RQ5 전체에 답했거나 논문 Results가 완성됐다고 주장하지 않는다. 준비 상태는 [RESULTS_READINESS.md](../RESULTS_READINESS.md)를 따른다. 운영 P0와 Qwen shadow/QLoRA 정책은 별도 로드맵을 유지한다.
