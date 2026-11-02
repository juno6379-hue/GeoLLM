# 운영 Dataset 원문·위치 문자열 감사 — 2026-11-02

## 범위와 보존

운영 `gbhd_s101.knowledge.document_chunks` 전체를 REPEATABLE READ / READ ONLY로 추출했다. 23,215청크, 임베딩 NULL 0이며 원문 JSONL SHA256은 `6cac588ce700855a179e032ffe38d1d194f3c95d065ce4d56bcca512665d2b66`이다. 논문·holdout·benchmark 입력이나 정답은 읽지 않았다. 모델 호출·재임베딩·학습·원본/운영 DB 갱신은 없다.

Dataset 244파일, 10,867,342,303 bytes를 전부 SHA256 재계산하여 10월31일 manifest의 경로별 해시와 244/244 일치를 확인했다. ZIP/Office archive 83개 직접 member 1,964개의 이름·크기·CRC metadata도 별도 보존했다. 일반 목록만으로 CRC 내용 검사나 모든 중첩 archive 검사를 완료했다고 하지 않는다.

전체 23,215벡터의 차원은 1,024다. 모델명 metadata는 14,746행에 있으며 나머지 8,469행은 없다. 모델 digest·입력 hash·완료시각은 각 5,622행에 있으며 입력 hash는 5,622/5,622 현재 청크 원문과 일치했다. metadata 존재와 입력 hash 일치는 저장 벡터의 생성/내용을 독립 재검증한 것이 아니다. 재임베딩 없이 이 제한을 해소했다고 하지 않는다. 재현은 `scripts.audit_dataset_embedding_provenance`이다.

원시 자료는 `outputs/dataset_location_audit_20261102/source/`에 있다. 전체 원문, source별 checkpoint, 검사 기록은 runtime 산출물로 소스 코드와 구분한다.

## 검사 계약

- 원본 파일 SHA, 청크 원문 UTF-8 SHA, page/row/field/XML locator를 각각 검사한다. PDF는 소스별 1회 읽고 해당 page text를 대조한다. SHP 안내본문은 원본 DBF 필드와 안내 header를 재구성한다. CSV는 기록된 행 범위와 header를 대조한다.
- `VERIFIED_TEXT`는 현재 감사 snapshot의 원본 해시와 원문 대조가 함께 확인된 경우다. 의미 정답률, 최신성, 도표/OCR 완전성, 좌표의 실제 위치 정확성을 뜻하지 않는다.
- 추출기 공백 차이와 U+FFFD 차이만 확인된 경우는 `UNVERIFIED`로 분리한다. 공백을 없애서 숫자를 합칠 수 있으므로 relaxed comparison은 검증 승격 근거로 쓰지 않는다. 남는 대조 불일치는 `MISMATCH`이며 원본과 DB를 자동 수정하지 않는다.
- HWP 2,566청크는 OLE BodyText/Section·압축 record·문자제어 parser로 재대조하여 일치했다. XLS/XLSX 472청크도 원문 sheet/row locator와 일치했다. 1차 감사의 미지원 HWP와 host의 누락된 openpyxl/xlrd 오류는 그대로 남기고 별도 복구 결과를 추가했다. host에 openpyxl 3.1.5 / xlrd 2.0.2 / olefile 0.47을 설치했으며 운영 컨테이너나 dependency lock은 변경하지 않았다.
- 기존 source_file이 `/app/` 경로인 378청크와 staging 경로인 468청크는 전체 SHA와 원본 경로를 연결한 별도 repair candidate를 만든다. 후보 846건을 DB에 적용하지 않는다. full SHA로 연결되지 않는 300건은 미해결로 보존한다. partial SHA 22건을 full SHA 검증으로 승격하지 않는다.
- nested archive 본문 비교는 명시 member locator를 보존한다. FC XML의 source hash 연결은 생성된 설명문 전체의 의미/속성 completeness 검증과 다르다.

## 지명·좌표

모든 청크에 지명 접미사와 좌표 표기 정규식 후보 검사를 수행한다. 한국어 어휘/방향 표기 일부를 인식하는 검사이며 모든 지명의 완전 추출이나 entity linking 완료가 아니다. 문자열·offset·원문 hash를 보존하며 후보를 좌표 권위로 쓰지 않는다.

별도 명시 축/방위 좌표 검사에서 23,215청크, 13,989축, 겹치지 않는 6,672후보 쌍을 확인했다. 6,669쌍은 인식한 구문의 숫자 범위만 통과했으며, 3쌍은 `북위 35도 02분 60초`의 초 값 때문에 무효다. 동일 표기의 중복 청크를 독립 오류 3개라고 주장하지 않는다. 60초를 자동 올림하거나 원문을 수정하지 않는다. 일반 decimal pair는 축/CRS를 추정하지 않는다. 인접 문장이 서로 다른 위치를 말할 가능성도 남는다.

소형선항만의 객체 연결은 공간 감사의 `verified_chunk_object_links_v3.jsonl`과 chunk/content/source hash 및 source ID를 대조해 결합한다. 원문 객체명도 metadata와 확인한다. 항만 대표점이며 입구 좌표가 아니다. 현재 답변 시점 DB 재조회로 표시하지 않는다.

## 산출물과 재현

1. `docker exec geollm_backend python -m scripts.audit_dataset_locations --export` — 새 출력 경로를 사용해야 하며 기존 snapshot 덮기는 거부한다.
2. `.venv/Scripts/python.exe -m scripts.audit_dataset_locations` — 원본 전체 해시, source별 checkpoint 재개, 본문/후보 검사.
3. `.venv/Scripts/python.exe -m scripts.audit_dataset_archive_members`
4. `.venv/Scripts/python.exe -m scripts.audit_dataset_source_resolution`
5. `.venv/Scripts/python.exe -m scripts.audit_dataset_coordinate_literals`
6. `.venv/Scripts/python.exe -m scripts.classify_dataset_text_mismatches` — 최종 checkpoint 전부 생성 후 실행.
7. `.venv/Scripts/python.exe -m scripts.recover_dataset_source_locators` 및 `.venv/Scripts/python.exe -m scripts.audit_dataset_embedding_provenance`
8. `.venv/Scripts/python.exe -m scripts.finalize_dataset_source_audit` — 전체 청크 ID/행수·snapshot SHA·모든 불일치 분류·객체 연결 hash gate 후 compact receipt 생성. 이미 발행된 receipt 덮기는 거부한다.
9. `.venv/Scripts/python.exe -m pytest tests/unit/test_audit_dataset_locations.py -q`

`compact_receipts.jsonl`은 chunk ID, exact content/source hash, 원문 locator, `VERIFIED_TEXT/MISMATCH/UNVERIFIED`, 이유, 명시 좌표 구문 경고, 객체 연결을 담는다. `receipt_manifest.json`의 `complete`는 전수 검사 작업 완료이며 전체 의미·공간 정확성 완료가 아니다. 운영 반영과 실제 답변 검증은 부모 작업의 별도 절차다.

처음 export가 끝나기 전에 시작한 부분 감사는 735행 관측·청크 검사0에서 중단했다. 완료 snapshot manifest SHA/행수 gate를 추가하고 23,215행으로 다시 실행했다. 초기 로그와 중단 설명은 `initial_partial_attempt.json`에 보존했다. source별 checkpoint와 명시 상태를 통해 중단·커밋을 완료로 취급하지 않는다.

최종 분류 계수는 `receipt_manifest.json`과 아래 최종 검증 기록을 따른다.

## 최종 전수 분류와 실제 보완

- 전체 23,215행: `VERIFIED_TEXT` 19,390 / `UNVERIFIED` 3,822 / `MISMATCH` 3. 본문 정확도나 전체 서비스 정확도 비율이 아니다. 단위검사는 원문 locator·숫자변화·좌표축/분초범위·CSV 중복 header와 chunk 경계를 포함하여 16 passed다.
- 지명·좌표 정규식 후보는 64,347개다. 중복 청크와 같은 문장을 포함하며 의미 검증된 객체 수가 아니다.
- HWP/worksheet 추가 원문 검증 3,038행과 archive member 378행은 확인했다. nested member 경로의 `\\`/`/` 차이는 고유 원본 member 이름으로 연결하며 source hash를 함께 확인했다. FC XML 468행은 원본 hash 연결만으로 생성 설명의 모든 속성 정확성을 확정하지 않는다.
- 원문 전체 재대조 1차 분류와 추가 복구를 구분한다. 초기 receipt 19,048/4,161/6은 `receipt_versions/v1/`에 보존하고 최종 공개용은 19,390/3,822/3으로 확정했다.
- 최종 receipt SHA256: `ecb2cfdbcb297472069f824e2d20ce079bfd296ee5e0d0eae3dad011990b6bd7`, 12,920,733 bytes. 공간 연결 v3 SHA256: `7f4a12af71785b5200993b69e46309495417b43c9a83c1a38940092e6d3ed8e6`. 객체 연결 2,329행과 초 값 무효 경고 3청크를 exact content/source hash로 결합했다.

실제 CSV 결함은 `해양수산부_행정규칙_20240909.csv`의 동일한 빈 header 두 개(0-based 열25·26)를 `csv.DictReader`가 dictionary key로 합치면서 앞 열 값을 잃는 문제다. source row16의 `N`, row40·82의 `2015-01-18`이 빠졌다. 의미가 정해지지 않은 빈 header 열의 원문 값이며 임의로 법령 필드 의미를 부여하지 않는다. 원래 추출기로 문제 3청크의 저장 본문을 정확히 재현했다. row 범위가 1–17/35–51/69–85이고 char offset이 없는 행 단위 추출이므로 정상적인 문자 chunk 절단이 아니다.

`scripts/build_document_rag_chunks.py`를 positional CSV reader로 수정하여 중복 header·빈 header·추가 열·quoted multiline을 보존한다. 일반 CSV의 본문/ID는 유지한다. 실제 정상 법령 CSV 2파일의 3,916청크는 변경 전후 본문/ID가 모두 같다. 문제가 있는 파일은 `csv_positional_v2`와 content SHA를 포함하는 새로운 청크 ID로 6개 revision 후보를 만들었다. 기존 ID와 겹침0, 범위1–16/17–33/34–50/51–66/67–83/84–100이다. `csv_reextracted_revision_candidates.json`과 원문 전체 열 기반 `csv_text_repair_candidates.jsonl`은 미적용 후보다.

이 작업에서 기존 DB 청크·벡터를 덮거나 새 임베딩을 만들지 않았다. 문제 3행의 embedding 생성 metadata는 비어 있어 과거 모델/digest를 확정할 수 없다. 새로운 임베딩·원본 보존 archive·활성 revision 전환과 rollback은 별도 재색인 절차가 필요하다. 우선 현재 원문 불일치 3행을 실제 답변 근거에서 제외하는 운영 보완은 부모 작업에서 검증한다. 원본 text를 바꾼 뒤 기존 벡터를 재사용하지 않는다.

## 사용자 승인 후 CSV revision 적용의 독립 재검증

위 문단은 baseline 감사 종료 시점이다. 이후 부모가 별도 운영 에이전트의 새6 임베딩 및 트랜잭션 적용을 승인했다. 원문 감사 에이전트는 모델/DB 쓰기를 수행하지 않고 적용 전 원본 및 적용 후 현재 DB를 독립 검증했다.

- 새6 본문은 원본 cp949 CSV를 별도 `csv.reader`로 다시 읽어 header 27열과 100행 전부 exact 비교했다. 행 범위 합집합이 1..100과 일치하고 중복·누락0, 원본 full SHA·명시 header/row locator·새 ID를 확인했다. 현재 DB 새6의 text/source hash/source ID/locator metadata도 후보와 일치했다.
- 새6의 현재 벡터는 1,024차원 finite이고 입력 SHA가 새본문과 같으며 생성 receipt의 model digest는 `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`다. 과거 벡터의 모델 이력이 확인됐다는 뜻이 아니다. 기존6의 본문·source hash·저장 벡터 문자열을 적용 전 자료와 대조하여 그대로임을 확인했다.
- 전체 현재 DB를 READ ONLY로 재수집했다. 저장 23,221 / 활성 23,215 / SUPERSEDED 보존 6. 기존 비대상 23,209행의 content·metadata·출처·embedding 존재/차원은 baseline과 전부 동일하고 대상12행은 직전 독립 delta snapshot과 같았다. 비대상 저장 vector 값 자체는 다시 전량 추출하지 않았다.
- 새 receipt는 `source/revision_v2/compact_receipts.jsonl`. stored 기준 VERIFIED_TEXT 19,396 / UNVERIFIED 3,822 / MISMATCH 3, active 기준 VERIFIED_TEXT 19,396 / UNVERIFIED 3,819 / MISMATCH 0이다. 기존 불일치3의 원문/판정은 SUPERSEDED 이력으로 남는다. 이를 모든 의미·위치 오류가 없어졌다는 뜻으로 쓰지 않는다.
- 최종 receipt SHA256 `e3f25d35ff28170987064de7df30475c30f88d214b90d4890a7b9e923bb23dac`, manifest SHA256 `da9f3cc91aa6a1545cf5698c8d9d07b781ad07e86c2c6d5c6a35684826a876e7`. 전체 gzip JSONL snapshot SHA256 `af2173717804be8f6ee9fcc40491df1951fdf33e3f180ddd1886c1c2e88e6147`, 대상12 delta SHA256 `84f1e0f436ef3d914e7cffc2c1553e82b92a507d4c0367d58a8b910eae73cd90`. baseline snapshot과 receipt는 덮지 않았다.

재현: `scripts.audit_dataset_csv_revision_delta`로 원본 후보검사, backend에서 같은 모듈 `--export`로 read-only delta, host에서 `--verify-delta`로 새 receipt 생성. `scripts.verify_dataset_revision_full_snapshot --export`는 backend 전체 gzip snapshot, host의 같은 모듈 기본 실행은 비대상 전체 대조다. 이미 생성한 snapshot/receipt는 덮기 거부하므로 새 검증은 명시적인 새 버전 경로를 사용해야 한다. 최종 근거는 `revision_v2/verification.json`, `full_corpus_verification.json`, `receipt_manifest.json`이다. 실제 답변·검색·UI 검증 및 배포는 부모의 별도 운영 검증 기록을 따른다.
