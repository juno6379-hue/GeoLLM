from enum import Enum
from typing import Any, Dict

from shared.observability.logger import get_logger

logger = get_logger("spatial_analysis_agent.sql_compiler")


class SQLTemplateName(str, Enum):
    FEATURE_DWITHIN = "feature_dwithin"
    FEATURE_WITHIN_AREA = "feature_within_area"
    NEAREST_FEATURE = "nearest_feature"


class SQLTemplateCompiler:
    """Compile spatial queries against the deployed GBENC physical schema."""

    def __init__(self):
        self.templates = {
            SQLTemplateName.FEATURE_DWITHIN: """
SELECT f.feature_instance_id AS id, f.feature_type_code AS nftc_code,
       'NFTC:' || f.feature_type_code::text AS feature_name,
       GeometryType(f.geometry) AS geometry_type,
       ST_AsGeoJSON(f.geometry) AS geojson,
       ST_Distance(ST_SetSRID(f.geometry, 4326)::geography,
                   ST_SetSRID(l.reference_point, 4326)::geography) AS distance_m,
       f.attributes AS attr
FROM projection.s101_feature_current AS f
CROSS JOIN location AS l
WHERE f.feature_type_code = ANY(:nftc_codes)
  AND f.geometry IS NOT NULL
  AND ST_DWithin(ST_SetSRID(f.geometry, 4326)::geography,
                 ST_SetSRID(l.reference_point, 4326)::geography, :distance_m)
ORDER BY distance_m, f.feature_instance_id
LIMIT :result_limit;
""",
            SQLTemplateName.FEATURE_WITHIN_AREA: """
SELECT f.feature_instance_id AS id, f.feature_type_code AS nftc_code,
       'NFTC:' || f.feature_type_code::text AS feature_name,
       GeometryType(f.geometry) AS geometry_type,
       ST_AsGeoJSON(f.geometry) AS geojson,
       f.attributes AS attr
FROM projection.s101_feature_current AS f
CROSS JOIN location AS l
WHERE f.feature_type_code = ANY(:nftc_codes)
  AND f.geometry IS NOT NULL
  AND f.geometry && l.geom AND ST_Intersects(f.geometry, l.geom)
ORDER BY f.feature_instance_id
LIMIT :result_limit;
""",
            SQLTemplateName.NEAREST_FEATURE: """
SELECT f.feature_instance_id AS id, f.feature_type_code AS nftc_code,
       'NFTC:' || f.feature_type_code::text AS feature_name,
       GeometryType(f.geometry) AS geometry_type,
       ST_AsGeoJSON(f.geometry) AS geojson,
       ST_Distance(ST_SetSRID(f.geometry, 4326)::geography,
                   ST_SetSRID(l.reference_point, 4326)::geography) AS distance_m
FROM projection.s101_feature_current AS f
CROSS JOIN location AS l
WHERE f.feature_type_code = ANY(:nftc_codes)
  AND f.geometry IS NOT NULL
ORDER BY ST_SetSRID(f.geometry, 4326) <-> ST_SetSRID(l.reference_point, 4326)
LIMIT :result_limit;
""",
        }

    def compile(self, query_plan: Dict[str, Any]) -> Dict[str, Any]:
        analysis_type = query_plan.get("analysis_type")
        nftc_codes = query_plan.get("target", {}).get("nftc_codes", [])
        place_id = query_plan.get("location", {}).get("place_id")
        distance_m = query_plan.get("spatial", {}).get("distance_m", 1000)
        result_limit = query_plan.get("output", {}).get("limit", 100)
        base_geometry = query_plan.get("base_geometry")

        if not place_id and not base_geometry:
            return {"error": "Missing place_id or base_geometry"}
        if place_id:
            return {"error": "place_id requires geometry resolution before SQL compilation"}
        if not nftc_codes or any(int(code) <= 0 for code in nftc_codes):
            return {"error": "Resolved positive nftc_codes are required"}

        if analysis_type in ("feature_dwithin", "feature_search_by_radius"):
            template_id = SQLTemplateName.FEATURE_DWITHIN
        elif analysis_type == "feature_within_area":
            template_id = SQLTemplateName.FEATURE_WITHIN_AREA
        elif analysis_type == "nearest_feature":
            template_id = SQLTemplateName.NEAREST_FEATURE
        else:
            return {"error": f"Unsupported analysis_type: {analysis_type}"}

        params = {
            "nftc_codes": [int(code) for code in nftc_codes],
            "result_limit": int(result_limit),
            "base_geometry": base_geometry,
            "distance_m": float(distance_m),
        }
        location_cte = """
WITH location AS (
    SELECT ST_GeomFromText(:base_geometry, 4326) AS geom,
           ST_GeomFromText(:base_geometry, 4326) AS reference_point
)
"""
        return {
            "sql": location_cte.strip() + "\n" + self.templates[template_id].strip(),
            "params": params,
            "template_id": template_id,
        }


compiler = SQLTemplateCompiler()
