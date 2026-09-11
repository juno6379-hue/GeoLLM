CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS projection;

DROP MATERIALIZED VIEW IF EXISTS projection.s101_feature_valid_anchor;

CREATE MATERIALIZED VIEW projection.s101_feature_valid_anchor AS
SELECT
    feature_instance_id,
    dataset_id,
    dataset_name,
    feature_type_code,
    feature_type_name,
    product_specification,
    GeometryType(geometry) AS geometry_type,
    ST_PointOnSurface(geometry)::geometry(Point, 4326) AS anchor_geometry
FROM projection.s101_feature_valid
WHERE geometry IS NOT NULL
  AND NOT ST_IsEmpty(geometry)
  AND ST_IsValid(geometry)
  AND product_specification = 'INT.IHO.S-101.2.0';

CREATE UNIQUE INDEX IF NOT EXISTS idx_s101_feature_valid_anchor_feature_instance_id
    ON projection.s101_feature_valid_anchor (feature_instance_id);

CREATE INDEX IF NOT EXISTS idx_s101_feature_valid_anchor_geometry
    ON projection.s101_feature_valid_anchor USING gist (anchor_geometry);

CREATE INDEX IF NOT EXISTS idx_s101_feature_valid_anchor_feature_type_code
    ON projection.s101_feature_valid_anchor (feature_type_code);

ANALYZE projection.s101_feature_valid_anchor;
