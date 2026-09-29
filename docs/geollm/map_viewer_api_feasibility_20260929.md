# parser & Map_viewer API 연동 가능성 — 2026-09-29

## 판단

기술적으로 가능하다. 현재 GeoLLM Leaflet 지도에 WebViewer의 PNG XYZ 타일을 연결하는 방식을 우선 권장한다. 지도 전체 교체와 객체 선택/근거 연동은 별도 단계다. 이번 작업은 소스와 상태를 읽은 타당성 검토이며 연동 구현·서비스 시작·라이선스 발급은 수행하지 않았다.

## 확인 근거

- GeoLLM `services/orchestrator/static/index.html`: Leaflet 1.9.4, 기본 OSM, 기존 WMS `localhost:11002/encService`, 질의 시 EPSG:4326 bbox 문맥 및 GeoJSON 결과 표시 구조.
- `D:/dev/WebViewer/apps/api/src/publicMapApi.ts`, `publicMapServer.ts`, `docs/licensed-rest-api.md`: 3002 공개 REST API, X-API-Key, 라이선스 Stage/Origin/일일 한도 검사, TileJSON/512px PNG XYZ/MapLibre style. WMS 계약이 아니므로 URL만 바꾸면 안 된다.
- 공개 경로: `/v1/maps/s101/stages`, `/v1/maps/s101/stages/{stage}/tilejson.json`, `/v1/maps/s101/stages/{stage}/tiles/{z}/{x}/{y}.png`, `/v1/maps/s101/style.json`.
- 내부 `routes.ts`에는 `/api/features`, `/api/search/features`, `/api/features/:featureInstanceId`가 있다. 공개 라이선스 API에 객체 조회는 아직 없다. GeoJSON bbox는 EPSG:4326을 사용한다.
- 실제 3000 `/health`: HTTP 200, database=ok, projection=ok, FC/PC=2.0.0. 3002 `/health`는 연결 거부, GeoLLM 8000은 HTTP 전송 오류. 원인은 이번 범위에서 진단하지 않았다.
- 로컬 PNG manifest Stage 0~4는 complete=true, 각각 2354/6804/26756/2234/8589개 기록. Stage 5/6 manifest는 위 디렉터리 조회에서 확인하지 못했다. 전체 타일 파일/이미지·공개 API ready를 검증한 결과는 아니다. 공개 API는 sourcePipeline/범위/타일 수 등 추가 완결성 검사를 통과한 Stage만 제공한다.

## 권장 연결

GeoLLM 브라우저 → GeoLLM 지도 API proxy → WebViewer 공개 지도 API → PNG cache.

1. 공개 서비스 3002 준비 상태와 GeoLLM 8000 오류를 확인한다. 유효한 이용권으로 stages/TileJSON/대표 PNG/권한 실패를 검사한다.
2. GeoLLM 서버 설정에 provider URL과 키를 보관하고 고정된 지도 경로만 proxy한다. Leaflet 기본 이미지 타일 요청은 X-API-Key를 직접 넣지 않으므로 서버가 헤더를 부여하는 방식이 적합하다. TileJSON의 타일 URL도 proxy 경로로 변환한다. 관리자 경로를 노출하지 않는다.
3. 기존 지도에 S-101 XYZ 레이어를 추가하고 Stage별 줌/경계/512px 규약을 맞춘다. 512px 이미지 해상도와 XYZ 지리 격자를 혼동하지 않도록 기준점으로 정합성을 검사한다. 미완료 Stage, 401/403/429/503을 명시적으로 표시한다.
4. 지도 이동/viewport/선택 지점/분석 GeoJSON은 기존 질의 UI와 연동한다. Docker backend가 호스트 API에 접근할 경우 host.docker.internal 및 실제 바인딩/프록시 도달성을 검증한다. 127.0.0.1 바인딩에 무조건 접근할 수 있다고 가정하지 않는다.
5. 객체 선택은 별도 읽기 전용 adapter 또는 라이선스 객체 조회 API를 만든다. PNG에는 feature ID가 없으므로 bbox/클릭 위치에 대한 GeoJSON 조회가 필요하다. 내부 3000 전체를 브라우저에 공개하지 않는다.
6. provider+dataset/version+feature ID/FOID로 원천을 식별한다. GeoLLM은 현재 자체 S101 DB의 projection.s101_feature_valid ID를 조회하므로, 다른 DB의 숫자 ID를 그대로 대입하면 안 된다. 같은 원천/판인지 확인하거나 API 기반 binding adapter를 도입한다.
7. 실행은 기존 ExecutionValidator를 거친다. 지도 표시 성공이나 provider 응답만으로 분석 실행 승인·공식 portrayal 근거 완성을 선언하지 않는다. Qwen은 shadow 유지.

## 대안과 범위

- 전체 WebViewer를 iframe으로 넣으면 별도 postMessage 계약(이동/선택/레이어/문맥 및 origin 검증)이 필요하다. 현재 공개 API는 iframe 제공이 범위 밖이고 앱 소스에서 해당 메시지 연결을 찾지 못했다.
- MapLibre로 교체하면 제공 style.json을 활용할 수 있지만 기존 Leaflet 분석 레이어/클릭/영역 문맥을 이관해야 하므로 초기 연동보다 범위가 크다.
- 다음 작업은 서비스·이용권·대표 타일 확인 → Leaflet proxy 연동 → 좌표/줌 정합성 → 객체 식별/근거 adapter 순서다. Phase A 전체 회귀·최신 API 재검증은 기존 인계대로 미완료다.
