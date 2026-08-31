-- Ensure production spatial indexes for S-101 v2 serving queries.
-- Safe to rerun: all indexes are guarded with IF NOT EXISTS.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_geometry
    ON projection.s101_feature_current
    USING gist (geometry);

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_geography
    ON projection.s101_feature_current
    USING gist ((geometry::geography))
    WHERE geometry IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_type_geometry_gist
    ON projection.s101_feature_current
    USING gist (feature_type_code, geometry)
    WHERE geometry IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_feature_type_code
    ON projection.s101_feature_current
    USING btree (feature_type_code);

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_dataset_id
    ON projection.s101_feature_current
    USING btree (dataset_id);

ANALYZE projection.s101_feature_current;
