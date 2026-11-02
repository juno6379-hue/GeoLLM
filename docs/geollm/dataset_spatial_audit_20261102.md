# Dataset 공간 원천 전수 대조 — 2026-11-02

운영 DB와 Dataset 원본만 읽었다. 연구·benchmark·holdout 파일/DB 및 모델은 읽거나 실행하지 않았고, 운영 데이터·좌표·임베딩·coverage 승인을 변경하지 않았다. 전체 의미 정확도 검증 완료가 아니다.

## 실제 확인

- `serving.dataset_source_records` 1,338,776행. 정적 SHP 209,952행과 CSV 1,128,824행을 별도 전수 대조했다. provenance hash/locator 누락·불일치0, 원천별 row_index 중복0.
- 정적 37 member를 원본 ZIP에서 다시 읽고 원본 SHA256·명시 PRJ·stable ID·행번호를 대조한 뒤 독립 pyproj로 CRS→4326, 2D 변환했다. 209,952행 모두 비교, 140,213행 WKB byte 동일(원본 null1 포함), 69,739행은 byte 차이지만 동일 geometry 구조와 좌표 허용오차 내 일치. 최대 차이 **3.966249551012879e-11도**, 기준1e-8도 초과0. 기존 PostGIS PROJ7.2.1과 독립 pyproj3.7.2/PROJ9.5.1의 부동소수 표현 차이와 양립하며 원인을 개별 연산까지 단정하지 않는다. 실패를 삭제한 것이 아니라 첫 byte 비교 산출물을 보존하고 v2에 byte/tolerance 분모를 분리했다. 원본 geometry 수리·MakeValid·dedup 없음.
- 정적 geometry_present209,951, invalid173, 전세계경위범위밖172, 한국주변guard밖3,830. 이 숫자는 중복된다. 기존 geometry_valid=true206,120 중 규칙위반0. 나머지 정적3,832는 이미 제외 상태다. CSV의 no-geometry1,128,824를 불량기하로 세지 않는다.
- CSV17원천 전체를 원본 SHA256 확인 후 스트리밍 재파싱했다. 헤더/값배열/원본행번호/row_index/stable ID/geom NULL 모두 1,128,824행 일치, 누락·초과·불일치0. JSONB 배열 텍스트 MD5는 행 대조 보조이며 원본 파일 무결성은 SHA256이다. 좌표를 추정하지 않았고 시계열 의미·집계 완결성은 별도다.
- 소형항만439/해양지명1,146/섬지명1,140/항로표지314, 총3,039개는 원본 속성·ID·SHA와 PostGIS 원본 재변환 기하가 모두 일치했다. 전부 valid/SRID4326. 섬지명56개는 한국주변guard 밖이지만 남서제도·남중국해 등 원문 자체의 국외좌표와 일치한다. 잘못된 좌표로 간주하거나 삭제하지 않았다.
- Dataset 단독 SHP 및 직접 ZIP 내부 SHP256개는 대응 PRJ가 모두 존재하고 strict 판별로 인식된다. 이번 검사에서 unknown CRS→4326 fallback 실제 발생 증거는 없다. 중첩 ZIP 내부 재귀 전체까지 완료했다고 주장하지 않는다. 기존 importer의 미상 CRS fallback 코드 자체는 별도 잠재적 제한이다.

## 문서와 공간 객체 연결

소형항만 문서2,329개 모두 source_id/hash/원본 DBF field가 일치한다. 2,325개는 원문필드 literal 포함, 4개는 기존 추출과 같은 앞뒤 공백/개행 strip 후 포함이다. 원본필드 hash와 content hash를 모두 보존했다. 439개 원문 항만기준점과 직접 연결되는 `describesHarbourRecord` 조회 관계이며 항만 입구·canonical 동일성·현행 위치 권위가 아니다. 검증 관계는 `verified_chunk_object_links_v3.jsonl`에 object ID/name/relation, source field/row, normalization, content/sourcefield hash로 저장했다. 이름도 원문 NAME.strip과 DB name 일치를 검사했다.

Dataset `derivedFromSource`만으로 의미 관계 완료를 주장하지 않는다. 항로서지 등의 좌표 언급은 기준 장소·대상 객체 동일성이 검증되기 전까지 후보다. 후속으로 정적37개member의 원본DBF를 기록된 인코딩으로 strict 재파싱하여 209,952행 속성사전·ID·locator까지 전수 대조했다. 원본SHA 일치 및 속성값누락·불일치0. 원문필드보존은 의미·최신성·권위완료를뜻하지않는다.

부모가 별도로 `scripts/audit_coordinate_object_candidates.py`로 명시좌표범위valid6,669쌍과원문Point/MultiPoint3,039개를 100m 하버사인 근접대조했다. `outputs/dataset_location_audit_20261102/coordinate_object_candidates_v2`의30쌍(다중3)은 검수후보이며 객체동일성verified0/authorityfalse다. 소형항만2,329개검증관계와별도이며 원문대상·CRS·동일성검수전 runtime승격금지. 후보없음을실세계부재로해석하지않는다.

## 검색과 실패 이력

- 현재 `coastal_knowledge.py`의 source_records 경로는 geometry를 반환하지 않는 메타데이터 검색이며 `coordinate_authority=false`를 유지한다. services/shared/data Python 검색에서 조회와 실행승인 바인딩 두 사용처를 확인했다. 공간사용 가능한 상태라고 의미권위를 승격하지 않았다.
- 기존 filename/property GIN trigram 인덱스는 존재한다. EXPLAIN은 양식장 SeqScan, 수로 ParallelSeqScan을 택했다. 현재 실제3초 제한 재현은 양식장0.706초/수로0.232초 성공. 파일명우선 대체는 수로에서57014/3초 timeout이므로 개선책으로 채택하지 않았다. 캐시·부하·LIMIT 무정렬 영향이 있고 이 관측을 지속 SLO나 과거 장애 해소로 해석하지 않는다.
- 첫 독립검사에서 한 ZIP 멤버의 cp437/cp949 런타임명 차이로 중단했다. 원본·로그 보존 후 원본 bytes의 가역 인코딩 변환으로 locator를 해소했다. basename 추측을 사용하지 않는다. v1 byte mismatch와 v2 수치·구조검사를 분리 보존한다.
- 읽기 전용 검사지만 모든 단계를 하나의 전역 freeze/snapshot으로 실행한 것은 아니다. 각 원천 SHA와 관측 시점·receipt를 확인한 결과다.

## 재현

호스트 감사 전용 의존성: 기존 shapely2.1.2와 pyshp, 추가 `pyproj==3.7.2` (운영 runtime/lock 변경 없음). 출력은 `outputs/dataset_location_audit_20261102/spatial`이며 기존 산출물 보존 후 새 출력 버전을 사용한다. 모든 public 감사스크립트는 `--output`으로 새 출력root를 지정한다. 최종receipt/원시export 대상이 이미 존재하면 실행 전 FileExistsError로 거부하며 묵시적 덮어쓰기·resume는 없다. 실패재현은 새root를 사용한다. 아래의 `<새run>`을 한 새이름으로 정하고 호스트와컨테이너의같은bind-mount경로를 사용한다.

1. backend: `python -m scripts.audit_dataset_spatial_links --output /app/outputs/<새run>/spatial`
2. host: `.venv/Scripts/python.exe -m scripts.reconcile_dataset_place_sources --output outputs/<새run>/spatial`
3. backend: `python -m scripts.verify_dataset_place_geometry --output /app/outputs/<새run>/spatial`
4. backend: `python -m scripts.export_dataset_static_audit --output /app/outputs/<새run>/spatial`; host: `.venv/Scripts/python.exe -m scripts.audit_dataset_static_geometry --output outputs/<새run>/spatial`
5. backend: `python -m scripts.export_dataset_csv_audit --output /app/outputs/<새run>/spatial`; host: `.venv/Scripts/python.exe -m scripts.audit_dataset_csv_rows --output outputs/<새run>/spatial`
6. backend: `python -m scripts.export_dataset_static_properties --output /app/outputs/<새run>/spatial`; host: `.venv/Scripts/python.exe -m scripts.audit_dataset_static_attributes --output outputs/<새run>/spatial`
7. host: `.venv/Scripts/python.exe -m scripts.audit_dataset_crs_inventory --output outputs/<새run>/spatial`; backend: `python -m scripts.export_verified_harbour_links --output /app/outputs/<새run>/spatial`, `python -m scripts.probe_dataset_record_search --output /app/outputs/<새run>/spatial`
8. `.venv/Scripts/python.exe -m pytest tests/unit/test_dataset_spatial_audit.py -q` → 5 passed. 인코딩 full-path 가역성/추정 거부, 축반전·큰좌표차이 거부, 미세반올림·geometry구조, CSV배열 값/순서 보존, 기존증거덮기거부를 검사했다. 별도 CLI 신규root에서 CRS256확인→같은root재실행은의도된FileExistsError를확인했다.

`manifest_v2.json`은 추가속성검사/CLI보완소스까지 포함하고 기존manifest는보존했다. 주요 최종receipt 및2,329연결 파일 SHA를 기록한다. 운영 runtime 소스 수정·DB mutation·새 임베딩·API/모델 호출·커밋 없음. 다음은 검증된 조회 관계를 source/contenthash와 함께 답변에 연결하고, 미검증 위치언급·법적범위·최신판·canonical 동일성을 별도 검수하는 것이다.
