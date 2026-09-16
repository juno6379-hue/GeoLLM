from shared.schemas.agent import ExecutionSlots, PlanStatus, QueryExecutionContext
from services.orchestrator.execution_validator import validate_execution_context
from services.orchestrator.schema_binding_adapter import SchemaBindingAdapter


def _fake_relation_info(relation):
    if relation == "projection.s101_feature_current":
        return {
            "exists": True,
            "count": 10,
            "columns": [
                {"name": "feature_instance_id", "type": "bigint"},
                {"name": "feature_type_code", "type": "integer"},
                {"name": "feature_type_name", "type": "text"},
                {"name": "geometry", "type": "geometry"},
            ],
        }
    if relation == "serving.accident_s101_relation_current":
        return {
            "exists": True,
            "count": 23,
            "columns": [
                {"name": "event_id", "type": "text"},
                {"name": "feature_instance_id", "type": "bigint"},
                {"name": "accident_geometry", "type": "geometry(Point,4326)"},
                {"name": "anchor_geometry", "type": "geometry(Point,4326)"},
                {"name": "distance_meters", "type": "numeric"},
            ],
        }
    if relation in {
        "serving.planned_port_area_current",
        "serving.eddy_hazard_area_current",
        "serving.island_gazetteer_current",
        "serving.vessel_traffic_control_area_current",
        "serving.hazard_area_current",
        "serving.protected_area_current",
    }:
        return {
            "exists": True,
            "count": 1,
            "columns": [
                {"name": "source_id", "type": "text"},
                {"name": "layer_id", "type": "text"},
                {"name": "source_asset", "type": "text"},
                {"name": "source_member", "type": "text"},
                {"name": "name", "type": "text"},
                {"name": "native_srid", "type": "integer"},
                {"name": "properties", "type": "jsonb"},
                {"name": "provenance", "type": "jsonb"},
                {"name": "geometry", "type": "geometry(Geometry,4326)"},
            ],
        }
    if relation == "serving.dynamic_traffic_layer":
        return {
            "exists": True,
            "count": 17472,
            "columns": [
                {"name": "source_id", "type": "text"},
                {"name": "observed_at", "type": "timestamp with time zone"},
                {"name": "observed_month", "type": "date"},
                {"name": "layer_id", "type": "text"},
                {"name": "layer_source", "type": "text"},
                {"name": "grid_id", "type": "text"},
                {"name": "grid_level", "type": "integer"},
                {"name": "vessel_count_total", "type": "integer"},
                {"name": "geom", "type": "geometry(Geometry,4326)"},
            ],
        }
    if relation == "serving.dynamic_traffic_tile_layer":
        return {
            "exists": True,
            "count": 720174,
            "columns": [
                {"name": "source_id", "type": "text"},
                {"name": "observed_at", "type": "timestamp with time zone"},
                {"name": "observed_month", "type": "date"},
                {"name": "layer_id", "type": "text"},
                {"name": "layer_source", "type": "text"},
                {"name": "zoom_level", "type": "integer"},
                {"name": "tile_x", "type": "integer"},
                {"name": "tile_y", "type": "integer"},
                {"name": "tile_path", "type": "text"},
            ],
        }
    return {"exists": False, "columns": [], "count": None}


def test_schema_binding_adapter_builds_radius_bindings(monkeypatch):
    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)

    result = adapter.build_bindings(
        {"analysis_type": "feature_search_by_radius"},
        {"location_text": "부산항", "distance_m": 3000, "target_features": ["Wreck"]},
    )

    assert not result.blockers
    assert result.data_bindings[0].relation == "projection.s101_feature_current"
    assert result.data_bindings[0].geometry_column == "geometry"
    assert {binding.tool_id for binding in result.tool_bindings} >= {
        "gbenc.s101_feature_search_by_radius",
        "postgis.dwithin",
    }


def test_execution_validator_blocks_unresolved_geometry(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "feature_search_by_radius"},
        slots=ExecutionSlots(location_text="부산항", distance_m=3000, target_features=["Wreck"]),
        spatial={"spatial_context": {"base_location": "부산항", "geometry": None}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.NEEDS_USER_INPUT
    assert "NEEDS_USER_INPUT: reference geometry is unresolved" in validated.blockers


def test_execution_validator_marks_ready_with_bindings(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "feature_search_by_radius"},
        slots=ExecutionSlots(
            location_text="부산항",
            reference_geometry="POINT(129.05 35.1)",
            distance_m=3000,
            target_features=["Wreck"],
        ),
        spatial={"spatial_context": {"base_location": "부산항", "geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert validated.data_bindings
    assert validated.tool_bindings


def test_area_search_does_not_require_distance(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "feature_within_area"},
        slots=ExecutionSlots(
            location_text="부산항",
            reference_geometry="POLYGON((129 35,129.1 35,129.1 35.1,129 35.1,129 35))",
            target_features=["Wreck"],
        ),
        spatial={"spatial_context": {"geometry": "POLYGON((129 35,129.1 35,129.1 35.1,129 35.1,129 35))"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert "NEEDS_USER_INPUT: distance_m is required" not in validated.blockers


def test_nearest_search_validates_k(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "nearest_feature"},
        slots=ExecutionSlots(
            reference_geometry="POINT(129.05 35.1)",
            target_features=["AnchorageArea"],
            filters={"k": 101},
        ),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.BLOCKED_POLICY
    assert "BLOCKED_POLICY: nearest k exceeds max 100" in validated.blockers


def test_document_search_does_not_require_spatial_slots(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)
    monkeypatch.setenv("OLLAMA_EMBEDDING_URL", "http://localhost:11434/api/embed")
    monkeypatch.setenv("EMBEDDING_MODEL", "bge-m3")

    qec = QueryExecutionContext(
        original_query="S-101 2.0에서 Wreck 정의를 설명해줘",
        normalized_query="S-101 2.0 Wreck 정의",
        route_plan={"analysis_type": "document_search", "primary_agent": "Standard RAG Agent"},
        slots=ExecutionSlots(),
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not any("geometry" in blocker for blocker in validated.blockers)
    assert validated.tool_bindings[0].tool_id == "rag.graph_scoped_retrieve"


def test_accident_relation_requires_feature_instance(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "accident_relation_lookup"},
        slots=ExecutionSlots(),
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.NEEDS_USER_INPUT
    assert "NEEDS_USER_INPUT: feature_instance_id is required for accident relation lookup" in validated.blockers


def test_accident_relation_ready_with_feature_instance(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "accident_relation_lookup"},
        slots=ExecutionSlots(feature_instance_id=123),
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert validated.data_bindings[0].relation == "serving.accident_s101_relation_current"
    assert validated.data_bindings[0].distance_column == "distance_meters"
    assert validated.tool_bindings[0].tool_id == "accident.s101_relation_lookup"


def test_tidal_current_layer_blocks_until_ingested(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "current_tidal_lookup"},
        slots=ExecutionSlots(
            reference_geometry="POINT(129.05 35.1)",
            target_layers=["tidal_current_surface"],
        ),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.BLOCKED_DATA
    assert any("tidal_current_surface" in blocker for blocker in validated.blockers)
    assert validated.tool_bindings[0].tool_id == "ocean.current_tidal_lookup"


def test_tidal_current_metadata_only_still_blocks_value_lookup(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    adapter.layer_registry["layers"]["tidal_current_surface"]["execution_status"] = "metadata_only"
    adapter.layer_registry["layers"]["tidal_current_surface"]["metadata_table"] = "serving.tidal_current_surface_metadata"
    adapter.layer_registry["layers"]["tidal_current_surface"]["parser_status"] = "NEEDS_BINARY_GRID_SPEC"
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "current_tidal_lookup"},
        slots=ExecutionSlots(reference_geometry="POINT(129.05 35.1)"),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.BLOCKED_DATA
    assert any("metadata table" in blocker for blocker in validated.blockers)


def test_planned_port_layer_ready_after_ingestion(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "planned_port_overlay"},
        slots=ExecutionSlots(reference_geometry="POINT(129.05 35.1)"),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert validated.data_bindings[0].relation == "serving.planned_port_area_current"
    assert validated.tool_bindings[0].tool_id == "development.planned_port_overlay"


def test_island_gazetteer_ready_after_ingestion(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "island_gazetteer_lookup"},
        slots=ExecutionSlots(reference_geometry="POINT(129.05 35.1)"),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert validated.data_bindings[0].relation == "serving.island_gazetteer_current"
    assert validated.tool_bindings[0].tool_id == "place.island_gazetteer_lookup"


def test_eddy_hazard_layer_ready_after_ingestion(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "eddy_hazard_lookup"},
        slots=ExecutionSlots(reference_geometry="POINT(129.05 35.1)"),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert validated.data_bindings[0].relation == "serving.eddy_hazard_area_current"
    assert validated.tool_bindings[0].tool_id == "hazard.eddy_lookup"


def test_vessel_traffic_control_area_ready_after_ingestion(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "vessel_traffic_control_area_overlay"},
        slots=ExecutionSlots(reference_geometry="POINT(129.05 35.1)"),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert validated.data_bindings[0].relation == "serving.vessel_traffic_control_area_current"
    assert validated.tool_bindings[0].tool_id == "traffic.control_area_overlay"


def test_hazard_area_lookup_ready_after_ingestion(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "hazard_area_lookup"},
        slots=ExecutionSlots(reference_geometry="POINT(126.7 37.3)", distance_m=50000),
        spatial={"spatial_context": {"geometry": "POINT(126.7 37.3)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert "serving.hazard_area_current" in {binding.relation for binding in validated.data_bindings}
    assert validated.tool_bindings[0].tool_id == "hazard.area_lookup"


def test_protected_area_lookup_ready_after_ingestion(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "protected_area_lookup"},
        slots=ExecutionSlots(reference_geometry="POINT(126.7 37.3)", distance_m=50000),
        spatial={"spatial_context": {"geometry": "POINT(126.7 37.3)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert validated.data_bindings[0].relation == "serving.protected_area_current"
    assert validated.tool_bindings[0].tool_id == "protected.area_lookup"


def test_sea_parting_blocks_until_ingested(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "sea_parting_prediction_lookup"},
        slots=ExecutionSlots(reference_geometry="POINT(126.6 37.1)"),
        spatial={"spatial_context": {"geometry": "POINT(126.6 37.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.BLOCKED_DATA
    assert any("sea_parting_prediction" in blocker for blocker in validated.blockers)
    assert validated.tool_bindings[0].tool_id == "tide.sea_parting_lookup"


def test_dynamic_traffic_ready_after_ingestion(monkeypatch):
    from services.orchestrator import execution_validator

    adapter = SchemaBindingAdapter()
    monkeypatch.setattr(adapter, "_inspect_relation", _fake_relation_info)
    monkeypatch.setattr(execution_validator, "schema_binding_adapter", adapter)

    qec = QueryExecutionContext(
        route_plan={"analysis_type": "traffic_search_by_time_space"},
        slots=ExecutionSlots(
            reference_geometry="POINT(129.05 35.1)",
            target_dynamic_layers=["ais_route_analysis"],
        ),
        spatial={"spatial_context": {"geometry": "POINT(129.05 35.1)"}},
    )

    validated = validate_execution_context(qec)

    assert validated.readiness == PlanStatus.EXECUTION_READY
    assert not validated.blockers
    assert validated.data_bindings[0].relation == "serving.dynamic_traffic_layer"
    assert validated.tool_bindings[0].tool_id == "traffic.dynamic_layer_search"
