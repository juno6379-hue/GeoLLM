CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS projection;
CREATE SCHEMA IF NOT EXISTS knowledge;

DROP VIEW IF EXISTS projection.s101_feature_geojson;
DROP MATERIALIZED VIEW IF EXISTS projection.s101_feature_current;

CREATE MATERIALIZED VIEW projection.s101_feature_current AS
SELECT
    f.seq::bigint AS feature_instance_id,
    d.dataset_id::bigint AS dataset_id,
    d.dataset_id::bigint AS dataset_version_id,
    f.seq::bigint AS feature_record_id,
    f.featurecode::integer AS feature_type_code,
    NULL::integer AS foid_agen,
    f.foid::bigint AS foid_fidn,
    NULL::integer AS foid_fids,
    'ACTIVE'::text AS lifecycle_status,
    COALESCE(attrs.attributes, '{}'::jsonb) AS attributes,
    ST_SetSRID(f.geom, 4326) AS geometry,
    now()::timestamptz AS rebuilt_at,
    f.featurecode::integer AS raw_feature_type_code,
    ident.feature_type_code::text AS feature_type_name,
    m.minscale::integer AS min_scale,
    m.maxscale::integer AS max_scale,
    d.product_specification::text AS product_specification,
    d.dataset_name::text AS dataset_name
FROM public.s101_feature AS f
JOIN public.s101_legacy_meta_binding AS b
  ON b.legacy_meta_seq = f.meta_seq
JOIN public.s101_dataset AS d
  ON d.dataset_id = b.dataset_id
LEFT JOIN public.s101_meta AS m
  ON m.seq = f.meta_seq
LEFT JOIN public.s101_feature_identity AS ident
  ON ident.feature_seq = f.seq
LEFT JOIN LATERAL (
    SELECT jsonb_object_agg(a.attrname, a.attrvalue ORDER BY a.attribute_ordinal) AS attributes
    FROM public.s101_feature_attr_value AS a
    WHERE a.feature_seq = f.seq
) AS attrs ON true
WHERE d.product_specification = 'INT.IHO.S-101.2.0'
  AND f.geom IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_s101_feature_current_feature_instance_id
    ON projection.s101_feature_current (feature_instance_id);

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_geometry
    ON projection.s101_feature_current USING GIST (geometry);

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_feature_type_code
    ON projection.s101_feature_current (feature_type_code);

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_dataset_id
    ON projection.s101_feature_current (dataset_id);

CREATE INDEX IF NOT EXISTS idx_s101_feature_current_product_specification
    ON projection.s101_feature_current (product_specification);

ANALYZE projection.s101_feature_current;

CREATE OR REPLACE VIEW projection.s101_feature_geojson AS
SELECT
    feature_instance_id,
    dataset_id,
    feature_type_code,
    feature_type_name,
    ST_AsGeoJSON(geometry)::jsonb AS geometry,
    attributes,
    product_specification,
    dataset_name
FROM projection.s101_feature_current;

CREATE TABLE IF NOT EXISTS knowledge.document_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    product_id TEXT,
    standard_type TEXT,
    title TEXT,
    section TEXT,
    version TEXT,
    language TEXT DEFAULT 'ko',
    content TEXT NOT NULL,
    keywords TEXT[],
    related_features TEXT[],
    related_concepts TEXT[],
    clearance_level TEXT DEFAULT 'PUBLIC',
    source_file TEXT,
    source_url TEXT,
    page_no INTEGER,
    metadata JSONB NOT NULL,
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT NOW(),
    source_id TEXT,
    source_sha256 TEXT
);

ALTER TABLE knowledge.document_chunks
    ADD COLUMN IF NOT EXISTS embedding vector(1024);

CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata
    ON knowledge.document_chunks USING GIN (metadata);

CREATE INDEX IF NOT EXISTS idx_document_chunks_s101_20
    ON knowledge.document_chunks ((metadata->>'product_specification'), product_id, version);
