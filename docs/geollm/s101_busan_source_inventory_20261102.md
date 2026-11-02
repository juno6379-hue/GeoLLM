# 부산 S-101 원천 범위와 Wreck 목록 등록 근거

2026-11-02. 운영 원천 목록 조회를 위한 등록이다. 연구 snapshot·GOLD·홀드아웃과 별도이며 실세계 완전성 또는 전국 coverage 승인이 아니다.

## 확인한 세 축

1. **Source corpus identity**: 현재 `projection.s101_feature_current`의 Wreck 전체 4,339행을 대상으로 ID, dataset/version, feature type, attributes, EWKB를 고정했다. 실행 transaction에서 같은 target 집합의 전체 행을 다시 대조한다. 각 Wreck의 원문 geometry까지 독립 검증했다는 뜻은 아니다.
2. **Source geographic coverage**: 원본 S-101 cell `101KR005G3B33.000`의 DataCoverage를 독립 ISO8211 reader로 복원했다. 원천 DataCoverage 영역 안에 요청 반경 전체가 들어오는지 검사한다. 이 등록은 부산 cell 1개의 선언 범위에 한정하며 다른 cell의 범위를 대신하지 않는다.
3. **Real-world completeness**: UNKNOWN이다. 원천 내 일치 결과 0건이 실세계 침선 부재를 뜻하지 않는다. 실세계 전체성·최근접 요청은 이 목록 계약으로 축소하지 않는다.

원천 존재와 hash 일치만으로 실행 권한을 주지 않는다. 슬롯·요청 제약·geometry·도구·원천과 범위 확인 후 최종 허용은 기존 ExecutionValidator가 결정한다.

범위 밖/경계 걸침도 원천 목록 검증 결과를 버리지 않는다. `source_corpus_status=VERIFIED`를 유지하면서 `geographic_coverage_status=SOURCE_DECLARED_DOMAIN_OUTSIDE/PARTIAL`, 차단 상태 `OUT_OF_COVERAGE/PARTIAL`, `real_world_completeness=UNKNOWN`을 각각 기록한다. 원천이 존재하는데 요청 범위를 벗어난 상황을 자료 부재로 설명하지 않는다.

`2022 CSV에 수록된 모든 해양지명`, `현재 원천 목록에 등록된 모든 Wreck`, `all Wrecks in the registered dataset`은 명시된 유한 원천 목록의 전수 조회다. 이 경우 `모든/all`만으로 실세계 전체성을 요구한다고 판정하지 않는다. 반면 `모든 침선을 빠짐없이`, 모호한 `자료에서 ... 빠짐없이`, 명시적 실세계/실제 해역 전체성 및 최근접은 계속 차단한다. 원천 한정 표현이 있어도 registry/identity/geometry 검증을 대신하거나 `require_complete_coverage=true`를 덮지 않는다.

실제 API의 `2022 CSV에 수록된 독도 주변 5km 이내의 모든 해양지명` 오차단을 재현해, 같은 대상에 붙는 장소·반경 수식이 원천 한정과 전수 수량어 사이에 올 수 있도록 보완했다. 다른 대상의 설명/참고 또는 다른 절에 나온 원천 한정으로 비한정 전수 검색을 허용하지 않는다. 소수 반경의 소수점도 문장 경계로 잘못 자르지 않는다. 관련 정상·부정 회귀 130개 통과 후 실제 API를 별도 재실행한다.

## 원본과 실제 DB의 대조

- 원본 archive: `D:/dev/s100-parser/20260703_808셀.zip`.
- member: `S100_ROOT/S-101/DATASET_FILES/101KR005G3B33/101KR005G3B33.000`.
- source SHA256: `b4bf2ff9c9a6dff8d4595d418289c94d7078f46e378504e6097cb80cb847284b`.
- DB `s101_dataset.dataset_id=292`의 dataset name/source hash와 원본 bytes가 일치했다.
- 원본 FTCS는 feature code 4를 DataCoverage로 선언한다. FRID `(100,20)` → SPAS surface `(130,1179)` → RIAS composite `(125,1571)` → CUCO/PTAS/C2IL/C2IT를 따라 원본 좌표 234개를 복원했다. bbox 추정·polygon repair·임의 버퍼는 사용하지 않았다.
- 원본 CSID/CRSH에 `WGS84`와 authority code `4326`이 명시돼 있다. raw hex `01010157475338341f343332361f021f`. 좌표 크기만 보고 CRS를 추정하지 않았다.
- 원본 DSSI multiplier는 X/Y 각각 10,000,000, offset은 0이다.
- live DataCoverage `feature_instance_id=934678`의 polygon은 86개 좌표이나 중복 좌표 제거/표현 차이를 제외한 위상이 정확히 같다. Shapely `equals=true`, symmetric difference area `0.0`을 확인했다.

## 등록 자산과 동결

`data/source_inventory/s101_busan_20261102/`에 원본 `.000`과 `wreck_inventory.json`을 보존했다. manifest의 `source_proof`가 원본 파일 경로·hash·위 topology locator를 담는다. registry가 manifest bytes를 고정하고 verifier가 원본 bytes hash 및 원본 topology와 live DataCoverage를 다시 확인한다.

- manifest SHA256: `18acd6ab8cf314cc397837aa3e982bf681b9a5cb8ce39cfb4532b67fee2f09bb`.
- target snapshot: `sha256:867fa1676b632b3684415ff03a78fddb2862915d650acc8552f9f98767cb5a36`.
- 계약: `s101_target_inventory_v2`, 대상 `Wreck`, 연산 `feature_search_by_radius`/`feature_dwithin`, 서버 기본 목록 조회 허용.

이전 v1 전체 projection 비교는 약 80만 객체를 매번 전송해야 하므로, v2는 명시된 target 전체 membership을 비교한다. 일부 Wreck 행을 제외해 성능을 높인 것이 아니다. target 추가·행 추가/삭제·속성/geometry 변경은 hash/전체 행 비교에서 차단한다. 검증된 target 이외 객체에는 이 권한을 재사용하지 않는다.

Docker backend에서 READ ONLY / REPEATABLE READ / statement_timeout 5s 조건으로 실제 verifier를 실행해 VERIFIED, 4,339행, 약 0.50초를 확인했다. DB 쓰기는 수행하지 않았다. 본문·지도·근거의 SOURCE_CORPUS/absence=false와 실제 API 정상·부정 결과는 부모의 통합 검증 산출물로 확인한다.

v2 원천 검증과 기존 source/coverage 회귀 127개가 통과했다. 원본 CRS 변경, 다른 feature 지정, target 추가·행 추가/삭제·속성/geometry 변경·원본/live 범위 변경은 차단했다. 독립 감사 테스트와 중복 합산하지 않는다.

새 논문 실행 시 registry YAML뿐 아니라 manifest JSON과 `source_proof.source_asset` 원본 bytes도 동결해야 한다. 연구 부산 subset은 이 운영 inventory와 다르므로 연구 전용 권위 경로 검증 없이 운영 등록을 그대로 연구의 정상 대조 허용 근거로 사용하지 않는다.
