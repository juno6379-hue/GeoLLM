# Schema Registry 및 데이터베이스 조회 규칙

## 1. 실제 객체 구분

### 1.1 물리 테이블

- `public.feature`
- `public.enc_meta`
- `public.codeinformation`
- `public.attribute_code`

### 1.2 조회용 파생 뷰

동일한 스키마에서 물리 테이블과 같은 이름의 뷰를 만들지 않는다.

```sql
CREATE OR REPLACE VIEW public.v_feature_readable AS
SELECT
    f.seq,
    f.meta_seq AS meta_seq_id,
    split_part(em.dsnm, '__', 1)::varchar(25) AS dataset_name,
    f.nftc AS nftc_code,
    ci.name AS feature_name,
    f.rver,
    f.geom,
    f.attr,
    f.reg_date,
    f.rrnm,
    f.data_geom
FROM public.feature AS f
LEFT JOIN public.enc_meta AS em
    ON f.meta_seq = em.seq
LEFT JOIN public.codeinformation AS ci
    ON ci.type = 0
   AND ci.code = f.nftc;
```

## 2. 주요 컬럼 정의

### `public.feature`

| 컬럼 | 타입 | 의미 |
|---|---|---|
| `seq` | bigint/integer 계열 | 피처 식별자 |
| `meta_seq` | bigint | ENC 메타데이터 참조값 |
| `nftc` | integer | 피처 코드 |
| `rver` | integer | 개정 버전 |
| `geom` | geometry | 기본 지오메트리 |
| `attr` | varchar(4096) | 인코딩된 속성 |
| `reg_date` | date | 등록일 |
| `rrnm` | integer | 추가 숫자형 메타데이터 |
| `data_geom` | geometry, nullable | 선택적 보조 지오메트리 |

### `public.codeinformation`

| 컬럼 | 타입 | 의미 |
|---|---|---|
| `type` | smallint | 코드 분류 |
| `code` | integer | `feature.nftc`와 연결되는 값 |
| `name` | varchar(64) | 사람이 읽을 수 있는 피처명 |

## 3. 허용 조인

```text
feature.meta_seq → enc_meta.seq
feature.nftc     → codeinformation.code (codeinformation.type = 0)
attribute_code.enc_meta_seq → enc_meta.seq
```

DDL에 외래 키가 선언되어 있지 않더라도 조회에서는 위 관계를 의도된 조인으로 사용할 수 있다.

## 4. 금지 규칙

```sql
-- 금지: nftc는 정수형이다.
WHERE f.nftc ILIKE '%Berth%'

-- 금지: 존재하지 않는 사람이 읽는 nftc 뷰 컬럼을 가정
WHERE public.feature.nftc = 'Berth'
```

허용 예시는 다음과 같다.

```sql
SELECT f.*
FROM public.feature AS f
JOIN public.codeinformation AS ci
  ON ci.type = 0
 AND ci.code = f.nftc
WHERE ci.name ILIKE '%Berth%';
```

또는:

```sql
SELECT *
FROM public.v_feature_readable
WHERE feature_name ILIKE '%Berth%';
```

## 5. Schema Registry JSON 예시

```json
{
  "public.feature": {
    "object_type": "table",
    "primary_key": ["seq"],
    "geometry_column": "geom",
    "columns": {
      "seq": "bigint",
      "meta_seq": "bigint",
      "nftc": "integer",
      "rver": "integer",
      "geom": "geometry",
      "attr": "varchar",
      "reg_date": "date",
      "rrnm": "integer",
      "data_geom": "geometry"
    },
    "allowed_operations": ["SELECT"],
    "default_limit": 100
  },
  "public.v_feature_readable": {
    "object_type": "view",
    "geometry_column": "geom",
    "columns": {
      "seq": "bigint",
      "meta_seq_id": "bigint",
      "dataset_name": "varchar",
      "nftc_code": "integer",
      "feature_name": "varchar",
      "geom": "geometry",
      "attr": "varchar"
    },
    "allowed_operations": ["SELECT"]
  }
}
```

## 6. SRID 사전 점검

```sql
SELECT
    ST_SRID(geom) AS srid,
    GeometryType(geom) AS geometry_type,
    COUNT(*) AS feature_count
FROM public.feature
WHERE geom IS NOT NULL
GROUP BY ST_SRID(geom), GeometryType(geom)
ORDER BY feature_count DESC;
```

정책:

- `4326`: geography 거리 연산 허용
- 알려진 비4326 SRID: `ST_Transform(..., 4326)` 후 geography 사용
- `0`: 실행 중단 및 `SRID_UNKNOWN`
- 복수 SRID 혼재: 데이터셋별 또는 행별 정책 적용
