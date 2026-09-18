# External Evidence Gap-Fill Pipeline

S-101 전자해도나 로컬 serving 레이어에 객체가 없을 때 `없음`으로 끝내지 않는다. 이 경우를 `External Evidence Gap`으로 기록하고, 다음 순서로 후보를 만든다.

1. Local authoritative registry
   - `data/spatial_layer_registry.yaml`, `data/place_geometry_registry.yaml`, `projection.s101_feature_current`, `serving.*_current`를 먼저 확인한다.
   - 여기서 나온 객체만 즉시 실행 결과로 사용할 수 있다.

2. Public authoritative source
   - 로컬에 없으면 국가유산포털, 국가유산청, 해양수산부, 환경부 같은 공공 authoritative source를 후보로 만든다.
   - 공공 출처라도 공식 경계/폴리곤이 없으면 자동 승격하지 않는다.

3. OSM/RAG candidate
   - OSM, Nominatim, Overpass, 웹/RAG 후보는 보조 후보로만 사용한다.
   - `authority_level=supplemental` 후보는 근거 발견과 비교에는 쓸 수 있지만, authoritative 객체로 자동 승격하지 않는다.
   - 공용 OSM API는 기본 비활성이다. live 후보 수집은 `--fetch-osm`과 `GEOLLM_OSM_USER_AGENT`가 있을 때만 실행한다.
   - Nominatim은 지명/주소 후보 검색에, Overpass는 주변 OSM tag 후보 검색에만 사용한다.

4. Validation and promotion
   - 후보는 `outputs/external_evidence/gap_fill_candidates.jsonl`에 기록한다.
   - 승격 후보는 `outputs/external_evidence/promotion_candidates.jsonl`에 별도로 기록한다.
   - 승격에는 공식 출처 URL, 공식 경계/폴리곤, authority metadata 검토가 필요하다.

## Runtime Contract

- 로컬 authoritative 결과가 있으면 그 결과를 우선 답변한다.
- 로컬 결과가 없고 외부 authoritative 후보가 있으면 “전자해도/로컬 레이어에는 없음, 다만 공공 authoritative 후보가 있음”으로 답한다.
- DB 체크가 실행되지 않았거나 일부 레이어가 막혔으면 `local_gap_confirmed=false`로 둔다. 다만 양성 로컬 매치가 없으면 외부 후보 생성은 허용하고, 답변에는 미확인 상태를 함께 표시한다.
- 동종 authoritative 레이어만 외부 후보 생성을 막을 수 있다. 예를 들어 `natural_heritage_protected_area` 질의에서 S-101 일반 피처가 주변에 있다는 사실은 context check이며, `protected_area` 결측 보완을 막는 blocking match가 아니다.
- OSM/RAG 후보는 “보조 후보”로 표시한다.
- Ollama는 애매한 의도/슬롯 검토에만 사용한다. 지명 좌표, 법령, 지정일, 면적, 건수 같은 사실의 authority로 사용하지 않는다.
- OSM/Nominatim/Overpass 결과는 지명·주소·tag 후보 생성에만 사용한다. 공공 authoritative source 또는 로컬 registry 검증 전에는 승격하지 않는다.
- 지도 표시는 검토 전에는 point fallback 또는 후보 레이어로만 표시한다.
- `execution_ready=true`는 로컬 객체, 검증된 geometry, 실행 가능한 tool binding이 모두 있을 때만 가능하다.

## Optional Live Candidate Fetch

기본 실행은 외부 API를 호출하지 않는다.

```powershell
python scripts\run_external_evidence_gap_fill.py --query "독도 부근 천연보호구역을 찾아줘" --fetch-osm
```

live OSM 후보 수집을 켜려면 정책상 식별 가능한 User-Agent가 필요하다.

```powershell
$env:GEOLLM_OSM_USER_AGENT="GeoLLM/0.1 contact@example.com"
python scripts\run_external_evidence_gap_fill.py --query "독도 부근 천연보호구역을 찾아줘" --fetch-osm
```

Ollama는 다음처럼 ambiguity review에만 사용한다.

```powershell
python scripts\run_external_evidence_gap_fill.py --query "독도 부근 천연보호구역을 찾아줘" --ask-ollama
```

## Dokdo Natural Heritage Example

질의:

```text
독도 부근 천연보호구역을 찾아줘
```

처리:

- 로컬 anchor: `dokdo`
- gap domain: `natural_heritage_protected_area`
- 로컬 확인 대상:
  - `protected_sea_area`
  - `GBENC_S101_feature`
  - `hazard_area_current`
- 공공 authoritative 후보:
  - `독도 천연보호구역`
  - 출처: 국가유산포털
  - 지정: 천연기념물
  - 지정일: 1982-11-16
  - 면적: 187,554 m2
- 승격 상태:
  - `NEEDS_GEOMETRY_REVIEW`
  - 공식 폴리곤 또는 경계 검토 전에는 authoritative spatial layer로 승격하지 않는다.

## Verification Commands

```powershell
python -m py_compile scripts\run_external_evidence_gap_fill.py
python -m pytest tests\unit\test_external_evidence_gap_fill.py -q
python scripts\run_external_evidence_gap_fill.py --query "독도 부근 천연보호구역을 찾아줘"
```
