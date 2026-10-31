BEGIN READ ONLY;
SET LOCAL statement_timeout='60000';
WITH anchor AS (SELECT ST_SetSRID(ST_MakePoint(131.86955555555556,37.24077777777778),4326) g),
harbour AS MATERIALIZED (SELECT ST_UnaryUnion(ST_Collect(geometry)) g FROM projection.s101_feature_current
 WHERE feature_type_name='HarbourAreaAdministrative' AND feature_instance_id=1137770 AND ST_IsValid(geometry)),
features AS (SELECT p.feature_instance_id::text id,p.feature_type_name feature,p.attributes,
 p.dataset_id,p.dataset_version_id,p.dataset_name,p.min_scale,p.max_scale,p.product_specification,p.foid_fidn,
 encode(ST_AsEWKB(p.geometry),'hex') geometry_ewkb,
 ST_AsGeoJSON(p.geometry,15)::jsonb geometry,ST_IsValid(p.geometry) valid,ST_SRID(p.geometry) srid,
 md5(ST_AsEWKB(p.geometry)) geometry_md5,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name='Wreck' THEN ST_Distance(p.geometry::geography,a.g::geography,true) END dokdo_distance_m,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_Covers(h.g,p.geometry) END harbour_covers,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_Intersects(h.g,p.geometry) END harbour_intersects,
 CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_DWithin(h.g::geography,p.geometry::geography,2000,true) END harbour_2km
 ,CASE WHEN ST_IsValid(p.geometry) AND p.feature_type_name IN ('AnchorageArea','RestrictedArea') THEN ST_Distance(h.g::geography,p.geometry::geography,true) END harbour_distance_m
 FROM projection.s101_feature_current p CROSS JOIN anchor a CROSS JOIN harbour h
 WHERE p.feature_type_name IN ('HarbourAreaAdministrative','AnchorageArea','RestrictedArea','Wreck','LightAllAround','LightSectored','Landmark','Building')),
navigation AS (SELECT p.source_id id,p.aid_no,p.name,p.active,p.properties,p.provenance,
 ST_AsGeoJSON(p.geometry,15)::jsonb geometry,ST_IsValid(p.geometry) valid,
 ST_Distance(p.geometry::geography,a.g::geography,true) dokdo_distance_m
 FROM serving.navigation_aid_current p CROSS JOIN anchor a)
SELECT jsonb_build_object('postgis_version',PostGIS_Full_Version(),
 'features',(SELECT jsonb_agg(f ORDER BY id) FROM features f),
 'navigation',(SELECT jsonb_agg(n ORDER BY id) FROM navigation n));
ROLLBACK;
