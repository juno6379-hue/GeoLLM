from enum import Enum
from typing import Any, Dict

from shared.observability.logger import get_logger

logger = get_logger("spatial_analysis_agent.sql_compiler")


class SQLTemplateName(str, Enum):
    FEATURE_DWITHIN = "feature_dwithin"
    FEATURE_WITHIN_AREA = "feature_within_area"
    NEAREST_FEATURE = "nearest_feature"
    SPATIAL_LAYER_LOOKUP = "spatial_layer_lookup"


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
WHERE ((:has_nftc_codes AND f.feature_type_code = ANY(:nftc_codes))
       OR (:has_feature_names AND f.feature_type_name = ANY(:feature_names)))
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
WHERE ((:has_nftc_codes AND f.feature_type_code = ANY(:nftc_codes))
       OR (:has_feature_names AND f.feature_type_name = ANY(:feature_names)))
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
WHERE ((:has_nftc_codes AND f.feature_type_code = ANY(:nftc_codes))
       OR (:has_feature_names AND f.feature_type_name = ANY(:feature_names)))
  AND f.geometry IS NOT NULL
ORDER BY ST_SetSRID(f.geometry, 4326) <-> ST_SetSRID(l.reference_point, 4326)
LIMIT :result_limit;
""",
        }

    @staticmethod
    def _expand_feature_names(feature_names: list[str]) -> list[str]:
        aliases = {
            "BuoyIsolatedDanger": ["IsolatedDangerBuoy"],
            "BeaconIsolatedDanger": ["IsolatedDangerBeacon"],
            "BuoyCardinal": ["CardinalBuoy"],
            "BeaconCardinal": ["CardinalBeacon"],
            "BuoyLateral": ["LateralBuoy"],
            "BeaconLateral": ["LateralBeacon"],
            "BuoySpecialPurpose": ["SpecialPurposeBuoy", "SpecialPurposeGeneralBuoy"],
            "BeaconSpecialPurpose": ["SpecialPurposeBeacon", "SpecialPurposeGeneralBeacon"],
        }
        expanded = []
        for name in feature_names:
            if not name:
                continue
            expanded.append(str(name))
            expanded.extend(aliases.get(str(name), []))
        return list(dict.fromkeys(expanded))

    @staticmethod
    def _safe_relation(relation: str) -> str:
        parts = relation.split(".")
        if len(parts) != 2 or not all(part.replace("_", "").isalnum() for part in parts):
            raise ValueError(f"Unsafe relation name: {relation}")
        return ".".join(parts)

    @staticmethod
    def _safe_column(column: str) -> str:
        if not column or not column.replace("_", "").isalnum():
            raise ValueError(f"Unsafe column name: {column}")
        return column

    def _compile_spatial_layer_lookup(self, query_plan: Dict[str, Any]) -> Dict[str, Any]:
        base_geometry = query_plan.get("base_geometry")
        distance_m = query_plan.get("spatial", {}).get("distance_m")
        result_limit = int(query_plan.get("output", {}).get("limit", 100))
        qec = query_plan.get("conditions", {}).get("_query_execution_context", {}) or {}
        bindings = qec.get("data_bindings") or []
        if not base_geometry:
            return {"error": "Missing base_geometry"}
        if not bindings:
            return {"error": "No validated data bindings for spatial layer lookup"}

        selects = []
        layer_ids = []
        for idx, binding in enumerate(bindings):
            relation = self._safe_relation(binding.get("relation", ""))
            geom_col = self._safe_column(binding.get("geometry_column") or "geometry")
            dataset_id = binding.get("dataset_id") or f"layer_{idx}"
            layer_ids.append(dataset_id)
            predicate = (
                f"ST_DWithin(ST_SetSRID(t.{geom_col}, 4326)::geography, "
                "ST_SetSRID(l.reference_point, 4326)::geography, :distance_m)"
                if distance_m is not None
                else f"t.{geom_col} && l.geom AND ST_Intersects(t.{geom_col}, l.geom)"
            )
            selects.append(
                f"""
SELECT
  t.source_id AS id,
  t.layer_id AS layer_id,
  COALESCE(NULLIF(t.name, ''), t.layer_id) AS feature_name,
  GeometryType(t.{geom_col}) AS geometry_type,
  ST_AsGeoJSON(t.{geom_col}) AS geojson,
  CASE
    WHEN :has_distance THEN ST_Distance(ST_SetSRID(t.{geom_col}, 4326)::geography, ST_SetSRID(l.reference_point, 4326)::geography)
    ELSE NULL
  END AS distance_m,
  t.properties AS attr,
  t.provenance AS source_provenance
FROM {relation} AS t
CROSS JOIN location AS l
WHERE t.layer_id = :layer_id_{idx}
  AND t.{geom_col} IS NOT NULL
  AND {predicate}
"""
            )

        location_cte = """
WITH location AS (
    SELECT ST_GeomFromText(:base_geometry, 4326) AS geom,
           ST_Centroid(ST_GeomFromText(:base_geometry, 4326)) AS reference_point
)
"""
        sql = location_cte.strip() + "\n" + "\nUNION ALL\n".join(selects) + "\nORDER BY distance_m NULLS LAST, layer_id, id\nLIMIT :result_limit;"
        params = {
            "base_geometry": base_geometry,
            "distance_m": float(distance_m or 0),
            "has_distance": distance_m is not None,
            "result_limit": result_limit,
        }
        for idx, layer_id in enumerate(layer_ids):
            params[f"layer_id_{idx}"] = layer_id
        return {
            "sql": sql,
            "params": params,
            "template_id": SQLTemplateName.SPATIAL_LAYER_LOOKUP,
            "db_route": "gbenc",
        }

    def compile(self, query_plan: Dict[str, Any]) -> Dict[str, Any]:
        analysis_type = query_plan.get("analysis_type")
        nftc_codes = query_plan.get("target", {}).get("nftc_codes", [])
        feature_names = query_plan.get("target", {}).get("feature_names", [])
        place_id = query_plan.get("location", {}).get("place_id")
        distance_m = query_plan.get("spatial", {}).get("distance_m")
        result_limit = query_plan.get("output", {}).get("limit", 100)
        base_geometry = query_plan.get("base_geometry")

        if not place_id and not base_geometry:
            return {"error": "Missing place_id or base_geometry"}
        if place_id:
            return {"error": "place_id requires geometry resolution before SQL compilation"}
        if analysis_type in {
            "spatial_layer_overlay",
            "current_tidal_lookup",
            "eddy_hazard_lookup",
            "hazard_area_lookup",
            "protected_area_lookup",
            "planned_port_overlay",
            "island_gazetteer_lookup",
            "sea_parting_prediction_lookup",
            "vessel_traffic_control_area_overlay",
        }:
            return self._compile_spatial_layer_lookup(query_plan)
        valid_codes = [int(code) for code in nftc_codes if int(code) > 0]
        valid_names = self._expand_feature_names([str(name) for name in feature_names if str(name).strip()])
        if not valid_codes and not valid_names:
            return {"error": "Resolved nftc_codes or feature_names are required"}

        if analysis_type in ("feature_dwithin", "feature_search_by_radius"):
            template_id = SQLTemplateName.FEATURE_DWITHIN
            if distance_m is None:
                return {"error": "distance_m is required for feature_dwithin"}
        elif analysis_type == "feature_within_area":
            template_id = SQLTemplateName.FEATURE_WITHIN_AREA
        elif analysis_type == "nearest_feature":
            template_id = SQLTemplateName.NEAREST_FEATURE
        else:
            return {"error": f"Unsupported analysis_type: {analysis_type}"}

        params = {
            "nftc_codes": valid_codes or [-1],
            "feature_names": valid_names,
            "has_nftc_codes": bool(valid_codes),
            "has_feature_names": bool(valid_names),
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
            "db_route": "gbenc",
        }


compiler = SQLTemplateCompiler()
