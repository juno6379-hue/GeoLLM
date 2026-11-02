# 144답변 독립 인간 의미 채점 안내

AAA·BBB의 기존 GOLD18 승인과 이번 144답변 채점은 구분한다. 현재 실제 답변별 인간 판단은 수령하지 않았다.
AAA_labels.jsonl / BBB_labels.jsonl을 각각 독립 작성한다. 상대 판단·coordinator_only 폴더·기계 채점 결과를 보지 않는다.
blinded_answers.jsonl은 방법명을 숨긴 원문 최종 답안과 승인 GOLD를 제공한다. 답변 문체/구조에서 방법이 추정될 수 있어 완전 블라인딩은 아니다.
고정 순서는 재현 가능하며 AAA와 BBB의 양식 순서는 반대다. 독립성은 접근통제가 아닌 절차적 분리다.
각 답변마다 dimensions 네 항목(true/false), rationale, answer_evidence_quote, gold_evidence_locator, human_label_source(실제 작성 기록), reviewed_at(YYYY-MM-DD), human_completed=true, independent_review_confirmed=true를 입력한다.
meaning_correct: 요청 의미와 사실 관계가 맞는가. required_tasks_complete: 필수 하위작업을 모두 충족하는가. evidence_supported: 주장이 제시한 원본 근거와 맞는가. no_unsupported_claims: 근거 없는 좌표/객체/실행/권위 주장이 없는가.
주 지표는 네 항목 모두 true인 답변의 비율이다. 정답 행동이 추가입력/자료범위 차단이면 그 행동과 설명의 적합성을 채점한다. 객체 검색 미실행 자체를 항상 의미오류로 처리하지 않는다.
원문 답안이 없으면 absence note를 인용하고 실패 사유를 기록한다. 사례별 판단 없이 전체 동일 값을 채우지 않는다.
독립 기록을 확정한 뒤 consensus_labels.jsonl에 합의 판단을 작성한다. reviewer_A/B_label_sha256은 각 실제 label 객체의 canonical JSON SHA256이다. disagreements와 agreement 모두 원래 A/B 기록으로 계산한다.
실행: .venv/Scripts/python.exe -m tools.scie_results_ui.prepare_semantic_review --import-labels <입력폴더> --output <새결과폴더>
입력폴더는 AAA_labels.jsonl, BBB_labels.jsonl, consensus_labels.jsonl을 포함한다. 기존 기록/결과는 덮지 않는다.
검증기는 실제 사람의 신원을 증명하지 않는다. 사람 작성 확인과 답변별 근거 기록을 요구하며 AI 판단을 HUMAN으로 바꾸어 입력해서는 안 된다.

## 확인한 기존 자료
Downloads의 A/B 18문항 파일은 AI 보조 GOLD 초안이다. 기존 승인 기록은 GOLD18 전체 승인으로, 144답변 label이 아니다. 따라서 144답변 인간 의미 정확도는 현재 null이다.

## 실제 작성 순서
원본 패키지를 작업 폴더로 복사한 뒤 AAA/BBB Markdown의 human-label JSON 블록을 편집한다. 원본 폴더는 변경하지 않는다.
Copy-Item -LiteralPath research/marine_geollm_scie/review/20261102_answer_semantic_review_v1 -Destination outputs/human_answer_submission_20261102 -Recurse
AAA/BBB 완료 후: .venv/Scripts/python.exe -m tools.scie_results_ui.prepare_semantic_review --prepare-consensus outputs/human_answer_submission_20261102 --markdown --output outputs/human_answer_consensus_20261102
새 합의 폴더의 consensus_labels.jsonl 실제 판단을 작성한 뒤: .venv/Scripts/python.exe -m tools.scie_results_ui.prepare_semantic_review --import-labels outputs/human_answer_consensus_20261102 --output outputs/human_answer_scored_20261102
원문 전체 hash와 정규화 표시답안 hash를 분리한다. 최종 답안 정규화에서 geometry 좌표 배열/대형 WKT·EWKB는 표시만 제외하고 객체 ID·거리·원천 hash·답변 본문을 유지한다. 정확한 원본은 coordinator 경로/hash로 보존한다. 문체·내부 식별자에 따른 부분 방법라벨 가림이다.
UI 반영은 --import-labels 시 --output을 research/marine_geollm_scie/review 아래의 새 폴더로 지정하고 --publish-ui를 명시한다. 기본은 비공개이며 기존 준비 패키지를 수정하지 않는다.
