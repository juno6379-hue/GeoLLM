-- Operational performance migration: exact name/code conflict query unchanged.
-- Run outside a transaction; does not modify source rows or research snapshots.
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_s101_feature_current_type_pair
ON projection.s101_feature_current (feature_type_name, feature_type_code);

-- Reversible rollback, only if this migration created the index:
-- DROP INDEX CONCURRENTLY projection.idx_s101_feature_current_type_pair;
