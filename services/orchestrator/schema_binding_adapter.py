import os
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from shared.observability.logger import get_logger
from shared.schemas.agent import DataBinding, ToolBinding

logger = get_logger("orchestrator.schema_binding_adapter")


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass
class BindingResult:
    data_bindings: List[DataBinding] = field(default_factory=list)
    tool_bindings: List[ToolBinding] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    inspected_relations: Dict[str, Any] = field(default_factory=dict)


def _load_yaml(path: Path) -> Dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}


class SchemaBindingAdapter:
    """Bind registry layer/tool names to the deployed DB schema.

    KG and dictionaries may propose candidates, but this adapter is the point
    where execution metadata is verified against registry entries and the
    actual database schema.
    """

    def __init__(self, connection=None) -> None:
        self.connection = connection
        self.layer_registry = _load_yaml(DATA_DIR / "spatial_layer_registry.yaml")
        self.traffic_layer_registry = _load_yaml(DATA_DIR / "traffic_layer_registry.yaml")
        self.time_series_registry = _load_yaml(DATA_DIR / "time_series_registry.yaml")
        self.tool_registry = _load_yaml(DATA_DIR / "tool_registry.yaml")
        self.template_registry = _load_yaml(DATA_DIR / "query_template_registry.yaml")

    def build_bindings(self, route_plan: Dict[str, Any], slots: Dict[str, Any]) -> BindingResult:
        result = BindingResult()
        analysis_type = route_plan.get("analysis_type") or slots.get("analysis_type")

        if analysis_type in {"selected_feature_lookup", "source_attribute_search"}:
            relation = 'projection.s101_feature_valid'
            inspected = self._inspect_relation(relation)
            result.inspected_relations[relation] = inspected
            columns = {column['name'] for column in inspected.get('columns', [])}
            if not inspected.get('exists') or not inspected.get('has_select') or not {'feature_instance_id', 'feature_type_name', 'attributes', 'geometry'} <= columns:
                result.blockers.append('BLOCKED_DATA: selected feature source schema unavailable')
            else:
                result.data_bindings.append(DataBinding(dataset_id=relation, relation=relation, srid=4326))
            tool = 'postgis.selected_feature_lookup' if analysis_type == 'selected_feature_lookup' else 'postgis.dwithin'
            self._bind_tool(tool, analysis_type, None, result)
        elif analysis_type in {"feature_search_by_radius", "feature_dwithin"}:
            if slots.get("target_layers") and not slots.get("target_features"):
                self._bind_spatial_layer_analysis("spatial_layer_overlay", slots, result)
            else:
                self._bind_feature_radius(route_plan, result)
        elif analysis_type in {"feature_within_area", "spatial_feature_search", "feature_search_by_area"}:
            self._bind_feature_area(route_plan, result)
        elif analysis_type in {"nearest_feature", "nearest_feature_search"}:
            self._bind_nearest_feature(route_plan, result)
        elif analysis_type in {"document_search", "rag.document_search", "graph_scoped_rag"}:
            self._bind_document_search(result)
        elif analysis_type in {"traffic_search_by_time_space", "dynamic_traffic_lookup"}:
            self._bind_dynamic_traffic(slots, result)
            self._bind_tool("traffic.dynamic_layer_search", "time_space_lookup", "traffic_search_by_time_space", result)
        elif analysis_type in {"observed_time_series_analysis", "time_series_observation_analysis"}:
            self._bind_time_series(slots, result)
            self._bind_tool("timeseries.observation_analyze", "time_series_metrics", "observed_time_series_analysis", result)
        elif analysis_type in {"observed_time_series_forecast", "time_series_forecast"}:
            self._bind_time_series(slots, result)
            self._bind_tool("timeseries.forecast", "forecast", "observed_time_series_forecast", result)
        elif analysis_type in {"accident_feature_relation", "accident_relation_lookup", "occurred_in_lookup"}:
            accident_binding = self.bind_accident_relation()
            result.data_bindings.extend(accident_binding.data_bindings)
            result.blockers.extend(accident_binding.blockers)
            result.warnings.extend(accident_binding.warnings)
            result.inspected_relations.update(accident_binding.inspected_relations)
            self._bind_tool("accident.s101_relation_lookup", "accident_relation_lookup", "accident_s101_relation_lookup", result)
        elif analysis_type == "accident_spatial_history_lookup":
            self._bind_accident_events(result)
            self._bind_tool("accident.spatial_history_lookup", "structured_accident_spatial_history_lookup", "accident_spatial_history_lookup", result)
        elif analysis_type in {
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
            self._bind_spatial_layer_analysis(analysis_type, slots, result)
        else:
            result.warnings.append(f"No deterministic binding rule for analysis_type={analysis_type}")

        return result

    def _bind_time_series(self, slots: Dict[str, Any], result: BindingResult) -> None:
        datasets = self.time_series_registry.get("datasets") or {}
        filters = slots.get("filters") if isinstance(slots.get("filters"), dict) else {}
        dataset_id = slots.get("dataset_id") or filters.get("dataset_id") or slots.get("target_dataset") or slots.get("target_term")
        source_path = slots.get("source_path") or filters.get("source_path")
        dataset = datasets.get(dataset_id) if dataset_id else None
        if not dataset and not source_path and len(datasets) == 1:
            dataset_id, dataset = next(iter(datasets.items()))
        if not dataset and not source_path:
            result.blockers.append("BLOCKED_DATA: time-series dataset_id or source_path is required")
            return
        if dataset and dataset.get("execution_status") == "fixture_only":
            result.blockers.append("BLOCKED_DATA: test fixture is not an operational time-series source")
            return
        if dataset and dataset.get("execution_status") in {"metadata_only", "needs_ingestion"} and not dataset.get("path"):
            result.blockers.append(
                f"BLOCKED_DATA: time-series dataset {dataset_id} is {dataset.get('execution_status')} and has no executable path"
            )
            return

        relation = source_path or (dataset or {}).get("path")
        if not relation:
            result.blockers.append(f"BLOCKED_CONFIG: invalid time-series source for dataset {dataset_id}")
            return

        root = Path(PROJECT_ROOT).resolve()
        try:
            path = (root / relation).resolve()
            path.relative_to(root)
        except (ValueError, OSError, RuntimeError):
            result.blockers.append("BLOCKED_POLICY: time-series source must stay under project root")
            return
        fixture_paths = {(root / row["path"]).resolve() for row in datasets.values()
                         if row.get("execution_status") == "fixture_only" and row.get("path")}
        if path in fixture_paths or path.is_relative_to(root / "data" / "fixtures"):
            result.blockers.append("BLOCKED_DATA: test fixture cannot be used through a source_path alias")
            return
        if not path.is_file():
            result.blockers.append("BLOCKED_DATA: time-series source file is unavailable")
            return
        if path.suffix.lower() not in {".csv", ".jsonl", ".ndjson"}:
            result.blockers.append("BLOCKED_CONFIG: unsupported time-series source format")
            return

        result.inspected_relations[relation] = {
            "exists": True,
            "kind": "file_time_series",
        }
        result.data_bindings.append(
            DataBinding(
                dataset_id=dataset_id or "ad_hoc_time_series",
                relation=relation,
                geometry_column=(dataset or {}).get("geometry_column", ""),
                srid=(dataset or {}).get("srid"),
                snapshot_version=str(self.time_series_registry.get("version", "")) or None,
                layer_type=(dataset or {}).get("layer_type", "time_series"),
                source_asset=(dataset or {}).get("source_asset") or relation,
                execution_status=(dataset or {}).get("execution_status", "executable"),
                read_only=True,
            )
        )

    def _bind_spatial_layer_analysis(self, analysis_type: str, slots: Dict[str, Any], result: BindingResult) -> None:
        default_layers = {
            "current_tidal_lookup": ["tidal_current_surface"],
            "eddy_hazard_lookup": ["eddy_hazard_area"],
            "hazard_area_lookup": [
                "eddy_hazard_area",
                "caution_warning_area",
                "speed_restriction_area",
                "entry_restricted_area",
                "anchoring_prohibited_area",
                "fishing_prohibited_area",
                "fishing_restricted_area",
                "dumping_ground_area",
            ],
            "protected_area_lookup": ["protected_sea_area"],
            "planned_port_overlay": ["planned_port_area"],
            "island_gazetteer_lookup": ["island_gazetteer"],
            "sea_parting_prediction_lookup": ["sea_parting_prediction"],
            "vessel_traffic_control_area_overlay": ["vessel_traffic_control_area"],
            "spatial_layer_overlay": [],
        }
        default_tools = {
            "current_tidal_lookup": ("ocean.current_tidal_lookup", "time_space_lookup", "current_tidal_lookup"),
            "eddy_hazard_lookup": ("hazard.eddy_lookup", "intersects", "eddy_hazard_lookup"),
            "hazard_area_lookup": ("hazard.area_lookup", "intersects", "hazard_area_lookup"),
            "protected_area_lookup": ("protected.area_lookup", "intersects", "protected_area_lookup"),
            "planned_port_overlay": ("development.planned_port_overlay", "intersects", "planned_port_overlay"),
            "island_gazetteer_lookup": ("place.island_gazetteer_lookup", "dwithin", "island_gazetteer_lookup"),
            "sea_parting_prediction_lookup": ("tide.sea_parting_lookup", "time_space_lookup", "sea_parting_prediction_lookup"),
            "vessel_traffic_control_area_overlay": ("traffic.control_area_overlay", "intersects", "vessel_traffic_control_area_overlay"),
            "spatial_layer_overlay": ("spatial.layer_overlay_lookup", "intersects", "spatial_layer_overlay_lookup"),
        }
        layers = list(slots.get("target_layers") or default_layers.get(analysis_type) or [])
        if not layers:
            result.blockers.append("NEEDS_USER_INPUT: target spatial layer is required")
        for layer_id in layers:
            self._bind_layer(layer_id, result)
        tool_id, operation, template_id = default_tools[analysis_type]
        self._bind_tool(tool_id, operation, template_id, result)

    def _bind_feature_radius(self, route_plan: Dict[str, Any], result: BindingResult) -> None:
        layer_id = route_plan.get("radius_layer_id") or "GBENC_S101_feature"
        template_id = route_plan.get("radius_template_id") or "feature_search_by_radius"
        self._bind_layer(layer_id, result)
        self._bind_tool("gbenc.s101_feature_search_by_radius", "feature_search_by_radius", template_id, result)
        self._bind_tool("postgis.dwithin", "ST_DWithin", template_id, result)

    def _bind_feature_area(self, route_plan: Dict[str, Any], result: BindingResult) -> None:
        self._bind_layer("GBENC_S101_feature", result)
        self._bind_tool("gbenc.s101_feature_search_by_radius", "feature_within_area", "feature_search_by_radius", result)

    def _bind_nearest_feature(self, route_plan: Dict[str, Any], result: BindingResult) -> None:
        self._bind_layer("GBENC_S101_feature", result)
        self._bind_tool("postgis.dwithin", "nearest_feature", "feature_search_by_radius", result)

    def _bind_document_search(self, result: BindingResult) -> None:
        self._bind_tool("rag.graph_scoped_retrieve", "document_search", "graph_scoped_rag", result)
        relation = "knowledge.document_chunks"
        info = self._inspect_relation(relation)
        result.inspected_relations[relation] = info
        columns = {item["name"] for item in info.get("columns", [])}
        required_columns = {"chunk_id", "source_id", "source_sha256", "content", "metadata", "embedding"}
        if not info.get("exists") or not info.get("has_select") or not required_columns <= columns:
            result.blockers.append("BLOCKED_DATA: document source schema or SELECT permission is unavailable")
        else:
            result.data_bindings.append(DataBinding(dataset_id=relation, relation=relation, geometry_column=""))

    def _bind_dynamic_traffic(self, slots: Dict[str, Any], result: BindingResult) -> None:
        layer_ids = list(slots.get("target_dynamic_layers") or slots.get("target_layers") or [])
        if not layer_ids:
            layer_ids = list((self.traffic_layer_registry.get("layers") or {}).keys())
        for layer_id in layer_ids:
            layer = (self.traffic_layer_registry.get("layers") or {}).get(layer_id)
            if not layer:
                result.blockers.append(f"BLOCKED_CONFIG: dynamic traffic layer not registered: {layer_id}")
                continue
            relation = layer.get("physical_table") or layer.get("expected_physical_table") or self.traffic_layer_registry.get("serving_relation")
            if not relation:
                result.blockers.append(f"BLOCKED_CONFIG: invalid relation for dynamic traffic layer {layer_id}")
                continue
            if layer.get("execution_status") == "needs_ingestion" and not layer.get("physical_table"):
                result.blockers.append(
                    f"BLOCKED_DATA: dynamic traffic layer {layer_id} is registered from {layer.get('source_path')} but not ingested into {relation}"
                )
                continue
            info = self._inspect_relation(relation)
            result.inspected_relations[relation] = info
            if not info.get("exists"):
                result.blockers.append(f"BLOCKED_CONFIG: relation not found: {relation}")
                continue
            columns = {col["name"]: col for col in info.get("columns", [])}
            if layer.get("layer_type") == "dynamic_traffic_tile" or layer.get("geometry_type") == "raster_tile":
                tile_path_column = layer.get("tile_path_column", "tile_path")
                for required_column in [
                    tile_path_column,
                    layer.get("zoom_column", "zoom_level"),
                    layer.get("tile_x_column", "tile_x"),
                    layer.get("tile_y_column", "tile_y"),
                ]:
                    if required_column not in columns:
                        result.blockers.append(f"BLOCKED_CONFIG: tile column not found: {relation}.{required_column}")
                        break
                else:
                    result.data_bindings.append(
                        DataBinding(
                            dataset_id=layer_id,
                            relation=relation,
                            geometry_column=tile_path_column,
                            srid=None,
                            snapshot_version=str(self.traffic_layer_registry.get("version", "")) or None,
                            layer_type="dynamic_traffic_tile",
                            source_asset=layer.get("source_path"),
                            execution_status=layer.get("execution_status"),
                            read_only=True,
                        )
                    )
                continue
            geometry_column = layer.get("geometry_column", "geom")
            if geometry_column not in columns:
                result.blockers.append(f"BLOCKED_CONFIG: geometry column not found: {relation}.{geometry_column}")
                continue
            result.data_bindings.append(
                DataBinding(
                    dataset_id=layer_id,
                    relation=relation,
                    geometry_column=geometry_column,
                    srid=4326,
                    snapshot_version=str(self.traffic_layer_registry.get("version", "")) or None,
                    layer_type="dynamic_traffic",
                    source_asset=layer.get("source_path"),
                    execution_status=layer.get("execution_status"),
                    read_only=True,
                )
            )

    def _bind_tool(self, tool_id: str, operation: str, template_id: Optional[str], result: BindingResult) -> None:
        tools = self.tool_registry.get("tools", {})
        templates = self.template_registry.get("templates", {})
        if tool_id not in tools:
            result.blockers.append(f"BLOCKED_CONFIG: tool not registered: {tool_id}")
            return
        if template_id and template_id not in templates:
            result.blockers.append(f"BLOCKED_CONFIG: query template not registered: {template_id}")
            return
        result.tool_bindings.append(
            ToolBinding(
                tool_id=tool_id,
                operation=operation,
                query_template_id=template_id,
                schema_version=str(self.tool_registry.get("version", "")) or None,
            )
        )

    def _bind_layer(self, layer_id: str, result: BindingResult) -> None:
        layer = self.layer_registry.get("layers", {}).get(layer_id)
        if not layer:
            result.blockers.append(f"BLOCKED_CONFIG: layer not registered: {layer_id}")
            return

        relation = layer.get("physical_table") or layer.get("expected_physical_table")
        geometry_column = layer.get("geometry_column", "geometry")
        code_column = layer.get("code_column")
        srid = layer.get("srid")
        execution_status = layer.get("execution_status")
        if not relation or "." not in relation:
            result.blockers.append(f"BLOCKED_CONFIG: invalid relation for layer {layer_id}")
            return
        if execution_status == "needs_ingestion" and not layer.get("physical_table"):
            source_ref = layer.get("source_asset") or layer.get("source_assets")
            result.blockers.append(
                f"BLOCKED_DATA: layer {layer_id} is registered from {source_ref} but not ingested into {relation}"
            )
            return
        if execution_status == "metadata_only":
            result.blockers.append(
                f"BLOCKED_DATA: layer {layer_id} has metadata table {layer.get('metadata_table')} but executable value geometry requires {layer.get('parser_status', 'parser completion')}"
            )
            return

        info = self._inspect_relation(relation)
        result.inspected_relations[relation] = info
        if not info.get("exists"):
            result.blockers.append(f"BLOCKED_CONFIG: relation not found: {relation}")
            return
        if info.get("has_select") is False:
            result.blockers.append(f"BLOCKED_POLICY: SELECT access denied: {relation}")
            return

        columns = {col["name"]: col for col in info.get("columns", [])}
        if geometry_column not in columns:
            result.blockers.append(f"BLOCKED_CONFIG: geometry column not found: {relation}.{geometry_column}")
            return
        if code_column and code_column not in columns:
            result.blockers.append(f"BLOCKED_CONFIG: code column not found: {relation}.{code_column}")
            return

        result.data_bindings.append(
                DataBinding(
                    dataset_id=layer_id,
                    relation=relation,
                    geometry_column=geometry_column,
                    srid=srid,
                    snapshot_version=str(self.layer_registry.get("version", "")) or None,
                    layer_type=layer.get("layer_type"),
                    source_asset=layer.get("source_asset") or ",".join(layer.get("source_assets") or []),
                    execution_status=execution_status,
                    read_only=True,
                )
            )

    def bind_accident_relation(self) -> BindingResult:
        result = BindingResult()
        layer = self.layer_registry.get("layers", {}).get("accident_s101_relation", {})
        relation = layer.get("physical_table") or "serving.accident_s101_relation_current"
        info = self._inspect_relation(relation)
        result.inspected_relations[relation] = info
        if not info.get("exists"):
            result.blockers.append(f"BLOCKED_CONFIG: relation not found: {relation}")
            return result

        columns = {col["name"]: col for col in info.get("columns", [])}
        for col in ("accident_geometry", "anchor_geometry", "distance_meters", "feature_instance_id", "event_id"):
            if col not in columns:
                result.blockers.append(f"BLOCKED_CONFIG: required column not found: {relation}.{col}")
        if not result.blockers:
            result.data_bindings.append(
                DataBinding(
                    dataset_id="accident_s101_relation",
                    relation=relation,
                    geometry_column="accident_geometry",
                    distance_column="distance_meters",
                    srid=4326,
                    snapshot_version="current",
                    layer_type=layer.get("layer_type", "accident_relation"),
                    execution_status=layer.get("execution_status", "executable"),
                    read_only=True,
                )
            )
        return result

    def _bind_accident_events(self, result: BindingResult) -> None:
        layer = self.layer_registry.get("layers", {}).get("accident_events", {})
        relation = layer.get("physical_table") or "serving.accident_events"
        geometry_column = layer.get("geometry_column", "geom")
        info = self._inspect_relation(relation)
        result.inspected_relations[relation] = info
        if not info.get("exists"):
            result.blockers.append(f"BLOCKED_CONFIG: relation not found: {relation}")
            return
        columns = {col["name"]: col for col in info.get("columns", [])}
        for col in (geometry_column, "event_id", "occurred_at", "authority", "cause", "accident_type"):
            if col not in columns:
                result.blockers.append(f"BLOCKED_CONFIG: required column not found: {relation}.{col}")
        if not result.blockers:
            result.data_bindings.append(
                DataBinding(
                    dataset_id="accident_events",
                    relation=relation,
                    geometry_column=geometry_column,
                    distance_column="distance_m",
                    srid=4326,
                    snapshot_version="current",
                    layer_type=layer.get("layer_type", "accident_event"),
                    execution_status=layer.get("execution_status", "executable"),
                    read_only=True,
                )
            )

    def _inspect_relation(self, relation: str) -> Dict[str, Any]:
        url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
        if not url and self.connection is None:
            return {"exists": False, "error": "S101_DB_URL or POSTGIS_URL is not configured"}

        schema, table = relation.split(".", 1)
        try:
            import psycopg2

            connection = nullcontext(self.connection) if self.connection is not None else psycopg2.connect(url, connect_timeout=3)
            with connection as conn:
                if self.connection is None:
                    conn.set_session(readonly=True)
                with conn.cursor() as cur:
                    cur.execute("SELECT set_config('statement_timeout', '5000', true)")
                    cur.execute("select to_regclass(%s)", (relation,))
                    exists = bool(cur.fetchone()[0])
                    columns: List[Dict[str, str]] = []
                    count = None
                    if exists:
                        cur.execute(
                            """
                            select a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod)
                            from pg_attribute a
                            join pg_class c on a.attrelid = c.oid
                            join pg_namespace n on c.relnamespace = n.oid
                            where n.nspname = %s
                              and c.relname = %s
                              and a.attnum > 0
                              and not a.attisdropped
                            order by a.attnum
                            """,
                            (schema, table),
                        )
                        columns = [{"name": row[0], "type": row[1]} for row in cur.fetchall()]
                    cur.execute("select has_table_privilege(to_regclass(%s), 'SELECT')", (relation,))
                    has_select = bool(cur.fetchone()[0])
                    return {"exists": exists, "columns": columns, "count": count, "has_select": has_select}
        except Exception as exc:
            logger.warning("Schema inspection failed", relation=relation, error=str(exc))
            return {"exists": False, "error": f"{type(exc).__name__}: {exc}"}


schema_binding_adapter = SchemaBindingAdapter()
