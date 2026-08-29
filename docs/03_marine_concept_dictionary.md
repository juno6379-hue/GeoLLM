# 해양 객체 개념 사전 및 매핑 규칙

## 1. 목적

사용자 자연어 객체명을 S-101/ENC 데이터베이스의 실제 피처명과 NFTC 코드로 연결한다.

```text
선석
→ MARINE_BERTH
→ Berth 후보
→ codeinformation.name 검색
→ codeinformation.code
→ feature.nftc
```

## 2. 데이터 모델

```sql
CREATE TABLE public.spatial_concept (
    concept_id varchar(100) PRIMARY KEY,
    canonical_name varchar(200) NOT NULL,
    name_ko varchar(200),
    name_en varchar(200),
    domain varchar(50) NOT NULL DEFAULT 'S-101',
    default_geometry_types jsonb,
    default_agent varchar(100),
    enabled boolean NOT NULL DEFAULT true
);

CREATE TABLE public.spatial_concept_synonym (
    seq bigserial PRIMARY KEY,
    concept_id varchar(100) NOT NULL,
    synonym varchar(200) NOT NULL,
    language varchar(10),
    priority integer NOT NULL DEFAULT 100
);

CREATE TABLE public.spatial_concept_mapping (
    seq bigserial PRIMARY KEY,
    concept_id varchar(100) NOT NULL,
    mapping_type varchar(50) NOT NULL,
    code_value integer,
    code_name varchar(200),
    confidence numeric(5,4),
    source varchar(200),
    verified boolean NOT NULL DEFAULT false
);
```

## 3. 초기 개념 사전

> 아래 영문 후보는 개념 탐색용이다. 최종 `code_name`과 `code_value`는 반드시 `public.codeinformation` 실제 조회 결과로 확정한다.

| concept_id | 한국어 | 영문 후보 | 예상 문맥 |
|---|---|---|---|
| `MARINE_BERTH` | 선석 | Berth | 항만 접안시설 |
| `MARINE_QUAY` | 부두, 안벽 | Quay, Wharf | 항만 구조물 |
| `MARINE_BREAKWATER` | 방파제 | Breakwater | 연안 구조물 |
| `MARINE_LIGHT` | 등대, 등표 | Light, Landmark | 항행표지 |
| `MARINE_ANCHORAGE` | 정박지 | AnchorageArea | 정박구역 |
| `MARINE_ROUTE` | 항로 | NavigationalTrack, Fairway | 항행구역 |
| `MARINE_ROCK_AWASH` | 간출암 | Rock, RockAwash | 위험물 |
| `MARINE_ROCK_EXPOSED` | 노출암 | Rock, Obstruction | 위험물 |
| `MARINE_COASTLINE` | 해안선 | Coastline | 해안 경계 |
| `MARINE_DEPTH_CONTOUR` | 수심선 | DepthContour | 수심 정보 |
| `MARINE_LAND_AREA` | 육지구역 | LandArea | 육상 영역 |

## 4. 동의어 등록 예시

```sql
INSERT INTO public.spatial_concept (
    concept_id, canonical_name, name_ko, name_en,
    default_geometry_types, default_agent
) VALUES (
    'MARINE_BERTH', 'Berth', '선석', 'Berth',
    '["LINESTRING", "MULTILINESTRING", "POLYGON", "MULTIPOLYGON"]'::jsonb,
    'SpatialQueryAgent'
);

INSERT INTO public.spatial_concept_synonym
    (concept_id, synonym, language, priority)
VALUES
    ('MARINE_BERTH', '선석', 'ko', 1),
    ('MARINE_BERTH', '접안선석', 'ko', 5),
    ('MARINE_BERTH', '계류선석', 'ko', 10),
    ('MARINE_BERTH', 'berth', 'en', 1);
```

## 5. 실제 코드 후보 조회

```sql
SELECT
    ci.code,
    ci.name
FROM public.codeinformation AS ci
WHERE ci.type = 0
  AND (
      ci.name ILIKE '%Berth%'
      OR ci.name ILIKE '%Quay%'
      OR ci.name ILIKE '%Wharf%'
  )
ORDER BY ci.name, ci.code;
```

공백 포함 입력은 토큰 사이에 `%`를 넣는다.

```text
Land Area → %Land%Area%
Depth Contour → %Depth%Contour%
```

## 6. 후보 점수화

```text
exact synonym match           +50
canonical name exact match    +40
database name exact match     +40
token ILIKE match             +20
context match                 +15
geometry type match           +10
verified mapping              +20
```

해석 정책:

- 최고 후보 1개, confidence ≥ 0.85 → `RESOLVED`
- 후보 간 점수 차이 < 0.10 → `AMBIGUOUS`
- 후보 없음 → `NOT_FOUND`
- 검증된 매핑 존재 → 우선 사용

## 7. Concept Resolver 출력

```json
{
  "original_term": "선석",
  "concept_id": "MARINE_BERTH",
  "canonical_name": "Berth",
  "candidate_names": ["Berth", "Quay", "Wharf"],
  "nftc_codes": [],
  "resolution_status": "CODE_LOOKUP_REQUIRED",
  "confidence": 0.92
}
```

코드 확정 후:

```json
{
  "original_term": "선석",
  "concept_id": "MARINE_BERTH",
  "canonical_name": "Berth",
  "nftc_codes": [153],
  "resolution_status": "RESOLVED",
  "confidence": 0.96
}
```

> 예시 코드 `153`은 실제 데이터베이스 조회 결과로 검증된 경우에만 사용한다.
