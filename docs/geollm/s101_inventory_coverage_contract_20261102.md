# 정상 S-101 목록 조회를 위한 원천 범위 계약 보완

상태: **일반 계약·검증기 구현 및 합성 회귀 완료, 실제 원천 등록·운영 검증 미완료**. 운영 `GBENC_S101_feature` registry에 신규 계약을 등록하지 않았으므로 현재 정상 CONTROL의 오차단이 해결됐다고 주장하지 않는다. 연구 snapshot/bbox를 운영 승인 coverage로 승격하지 않았다.

## 허용 경로

서버 소유 `corpus_contract.kind=s101_exact_inventory_v1`이 등록된 레이어에만 적용한다. `default_inventory_listing=true`가 명시된 경우 일반적인 제한 반경 목록 요청을 SOURCE_CORPUS로 처리할 수 있다. 실제 해역의 전체성·최근접·모든 객체를 요구하는 질의는 이 경로로 축소하지 않는다.

`services/orchestrator/s101_corpus.py`는 다음을 검사한다.

- 원천 manifest는 `data/source_inventory/` 아래이며 서버 registry의 `source_sha256`과 bytes가 일치해야 한다.
- manifest의 `schema_version`, `dataset_id`, `relation`, 행 식별자 유일성, 정렬된 전체 행의 SHA256 snapshot이 일치해야 한다.
- 실제 조회 transaction에서 전체 projection의 ID·dataset/version·feature type·attributes·EWKB를 manifest와 대조한다. 일부 행을 버려 맞추지 않는다.
- 허용 대상 feature는 원천에 존재하고 유효한 EPSG:4326 geometry를 가져야 한다.
- 원천 선언 범위는 `SOURCE_DECLARED_DATA_COVERAGE`, 명시 `crs=EPSG:4326`, 원문 locator, 유효한 지구 좌표 내 Polygon/MultiPolygon이어야 한다. 요청 반경의 보수적 전체 envelope가 범위 안에 있어야 한다. 객체 extent나 연구 bbox를 대신 쓰지 않는다.

검증 결과는 `CORPUS_VERIFIED`, `query_scope=SOURCE_CORPUS`, `geographic_coverage=UNKNOWN`, `absence_certified=false`다. 기존 승인 범위의 OUT_OF_COVERAGE/PARTIAL 판정을 덮어쓰지 않는다. 알 수 없는 source/변경된 DB/manifest/범위는 계속 차단한다.

## manifest 등록 전에 필요한 실제 증거

현재 자동 생성/등록 절차는 제공하지 않는다. 실제 DB와 원본 Dataset의 DataCoverage 객체를 조사하고 source 파일 전체 hash·객체 locator·polygon·CRS·dataset/version 관계를 별도 대조해야 한다. 단순 DB export에 `source_locator` 문자열을 넣었다고 원문 검증이 완료된 것은 아니다. 이 등록 감사가 완료되기 전에 `default_inventory_listing`을 켜지 않는다.

manifest 행의 필드는 `feature_instance_id`, `dataset_id`, `dataset_version_id`, `feature_type_name`, `attributes`, `geometry_identity`이다. 앞의 ID 필드는 DB `::text`, geometry는 `ST_AsEWKB(geometry)::text`의 값이다. `snapshot_version`은 문자열 ID 정렬 후 canonical JSON SHA256에 `sha256:`를 붙인다. `source_scope`는 원본 DataCoverage를 대조한 선언이며 실제 지리적 완전성 승인이 아니다.

## 최종 응답 제한

반경 결과 builder와 최종 응답 wrapper가 같은 scope 제한을 적용한다. 본문·claims·map metadata·evidence·task 결과에 원천 목록 한정과 부재 미보증을 남긴다. 원천 내 일치 행 0건은 `SOURCE_CORPUS_MATCHED_ROWS` 0으로 표시할 수 있지만 실세계 객체가 없다는 뜻은 아니다. 잘못된 `CORPUS_VERIFIED` receipt만으로 기존 미검증 empty 보호를 우회하지 못하도록 했다.

## 실제 검증 잔여

이번 세션 Docker daemon 기동 실패 때문에 live DB/API 검증을 완료하지 못했다. 다음 접속에서 Docker·원천·DB를 확인하고 검증된 manifest를 준비한 후 정상 부산점/범위 밖/경계 걸침/원천 변경/전체성/최근접/geometry 누락 질의를 실제 API와 executor transaction에서 검사한다. 원본 연구 결과와 홀드아웃은 변경하지 않았다. 새 논문 8방법 실행은 운영 실검증과 새로운 동결이 완료된 뒤 별도로 진행한다.
