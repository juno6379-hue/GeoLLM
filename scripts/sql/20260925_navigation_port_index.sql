-- Harbour-name and nearest-harbour lookups must not scan the whole ENC projection.
-- Run outside a transaction against S101_DB_URL; no source rows are modified.
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_s101_valid_harbour_name
ON projection.s101_feature_valid (product_specification, (attributes->>'name'))
WHERE feature_type_name = 'HarbourAreaAdministrative' AND geometry IS NOT NULL;

ANALYZE projection.s101_feature_valid;
