# v2 검토자료 반영 — 2026-10-30

사용자가 지정한 검수자 A·B·합의수정본 v2를 논문 연구용 기준으로 반영했다. 운영 라우팅, QEC 실행 권한, DB, 웹 소스는 변경하지 않았다.

## 입력과 승인 상태

원본은 `outputs/scie_annotation_ai_prefill_20261030/`에 있고, 실행 시점 사본은 `outputs/scie_review_v2_20261030/`에 보존했다.

| 원본 | SHA256 |
|---|---|
| 검수자A_18사례_AI사전검토_Dataset근거_v2.xlsx | 298e56ee5f401620c29d18908c031da467b362ae76326978ef8ecda1f1014a61 |
| 검수자B_18사례_AI사전검토_v2.xlsx | feb4b38125c9ae17af790ef70b18bdd0610b1553db4d8705dd3ebabca4d8db9b |
| 합의검토_18사례_AI합의수정본_v2.xlsx | 97ee97567ddf224a65ed592c4f09bb4cfb47e60700d656984b2a76ad3d0c95c3 |

합의문에 기록된 A/B 해시와 실제 파일이 일치한다. 파일명만 v2로 바뀐 것으로 보이는 경우도 내용 해시로 검증했다. 18개 ID·원문이 기존 benchmark와 일치한다. B의 화면 요약에는 생략된 내용이 있어 `입력필드전체`를 함께 보존했다. 합의 18행은 모두 DRAFT, `human_approval=false`이며 GOLD/인간 검수자 kappa로 승격하지 않았다. 주요수정 1 + 주요보완 8, 일치+보완 8, 일치 1은 문서상의 AI 검토 분류다.

## 실제 수행

- 원본 통합: `annotations_DRAFT.jsonl`, `workbook_cells.json`, 원본 XLSX 사본 및 해시 manifest를 별도 경로에 생성했다. 기존 검토안과 모델 응답을 덮어쓰지 않았다.
- 기존 완료 run `20261030_comparison_v2b`의 manifest/행수/원시 SHA256을 확인했다. 6문항 × B0–B4 × 3회 = 90행에 v2 합의를 연결했다. 신규 모델 호출은 없다. 18문항 중 나머지 12문항의 이 비교 실험은 미수행이다.
- 비공간 질의의 공간슬롯 없음, 명시 5km→5000m/dwithin, 선택 영역의 intersects만 사후 구조 진단했다. 전체 의미·속성 설명·근거 적합성·clarification 타당성을 자동 채점하지 않았다.
- Dataset CSV 원본도 읽기 전용으로 대조했다. 해양지명 1,146행 중 어느 필드든 독도 문자열을 포함한 행 14, 독도 정확 값 0. 부산청 항로표지 314행 중 등대 문자열 포함 50, 독도 포함 0. 문서와 부합하지만 전국 coverage·좌표·공간 정답을 입증하지 않는다. 다른 ZIP/DB dump의 공간 객체집합은 이번 실행에서 재검증하지 않았다.

## 관측 결과

| 방법 | 출력 | 슬롯 재검토 필요 출력 | 계획 미제공 |
|---|---:|---:|---:|
| B0 | 18 | 8 | 1 |
| B1 | 18 | 5 | 0 |
| B2 | 18 | 4 | 0 |
| B3 | 18 | 9 | 0 |
| B4 | 18 | 4 | 0 |

총 30개 출력에서 제한된 슬롯 조건과 불일치를 관측했고, 1개 출력은 계획이 없다. 여러 필드가 함께 어긋날 수 있으므로 필드별 건수를 독립 오류 건수로 합산하지 않는다. 조건을 통과한 출력도 정답이라는 뜻은 아니다. 6문항은 영어 5/한국어 1의 편의 표본이며 반복을 독립 사례로 취급하지 않는다. B3는 도구 계획만 작성하고 실제 실행하지 않았다.

예: `PILOT_Q1_03` B2 반복 0은 정의 질문에 `action=search`, `location_text=S-101`, `radius_m=0`, `spatial_relation=dwithin`을 생성했다. `PILOT_Q2_03` B2 반복 0은 `product`, `feature_candidates`를 속성으로 제시했다. 이들은 표준 객체 정의·속성 설명과 검색 공간 조건을 혼동하는 재검토 사례다. 원문 응답과 v2 합의를 보고서에 함께 보존했다. 실제 서비스에서 같은 오류가 재현됐다는 뜻은 아니다.

상세 18문항 기준 및 90행 출력: `outputs/scie_review_v2_20261030/v2_comparison_KR.md`.

## 다음 순서

1. v2의 남은 조건을 확정한다: 등대 구조/등화 및 시설 중복 정책, Feature별 속성 binding, 독도 기준 geometry, 부산항 polygon과 거리/경계 포함 정책. 합의문을 정확도 정답으로 사용하려면 별도 사람 검수가 필요하다.
2. 고정한 Dataset·기준 geometry를 사용해 독립 공간 oracle을 만든다. Q4 세 언어·단위 표현은 동일 object set인지 검증한다. 실제 값과 표준 허용속성 설명을 분리한다.
3. 이번 6문항 사후 진단 결과를 보고 평가 기준을 보강한 사실을 명시하고, 사전에 고정한 기준으로 나머지 12문항 및 독립 holdout을 실행한다. 이번 자료는 이미 노출된 pilot이며 holdout으로 재사용하지 않는다.
4. 실행형 B3/full P, ablation, bounded recovery 및 본실험은 계속 미완료다. 후보 오류는 연구 기록에 남기고 실제 API 재현 후 별도 운영 수정으로 넘긴다. 이번에는 운영 소스를 수정하지 않았다.

## 재현

```powershell
.venv/Scripts/python.exe -m research.marine_geollm_scie.runners.review_v2_diagnostics --input-dir outputs/scie_annotation_ai_prefill_20261030 --model-run research/marine_geollm_scie/runs/20261030_comparison_v2b --output outputs/scie_review_v2_<새이름>
.venv/Scripts/python.exe -m pytest research/marine_geollm_scie/tests/test_review_v2_diagnostics.py research/marine_geollm_scie/tests/test_metrics.py -q
```

출력 경로가 이미 있으면 중단한다. 원본 해시·질의·DRAFT 상태가 다르면 수동 확인이 필요하며 자동 GOLD 변환을 하지 않는다. 원본 파일/모델 run은 로컬 산출물이고 Git에는 재현 코드·검토 기준 사본·해시·이 문서를 보존한다.
