CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS serving;

DROP MATERIALIZED VIEW IF EXISTS serving.accident_s101_relation_current;

CREATE MATERIALIZED VIEW serving.accident_s101_relation_current AS
WITH anchor_candidates AS (
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
        anchor.feature_instance_id,
        anchor.dataset_id,
        anchor.dataset_name,
        anchor.feature_type_code,
        anchor.feature_type_name,
        anchor.product_specification,
        anchor.anchor_geometry,
        row_number() OVER (
            PARTITION BY a.event_id
            ORDER BY a.geom <-> anchor.anchor_geometry
        ) AS anchor_rank
    FROM serving.accident_events AS a
    JOIN LATERAL (
        SELECT
            feature_instance_id,
            dataset_id,
            dataset_name,
            feature_type_code,
            feature_type_name,
            product_specification,
            anchor_geometry
        FROM projection.s101_feature_valid_anchor
        WHERE a.geom IS NOT NULL
        ORDER BY a.geom <-> anchor_geometry
        LIMIT 20
    ) AS anchor ON true
    WHERE a.geom IS NOT NULL
),
measured AS (
    SELECT
        c.event_id,
        c.occurred_at,
        c.authority,
        c.sea_area,
        c.accident_type,
        c.cause,
        c.vessel_type,
        c.tonnage,
        c.accident_geometry,
        c.feature_instance_id,
        c.dataset_id,
        c.dataset_name,
        c.feature_type_code,
        c.feature_type_name,
        c.product_specification,
        c.anchor_geometry,
        c.anchor_rank,
        ROUND(ST_DistanceSphere(c.accident_geometry, f.geometry)::numeric, 3) AS distance_meters,
        ST_Intersects(f.geometry, c.accident_geometry) AS intersects
    FROM anchor_candidates AS c
    JOIN projection.s101_feature_valid AS f
      ON f.feature_instance_id = c.feature_instance_id
),
ranked AS (
    SELECT *,
           row_number() OVER (
               PARTITION BY event_id
               ORDER BY distance_meters, anchor_rank, feature_instance_id
           ) AS relation_rank
    FROM measured
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
    anchor_geometry,
    anchor_rank,
    distance_meters,
    CASE
        WHEN intersects THEN 'INTERSECTS'
        WHEN distance_meters <= 50 THEN 'WITHIN_50M'
        WHEN distance_meters <= 100 THEN 'WITHIN_100M'
        WHEN distance_meters <= 500 THEN 'WITHIN_500M'
        WHEN distance_meters <= 1000 THEN 'WITHIN_1000M'
        ELSE 'NEAREST_OVER_1000M'
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

CREATE INDEX IF NOT EXISTS idx_accident_s101_relation_anchor_geometry
    ON serving.accident_s101_relation_current USING gist (anchor_geometry);

ANALYZE serving.accident_s101_relation_current;
