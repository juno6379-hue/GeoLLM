# 항로서지·소형선항만 안내 원천 연결 — 2026-10-01

## 범위와 실제 상태

Dataset 전체 중 사용자 우선순위인 `항로서지`와 `소형선항만 안내정보`를 처리했다. 전체 Dataset 완료로 확대하지 않는다.

- 원본 PDF 30개, HWP 28개를 SHA-256으로 식별했다. PDF 1,644쪽 중 텍스트 없는 페이지 61쪽은 inventory에 기록했다. 표지·공백·그림 여부를 전부 시각 검수한 것은 아니며 OCR은 미수행이다.
- HWP5 BodyText를 압축 해제하고 문단 텍스트를 추출했다. HWP는 section/문자 offset을 사용하며 PDF 페이지로 가장하지 않는다. PDF/HWP의 동일 발췌는 중복 제거하되 대체 원천 locator를 보존한다. 서로 다른 판의 의미 동등성을 확정하지 않는다.
- 원문 청크 8,440개: 항로지 6,111개, 소형선항만 안내 2,329개. 운영 `knowledge.document_chunks`에 적재했다. `embedding IS NULL`은 미완료다. 전체 임베딩 완료를 선언하지 않는다.
- 소형선항만 439건을 `serving.small_harbour_guide`에 적재했다. 원천 PRJ를 확인해 EPSG:5179 → 4326으로 변환했으며 geometry validity와 경위도 범위 439/439를 확인했다. 대표점은 입구 geometry가 아니다.
- DBF 394개 기록에 잘린 UTF-8 필드가 있다. 속성별 손상을 기록했고 254-byte 필드 잘림 경고를 표시한다. 원천 연도는 행마다 다르며 다대포항 2017, 부산항 2020처럼 개별 표시한다. 부산항 명칭의 창원 주소/신항 부근 대표점을 부산북항 입구로 치환하지 않는다.

## 지식 연결 및 서비스

- `DocumentChunk → mentionsPlaceName → PlaceNameMention`과 `DocumentChunk → describesHarbourRecord → HarbourGuideRecord`를 생성했다. 후자는 공간 테이블 source_id와 연결된다. 출처/hash/페이지·필드 locator를 보존한다.
- 이름 언급은 동명이칭의 동일성, 항만 입구 좌표, 방파제 방향 등 의미 관계의 승인과 다르다. 새 타입·관계는 KG ontology contract에 선언했고 retrieval-only로 사용한다. 전체 해양 온톨로지의 완성은 아니다.
- `GET /api/v1/coastal-evidence?query=...`: 별도 ExecutionValidator 문서 조회 계약으로 원문·KG 링크·항만 기록·실시간 임베딩 건수를 제공한다. 지도 승인과 분리한다. 기본은 빠른 원문 검색이며 `semantic=true`는 실제 bge-m3와 pgvector를 사용하고 완료 벡터만 조회한다.
- 웹 질의에서 근거 검색을 별도로 호출해 분석 아래에 출처·발췌·완료 건수를 표시한다. 위치 확인 대기 응답에도 관련 원문 발췌를 표시한다. 늦은 응답은 generation으로 차단한다. 원문 검색을 공간 실행 완료로 바꾸지 않는다.
- `GET /api/v1/coastal-explanation?query=...`: Qwen에 검색 원문을 제공하고 관련 발췌 ID만 선택하게 한다. 서버가 원문으로 복원한 인용만 표시한다. 의도 분류 Qwen 응답과 구분하며 사실/좌표/실행 권위로 사용하지 않는다.

## 발견한 실패와 검증

- 첫 자유 인용 Qwen은 두도·감래포 설명을 부산항 입구로 바꿨다. 원문 일치 검사가 이를 거부했다. 원본은 `outputs/coastal_knowledge/comparisons/`에 보존했다. 후속 발췌 ID 선택으로 자유 재작성 자체를 제거했다.
- 후속 실제 Qwen(qwen2.5:1.5b) 발췌 ID 선택은 3개 인용을 반환했고 모두 원문 일치 검사 통과. PDF와 HWP의 동일 내용이 포함되므로 독립 근거 3개로 해석하지 않는다. 웹 버튼 실행과 표시도 확인했다.
- 실제 bge-m3/pgvector 검색은 `source_scoped_lexical_and_vector`로 실행돼 부산항 관련 벡터 결과 5개를 반환했다. 당시 90/8,440 벡터만 적재된 부분 검증이며 전체 vector coverage/정확도를 뜻하지 않는다.
- 전체 router import를 포함한 추가 단위 검사는 초기화가 장시간 지연돼 중단했다. 그 검사는 제거하고 SSE 보존을 실제 API에서 검증한다. 앞의 Python 26/Node 5 통과 범위와 구분한다.
- 초기 DBF UTF-8 끝부분 잘림, HWP surrogate, PDF NUL 문제를 발견해 대체문자/제어문자 처리 및 원천 경고로 보완했다. 손상을 복원했다고 주장하지 않는다.
- Python 관련 회귀 26 passed, Node 5 passed. Node에는 이전 질의의 늦은 근거 혼입 방지와 지도 미승인 유지 검사가 포함된다.
- 실제 원문 API: 부산항·다대포항·울릉도 각각 발췌 5개, 없는 지명 0개. 이는 의미 정확도 100%가 아니다. `항만` 일반어가 관련 없는 자료를 반환하는 문제를 보완했다. 원시 결과는 `outputs/coastal_knowledge/runtime_checks/`.
- 최종 SSE 재검증: 부산항 입구로 이동은 NEEDS_CLARIFICATION을 유지하면서 별도 문서 조회 승인과 발췌 5개를 보존했다. 이후 실제 원문 API 4건도 다시 통과했다(0.78~0.94초). 웹에는 원문 발췌와 Qwen 원문 인용 완료가 표시됐으며 `web-source-comparison.png`에 보존했다.
- 남해안동부 PDF 6쪽(인쇄 104쪽)을 렌더링해 오륙도/영도–부산항 입구 동·서쪽 서술을 시각 확인했다. 전체 표·해도 검수와 최신성 검증은 남는다.

## 재현 및 다음 확인

1. 호스트 Python에서 pypdf, pyshp를 준비하고 `python -m scripts.build_coastal_knowledge`로 PDF·SHP를 추출한다. `olefile==0.47`로 `python -m scripts.build_coastal_knowledge --hwp`를 실행한다. 생성물은 `outputs/coastal_knowledge/`이다.
2. `docker exec geollm_backend python -m scripts.build_coastal_knowledge --load`로 실제 본문·공간자료를 적재한다.
3. `docker exec geollm_backend python -u -m scripts.build_coastal_knowledge --embed`로 임베딩을 재개한다. bge-m3, 1024차원, CPU 4스레드, 2개 배치. DB advisory lock으로 중복 worker를 막는다. 매 배치 파일+DB 저장. 컨테이너 재시작 시 다시 실행해야 한다.
4. `embedding_progress.json` 숫자만 믿지 말고 worker 프로세스·로그와 운영 DB `COUNT(embedding)`을 대조한다. 중단 뒤 progress가 RUNNING으로 남을 수 있다. 원천 청크 8,440개 전체의 벡터 적재와 차원·NULL 검증 전 완료 선언 금지.
5. `python -m scripts.check_coastal_knowledge` 및 `--model`, `--semantic`, `--stream`으로 각각 원문/모델/벡터/SSE 경로를 검증한다. 임베딩 진행 중에는 semantic 미수록 지명 결과가 없을 수 있다.
6. P0: 전체 임베딩 완료 → 전체 벡터 대표 질의/부정 사례 → 빈 PDF 페이지·DBF 손상 원천 보완 → 판·최신성/항만 식별 검수 → 원문 근거가 있는 실제 입구·항로·방파제 관계 검수. Qwen shadow와 ExecutionValidator 단일 권한을 유지한다.

런타임 JSONL·벡터·PDF 원본·로그·화면은 Git 소스 커밋에서 제외한다.
