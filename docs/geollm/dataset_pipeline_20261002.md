# Dataset 전체 원천 대조와 검색 연결 (2026-10-02)

## 범위와 판정

244개 파일의 전체 SHA-256을 새로 계산했다. 기존 `dataset_embedding_coverage`의 파일명 기반 embedded 추정과 `partial:` 해시는 본문 적재 증거로 사용하지 않는다. 동일 해시 복사본은 처리 근거를 공유하되, 기존 본문이 존재한다는 것만으로 모든 페이지/행을 처리했다고 판정하지 않는다.

`outputs/dataset_pipeline/audit.json`과 `audit.md`가 원본별 추출, 본문/벡터, 원천 행/유효 geometry, 출처 연결을 대조하는 실행 산출물이다. 원본·임시 산출물·벡터는 Git에 포함하지 않는다.

## 구현

- `scripts/dataset_pipeline.py`: DB snapshot, PDF/XLS/XLSX/HML/HWPX/DOCX 본문 추출, 원본 해시 검증, 페이지/시트 행/XML locator, 신규 본문 적재, DB 기준 임베딩 재개, 실제 DB에서 출처 그래프 생성, 원본별 대조. HML binary payload는 본문에서 제외한다. PDF 빈 페이지와 판·표 배치 미검증을 보존한다.
- `scripts/dataset_spatial_pipeline.py`: 누락 정적 SHP의 전체 geometry/속성 추출, 정확한 EPSG:5179 파라미터 검증, CP949/UTF-8 판독, 원본 record ID, PostGIS 변환·유효성/국내 범위 검사. 유효하지 않은 geometry를 임의 보정하지 않는다. 실패 member는 전체 성공으로 적재하지 않는다. CSV는 모든 행과 헤더를 보존하되 열 이름만으로 좌표를 추정하지 않는다.
- `serving.dataset_source_records`는 원천 보존·근거 조회용이다. 적재만으로 registry를 executable/authoritative로 승격하지 않는다. 여러 축척의 같은 객체도 서로 다른 원천 record로 보존하며 고유 실세계 객체 수로 합산하지 않는다.
- Dataset 근거 조회와 Qwen 인용 선택 API를 웹의 기존 분석 아래 근거 영역 및 SSE 최종 결과에 연결했다. 기존 응답 필드 `coastal_evidence`는 호환 목적으로 유지한다. 파일 profile을 본문과 구분하고, CSV 원천 기록 검색 범위를 자료명으로 명시한다.
- `dataset_source_lookup`은 ExecutionValidator가 문서·원천 기록 SELECT를 검증한다. 지도 실행 승인을 뜻하지 않는다. KG의 `derivedFromSource`는 provenance 관계이며 의미/좌표 권위를 생성하지 않는다.
- Qwen 원문 인용은 검색된 후보 ID를 선택하게 하고, 실제 원문 일치를 검증한다. 원문 없이 만든 Qwen 설명은 `UNVERIFIED_MODEL_EXPLANATION`으로 따로 저장하며 실행·사실 근거로 사용하지 않는다.

## 실제 관측

- 기존 항로서지 6,111 + 소형선항만 2,329 = 8,440개는 DB에서 모두 embedding 존재 및 1,024차원을 확인했다. 기존 전체 문서 16,853개도 모두 벡터가 있었다. 이는 Dataset 전체 coverage를 뜻하지 않는다.
- 추가 문서 32개, 본문 6,362개 추출·DB 적재. 해양공간 관련 MOF 원문, SOLAS, 해양사고 사례집, 용어사전 등이 포함된다. 추출 실패 0건이며 빈 PDF 페이지는 OCR/빈 페이지 구분 검수가 남는다.
- 누락 정적 SHP 37개 member에서 209,952행 추출. 초기 병원·소방서의 encoding 예외 처리가 잘못돼 실패했고 CP949 재시도로 복구했다. 실제 적재/유효 수는 `spatial_loaded.json`과 DB를 확인한다.
- CSV 17개 고유 원본, 1,128,824행 추출. 가장 큰 자료는 2016년 AIS 선박통계 1,048,574행이다. 현재/실시간 통항량으로 해석하지 않는다.
- 신규 본문 적재 전 `해양공간관리계획` 검색 0건; 적재 후 부산 계획 PDF와 특성평가 PDF에서 5건 확인. `해양사고심판`은 사례집 본문도 검색된다. 없는 자료 질의는 0건. 검색 성공을 정답률/완결성으로 표현하지 않는다.
- 부산항 입구 Qwen 선택 인용 3개가 원문 검증을 통과했다. 추가 원문 없는 설명과 Dataset 검색 비교의 원본은 `runtime-*.json`에 보존한다.
- `해양공간관리계획` Qwen 단독 설명은 효율적 이용·보호·개발이라는 개요 수준이었다. “해양·해상·해상자원으로 분류”는 제공된 근거가 없는 모델 주장이고 220 token 제한으로 문장이 잘렸다. 실제 부산 계획 PDF 18쪽은 해양공간특성평가·해양용도구역제·이용/개발/보전 방향, 126쪽은 어업활동보호구역의 정의를 제공한다. Qwen이 고른 200쪽의 과거 지역협의회는 원문 일치는 맞지만 일반적인 정의 질문에 대한 관련성은 낮다. 인용 일치와 의미 적합도는 별개이며 3개 인용은 같은 문서의 다른 쪽이다.
- 최초 관련 회귀 Python 28 passed, Node 5 passed. 최종 확장 회귀 및 배포 후 결과는 로드맵 최신 인계를 따른다.
- 최종 정적 공간 적재 209,952행 중 206,120행이 유효성·국내 범위 조건을 통과했다. 나머지 3,832행은 보존하되 공간 사용에서 제외한다. CSV 1,128,824행 전체 적재 확인. 출처 그래프 23,418 노드/23,232 관계. 의미 온톨로지 전체 승인이나 실세계 객체 중복 제거를 뜻하지 않는다.
- 확장 Python 31 passed, 문서 조회 실패/공간 timeout 격리 후 관련 6 passed(중복 포함), Node 5 passed. 적재 중 벡터 양식장 조회에서 HTTP 500을 추가 관측했다. 검색 인덱스와 문서 조회 장애 상태를 보완했으며 최종 배포 API 확인을 별도로 기록한다.
- 최종 API 재배포 후 lexical 5/5(0.319~5.262초), 실제 bge-m3/pgvector 5/5(0.560~2.703초), HTTP 오류 0. 벡터 결과는 부산항 5, 해양공간관리계획 2, 양식장 5, 수로 5, 없는 자료 0개이며 공간 기록도 negative 0개다. 수로→수로 유지 회귀가 실제 API에서도 확인됐다. 전체 임베딩이나 의미 정확도 평가를 뜻하지 않는다.

## 남은 작업과 재현

종료 전 worker 진행 파일은 신규 72/6,362개, 대기 6,290개였다. 기존 56개 관측 이후 증가를 확인했다. 최종 API 검증은 통과했지만 브라우저 새로고침 검증은 CDP timeout으로 미완료이며 웹 표시 검증을 별도로 재개한다.

전체 완료가 아니다. 임베딩 worker/공간·CSV 적재 진행은 로그 파일만 믿지 말고 DB와 대조한다. 컨테이너 restart는 worker를 종료한다. batch commit 후 재개 가능하며 공간 적재는 기존 source_id를 건너뛴다. CSV 재실행은 source_id 충돌 무시로 중복 삽입을 막는다.

```powershell
python -m scripts.build_dataset_inventory --output-root outputs/dataset_pipeline
docker exec geollm_backend python -m scripts.dataset_pipeline snapshot
# 호스트 추출: pypdf/xlrd/openpyxl이 있는 Python runtime에서 실행
python -m scripts.dataset_pipeline extract
python -m scripts.dataset_spatial_pipeline extract
python -m scripts.dataset_spatial_pipeline extract --retry
python -m scripts.dataset_spatial_pipeline csv_records
docker exec geollm_backend python -m scripts.dataset_pipeline load
docker exec geollm_backend python -m scripts.dataset_spatial_pipeline load
docker exec geollm_backend python -m scripts.dataset_spatial_pipeline load_csv
docker exec geollm_backend python -m scripts.dataset_pipeline embed
docker exec geollm_backend python -m scripts.dataset_pipeline graph
docker exec geollm_backend python -m scripts.dataset_pipeline snapshot
python -m scripts.dataset_pipeline audit
python -m scripts.check_dataset_pipeline --model
python -m scripts.check_dataset_pipeline --semantic
```

큰 JSONL의 Windows bind-mount 읽기 병목은 `docker cp`로 컨테이너 `/tmp`에 복사하고 `--records-file /tmp/<파일>`로 적재할 수 있다. 복사 완료와 크기를 확인한 뒤 사용한다. DB snapshot을 먼저 읽고 동일 source_id를 재사용한다.

P0: 신규 임베딩 전체 완료와 실제 벡터 검색, 대량 적재 최종 행/유효성 대조, 빈 페이지 OCR 필요 판정, source-level 완전성(기존 표준/법령 포함), archive 내부 문서/서명/중첩 ZIP·TAR의 완전성 검증. 수치조류 `.data`의 encoding/grid/time 사양은 여전히 미확정이며 동봉 XLSX에서도 해당 바이너리 사양을 찾지 못했다. SQL dump를 자동 복원하거나 바이너리를 임의 수치로 해석하지 않았다.

P1: source record→canonical entity/의미 관계 검수, 기존 바다갈라짐 좌표와 원천 기준점 lineage 재검증, 독립 human gold와 Qwen 설명의 의미 적합도 평가. 문서 판·최신성 및 DBF 필드 잘림도 기존 제한이다. Qwen shadow/QLoRA DEFER를 유지한다.
