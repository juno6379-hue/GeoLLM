# 18개 파일럿 질문과 전문가 검수 양식

사용자가 직접 검수자를 선정하고 양식을 작성하기로 했다. 검수자 A/B에게 각각 별도 파일을 배포하여 모델 답안이나 다른 검수자의 판단을 보기 전에 독립적으로 작성한다. 본 파일은 **GOLD 검수를 준비하는 DRAFT 양식**이며 작성만으로 GOLD가 되지 않는다.

## 사용할 파일

- [검수자 A Excel 양식](../../../../../outputs/scie_annotation_20261030/검수자A_18사례_DRAFT.xlsx)
- [검수자 B Excel 양식](../../../../../outputs/scie_annotation_20261030/검수자B_18사례_DRAFT.xlsx)
- [합의 검토 Excel 양식](../../../../../outputs/scie_annotation_20261030/합의검토_18사례_DRAFT.xlsx)
- [원본 18개 질문](../../query_cases_v1.jsonl)
- [A 원본 JSONL](reviewer_A/annotations_DRAFT.jsonl), [B 원본 JSONL](reviewer_B/annotations_DRAFT.jsonl), [합의 원본 JSONL](adjudication_DRAFT.jsonl)

Excel 파일은 로컬 `outputs/scie_annotation_20261030/`에 있으며 Git의 ignored 산출물이다. 다른 컴퓨터에서는 아래 생성기를 실행해야 한다. 원본 질문·JSONL·GOLD 파일은 변경하지 않았다.

## 작성·승인 순서

1. 사용자가 A/B 검수자를 정하여 각 파일을 별도로 전달한다.
2. 노란색 칸에 검수자 식별자, 날짜, 의미·QEC·기대 행동·허용 대안·독립 공간 검증·필수 근거를 작성한다. 모르는 값은 빈칸으로 남기고 불확실성을 기록한다.
3. 독립 제출 원본을 보존하고 파일 SHA256를 계산한다.
4. 불일치를 합의 검토 파일에 기록하고 근거를 확인하거나 제3 검토를 진행한다.
5. 담당자가 완료된 검수·합의·원천을 수동 승인한 뒤 별도 절차로 GOLD 반영 여부를 결정한다. Excel에는 자동 승격·자동 DB 반영·매크로가 없다.

상태는 DRAFT로 유지한다. 기존 18개는 이미 파일럿에 노출되었으므로 독립 holdout으로 재사용하지 않는다. 추가 holdout은 원질의·항만·동등표현 그룹을 분리하여 새로 구성한다.

## 생성·검증 기록

2026-10-30 생성본은 각각 18개 사례, 근거 원문 527개 분할행을 포함한다. 저장된 XLSX XML에서 사례 ID/질의 원문 일치, 정답 빈칸, DRAFT, 수식 없음, 분할 근거를 연결했을 때 원본 source_text와 완전 일치를 확인했다. 작은 범위 렌더로 검수·합의·근거·안내 배치를 확인했다. Excel 데스크톱의 직접 입력 동작은 별도로 검증하지 않았다. DRAFT 목록 검증은 실수 방지용이며 보안 잠금이나 GOLD 승인을 대신하지 않는다.

| 파일 | SHA256 |
|---|---|
| 검수자A_18사례_DRAFT.xlsx | `a4e6bdb5e814dcb61ab02b0eb45ac718a35b73b34351e3fc099d12393354658d` |
| 검수자B_18사례_DRAFT.xlsx | `e1051027e8439d1b368a14fc923f9eab03b75f76449a9b3974e10c6365789394` |
| 합의검토_18사례_DRAFT.xlsx | `d41f374fc2f1fdbe9be20df189a6c4dea10b8cebc549d96123ba3e1d9dc8be84` |

상기 해시는 제공된 기존 파일의 해시다. 재생성 파일은 라이브러리·메타데이터 차이로 바이너리 해시가 달라질 수 있으며 별도 검증한다. 기존 파일을 재생성하거나 덮어쓰지 않았다.

## 재현 가능한 생성 소스

생성기: [export_annotation_workbooks.mjs](../../../runners/export_annotation_workbooks.mjs).

입력은 이 폴더의 기존 `reviewer_A/annotations_DRAFT.jsonl`이다. 빈 양식의 공개 질의와 source_materials만 사용하고 A/B의 답변 필드를 복사하지 않는다. A/B 각각 동일한 빈 시작 양식이며 모델 답변·예상 답변은 포함하지 않는다. 원천 FC/KG를 새로 읽거나 모델을 실행하지 않는다.

```text
node export_annotation_workbooks.mjs --input-dir <검수JSONL폴더> --output-dir <새출력폴더> --render
```

대체 환경변수는 `SCIE_ANNOTATION_INPUT_DIR`, `SCIE_ANNOTATION_OUTPUT_DIR`다. `--render`는 작은 QA 이미지도 생성한다. 생략하면 표 데이터·XLSX만 생성하므로 새로운 배포본은 별도 시각 검증을 수행한다. 기존 동명 workbook이 있으면 덮어쓰지 않고 실패한다. 입력/출력 경로에 사용자 개인 경로나 고정 C 드라이브 의존성은 없다.

### 번들 의존성 연결

- Codex의 `load_workspace_dependencies`로 해당 환경의 번들 Node 실행파일과 `node_modules` 위치를 확인한다. 생성기는 공개 `@oai/artifact-tool` 패키지를 import한다. 저장소 의존성에 새로 설치하거나 번들 디렉터리를 수정하지 않는다.
- 생성기를 실행할 쓰기 가능한 임시 폴더에 번들 `node_modules`를 가리키는 symlink 또는 Windows junction을 만든다. 운영 저장소의 기존 `node_modules`를 교체하지 않는다.
- 입력·출력에는 절대경로를 전달한다. 임시 폴더에서 실행해도 데이터 위치가 바뀌지 않는다.
- Windows에서 출력 드라이브가 junction을 지원하지 않으면 junction을 지원하는 로컬 임시 디렉터리에 생성기 사본과 연결만 두고 실행한다. 이번 생성에서는 D 드라이브 junction이 실패하여 이 방식으로 해결했다. 임시 디렉터리의 개인 경로를 소스에 넣지 않았다.
- Codex가 새 workbook을 작성할 때는 spreadsheets 스킬의 `mark_artifact_operation_started.mjs` 단계를 수행하고 해당 스킬의 검증 절차를 따른다. 번들 설치나 대량 렌더링은 필요하지 않다.

문법/인자 검사는 다음과 같이 생성 없이 할 수 있다.

```text
node --check export_annotation_workbooks.mjs
node export_annotation_workbooks.mjs --help
```

소스 보존 작업은 기존 workbook·JSONL·GOLD·모델 실험 결과를 변경하지 않았다.
