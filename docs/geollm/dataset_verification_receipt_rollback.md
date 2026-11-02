# Dataset 원문 감사 receipt와 롤백

`data/source_verification/current.json`은 버전별 `manifest.json` 상대 경로와 SHA256을 고정한다. manifest는 `receipts.jsonl`의 전체 hash, 감사 snapshot hash·시각, 연결한 공간 감사 hash를 보존한다. 새 버전은 새 폴더로 게시하며 과거 receipt·본문·벡터를 덮어쓰지 않는다.

현재 조회 행의 `metadata.retrieval_status=SUPERSEDED`는 SQL 검색과 공통 답변 필터, Dataset 발췌 단계에서 제외한다. 진단 ID와 상태는 남기며 원문 삭제가 아니다. receipt에 기록된 **감사 당시** `retrieval_status`는 현재 DB 상태와 구분한다. 현재 ACTIVE인 행을 과거 SUPERSEDED 기록만으로 차단하지 않는다. 다만 현재 청크 ID·본문 hash·원천 hash까지 일치하는 원문 MISMATCH 판정은 별도 검사한다.

롤백은 운영 변경으로 취급한다. 이전 버전 폴더의 manifest와 receipt hash를 먼저 재검증하고, 현재 포인터를 별도 인계 산출물에 보존한 뒤 `current.json`을 해당 이전 manifest 경로·hash로 원자적으로 교체한다. 원천 청크 활성 상태의 복원은 별도 DB 복구 절차다. **포인터 변경만으로 DB 행을 ACTIVE로 바꾸거나 임베딩을 복원하지 않는다.** 이전 상태 복원이 필요하면 적용 전 export·기록된 typed archive를 사용하여 승인된 복구 절차로 수행하고, 변경 전후 ID·본문·원천 hash와 활성 상태를 검증한다.

롤백 후에는 기존 정상 답변, 원문 불일치 제외, SUPERSEDED 제외, 교체된 현재 청크의 과거 receipt 불일치, 좌표 형식 경고 및 공간 객체 연결을 실제 API에서 다시 확인한다. 과거 감사는 현재 의미 정확성·좌표 권위나 최신 DB 객체 상태를 보증하지 않는다. 새 검증이 끝나기 전 과거 관측을 현재 운영 검증으로 승격하지 않는다. 연구 동결본·논문 지표·홀드아웃에는 롤백을 소급 적용하지 않는다.
