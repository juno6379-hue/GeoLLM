# 운영 공간 데이터 범위 검사와 SQL 단계 관측

이번 변경은 운영 오류 방지이며 논문 정답 객체나 질문 ID를 사용하지 않는다. 연구용 GOLD·snapshot·기존 결과를 변경하지 않는다.

## 범위 계약

`spatial_coverage.assess_coverage`는 서버 `spatial_layer_registry`의 `coverage_contract.path/sha256`로 지정된 파일만 읽는다. 해당 파일이 APPROVED이고 source locator·dataset/relation·binding snapshot version·target Feature·EPSG:4326가 모두 일치해야 범위 판단에 사용한다. 요청 QEC의 `coverage_status=VERIFIED` 같은 플래그는 무시한다. 적재 객체들의 bbox를 실제 자료 수집 범위로 만들지 않는다.

공간 계약을 만족하는 선언이 있으면 요청 영역이 coverage에 포함되는지 확인한다. 반경은 보수적인 경위도 외접 사각형으로 검사하며 반경 50km 이하·극지/날짜변경선 외부로 제한한다. 이 외접영역으로 충분성을 확정하지 못하면 PARTIAL/UNKNOWN으로 처리한다. 이 검사는 공간 정답 거리 계산을 대체하지 않는다. 최근접은 기준점 포함만으로 충분하지 않으므로 별도 `nearest_domain_complete=true` 계약 없이는 UNKNOWN이다.

현재 운영 layer registry에는 승인·snapshot 연결된 coverage 계약이 **없다**. 따라서 이번 작업으로 전국/부산권의 coverage를 검증했다고 말할 수 없다. 운영 source scope 선언 확보·검수·실제 snapshot binding 연결이 남아 있다. 파일 hash는 내용 일치 증거이지 권위 출처 진위 자동 인증이 아니다.

## 실행 정책

- OUT_OF_COVERAGE/PARTIAL: ExecutionValidator에서 `BLOCKED_DATA: DATA_OUT_OF_SCOPE`.
- UNKNOWN이며 최근접 또는 `slots.filters.require_complete_coverage=true`: `BLOCKED_DATA: DATA_COVERAGE_UNVERIFIED`.
- UNKNOWN인 일반 반경/영역 관측: 경고를 보존하고 원천 행 조회만 허용한다. 0행은 기존 PARTIAL/NO_EVIDENCE, 확정 count=null/observed_count=0을 유지한다.
- coverage receipt를 승인 input_hash에 포함해 승인 뒤 변경 시 권한이 무효화된다. 의미 추론이나 누락 geometry/source 선택을 하지 않는다.
- 범위 밖 결과의 비실행 상태는 실제 executor 관측과 함께 확인해야 한다. 단위 fixture를 실DB 비실행 증거로 취급하지 않는다.

## DB 시간초과 조사

`s101_radius_execution`은 `execution_validation`, `feature_code_verification`, `spatial_select`, `snapshot_receipt` 단계별 완료/실패·elapsed_ms·sqlstate를 QEC provenance에 기록한다. SQL문/인수/접속정보/DB 오류 원문은 기록하지 않는다. 기존 73.735초 DB_TIMEOUT의 단계는 원본에 없어 소급 확정하지 않는다. 신규 실제 SSE 재현 `outputs/reliability_coverage_gate_runtime_20261101_v1/empty.json`에서는 `feature_code_verification`이 30,049ms 후 QueryCanceled/57014로 실패했음을 확인했다.

이 쿼리는 위치와 무관한 전체 materialized view의 name/code DISTINCT 검사이며 기존 code-only 인덱스는 약6.4만 행의 heap 조회와 정렬을 유발했다. 검사 의미를 유지하며 운영 DB `gbhd_s101`에 `(feature_type_name, feature_type_code)` covering index를 `CONCURRENTLY` 추가했다. migration은 `scripts/sql/20261101_s101_feature_pair_index.sql`, 검사기는 `scripts/check_s101_feature_pair_index.py`다. 원천 행·연구DB·timeout은 변경하지 않았다.

실제 전후 결과는56쌍이며 SHA256 `b00aabfe749e33a33dfb1308a9233edef6d411f914de23bf21e7842ec8bf4242`로 동일하다. 전 계획은 Bitmap Heap Scan/34,038 shared read blocks/외부 정렬, 후 계획은 Index Only Scan/Heap Fetches0/shared read0으로 바뀌었다. 측정 조회0.881초→0.0765초는 cache/순서 영향을 포함하므로 cold start SLO나 전체API 개선율로 주장하지 않는다. 원본은 `outputs/reliability_feature_pair_index_20261101_v1/verification.json`; index valid/ready 확인. backend 재기동 후 실제API 검증은 부모가 수행한다. 과거 실패 원본은 유지한다.

projection materialized view를 DROP/재생성하는 배포에서는 인덱스 migration을 다시 적용해야 한다. 롤백은 해당 migration에서 생성한 인덱스만 `DROP INDEX CONCURRENTLY projection.idx_s101_feature_current_type_pair`로 제거한다. 이미 존재하던 인덱스를 임의 제거하지 않는다.

운영 소스 변경으로 논문 비교는 새 source hash의 전체 동결 실행이 필요하다.

주 에이전트 재검증: 관련177tests passed. 새 계측을 배포한 실제SSE v1에서 `feature_code_verification`이 30,049.747ms 후 SQLSTATE57014로 실패했다. 운영 covering index 적용 후 v2는 3/3 통과: 부산1m 관측0/PARTIAL 11.671초, 1km25건/COMPLETED 13.656초, 60km/BLOCKED 13.203초. source_unchanged=true. 원본은 `outputs/reliability_coverage_gate_runtime_20261101_v1,v2`; 실패 원본을 덮지 않았다. 이 재검증은 인덱스 적용 후 이미 실행 중인 API에서 수행했으며 DB cold-cache SLO를 증명하지 않는다.
