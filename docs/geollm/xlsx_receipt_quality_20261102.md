# XLSX 저장 XML과 셀 본문 검증 분리 — 2026-11-02

## 발견과 범위

`outputs/api_probe_20261102_v1/raw/17.json`의 “S-101이 뭐야” 답변은 S-158-101 XLSX 청크를 근거로 사용했다. `validation_53ed85733d10cddfb9c7a7dd`에는 `683 694 695…`라는 저장 XML 문자열이 있었다. 기존 receipt는 원문 저장 문자열의 일치만 확인한 `VERIFIED_TEXT`였으며, 기존 `MISMATCH` 99개에 포함되지 않았다. 따라서 일반 RAG 필터 누락이 아니라 기존 원문 대조의 검증 범위가 워크시트 셀 값과 구분되지 않은 문제다.

이번 read-only 감사는 v3 FC receipt 중 활성 상태이며 source locator가 XLSX를 명시한 35개를 대상으로 한다. 원천 ZIP·XLSX 바이트 해시, chunk ID·본문 해시·원천 해시를 고정한 뒤 shared strings와 worksheet cell 값을 해독해 비교한다. 숫자 비율로 판정하지 않으며 실제 숫자 셀은 허용한다. 셀 순서로 연결한 실제 값에 고유 본문 span이 없으면 `CELL_TEXT_UNVERIFIED`로 기록한다. 이는 자료 부재나 문장 자체의 거짓을 의미하지 않는다.

## 결과와 불변 원본

- 35개 모두 `NO_DECODED_CELL_VALUE_SPAN`; 기존 `VERIFIED_TEXT`에서 별도 overlay `UNVERIFIED`로 변경하는 후보다.
- 위 문서와 `validation_64eefb66a70188d54df71245` 모두 포함된다. 후자는 읽을 수 있는 속성 문자열이지만 저장된 전체 본문을 해독된 셀 순서에서 확인하지 못했다.
- 기존 활성 `MISMATCH` 99개는 변경하지 않았다. FC302, 다른 PDF, DB, 임베딩, 논문, 홀드아웃은 변경하지 않았다.
- 원본 `data/source_verification/20261102_v3_fc` manifest SHA: `0407bbfb721b595027e6b350db57763c08c1853cac3cc69a378d6490555dc75a`.
- 후보 `outputs/xlsx_receipt_quality_20261102_v1/receipt_manifest.json` SHA: `d745db856cef8f525e72980482b71586e39fb44128152460621b8f25c4690f79`.
- 품질 증거 `quality_evidence.jsonl` SHA: `a5c6f5cfbc946dd457e00c755a5fe56ce91fe71c8ce844aec414326a36b66376`.

## 소비 계약과 게시

공통 `dataset_verification`은 ID·본문·원천 해시와 품질 evidence 해시가 결합된 receipt를 확인한다. 미검증 또는 현재 identity가 달라지면 `SOURCE_EXTRACTION_UNVERIFIED`로 답변 사용에서 제외한다. 일반 RAG, Dataset 발췌, graph excerpt에 같은 제외 조건을 적용한다. 별도 제외 개수와 미검증 사유를 기록하며 검색 0건이나 원문 부재로 바꾸지 않는다.

후보는 아직 운영 포인터에 게시하지 않았다. 부모 검증자 승인 후 다음 새 버전으로 게시하고 backend 재시작 및 실제 RAG 소비를 확인한다. v3를 덮어쓰지 않는다.

```powershell
python -m scripts.publish_dataset_verification --source outputs/xlsx_receipt_quality_20261102_v1 --version 20261102_v4_xlsx_quality
```

## 한계와 후속

새 감사는 receipt locator로 식별된 활성 XLSX 35개에 한정된다. 모든 XLSX·Dataset의 본문이나 의미 검증 완료를 뜻하지 않는다. 기존 MISMATCH99의 셀 기반 재추출 302개 후보는 별도 작업이다. 이번 35개도 검증 가능한 셀 기반 본문으로 재추출·개정한 뒤 새 임베딩과 receipt가 필요하다. 수식은 평가하지 않으며 셀 값 일치는 의미 정확성·위치·좌표 권위를 부여하지 않는다. 모델 호출 없이 원본 바이트와 소비 필터만 검증했고 실제 API 확인은 부모 검증자가 수행한다.
