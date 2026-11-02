# 행정규칙 CSV 원문 손실 복구

운영 `gbhd_s101`의 `Dataset/해양수산부_행정규칙_20240909.csv` 원천 6청크를 새 positional revision으로 전환했다. CSV 중복 빈 헤더를 `DictReader`가 덮어쓰면서 일부 셀을 누락하던 문제다. 원본 CSV hash는 `36895adb1d01cf67943246f7559c7c07b43d294e2152a799bec6a1ba5706d382`이며 원본 파일은 변경하지 않았다.

## 적용과 보존

- 수정 생성기의 새 6개 ID·전체 본문·메타데이터를 원본 CSV에서 다시 추출하여 후보와 대조했다. 행 범위는 1–16, 17–33, 34–50, 51–66, 67–83, 84–100이며 헤더·행 locator를 보존한다.
- 현재 질의 임베딩 설정 `bge-m3`와 같은 모델 `bge-m3:latest`, digest `7907646426070047a77226ac3e684fbbe8410524f7b4a74d02837e43f2146bab`로 새 6벡터를 생성했다. `truncate=false`, 1,024차원·유한·비영벡터·전체 입력 hash를 검사했다. 과거 벡터의 생성 모델을 확인했다는 뜻이 아니다. 과거 모델은 계속 미확인이다.
- `SERIALIZABLE` transaction에서 사전 export 전체 행 hash를 다시 검사하고 새 6행을 삽입했다. 구 6행은 본문·벡터·기존 메타데이터를 유지하고 `metadata.retrieval_status=SUPERSEDED` 및 새 ID 연결만 추가했다.
- `knowledge.document_chunk_revision_archive`에 BEFORE 6행과 AFTER 12행의 전체 JSON, 벡터, 행별 SHA256을 보존했다. DB mutation은 운영 DB 이름이 `gbhd_s101`일 때만 가능하다. 연구 DB/run/GOLD/holdout은 이 절차에서 사용하지 않았다.
- 커밋 후 읽기전용 재조회에서 구 6행의 모든 비메타데이터 필드·벡터와 기존 메타데이터 키가 동일함을 확인했다. BEFORE archive 전체 hash가 사전 export와 일치하고 AFTER 12행 hash가 적용 receipt와 일치했다.
- 저장 23,221행, 활성 23,215행, superseded 6행. 새 6행의 실제 `vector_dims=1024`를 확인했다. 저장 행 수를 활성 검색 대상 수로 혼동하지 않는다.

운영 검색 SQL의 superseded 제외와 공통 원문 MISMATCH 필터는 별도 검색 계층 변경이다. 원문·공간 연결 delta 감사 및 실제 API 본문 검증은 부모 통합 절차에서 별도로 확인한다. 기존 3개 MISMATCH 감사 기록은 과거 revision 증거로 보존하며 소급 정정하지 않는다.

## 검증 및 산출물

`tests/unit/test_csv_document_revision_repair.py`: 15 passed. 입력·모델·벡터 mismatch, 원본 export 변경, ID 충돌, 동시 변경 CAS, 기존 receipt 덮어쓰기 거부 등을 확인했다.

운영 산출물은 `outputs/csv_document_revision_20261102_v1/`에 있다.

- `before.json`: 전체 원문·벡터 사전 export, rows SHA `ea5cf392f42899e682108d2e58a2b27c13a2aaaf49d8efb0e3e601c1a0f8bae8`.
- `prepared.json`: 원본 재추출 대조 및 신규 6청크.
- `embedded.json`: 신규 임베딩 6receipt, 파일 SHA `069d640a7430d93245dbfd9afab6a6828a56f82598807ce1b5c50401e7d4a024`.
- `applied.json`: commit 후 적용 receipt, 파일 SHA `386e32802c6ef5056d8935a4c5a5a95790469812c953380c45b0e37bb8147f19`.
- `post_commit_verification.json`: 실제 DB 재조회·원본 보존·archive·차원 검증.

Batch는 `csv-positional-v2-68c8097385de0b09`다. 각 단계는 기존 출력 파일 덮어쓰기를 거부한다. `.pending.json`은 commit 확정 receipt가 아니며 최종 파일과 구분한다.

## 롤백

실제 롤백은 수행하지 않았다. 다음 명령은 현재 12행이 적용 후 hash와 일치할 때만 실행한다. 구 6행의 전체 원문·벡터·메타데이터를 archive에서 복원하고 새 6행은 삭제하지 않고 SUPERSEDED로 보존한다. 원상 복원된 과거 손실 청크는 감사 MISMATCH 차단을 계속 받는다.

```powershell
docker exec geollm_backend python -m scripts.repair_csv_document_revision rollback --input outputs/csv_document_revision_20261102_v1/applied.json --sha256 386e32802c6ef5056d8935a4c5a5a95790469812c953380c45b0e37bb8147f19 --output outputs/csv_document_revision_20261102_v1/rollback.json
```

새 revision에 후속 변경이 생기면 자동 롤백하지 않고 CAS 거절 원인을 확인한다. 일반 원천 전체 복구 도구가 아니라 감사된 특정 CSV 6청크의 손실 없는 전환 절차다.
