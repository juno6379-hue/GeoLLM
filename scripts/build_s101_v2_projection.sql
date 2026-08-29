-- Rebuild the serving projection without modifying canonical source tables.
SET client_min_messages TO error;
BEGIN;

TRUNCATE TABLE projection.s101_feature_geojson;
TRUNCATE TABLE projection.s101_feature_current;
TRUNCATE TABLE projection.s101_dataset_current;

CREATE TEMP TABLE latest_dataset_version ON COMMIT DROP AS
SELECT DISTINCT ON (dataset_id)
       dataset_id,
       dataset_version_id,
       dsnm,
       edition_number,
       update_number,
       purpose
FROM canonical.dataset_version
ORDER BY dataset_id, edition_number DESC NULLS LAST,
         update_number DESC, dataset_version_id DESC;

INSERT INTO projection.s101_dataset_current (
    dataset_id, dataset_version_id, dsnm, product_id,
    edition_number, update_number, purpose,
    min_scale, max_scale, bbox, conformance_status, rebuilt_at
)
SELECT dv.dataset_id,
       dv.dataset_version_id,
       dv.dsnm,
       d.product_id,
       dv.edition_number,
       dv.update_number,
       dv.purpose,
       NULL,
       NULL,
       CASE WHEN g.geometry IS NULL THEN NULL
            ELSE ST_Envelope(ST_Expand(g.geometry, 0.000001))::geometry(Polygon,4326) END,
       NULL,
       now()
FROM latest_dataset_version dv
JOIN canonical.dataset d ON d.dataset_id = dv.dataset_id
LEFT JOIN LATERAL (
    SELECT ST_Collect(
               CASE WHEN ST_IsValid(sr.derived_geometry)
                    THEN sr.derived_geometry
                    ELSE ST_MakeValid(sr.derived_geometry)
               END
           ) AS geometry
    FROM canonical.spatial_record sr
    WHERE sr.dataset_version_id = dv.dataset_version_id
      AND sr.derived_geometry IS NOT NULL
) g ON true;

CREATE TEMP TABLE feature_geometry ON COMMIT DROP AS
SELECT fr.feature_record_id,
       fr.feature_instance_id,
       ST_Collect(
           CASE WHEN ST_IsValid(sr.derived_geometry)
                THEN sr.derived_geometry
                ELSE ST_MakeValid(sr.derived_geometry)
           END
       ) AS geometry
FROM canonical.feature_record fr
JOIN canonical.spatial_reference sref
  ON sref.feature_record_id = fr.feature_record_id
JOIN canonical.spatial_record sr
  ON sr.spatial_record_id = sref.spatial_record_id
WHERE sr.derived_geometry IS NOT NULL
GROUP BY fr.feature_record_id, fr.feature_instance_id;

INSERT INTO projection.s101_feature_current (
    feature_instance_id, dataset_id, dataset_version_id,
    feature_record_id, feature_type_code,
    foid_agen, foid_fidn, foid_fids, lifecycle_status,
    attributes, geometry, rebuilt_at
)
SELECT fi.feature_instance_id,
       fi.dataset_id,
       fr.dataset_version_id,
       fr.feature_record_id,
       fr.nftc,
       fi.foid_agen,
       fi.foid_fidn,
       fi.foid_fids,
       fi.lifecycle_status,
       COALESCE(attrs.attributes, '{}'::jsonb),
       fg.geometry,
       now()
FROM canonical.feature_instance fi
JOIN canonical.feature_record fr
  ON fr.feature_instance_id = fi.feature_instance_id
JOIN latest_dataset_version dv
  ON dv.dataset_version_id = fr.dataset_version_id
LEFT JOIN feature_geometry fg
  ON fg.feature_record_id = fr.feature_record_id
LEFT JOIN LATERAL (
    SELECT jsonb_object_agg(
               COALESCE(NULLIF(fav.catalogue_name, ''),
                        'attribute_' || fav.atin::text || '_' || fav.atix::text),
               COALESCE(
                   to_jsonb(fav.value_text),
                   to_jsonb(fav.raw_value),
                   to_jsonb(fav.value_integer),
                   to_jsonb(fav.value_numeric),
                   to_jsonb(fav.value_boolean),
                   to_jsonb(fav.value_date)
               )
           ) AS attributes
    FROM canonical.feature_attribute_value fav
    WHERE fav.feature_record_id = fr.feature_record_id
) attrs ON true;

INSERT INTO projection.s101_feature_geojson (
    feature_instance_id, dataset_id, feature_type_code,
    properties, geometry_geojson, bbox, rebuilt_at
)
SELECT feature_instance_id,
       dataset_id,
       feature_type_code,
       attributes,
       CASE WHEN geometry IS NULL THEN NULL ELSE ST_AsGeoJSON(geometry)::jsonb END,
       CASE WHEN geometry IS NULL THEN NULL
            ELSE ST_Envelope(ST_Expand(geometry, 0.000001))::geometry(Polygon,4326) END,
       now()
FROM projection.s101_feature_current
WHERE geometry IS NOT NULL;

INSERT INTO audit.projection_build (
    projection_name, started_at, finished_at, row_count, status
)
VALUES (
    's101_v2_current', now(), now(),
    (SELECT count(*) FROM projection.s101_feature_current),
    'SUCCEEDED'
);

COMMIT;
