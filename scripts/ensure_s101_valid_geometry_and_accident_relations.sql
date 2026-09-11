CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS projection;
CREATE SCHEMA IF NOT EXISTS serving;

DROP MATERIALIZED VIEW IF EXISTS serving.accident_s101_relation_current;
DROP MATERIALIZED VIEW IF EXISTS projection.s101_feature_valid;

CREATE MATERIALIZED VIEW projection.s101_feature_valid AS
WITH repaired AS (
    SELECT
        feature_instance_id,
        dataset_id,
        dataset_version_id,
        feature_record_id,
        feature_type_code,
        foid_agen,
        foid_fidn,
        foid_fids,
        lifecycle_status,
        attributes,
        rebuilt_at,
        raw_feature_type_code,
        feature_type_name,
        min_scale,
        max_scale,
        product_specification,
        dataset_name,
        GeometryType(geometry) AS original_geometry_type,
        ST_IsValid(geometry) AS original_geometry_valid,
        CASE
            WHEN ST_IsValid(geometry) THEN NULL::text
            ELSE ST_IsValidReason(geometry)
        END AS original_invalid_reason,
        ST_Force2D(
            CASE
                WHEN ST_IsValid(geometry) THEN ST_SetSRID(geometry, 4326)
                WHEN ST_Dimension(geometry) = 0 THEN ST_SetSRID(ST_CollectionExtract(ST_MakeValid(geometry), 1), 4326)
                WHEN ST_Dimension(geometry) = 1 THEN ST_SetSRID(ST_CollectionExtract(ST_MakeValid(geometry), 2), 4326)
                ELSE ST_SetSRID(ST_CollectionExtract(ST_MakeValid(geometry), 3), 4326)
            END
        )::geometry(Geometry, 4326) AS geometry
    FROM projection.s101_feature_current
    WHERE geometry IS NOT NULL
      AND product_specification = 'INT.IHO.S-101.2.0'
)
SELECT *,
       NOT original_geometry_valid AS was_geometry_repaired
FROM repaired
WHERE geometry IS NOT NULL
  AND NOT ST_IsEmpty(geometry)
  AND ST_IsValid(geometry);

CREATE UNIQUE INDEX IF NOT EXISTS idx_s101_feature_valid_feature_instance_id
    ON projection.s101_feature_valid (feature_instance_id);

CREATE INDEX IF NOT EXISTS idx_s101_feature_valid_geometry
    ON projection.s101_feature_valid USING gist (geometry);

CREATE INDEX IF NOT EXISTS idx_s101_feature_valid_geography
    ON projection.s101_feature_valid USING gist ((geometry::geography));

CREATE INDEX IF NOT EXISTS idx_s101_feature_valid_feature_type_code
    ON projection.s101_feature_valid (feature_type_code);

CREATE INDEX IF NOT EXISTS idx_s101_feature_valid_dataset_id
    ON projection.s101_feature_valid (dataset_id);

CREATE INDEX IF NOT EXISTS idx_s101_feature_valid_product_specification
    ON projection.s101_feature_valid (product_specification);

ANALYZE projection.s101_feature_valid;

CREATE MATERIALIZED VIEW serving.accident_s101_relation_current AS
WITH candidates AS (
    SELECT
        a.event_id,
        a.occurred_at,
        a.authority,
        a.sea_area,
        a.accident_type,
        a.cause,
        a.vessel_type,
        a.tonnage,
        a.geom AS accident_geometry,
        f.feature_instance_id,
        f.dataset_id,
        f.dataset_name,
        f.feature_type_code,
        f.feature_type_name,
        f.product_specification,
        ROUND(ST_Distance(a.geom::geography, f.geometry::geography)::numeric, 3) AS distance_meters,
        ST_Intersects(f.geometry, a.geom) AS intersects
    FROM serving.accident_events AS a
    JOIN projection.s101_feature_valid AS f
      ON a.geom IS NOT NULL
     AND f.geometry && ST_Expand(a.geom, 0.02)
     AND ST_DWithin(a.geom, f.geometry, 0.02)
    WHERE ST_Distance(a.geom::geography, f.geometry::geography) <= 1000
),
ranked AS (
    SELECT *,
           row_number() OVER (
               PARTITION BY event_id
               ORDER BY distance_meters, feature_instance_id
           ) AS relation_rank
    FROM candidates
)
SELECT
    event_id,
    occurred_at,
    authority,
    sea_area,
    accident_type,
    cause,
    vessel_type,
    tonnage,
    accident_geometry,
    feature_instance_id,
    dataset_id,
    dataset_name,
    feature_type_code,
    feature_type_name,
    product_specification,
    distance_meters,
    CASE
        WHEN intersects THEN 'INTERSECTS'
        WHEN distance_meters <= 50 THEN 'WITHIN_50M'
        WHEN distance_meters <= 100 THEN 'WITHIN_100M'
        WHEN distance_meters <= 500 THEN 'WITHIN_500M'
        ELSE 'WITHIN_1000M'
    END AS relation_type,
    relation_rank,
    now()::timestamptz AS joined_at
FROM ranked
WHERE relation_rank <= 5;

CREATE INDEX IF NOT EXISTS idx_accident_s101_relation_event_id
    ON serving.accident_s101_relation_current (event_id);

CREATE INDEX IF NOT EXISTS idx_accident_s101_relation_feature_instance_id
    ON serving.accident_s101_relation_current (feature_instance_id);

CREATE INDEX IF NOT EXISTS idx_accident_s101_relation_type
    ON serving.accident_s101_relation_current (relation_type);

CREATE INDEX IF NOT EXISTS idx_accident_s101_relation_feature_type_code
    ON serving.accident_s101_relation_current (feature_type_code);

CREATE INDEX IF NOT EXISTS idx_accident_s101_relation_accident_geometry
    ON serving.accident_s101_relation_current USING gist (accident_geometry);

ANALYZE serving.accident_s101_relation_current;
