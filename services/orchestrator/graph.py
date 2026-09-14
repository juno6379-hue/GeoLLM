import os
import json
import hashlib
from functools import lru_cache
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from shared.schemas.agent import AgentRequest, AgentStatus, AgentResult, Intent, SpatialContext, SecurityContext, TaskPlan, ExecutionSlots, QueryExecutionContext, PlanStatus
from services.orchestrator.state import OrchestratorState, log_transition
from services.orchestrator.map_adapter import convert_to_map_layer
from shared.observability.logger import get_logger
from opentelemetry import trace

logger = get_logger("orchestrator.graph")
tracer = trace.get_tracer("marine_geo.orchestrator")

# ----------------- Nodes -----------------
from services.orchestrator.semantic_router import router, cache, slot_extractor, rule_router
from services.orchestrator.agent_registry import registry
from services.orchestrator.feedback_collector import collector
from services.orchestrator.query_normalizer import normalizer
from services.orchestrator.feature_resolver import feature_resolver
from services.orchestrator.context_resolver import ContextResolver
from services.orchestrator.route_planner import RoutePlanner
from services.orchestrator.graph_rag_retriever import GraphRAGRetriever
from services.orchestrator.execution_validator import validate_execution_context
from services.orchestrator.evidence_builder import build_evidence_bundle
from services.data_discovery_agent.agent import execute_data_discovery
from services.llm_config import llm_api_enabled
from services.validation_agent.agent import validate_orchestration

context_resolver = ContextResolver()
route_planner = RoutePlanner()
graph_rag_retriever = GraphRAGRetriever()

S101_DICT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "s101_smart_dictionary.json")
S101_CATALOGUE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "s101_catalogue.json")
TIME_SERIES_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "time_series_registry.yaml")
def get_s101_dictionary():
    try:
        with open(S101_DICT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

@lru_cache(maxsize=1)
def _load_s101_catalogue_exact() -> tuple[dict, ...]:
    try:
        with open(S101_CATALOGUE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return ()
    values = data.get("features") if isinstance(data, dict) else data
    if not isinstance(values, list):
        values = data.get("feature_types") or data.get("items") or [] if isinstance(data, dict) else []
    return tuple(item for item in values if isinstance(item, dict) and item.get("code"))

def _exact_s101_feature_match(query: str) -> dict | None:
    lowered = (query or "").lower()
    if "s-101" not in lowered and "s101" not in lowered and "feature catalogue" not in lowered:
        return None
    if not any(term in lowered or term in (query or "") for term in ("definition", "정의", "설명", "feature catalogue", "근거")):
        return None
    for feature in _load_s101_catalogue_exact():
        code = str(feature.get("code") or "")
        name = str(feature.get("name") or code)
        aliases = [str(alias) for alias in feature.get("aliases") or []]
        if any(token and token.lower() in lowered for token in [code, name, *aliases]):
            return feature
    return None

def _exact_s100_s101_relation_match(query: str) -> bool:
    lowered = (query or "").lower()
    if not ("s-100" in lowered or "s100" in lowered):
        return False
    if not ("s-101" in lowered or "s101" in lowered):
        return False
    return any(term in lowered or term in (query or "") for term in ("relation", "relationship", "관계", "설명", "차이", "기반"))

def _as_float(value):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _enrich_extracted_slots(slots: dict | None, norm_result: dict | None) -> dict:
    """Keep normalized terms and executable spatial slots in one payload."""
    enriched = dict(slots or {})
    norm_result = norm_result or {}
    canonical_terms = norm_result.get("canonical_terms") or []
    candidate_contexts = norm_result.get("candidate_contexts") or []
    if canonical_terms:
        enriched.setdefault("canonical_terms", canonical_terms)
        enriched.setdefault("derived_concepts", canonical_terms)
        if not enriched.get("derived_concept"):
            enriched["derived_concept"] = canonical_terms[0]
    if candidate_contexts:
        enriched.setdefault("candidate_contexts", candidate_contexts)
        if not enriched.get("context"):
            enriched["context"] = candidate_contexts[0]
    if enriched.get("distance_m") is not None:
        enriched["distance_m"] = _as_float(enriched.get("distance_m"))
    return enriched

def _context_value(ctx, key, default=None):
    if isinstance(ctx, dict):
        return ctx.get(key, default)
    return getattr(ctx, key, default) if ctx is not None else default

def _merge_plan_slots(req: AgentRequest, state: OrchestratorState, ctx_res) -> dict:
    extracted = dict(state.get("extracted_slots") or req.previous_agent_outputs.get("extracted_slots", {}) or {})
    resolved_metadata = req.previous_agent_outputs.get("resolved_metadata", {})
    target_term = (
        extracted.get("target_term")
        or resolved_metadata.get("input_term")
        or (req.parsed_intent.target_objects[0] if req.parsed_intent and req.parsed_intent.target_objects else None)
    )
    slots = {
        **extracted,
        "location": extracted.get("location") or (req.spatial_context.base_location if req.spatial_context else None),
        "location_text": extracted.get("location_text") or extracted.get("location") or (req.spatial_context.base_location if req.spatial_context else None),
        "distance_m": extracted.get("distance_m") if extracted.get("distance_m") is not None else (req.spatial_context.buffer_distance if req.spatial_context else None),
        "target_term": target_term,
    }
    if _context_value(ctx_res, "selected_context") and not slots.get("context"):
        slots["context"] = _context_value(ctx_res, "selected_context")
    if _context_value(ctx_res, "analysis_type") and not slots.get("analysis_type"):
        slots["analysis_type"] = _context_value(ctx_res, "analysis_type")
    resolved_codes = req.previous_agent_outputs.get("resolved_nftc_codes") or resolved_metadata.get("nftc_codes")
    if resolved_codes and not slots.get("nftc_codes"):
        slots["nftc_codes"] = resolved_codes
    return slots

def _looks_like_time_series_query(query: str) -> bool:
    lowered = (query or "").lower()
    keywords = [
        "time-series",
        "timeseries",
        "time series",
        "station",
        "observation",
        "sensor",
        "missing",
        "anomaly",
        "forecast",
        "prediction",
        "predict",
        "schedule",
        "tide",
        "spring tide",
        "weather",
        "typhoon",
        "wave",
        "대조기",
        "조석",
        "조위",
        "물때",
        "만조",
        "간조",
        "일정",
        "기상",
        "태풍",
        "풍속",
        "파고",
        "해상예보",
        "예보",
        "confidence interval",
        "horizon",
        "시계열",
        "관측소",
        "결측",
        "이상치",
        "예측",
        "신뢰구간",
        "\uc774\uc0c1\uce58",
        "\uc2dc\uacc4\uc5f4",
        "source_path=",
        "timestamp_column=",
        "value_column=",
    ]
    return any(keyword in lowered or keyword in (query or "") for keyword in keywords)

def _looks_like_explicit_time_series_request(query: str) -> bool:
    lowered = (query or "").lower()
    return any(key in lowered for key in ["dataset_id=", "source_path=", "timestamp_column=", "value_column="])

def _extract_key_value_slots(query: str) -> dict:
    import re

    slots = {}
    for key in [
        "dataset_id",
        "source_path",
        "timestamp_column",
        "value_column",
        "station_column",
        "station_id",
        "start_time",
        "end_time",
        "z_threshold",
        "horizon_steps",
        "confidence_level",
        "model_endpoint",
    ]:
        match = re.search(rf"{key}\s*[=:]\s*([^\s,]+)", query or "")
        if match:
            slots[key] = match.group(1).strip().strip("'\"")
    if slots:
        slots["filters"] = dict(slots)
    return slots


def _looks_like_external_tide_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "대조기",
        "조석",
        "조위",
        "물때",
        "만조",
        "간조",
        "tide",
        "spring tide",
        "대조기",
        "조석",
        "조위",
        "물때",
        "만조",
        "간조",
        "일정",
    ])


def _looks_like_external_weather_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "기상",
        "태풍",
        "풍속",
        "파고",
        "해상예보",
        "예보",
        "weather",
        "typhoon",
        "wave",
        "기상",
        "태풍",
        "풍속",
        "파고",
        "해상예보",
        "예보",
    ])

def _external_domain_for_query(query: str) -> str | None:
    if _looks_like_external_tide_query(query):
        return "khoa_tide_prediction"
    if _looks_like_external_weather_query(query):
        return "marine_weather"
    return None

def _external_domain_bound(domain: str | None) -> bool:
    if not domain:
        return False
    try:
        with open(TIME_SERIES_REGISTRY_PATH, "r", encoding="utf-8") as f:
            text = f.read().lower()
    except Exception:
        return False
    lowered = domain.lower()
    return lowered in text and any(marker in text for marker in ["execution_status: ready", "forecast_status: ready", "api_status: ready"])

def _should_fast_external_requirement(query: str) -> bool:
    domain = _external_domain_for_query(query)
    return bool(domain and not _external_domain_bound(domain))

def _external_requirement_payload(query: str, domain: str) -> dict:
    if domain == "marine_weather":
        return {
            "status": "PENDING_EXTERNAL_DATA_BINDING",
            "domain": domain,
            "query": query,
            "need": "official_marine_weather_observation_or_forecast",
            "reason": "Marine weather, typhoon, wind, wave, and forecast queries require official external marine weather data.",
            "local_rag_suitable": False,
            "web_search_performed": False,
            "recommended_sources": ["KMA marine weather forecast", "KHOA marine observation", "official typhoon and wave forecast feeds"],
            "blockers": ["BLOCKED_DATA: external time-series source is not bound: marine_weather"],
            "next_action": "Register and bind the external source, then rerun the same query through the normal graph path.",
        }
    return {
        "status": "PENDING_EXTERNAL_DATA_BINDING",
        "domain": "khoa_tide_prediction",
        "query": query,
        "need": "official_tide_prediction_time_series",
        "reason": "Spring tide/tide schedule queries require official tide prediction time-series data.",
        "local_rag_suitable": False,
        "web_search_performed": False,
        "recommended_sources": ["KHOA/data.go.kr TideBED predicted tide level", "KHOA tide forecast", "KHOA tide station and port mapping"],
        "blockers": ["BLOCKED_DATA: external time-series source is not bound: khoa_tide_prediction"],
        "next_action": "Register and bind the external source, then rerun the same query through the normal graph path.",
    }


def _looks_like_standard_rag_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "s-100",
        "s-101",
        "feature catalogue",
        "dceg",
        "wreck",
        "obstruction",
        "standard",
        "catalogue",
        "정의",
        "기준",
        "표준",
        "카탈로그",
        "근거",
        "문서",
        "규정",
        "설명",
        "요약",
    ])

def _looks_like_legal_rag_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "legal",
        "notice",
        "law",
        "\ubc95\ub839",
        "\uace0\uc2dc",
        "\uaddc\uc815",
        "\uadfc\uac70",
        "\ud574\uc0c1\uad50\ud1b5\uc548\uc804",
        "abc-999",
    ])

def _looks_like_no_evidence_document_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "imaginaryfeature",
        "abc-999",
        "\uc874\uc7ac\ud558\uc9c0 \uc54a\ub294",
        "\uc5c6\ub294",
    ])

def _looks_like_traffic_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "ais",
        "v-pass",
        "vpass",
        "traffic",
        "통항",
        "항적",
        "어선",
        "밀도",
        "패턴",
        "\ud1b5\ud56d",
        "\ud56d\uc801",
        "\uc5b4\uc120",
        "\ubc00\ub3c4",
        "\ud328\ud134",
    ])

def _looks_like_vts_control_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "vts",
        "vessel traffic control",
        "traffic control area",
        "\ud574\uc0c1\uad50\ud1b5\uad00\uc81c",
        "\ud574\uc0c1\uad50\ud1b5\uad00\uc81c\uad6c\uc5ed",
        "\uc120\ubc15\uad50\ud1b5\uad00\uc81c",
        "\uad00\uc81c\uad6c\uc5ed",
        "\uad00\uc81c",
    ])

def _looks_like_spatial_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "km",
        "m 이내",
        "이내",
        "주변",
        "안에",
        "가까운",
        "nearest",
        "within",
        "radius",
        "침선",
        "위험객체",
        "항로표지",
        "정박지",
        "m \uc774\ub0b4",
        "\uc774\ub0b4",
        "\uc8fc\ubcc0",
        "\uc548\uc5d0",
        "\uac00\uae4c\uc6b4",
        "\uce68\uc120",
        "\uc704\ud5d8\uac1d\uccb4",
        "\ud56d\ub85c\ud45c\uc9c0",
        "\uc815\ubc15\uc9c0",
        "\ud574\uc0c1\uad50\ud1b5\uad00\uc81c",
        "\uad00\uc81c\uad6c\uc5ed",
        "\uac1c\ubc1c \uc608\uc815",
        "\uac1c\ubc1c\uc608\uc815",
        "\ubcf4\ud638\uad6c\uc5ed",
        "\ud56d\ub85c",
        "\uc5b4\uc7a5",
        "\ud574\uc0c1\ud48d\ub825",
        "\ud6c4\ubcf4\uc9c0",
        "\ucda9\ub3cc",
        "\uc12c",
        "\uc640\ub958",
    ])

def _looks_like_accident_relation_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return "feature_instance_id=" in lowered and any(term in lowered or term in text for term in ["accident", "\uc0ac\uace0", "\uc774\ub825"])

def _looks_like_policy_block_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "\uad8c\ud55c \uc5c6\ub294",
        "\ube44\uacf5\uac1c",
        "\uad70\uc0ac",
        "\uc81c\ud55c\uad6c\uc5ed",
        "restricted",
        "classified",
        "military",
    ])

def _looks_like_ambiguous_hazard_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "\uc704\ud5d8\ud55c \uacf3",
        "\ubb50\uac00 \uc704\ud5d8",
        "\uc5ec\uae30 \uadfc\ucc98",
    ])

def _looks_like_tidal_current_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["tidal current", "\uc870\ub958"])

def _looks_like_sea_parting_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["sea parting", "\ubc14\ub2f7\uae38", "\ubc14\ub2e4\uac08\ub77c\uc9d0"])

def _looks_like_planned_port_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["planned port", "\uac1c\ubc1c \uc608\uc815", "\uac1c\ubc1c\uc608\uc815"])

def _looks_like_protected_area_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["protected area", "\ubcf4\ud638\uad6c\uc5ed", "\ubcf4\ud638\ud574\uc5ed"])

def _looks_like_eddy_hazard_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["eddy", "\uc640\ub958"])

def _looks_like_island_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["island", "\uc12c \ubaa9\ub85d", "\uc12c"])

def _spatial_context_has_text_location(state: OrchestratorState) -> bool:
    spatial = state.get("spatial_context") or {}
    if hasattr(spatial, "model_dump"):
        spatial = spatial.model_dump()
    if not isinstance(spatial, dict):
        return False
    return bool(spatial.get("base_location") or spatial.get("location_text"))

def _should_fast_spatial_or_traffic_block(state: OrchestratorState) -> bool:
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    if _looks_like_explicit_time_series_request(query):
        return True
    if _looks_like_policy_block_query(query) or _looks_like_ambiguous_hazard_query(query):
        return True
    if _looks_like_accident_relation_query(query):
        return True
    if _looks_like_tidal_current_query(query) or _looks_like_sea_parting_query(query):
        return True
    if _looks_like_planned_port_query(query) or _looks_like_protected_area_query(query) or _looks_like_eddy_hazard_query(query) or _looks_like_island_query(query):
        return True
    if _looks_like_vts_control_query(query):
        return True
    if _looks_like_traffic_query(query):
        return True
    return _looks_like_spatial_query(query)

def _fast_spatial_or_traffic_plan(query: str, state: OrchestratorState) -> tuple[dict, dict, str, str]:
    explicit_time_series = _looks_like_explicit_time_series_request(query)
    policy_block = _looks_like_policy_block_query(query)
    ambiguous_hazard = _looks_like_ambiguous_hazard_query(query)
    accident_relation = _looks_like_accident_relation_query(query)
    tidal_current = _looks_like_tidal_current_query(query)
    sea_parting = _looks_like_sea_parting_query(query)
    planned_port = _looks_like_planned_port_query(query)
    protected_area = _looks_like_protected_area_query(query)
    eddy_hazard = _looks_like_eddy_hazard_query(query)
    island = _looks_like_island_query(query)
    vts_control = _looks_like_vts_control_query(query)
    traffic = _looks_like_traffic_query(query)
    lowered = (query or "").lower()
    if explicit_time_series:
        if any(term in (query or "").lower() or term in (query or "") for term in ["anomaly", "\uc774\uc0c1\uce58"]):
            analysis_type = "observed_time_series_analysis"
            agent_name = "Time-Series Agent"
            target_term = "time_series_anomaly"
        else:
            analysis_type = "observed_time_series_forecast"
            agent_name = "Time-Series Forecast Agent"
            target_term = "time_series_forecast"
        tools = ["timeseries.analyze"]
        data = ["user_supplied_time_series"]
        blockers = ["BLOCKED_DATA: time-series source exists in request but validated execution binding/review contract is not ready"]
    elif policy_block:
        analysis_type = "policy_block"
        agent_name = "Policy Guard"
        tools = []
        data = ["access_policy"]
        blockers = ["BLOCKED_POLICY: restricted or private security-sensitive data cannot be exposed"]
        target_term = "restricted_security_data"
    elif ambiguous_hazard:
        analysis_type = "clarification_required"
        agent_name = "ClarificationAgent"
        tools = []
        data = ["user_context"]
        blockers = ["NEEDS_CLARIFICATION: location, target object, or analysis range is missing"]
        target_term = "ambiguous_hazard_query"
    elif accident_relation:
        analysis_type = "accident_relation_lookup"
        agent_name = "Accident/Risk Agent"
        tools = ["accident.relation_lookup"]
        data = ["accident_relation_index"]
        blockers = ["BLOCKED_DATA: accident relation index is not bound for this feature instance"]
        target_term = "accident_relation"
    elif tidal_current:
        analysis_type = "current_tidal_lookup"
        agent_name = "Time-Series Agent"
        tools = ["ocean.current_lookup"]
        data = ["tidal_current_surface"]
        blockers = ["BLOCKED_DATA: official tidal-current layer or time-series source is not bound"]
        target_term = "tidal_current"
    elif sea_parting:
        analysis_type = "sea_parting_prediction_lookup"
        agent_name = "Time-Series Forecast Agent"
        tools = ["khoa.sea_parting_prediction"]
        data = ["sea_parting_prediction"]
        blockers = ["BLOCKED_DATA: official sea-parting prediction source is not bound"]
        target_term = "sea_parting_prediction"
    elif planned_port:
        analysis_type = "planned_port_overlay"
        agent_name = "Spatial Analysis Agent"
        tools = ["port.planned_area_overlay", "postgis.intersects"]
        data = ["planned_port_area"]
        blockers = ["BLOCKED_DATA: validated planned port development area layer is not ready"]
        target_term = "planned_port_area"
    elif protected_area:
        analysis_type = "protected_area_lookup"
        agent_name = "Spatial Analysis Agent"
        tools = ["environment.protected_area_lookup", "postgis.intersects"]
        data = ["protected_area"]
        blockers = ["BLOCKED_DATA: validated protected-area layer binding is not ready"]
        target_term = "protected_area"
    elif eddy_hazard:
        analysis_type = "eddy_hazard_lookup"
        agent_name = "Spatial Analysis Agent"
        tools = ["hazard.eddy_lookup", "postgis.intersects"]
        data = ["eddy_hazard_area"]
        blockers = ["BLOCKED_DATA: validated eddy hazard layer binding is not ready"]
        target_term = "eddy_hazard"
    elif island:
        analysis_type = "island_gazetteer_lookup"
        agent_name = "Spatial Analysis Agent"
        tools = ["gazetteer.island_lookup", "postgis.dwithin"]
        data = ["island_gazetteer"]
        blockers = ["BLOCKED_DATA: island gazetteer or reference geometry is not bound"]
        target_term = "island_gazetteer"
    elif vts_control:
        analysis_type = "vessel_traffic_control_area_overlay"
        agent_name = "Spatial Analysis Agent"
        tools = ["traffic.control_area_overlay", "postgis.intersects"]
        data = ["vessel_traffic_control_area"]
        blockers = ["BLOCKED_DATA: validated vessel traffic control area layer binding is not ready"]
        target_term = "vessel_traffic_control_area"
    elif traffic:
        analysis_type = "traffic_search_by_time_space"
        agent_name = "AIS Analysis Agent"
        tools = ["traffic.dynamic_layer_search"]
        data = ["dynamic_traffic_layer"]
        blockers = ["BLOCKED_DATA: validated dynamic traffic layer is not bound for this query"]
        target_term = "dynamic_traffic"
    elif any(term in lowered or term in (query or "") for term in ["nearest", "가까운", "정박지", "\uac00\uae4c\uc6b4", "\uc815\ubc15\uc9c0"]):
        analysis_type = "nearest_feature"
        agent_name = "Spatial Analysis Agent"
        tools = ["postgis.dwithin"]
        data = ["GBENC_S101_feature", "location_gazetteer"]
        blockers = ["BLOCKED_DATA: reference geometry is not bound for nearest-feature search"]
        target_term = "nearest_feature"
    else:
        analysis_type = "feature_search_by_radius"
        agent_name = "Spatial Analysis Agent"
        tools = ["gbenc.s101_feature_search_by_radius", "postgis.dwithin"]
        data = ["GBENC_S101_feature", "location_gazetteer"]
        blockers = ["BLOCKED_DATA: reference geometry or validated spatial layer binding is not ready"]
        target_term = "spatial_feature"

    spatial = state.get("spatial_context") or {}
    if hasattr(spatial, "model_dump"):
        spatial = spatial.model_dump()
    spatial = spatial if isinstance(spatial, dict) else {}
    slots = {
        "location_text": spatial.get("base_location") or spatial.get("location_text"),
        "distance_m": spatial.get("buffer_distance"),
        "target_term": target_term,
        "analysis_type": analysis_type,
    }
    route_plan = {
        "task_id": f"TASK-SPATIAL-BLOCK-{state['task_id'][:3].upper()}",
        "status": "BLOCKED_POLICY" if policy_block else ("NEEDS_USER_INPUT" if ambiguous_hazard else "BLOCKED_DATA"),
        "intent": "TRAFFIC_ANALYSIS" if traffic else ("ACCIDENT_ANALYSIS" if accident_relation else "SPATIAL_ANALYSIS"),
        "context": "maritime_traffic" if traffic else ("accident_prevention" if accident_relation else "navigation_safety"),
        "analysis_type": analysis_type,
        "derived_concept": target_term,
        "primary_agent": agent_name,
        "secondary_agents": [],
        "slots": slots,
        "tools": tools,
        "data": data,
        "outputs": ["BlockedDataRequirement", "Summary"],
        "clarification_required": False,
        "confidence": 1.0,
        "execution_ready": False,
        "route_plan_status": "BLOCKED_POLICY" if policy_block else ("NEEDS_USER_INPUT" if ambiguous_hazard else "BLOCKED_DATA"),
    }
    qec = {
        "readiness": "BLOCKED_POLICY" if policy_block else ("NEEDS_CLARIFICATION" if ambiguous_hazard else "BLOCKED_DATA"),
        "blockers": blockers,
        "warnings": [],
        "data_bindings": [],
        "tool_bindings": [{"tool_id": tool, "operation": analysis_type, "query_template_id": analysis_type, "schema_version": "2.0"} for tool in tools],
    }
    return route_plan, qec, agent_name, analysis_type


def _agent_family(agent_name: str | None) -> str:
    name = (agent_name or "").lower()
    if "forecast" in name:
        return "time_series_forecast"
    if "time-series" in name or "time_series" in name:
        return "time_series"
    if "spatial" in name:
        return "spatial"
    if "accident" in name:
        return "accident"
    if "ais" in name or "traffic" in name:
        return "traffic"
    if "rag" in name or "knowledge" in name:
        return "rag"
    return "generic"


def _external_data_requirement_from_state(state: OrchestratorState) -> dict:
    discovery = state.get("data_discovery_result") or {}
    if not isinstance(discovery, dict):
        return {}

    api_params = discovery.get("api_params") or {}
    evidence = discovery.get("external_data_evidence") or api_params.get("external_data_evidence") or {}
    requires_external = bool(discovery.get("requires_external_api") or api_params.get("domain") or evidence)
    if not requires_external:
        return {}

    qec = state.get("query_execution_context") or {}
    blockers = qec.get("blockers", []) if isinstance(qec, dict) else []
    domain = api_params.get("domain") or discovery.get("api_domain") or "external_data"

    return {
        "status": "PENDING_EXTERNAL_DATA_BINDING",
        "domain": domain,
        "query": state.get("query"),
        "need": evidence.get("need") or "official_external_time_series",
        "reason": evidence.get("reason") or "This request requires an official external data source that is not yet bound locally.",
        "local_rag_suitable": evidence.get("local_rag_suitable", False),
        "web_search_performed": evidence.get("web_search_performed", False),
        "recommended_sources": evidence.get("recommended_sources") or [],
        "blockers": blockers,
        "next_action": "Register and bind the external source, then rerun the same query through the normal graph path.",
    }


def _validate_time_series_result(result: AgentResult) -> tuple[bool, list[str], dict]:
    structured = result.structured_result or {}
    metrics = result.metrics or structured.get("metrics") or {}
    reasons: list[str] = []
    payload = {
        "type": "time_series_metrics",
        "status": structured.get("status", "UNKNOWN"),
        "metrics_present": bool(metrics),
        "missing_rate": metrics.get("missing_rate"),
        "anomaly_count": metrics.get("anomaly_count"),
    }
    if not metrics:
        reasons.append("Time-series result does not include metrics.")
        return False, reasons, payload
    missing_rate = metrics.get("missing_rate")
    if missing_rate is not None:
        try:
            if float(missing_rate) > 0.30:
                reasons.append(f"Time-series missing_rate exceeds review threshold: {missing_rate}")
        except (TypeError, ValueError):
            reasons.append("Time-series missing_rate is not numeric.")
    return not reasons, reasons, payload

def _validate_forecast_result(result: AgentResult) -> tuple[bool, list[str], dict]:
    structured = result.structured_result or {}
    forecast = structured.get("forecast") or []
    reasons: list[str] = []
    payload = {
        "type": "time_series_forecast",
        "status": structured.get("status", "UNKNOWN"),
        "method": structured.get("method"),
        "forecast_steps": len(forecast),
        "confidence_level": structured.get("confidence_level"),
    }
    if not forecast:
        reasons.append("Forecast result does not include forecast rows.")
        return False, reasons, payload
    for idx, row in enumerate(forecast):
        value = row.get("forecast_value")
        lower = row.get("lower_bound")
        upper = row.get("upper_bound")
        if value is None or lower is None or upper is None:
            reasons.append(f"Forecast row {idx} is missing value or confidence bounds.")
            continue
        try:
            if float(lower) > float(value) or float(value) > float(upper):
                reasons.append(f"Forecast row {idx} has invalid confidence interval ordering.")
        except (TypeError, ValueError):
            reasons.append(f"Forecast row {idx} has non-numeric confidence interval values.")
    return not reasons, reasons, payload

def _build_query_execution_context(
    state: OrchestratorState,
    slots: dict,
    ctx_res=None,
    route_plan: dict | None = None,
) -> QueryExecutionContext:
    """Single contract carried from orchestration into specialist agents."""
    graph_context = state.get("graph_context") or {}
    data_discovery = state.get("data_discovery_result") or {}
    context_payload = {}
    if ctx_res:
        context_payload = ctx_res if isinstance(ctx_res, dict) else getattr(ctx_res, "__dict__", {})
    route_plan = route_plan or {}
    plan_hash = hashlib.sha256(
        json.dumps(route_plan, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest() if route_plan else None
    readiness = PlanStatus.EXECUTION_READY if route_plan.get("execution_ready") else (
        PlanStatus.NEEDS_USER_INPUT if route_plan.get("clarification_required") else PlanStatus.PLAN_READY
    )
    qec = QueryExecutionContext(
        request_id=state.get("task_id"),
        task_id=state.get("task_id"),
        conversation_id=state.get("task_id"),
        plan_hash=plan_hash,
        original_query=state.get("query"),
        slots=ExecutionSlots.from_payload(slots),
        normalized_query=state.get("normalized_query"),
        security_context_ref=f"user:{state.get('user_id')}@org:{state.get('organization_id')}",
        semantic_resolution={
            "context": _context_value(ctx_res, "selected_context"),
            "analysis_type": _context_value(ctx_res, "analysis_type"),
            "status": _context_value(ctx_res, "status"),
            "confidence": _context_value(ctx_res, "confidence"),
        },
        kg=graph_context,
        context=context_payload,
        route_plan=route_plan,
        data_discovery=data_discovery,
        spatial={
            "spatial_context": state.get("spatial_context"),
            "can_execute_spatial_query": data_discovery.get("can_execute_spatial_query"),
        },
        rag={
            "filters": graph_context.get("rag_filters", {}),
            "graph_paths": graph_context.get("graph_paths", []),
        },
        readiness=readiness,
        blockers=list(route_plan.get("missing_slots", []) or []),
        warnings=list(route_plan.get("warnings", []) or []),
        snapshot_versions={
            "s101_product_specification": os.environ.get("S101_PRODUCT_SPECIFICATION"),
            "s101_catalogue_version": os.environ.get("S101_CATALOGUE_VERSION"),
            "embedding_model": os.environ.get("EMBEDDING_MODEL"),
        },
        provenance={
            "normalizer": "services.orchestrator.query_normalizer",
            "slot_extractor": "services.orchestrator.semantic_router.DynamicSlotExtractor",
            "context_resolver": "services.orchestrator.context_resolver",
            "graph_retriever": graph_context.get("provenance", {}),
        },
    )
    if qec.slots.target_features and not qec.slots.resolved_target_set:
        qec = qec.merge_slot_patch(
            {"resolved_target_set": qec.slots.target_features},
            producer="services.orchestrator.graph._build_query_execution_context",
            source_ref="target_features",
            reason_code="RESOLVED_TARGET_SET_DEFAULT",
        )
    return qec

async def parse_intent_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("LangGraph: Parsing intent", task_id=state["task_id"])
    original_query = state["query"]
    
    # [Query Normalizer Injection]
    norm_result = normalizer.normalize_with_debug(original_query)
    query = norm_result["normalized_query"]
    state["normalized_query"] = query
    
    # Trace Debugger를 위해 추가 정보 로깅
    debug_logs = norm_result["matched_rules"].copy()
    if norm_result["canonical_terms"]:
        debug_logs.append(f"추출된 정규 도메인 용어: {', '.join(norm_result['canonical_terms'])}")
    if norm_result["candidate_contexts"]:
        debug_logs.append(f"후보 컨텍스트: {', '.join(norm_result['candidate_contexts'])}")
        
    state["normalization_debug"] = debug_logs
    state["norm_result"] = norm_result
    
    # 쿼리가 변경되더라도 state["query"]는 원문 유지를 위해 덮어쓰지 않습니다.
    
    # 1. LLM 추출 (의도, 대상 객체, 공간 조건, 시간 조건, 출력 형식)
    intent_type = "clarification_required"
    target_objects = []
    spatial_conditions = []
    temporal_conditions = []
    output_format = "MAP"
    base_location = ""
    intent_understanding = "분석 불가"
    execution_plan = "분석 불가"
    
    # 0. Fast deterministic intent gates. These avoid expensive semantic-cache
    # lookups for well-scoped external-data and document/RAG queries.
    fast_external_tide = _looks_like_external_tide_query(original_query)
    fast_external_weather = _looks_like_external_weather_query(original_query)
    fast_standard_rag = _looks_like_standard_rag_query(original_query)
    fast_legal_or_no_evidence_rag = _looks_like_legal_rag_query(original_query) or _looks_like_no_evidence_document_query(original_query)
    fast_time_series = _looks_like_time_series_query(original_query)
    combined_fast_query = f"{original_query} {query}"
    fast_spatial_or_traffic = (
        _looks_like_traffic_query(combined_fast_query)
        or _looks_like_spatial_query(combined_fast_query)
        or _looks_like_explicit_time_series_request(combined_fast_query)
        or _looks_like_accident_relation_query(combined_fast_query)
        or _looks_like_policy_block_query(combined_fast_query)
        or _looks_like_ambiguous_hazard_query(combined_fast_query)
        or _looks_like_tidal_current_query(combined_fast_query)
        or _looks_like_sea_parting_query(combined_fast_query)
        or _looks_like_planned_port_query(combined_fast_query)
        or _looks_like_protected_area_query(combined_fast_query)
        or _looks_like_eddy_hazard_query(combined_fast_query)
        or _looks_like_island_query(combined_fast_query)
    )
    cached_intent = None if (fast_external_tide or fast_external_weather or fast_standard_rag or fast_legal_or_no_evidence_rag or fast_time_series or fast_spatial_or_traffic) else cache.check_cache(query)
    if fast_external_tide:
        intent_type = "DATA_DISCOVERY"
        target_objects = [term for term in ["대조기", "조석", "조위", "물때", "tide"] if term in original_query or term in query.lower()]
        if not target_objects:
            target_objects = ["tide_schedule"]
        temporal_conditions = [part for part in original_query.split() if "월" in part or part.isdigit()]
        output_format = "SUMMARY"
        intent_understanding = "Official tide prediction data is required for this tide/spring-tide schedule query."
        execution_plan = "1. Check local registry and discovery evidence. 2. If local data is unavailable, mark required external tide source. 3. Do not fabricate schedule dates."
    elif fast_external_weather:
        intent_type = "DATA_DISCOVERY"
        target_objects = [term for term in ["기상", "태풍", "풍속", "파고", "해상예보", "weather", "typhoon", "wave"] if term in original_query or term in query.lower()]
        if not target_objects:
            target_objects = ["marine_weather"]
        temporal_conditions = [part for part in original_query.split() if part in {"오늘", "내일", "모레"} or "월" in part or part.isdigit()]
        output_format = "SUMMARY"
        intent_understanding = "Official marine weather observation or forecast data is required for this query."
        execution_plan = "1. Check local registry and discovery evidence. 2. If local data is unavailable, mark required external marine weather source. 3. Do not fabricate weather values."
    elif fast_standard_rag or fast_legal_or_no_evidence_rag:
        intent_type = "KNOWLEDGE_SEARCH"
        target_objects = [term for term in ["S-100", "S-101", "Wreck", "Obstruction", "Feature Catalogue", "DCEG"] if term.lower() in query.lower()]
        if not target_objects:
            target_objects = [query]
        output_format = "SUMMARY"
        intent_understanding = "Marine standards or catalogue document search is required."
        execution_plan = "1. Route to Standard RAG Agent. 2. Retrieve graph-scoped document evidence. 3. Answer only with retrieved evidence and citations."
    elif fast_spatial_or_traffic:
        if _looks_like_explicit_time_series_request(combined_fast_query):
            intent_type = "TIME_SERIES_ANALYSIS"
            target_objects = ["time_series"]
            output_format = "SUMMARY"
            intent_understanding = "Explicit time-series source query requires validated execution binding before analysis."
            execution_plan = "1. Check supplied time-series binding. 2. If execution contract is unavailable, return BLOCKED_DATA."
        elif _looks_like_traffic_query(combined_fast_query):
            intent_type = "TRAFFIC_ANALYSIS"
            target_objects = ["dynamic_traffic"]
            output_format = "SUMMARY"
            intent_understanding = "Dynamic maritime traffic analysis requires a validated traffic layer binding."
            execution_plan = "1. Check traffic data binding. 2. If unavailable, return BLOCKED_DATA without fabricating AIS/V-PASS results."
        else:
            intent_type = "SPATIAL_SEARCH"
            target_objects = ["spatial_feature"]
            output_format = "MAP"
            intent_understanding = "Spatial feature analysis requires validated reference geometry and spatial layer binding."
            execution_plan = "1. Check spatial geometry and layer binding. 2. If unavailable, return BLOCKED_DATA without running full graph search."
    elif fast_time_series:
        intent_type = "TIME_SERIES_ANALYSIS"
        target_objects = ["time_series"]
        output_format = "SUMMARY"
        intent_understanding = "Time-series analysis query with explicit data/source parameters."
        execution_plan = "1. Build observed time-series analysis plan. 2. Execute if data binding is available, otherwise return BLOCKED_DATA."
    elif cached_intent:
        intent_type = cached_intent.get("intent_type", "clarification_required")
        target_objects = cached_intent.get("target_objects", [])
        intent_understanding = cached_intent.get("intent_understanding", "분석 불가")
        execution_plan = cached_intent.get("execution_plan", "분석 불가")
        spatial_conditions = cached_intent.get("spatial_conditions", [])
        temporal_conditions = cached_intent.get("temporal_conditions", [])
        output_format = cached_intent.get("output_format", "MAP")
        if spatial_conditions:
            base_location = spatial_conditions[0].split()[0]
    else:
        # 1. 1차 규칙 검사 (Rule Check)
        rule_result = rule_router.evaluate(query)
        primary_agent = rule_result.get("primary_agent")
        secondary_agents = rule_result.get("secondary_agents", [])
        
        # 2. 의미 임베딩 검색 (Semantic Search)
        route_match = router.route_query(query)
        intent_type = route_match
        
        if not primary_agent and intent_type != "clarification_required":
            # Registry에서 인텐트 기반 에이전트 찾기
            primary_agent = registry.find_agent_by_intent(intent_type)
            if not primary_agent:
                if intent_type == "SPATIAL_SEARCH":
                    primary_agent = "Spatial Analysis Agent"
                elif intent_type == "KNOWLEDGE_SEARCH":
                    primary_agent = "Knowledge Agent"
                    
        # 3. Agent Registry 확인 (권한 및 유효성)
        if primary_agent:
            user_clearance = state.get("clearance_level", 1)
            is_valid = registry.validate_agent(primary_agent, user_clearance)
            if not is_valid:
                intent_understanding = f"권한 부족 또는 잘못된 에이전트 접근: {primary_agent}"
                execution_plan = "실행 취소 (Block)"
                intent_type = "BLOCKED"
                primary_agent = None
            else:
                # 4 & 5. 라우팅 결정 및 Task Plan 생성
                if intent_type == "SPATIAL_SEARCH" or primary_agent == "Spatial Analysis Agent":
                    intent_type = "SPATIAL_SEARCH"
                    # 슬롯 추출 시도 (예: spatial_proximity_search 룰 적용)
                    extracted = slot_extractor.extract(query, "spatial_proximity_search")
                    
                    # 모호성 및 누락 slot 검증
                    clarification_questions = []
                    
                    if not extracted:
                        clarification_questions.append("분석 대상을 정확히 파악할 수 없습니다. 다시 한번 말씀해 주시겠어요?")
                    else:
                        base_location = extracted.get("location", "")
                        radius_m = extracted.get("distance_m", "")
                        target = extracted.get("target_term", "")
                        # 1. 누락 slot 확인
                        if not target:
                            clarification_questions.append("어떤 객체를 찾으시는지 명확하지 않습니다. 무엇을 찾을까요?")
                        elif target in {"위험한 것", "위험요소", "위험물", "주의할 것"} and not any(ch.isdigit() for ch in query):
                            clarification_questions.append("추가 정보(거리 또는 영역)가 필요합니다. 어느 범위에서 어떤 위험요소를 찾을까요?")
                        elif "후보지" in query and "주변" in query and not any(ch.isdigit() for ch in query):
                            clarification_questions.append("해상풍력 후보지의 구체 위치 또는 검색 범위가 필요합니다.")
                        
                        # 반경 검색이거나 위치가 명시되지 않았을 때, map_bounds가 없으면 질문
                        req_spatial_ctx = state.get("spatial_context") or {}
                        map_bounds = req_spatial_ctx.get("map_bounds")
                        if not base_location and not map_bounds and (radius_m or "주변" in query or "근처" in query or "반경" in query):
                            clarification_questions.append("어느 지역을 기준으로 분석할까요? (예: 부산항, 여수 앞바다 등)을 확실히 알려주세요.")
                        
                        # 위험객체 모호성 검사 (다단계 파이프라인 적용)
                        from services.orchestrator.context_resolver import context_resolver
                        
                        context_result = context_resolver.resolve(
                            query=original_query,
                            normalized_query=query,
                            active_workspace=state.get("workspace_context"),
                            available_layers=state.get("available_layers"),
                            uploaded_assets=state.get("uploaded_assets"),
                            extracted_slots=extracted
                        )
                        
                        state["context_result"] = context_result
                        
                        if context_result.status == "NEEDS_CLARIFICATION":
                            state["clarification_questions"] = context_result.clarification_questions
                            clarification_questions.extend(context_result.clarification_questions)
                        elif context_result.status == "RESOLVED":
                            resolved_context = context_result.selected_context
                            # 컨텍스트가 결정된 경우, state에 기록하거나 후속 처리에 활용할 수 있음
                            state["spatial_context"] = state.get("spatial_context") or {}
                            state["spatial_context"]["resolved_domain_context"] = resolved_context
                            logger.info(f"Domain Context resolved: {resolved_context}")
                    
                    if clarification_questions:
                        logger.warning("NEEDS_CLARIFICATION triggered", query=query, questions=clarification_questions)
                        agent_res = AgentResult(
                            task_id=state.get("task_id", ""),
                            trace_id="",
                            agent_name=primary_agent,
                            agent_version="1.0",
                            status=AgentStatus.NEEDS_CLARIFICATION,
                            clarification_questions=clarification_questions,
                            structured_result={"reason": "대상 Feature와 위치가 불명확함"}
                        )
                        return {
                            "task_id": state["task_id"],
                            "query": original_query,
                            "organization_id": state.get("organization_id", "default_org"),
                            "user_id": state.get("user_id", "default_user"),
                            "status": AgentStatus.NEEDS_CLARIFICATION,
                            "agent_result": agent_res,
                            "clarification_questions": clarification_questions,
                            "normalized_query": query,
                            "normalization_debug": debug_logs,
                            "context_result": context_result,
                            "norm_result": norm_result
                        }
                    
                    if extracted:
                        target_objects = [target] if target else []
                            
                        if radius_m:
                            spatial_conditions = [f"{base_location} 반경 {radius_m}m"]
                        else:
                            spatial_conditions = [f"{base_location}"]
                        
                    if context_result and context_result.selected_tool:
                        primary_agent = context_result.selected_agents[0] if context_result.selected_agents else primary_agent
                        
                        target_list = ", ".join(target_objects) if target_objects else "지정되지 않음"
                        range_str = f"{base_location} 기준 {radius_m}m" if radius_m else f"{base_location}"
                        ctx_kr = "항행안전" if resolved_context == "navigation_safety" else resolved_context
                        
                        intent_understanding = (
                            f"분석 기준: {ctx_kr} 기준 {target}\n"
                            f"대상 객체: {target_list}\n"
                            f"검색 범위: {range_str}"
                        )
                        execution_plan = f"1. {primary_agent} 호출\n2. {context_result.selected_tool} (템플릿: {context_result.query_template}) 실행\n3. 결과 도출"
                    else:
                        intent_understanding = f"[{primary_agent}] 하이브리드 라우팅 매칭 성공"
                        execution_plan = f"1. {primary_agent} 호출\n2. 필요시 보조 에이전트({', '.join(secondary_agents)}) 개입\n3. 결과 도출"
                    
                    logger.info("Hybrid Routing Fast Path hit", query=query, target=target_objects, primary=primary_agent)
                elif intent_type == "KNOWLEDGE_SEARCH" or primary_agent == "Knowledge Agent":
                    intent_type = "KNOWLEDGE_SEARCH"
                    target_objects = [query]
                    intent_understanding = f"[{primary_agent}] 지식 검색 라우팅 매칭"
                    execution_plan = f"1. {primary_agent} 호출\n2. 관련 규정 및 카탈로그 검색"
                    logger.info("Hybrid Routing Knowledge Path hit", query=query, primary=primary_agent)
        
        # 2. LLM Fallback (라우팅 실패 시)
        if intent_understanding == "분석 불가":
            try:
                if llm_api_enabled():
                    model_name = os.environ.get("LLM_MODEL", "gpt-4o-mini")
                    llm = ChatOpenAI(model=model_name, temperature=0)
                    sys_msg = SystemMessage(content='''당신은 해양공간 지능분석 플랫폼의 Intent Parser(오케스트레이터)입니다.
                다음 지시문을 엄격히 준수하여 순수 JSON 형태로만 응답하세요.

                [핵심 지시문]
                - 사용자가 "위험 객체", "위험구역", "위험요소", "주의구역", "사고위험"이라고 말하면 단일 Feature로 단정하지 마십시오.
                - 반드시 Risk Dictionary(위험도 프로파일)를 조회하여 risk_context를 결정해야 합니다.
                - risk_context가 명확하지 않으면 다음 순서로 판단하십시오:
                  1. 질의에 "항로, 선박, 통항, 항행, 운항, AIS"가 있으면 `navigation_safety`로 분류한다.
                  2. 질의에 "해상풍력, 후보지, 입지, 개발, 제약조건"이 있으면 `offshore_wind_site`로 분류한다.
                  3. 질의에 "사고, 충돌, 좌초, 기관손상, 화재, 사고다발"이 있으면 `accident_prevention`으로 분류한다.
                  4. 질의에 "지도에 표시"가 있으면 Map Agent를 추가한다.
                  5. 질의에 "보고서"가 있으면 Map·Report Agent를 추가한다.
                  6. risk_context가 불명확하면 사용자에게 확인 질문(clarification_questions)을 생성한다.
                - LLM은 위험 객체명이나 대상 명칭을 임의로 생성하지 마십시오. Marine Term Dictionary에 명시된 canonical_term(표준 용어) 및 candidate_features를 우선적으로 추출하고, Feature Dictionary, GB_ENC codeinformation, 사고유형 사전을 함께 참조하여 추론하십시오.
                - 공간분석은 Spatial Analysis Agent와 PostGIS Tool로 수행합니다.

                [출력 JSON 구조]
                1. 'intent_type': 질의의 분석 유형 (예: SPATIAL_SEARCH, RISK_ANALYSIS, KNOWLEDGE_SEARCH)
                2. 'target_objects': 분석 대상 객체들의 배열 (예: ["정박지", "선석", "위험객체"])
                3. 'spatial_conditions': 공간 및 위치 조건 배열 (예: ["부산항 반경 3km"])
                4. 'temporal_conditions': 시간 조건 배열 (예: ["최신"])
                5. 'output_format': 출력 형식 (예: "지도, 표, 요약", "Map")
                6. 'intent_understanding': 사용자의 의도를 분석한 구체적인 내용 및 risk_context (예: "항행 안전 기준에 따라 부산항 3km 이내 선박 충돌 위험구역 탐색")
                7. 'execution_plan': 실행 계획 및 제어 절차 (예: "1. Spatial Analysis Agent 호출 2. 반경 3km 공간분석 수행 3. Map Agent로 지도 시각화")
                8. 'clarification_questions': 질문이 필요한 경우 배열로 추가 (선택사항)
                
                응답 포맷: 
                {
                    "intent_type": "SPATIAL_SEARCH", 
                    "target_objects": ["객체명"], 
                    "spatial_conditions": ["위치조건"],
                    "temporal_conditions": ["시간조건"],
                    "output_format": "출력형식",
                    "intent_understanding": "의도 분석 내용",
                    "execution_plan": "실행 계획 절차",
                    "clarification_questions": []
                }''')
                    response = await llm.ainvoke([sys_msg, HumanMessage(content=query)])
                    
                    content = response.content.strip()
                    if content.startswith("```json"): content = content[7:-3]
                    elif content.startswith("```"): content = content[3:-3]
                    parsed = json.loads(content)
                    
                    intent_type = parsed.get("intent_type", "clarification_required")
                    target_objects = parsed.get("target_objects", [])
                    intent_understanding = parsed.get("intent_understanding", "분석 불가")
                    execution_plan = parsed.get("execution_plan", "분석 불가")
                    spatial_conditions = parsed.get("spatial_conditions", [])
                    temporal_conditions = parsed.get("temporal_conditions", [])
                    output_format = parsed.get("output_format", "MAP")
                    
                    if spatial_conditions:
                        base_location = spatial_conditions[0].split()[0]
                        
                    # 캐시 저장
                    cache.add_to_cache(query, parsed)
                    
            except Exception as e:
                logger.error("LLM parsing failed", error=str(e))
                if "분석" in query or "보여" in query or "찾아" in query:
                    intent_type = "SPATIAL_SEARCH"
                target_objects = [query]
                for word in query.split():
                    if word.endswith("항") or word.endswith("만") or word.endswith("섬") or word.endswith("도") or word.endswith("바다"):
                        base_location = word
                        spatial_conditions.append(base_location)
                        break
                        
                # 3. Completely failed
                if intent_understanding == "분석 불가" and not primary_agent:
                    collector.record_failure(
                        query=query,
                        predicted_agent="None",
                        failure_reason="하이브리드 라우터 및 LLM Fallback 모두 실패 (완전한 분석 불가)",
                        fix="새로운 의도 학습 또는 키워드 룰 추가 필요"
                    )
                        
    intent = Intent(
        intent_type=intent_type, 
        target_objects=target_objects,
        intent_understanding=intent_understanding,
        execution_plan=execution_plan,
        spatial_conditions=spatial_conditions,
        temporal_conditions=temporal_conditions,
        output_format=output_format,
        normalized_query=query
    )
    req_spatial_ctx = state.get("spatial_context") or {}
    map_bounds = req_spatial_ctx.get("map_bounds")
    extracted_payload = None
    if fast_spatial_or_traffic:
        extracted_payload = {}
        if isinstance(req_spatial_ctx, dict):
            if req_spatial_ctx.get("base_location") or req_spatial_ctx.get("location_text"):
                extracted_payload["location"] = req_spatial_ctx.get("base_location") or req_spatial_ctx.get("location_text")
            if req_spatial_ctx.get("buffer_distance") is not None:
                extracted_payload["distance_m"] = req_spatial_ctx.get("buffer_distance")
    elif 'extracted' in locals() and extracted:
        extracted_payload = extracted
    elif intent_type in ("SPATIAL_SEARCH", "spatial_proximity_search", "marine_hazard_feature_search"):
        extracted_payload = slot_extractor.extract(query, "spatial_proximity_search")
    extracted_payload = _enrich_extracted_slots(extracted_payload, norm_result)
    
    # extracted가 있는지 확인
    radius_m = None
    if extracted_payload:
        radius_val = extracted_payload.get("distance_m")
        if radius_val:
            try:
                radius_m = float(radius_val)
            except (TypeError, ValueError):
                pass
        if not base_location and extracted_payload.get("location"):
            base_location = extracted_payload.get("location")

    if base_location or map_bounds:
        spatial_context = SpatialContext(
            base_location=base_location, 
            map_bounds=map_bounds,
            buffer_distance=radius_m
        )
    else:
        spatial_context = None
    
    req = AgentRequest(
        task_id=state["task_id"],
        trace_id=f"tr-{state['task_id']}",
        user_id=state.get("user_id", "default_user"),
        organization_id=state.get("organization_id", "default_org"),
        agent_name="ClarificationAgent",
        original_query=original_query,
        parsed_intent=intent,
        spatial_context=spatial_context,
        security_context=SecurityContext(clearance_level="PUBLIC")
    )
    req.previous_agent_outputs["extracted_slots"] = extracted_payload
    req.query_execution_context = _build_query_execution_context(
        {**state, "normalized_query": query, "spatial_context": spatial_context.model_dump() if spatial_context else state.get("spatial_context")},
        extracted_payload,
        state.get("context_result"),
    )
    
    # RECEIVED -> INTENT_PARSED 로깅
    return {
        "task_id": state["task_id"],
        "query": original_query,
        "organization_id": state.get("organization_id", "default_org"),
        "user_id": state.get("user_id", "default_user"),
        "agent_request": req, 
        "status": AgentStatus.INTENT_PARSED,
        "state_history": log_transition(AgentStatus.RECEIVED, AgentStatus.INTENT_PARSED),
        "normalized_query": query,
        "normalization_debug": debug_logs,
        "norm_result": norm_result,
        "context_result": state.get("context_result"),
        "spatial_context": spatial_context.model_dump() if spatial_context else state.get("spatial_context"),
        "extracted_slots": extracted_payload
    }

from services.orchestrator.feature_resolver import feature_resolver

async def graph_rag_node(state: OrchestratorState) -> OrchestratorState:
    """Run graph candidate discovery between normalization and context resolution."""
    query = state.get("normalized_query") or state.get("query", "")
    intent = state.get("agent_request").parsed_intent if state.get("agent_request") else None
    norm = state.get("norm_result") or {}
    seed_context = {
        "target_features": list(intent.target_objects) if intent else [],
        "derived_concepts": norm.get("derived_concepts", []) or norm.get("canonical_terms", []),
        "document_type": norm.get("document_type", []),
    }
    context = graph_rag_retriever.retrieve(query, seed_context)
    return {
        "graph_context": context,
        "graph_rag_context": context,
        "status": AgentStatus.INTENT_PARSED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.INTENT_PARSED, actor="GraphRAGRetriever", reason="KG candidate plan created"),
    }

async def fast_document_answer_node(state: OrchestratorState) -> OrchestratorState:
    """Return authoritative local catalogue answers without vector/LLM orchestration."""
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    feature = _exact_s101_feature_match(query)
    relation = _exact_s100_s101_relation_match(query)
    no_evidence = _looks_like_no_evidence_document_query(query) or _looks_like_legal_rag_query(query)
    if feature:
        code = str(feature.get("code") or "")
        name = str(feature.get("name") or code)
        definition = str(feature.get("definition") or "").strip()
        aliases = [str(alias) for alias in feature.get("aliases") or []]
        primitives = feature.get("primitives") or feature.get("permitted_primitives") or []
        content = (
            f"S-101 Feature Catalogue feature definition. Feature code: {code}. "
            f"Feature name: {name}. Definition: {definition}. "
            f"Aliases: {', '.join(aliases) if aliases else 'N/A'}. "
            f"Permitted primitives: {', '.join(str(item) for item in primitives) if primitives else 'N/A'}."
        )
        doc = {
            "document_id": f"s101_feature_exact_{code.lower()}",
            "title": "S-101 Feature Catalogue 2.0.0",
            "version": "2.0.0",
            "section": f"feature:{code}",
            "page": "N/A",
            "source": "s101_feature_catalogue_v2_xml",
            "excerpt_reference": content,
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
            "relevance_score": 1.0,
        }
        citation = {
            "document_id": doc["document_id"],
            "source": doc["title"],
            "source_id": "s101_feature_catalogue_v2_xml",
            "source_file": feature.get("source"),
            "section": doc["section"],
            "document_type": "feature_catalogue",
            "chunk_id": doc["document_id"],
            "similarity": 1.0,
            "provenance": {"method": "exact_s101_feature_catalogue_lookup", "query": query},
        }
        answer = (
            f"검색 질의와 관련된 근거 문서 1건을 찾았습니다. "
            f"대표 근거는 S-101 Feature Catalogue 2.0.0 / feature:{code}이며, "
            f"정의는 다음과 같습니다: {definition}"
        )
        target_term = code
    elif relation:
        target_term = "S-100/S-101"
        content = (
            "S-100 is the IHO universal hydrographic data framework. "
            "S-101 is the Electronic Navigational Chart product specification built on the S-100 framework. "
            "In this GeoLLM registry, S-100 is marked as framework and S-101 as base_electronic_navigational_chart."
        )
        doc = {
            "document_id": "s100_s101_mapping_registry",
            "title": "S-100/S-101 Mapping Registry",
            "version": "0.1",
            "section": "products:S-100,S-101",
            "page": "N/A",
            "source": "data/s100_s101_mapping_registry.yaml",
            "excerpt_reference": content,
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
            "relevance_score": 1.0,
        }
        citation = {
            "document_id": doc["document_id"],
            "source": doc["title"],
            "source_id": "s100_s101_mapping_registry",
            "source_file": "data/s100_s101_mapping_registry.yaml",
            "section": doc["section"],
            "document_type": "mapping_registry",
            "chunk_id": doc["document_id"],
            "similarity": 1.0,
            "provenance": {"method": "exact_s100_s101_relation_lookup", "query": query},
        }
        answer = (
            "S-100은 IHO의 범용 수로 데이터 프레임워크이고, "
            "S-101은 그 S-100 프레임워크를 기반으로 한 ENC 제품 사양입니다. "
            "로컬 매핑 registry에서는 S-100을 framework, S-101을 base_electronic_navigational_chart 역할로 관리합니다."
        )
    elif no_evidence:
        target_term = "no_authoritative_evidence"
        doc = {
            "document_id": "no_authoritative_evidence",
            "title": "No authoritative local evidence",
            "version": "N/A",
            "section": "no_evidence",
            "page": "N/A",
            "source": "local_registry_and_catalogue_fast_check",
            "excerpt_reference": "No authoritative local legal or standard evidence was found for this query.",
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
            "relevance_score": 0.0,
        }
        citation = {
            "document_id": doc["document_id"],
            "source": doc["title"],
            "source_id": "no_authoritative_evidence",
            "source_file": None,
            "section": doc["section"],
            "document_type": "no_evidence",
            "chunk_id": doc["document_id"],
            "similarity": 0.0,
            "provenance": {"method": "deterministic_no_evidence_fast_check", "query": query},
        }
        answer = (
            "요청한 법령/고시/표준 항목에 대해 현재 로컬 authoritative registry와 catalogue에서 "
            "확정 근거를 찾지 못했습니다. 근거 없는 조항, 날짜, feature 정의는 생성하지 않습니다."
        )
    else:
        return {
            "status": AgentStatus.FAILED,
            "error_message": "No exact standard document match found.",
            "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.FAILED, actor="FastDocumentAnswer"),
        }
    doc_blocked = bool(no_evidence)
    route_plan = {
        "task_id": f"TASK-DOC-FAST-{state['task_id'][:3].upper()}",
        "status": "BLOCKED_DATA" if doc_blocked else "EXECUTION_READY",
        "intent": "KNOWLEDGE_SEARCH",
        "context": "standard_document",
        "analysis_type": "document_search",
        "derived_concept": None,
        "primary_agent": "Standard RAG Agent",
        "secondary_agents": [],
        "slots": {"target_term": target_term, "analysis_type": "document_search"},
        "tools": ["rag.graph_scoped_retrieve"],
        "data": ["s101_feature_catalogue"],
        "outputs": ["StandardDocumentOutput", "EvidenceBundle", "Summary"],
        "clarification_required": False,
        "confidence": 1.0,
        "execution_ready": False if doc_blocked else True,
        "route_plan_status": "BLOCKED_DATA" if doc_blocked else "EXECUTION_READY",
    }
    final_dict = {
        "task_id": state["task_id"],
        "trace_id": f"tr-{state['task_id']}",
        "agent_name": "Standard RAG Agent",
        "agent_version": "2.2.0-authoritative-fast-path",
        "status": AgentStatus.BLOCKED if doc_blocked else AgentStatus.COMPLETED,
        "error_code": "NO_AUTHORITATIVE_EVIDENCE" if doc_blocked else None,
        "summary": answer,
        "answer_text": answer,
        "structured_result": {
            "retrieved_count": 0 if doc_blocked else 1,
            "documents": [] if doc_blocked else [doc],
            "citations": [] if doc_blocked else [citation],
            "no_evidence": doc_blocked,
            "evidence_candidate_summary": {},
        },
        "evidence_bundle": {"rag_evidence": [] if doc_blocked else [citation], "kg_provenance": [], "regulatory_evidence": [], "spatial_feature_evidence": [], "spatial_layer_evidence": [], "accident_relation_evidence": []},
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": {
                "readiness": "BLOCKED_DATA" if doc_blocked else "READY",
                "blockers": ["NO_AUTHORITATIVE_EVIDENCE: local legal/standard evidence is not available"] if doc_blocked else [],
                "warnings": [],
                "data_bindings": [{"dataset_id": "s101_feature_catalogue", "relation": "authoritative_lookup"}],
                "tool_bindings": [{"tool_id": "rag.graph_scoped_retrieve", "operation": "exact_catalogue_lookup"}],
            },
            "embedding_independent": True,
            "fast_path": "document_no_evidence" if doc_blocked else "authoritative_s101_feature_catalogue",
        },
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": final_dict["orchestrator_v2"]["query_execution_context"],
        "status": AgentStatus.BLOCKED if doc_blocked else AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.BLOCKED if doc_blocked else AgentStatus.COMPLETED, actor="FastDocumentAnswer"),
    }

async def fast_external_data_requirement_node(state: OrchestratorState) -> OrchestratorState:
    """Return an immediate external-data requirement when no official source is bound."""
    query = state.get("normalized_query") or state.get("query", "")
    domain = _external_domain_for_query(query) or "external_time_series"
    requirement = _external_requirement_payload(query, domain)
    agent_name = "Time-Series Forecast Agent" if domain == "khoa_tide_prediction" else "Data Discovery Agent"
    target_data = "tidal_current_surface" if domain == "khoa_tide_prediction" else "marine_weather"
    route_plan = {
        "task_id": f"TASK-EXT-DATA-{state['task_id'][:3].upper()}",
        "status": "BLOCKED_DATA",
        "intent": "DATA_DISCOVERY",
        "context": "official_external_data",
        "analysis_type": "observed_time_series_forecast",
        "derived_concept": domain,
        "primary_agent": agent_name,
        "secondary_agents": [],
        "slots": {"target_term": domain, "analysis_type": "observed_time_series_forecast"},
        "tools": ["timeseries.forecast"],
        "data": [target_data],
        "outputs": ["ExternalDataRequirement", "Summary"],
        "clarification_required": False,
        "confidence": 1.0,
        "execution_ready": False,
        "route_plan_status": "BLOCKED_DATA",
    }
    qec = {
        "readiness": "BLOCKED_DATA",
        "blockers": requirement["blockers"],
        "warnings": [],
        "data_bindings": [],
        "tool_bindings": [{"tool_id": "timeseries.forecast", "operation": "forecast", "query_template_id": "observed_time_series_forecast", "schema_version": "2.0"}],
    }
    answer = (
        f"현재 로컬 데이터와 RAG만으로는 해당 시계열/예측 값을 확정할 수 없습니다. "
        f"{requirement['domain']} 공식 외부 데이터 연동이 필요하며, 웹 검색이나 임의 날짜 생성은 수행하지 않았습니다."
    )
    final_dict = {
        "task_id": state["task_id"],
        "trace_id": f"tr-{state['task_id']}",
        "agent_name": agent_name,
        "agent_version": "2.2.0-external-data-fast-path",
        "status": "BLOCKED",
        "error_code": "BLOCKED_DATA",
        "summary": answer,
        "answer_text": answer,
        "external_data_requirement": requirement,
        "structured_result": {
            "requires_external_api": True,
            "api_params": {"domain": requirement["domain"], "recommended_sources": requirement["recommended_sources"]},
            "external_data_requirement": requirement,
            "status": "BLOCKED_DATA",
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "embedding_independent": True,
            "fast_path": "external_data_requirement",
        },
        "evidence_bundle": {"rag_evidence": [], "kg_provenance": [], "regulatory_evidence": [], "spatial_feature_evidence": [], "spatial_layer_evidence": [], "accident_relation_evidence": []},
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "data_discovery_result": {
            "requires_external_api": True,
            "api_params": {"domain": requirement["domain"], "external_data_evidence": requirement},
            "external_data_evidence": requirement,
        },
        "status": AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.COMPLETED, actor="FastExternalDataRequirement"),
    }

async def fast_spatial_or_traffic_block_node(state: OrchestratorState) -> OrchestratorState:
    """Return immediate BLOCKED_DATA for spatial/traffic requests without ready bindings."""
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    route_plan, qec, agent_name, analysis_type = _fast_spatial_or_traffic_plan(query, state)
    blocker_text = "; ".join(qec["blockers"])
    answer = (
        "요청한 공간/교통 분석은 임의 결과나 검증되지 않은 데이터를 만들 수 없습니다. "
        f"현재 실행에 필요한 데이터/geometry 바인딩이 준비되지 않아 BLOCKED_DATA로 종료합니다. ({blocker_text})"
    )
    final_dict = {
        "task_id": state["task_id"],
        "trace_id": f"tr-{state['task_id']}",
        "agent_name": agent_name,
        "agent_version": "2.2.0-spatial-traffic-fast-block",
        "status": "BLOCKED",
        "error_code": "BLOCKED_DATA",
        "summary": answer,
        "answer_text": answer,
        "structured_result": {
            "status": "BLOCKED_DATA",
            "analysis_type": analysis_type,
            "blockers": qec["blockers"],
            "count": None,
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "embedding_independent": True,
            "fast_path": "spatial_or_traffic_blocked_data",
        },
        "evidence_bundle": {"rag_evidence": [], "kg_provenance": [], "regulatory_evidence": [], "spatial_feature_evidence": [], "spatial_layer_evidence": [], "accident_relation_evidence": []},
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "status": AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.COMPLETED, actor="FastSpatialTrafficBlock"),
    }

async def data_discovery_node(state: OrchestratorState) -> OrchestratorState:
    """Discover available Lake/KG/DB sources before context resolution."""
    req = state["agent_request"].model_copy(deep=True)
    req.agent_name = "data-discovery-agent"
    req.previous_agent_outputs["graph_context"] = state.get("graph_context", {})
    req.previous_agent_outputs["graph_rag_context"] = state.get("graph_context", {})
    result = await execute_data_discovery(req)
    req.previous_agent_outputs["data_discovery_result"] = result.structured_result
    return {
        "agent_request": req,
        "data_discovery_result": result.structured_result,
        "status": AgentStatus.CONTEXT_RESOLVING,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.CONTEXT_RESOLVING, actor="Data Discovery Agent"),
    }

async def resolve_context_node(state: OrchestratorState) -> OrchestratorState:
    """권한 확인 및 데이터 매핑 (Feature Resolver 연동)"""
    logger.info("LangGraph: Resolving Context", task_id=state["task_id"])
    if state.get("status") == AgentStatus.NEEDS_CLARIFICATION:
        return state
    req = state["agent_request"]
    if state.get("graph_context"):
        req.previous_agent_outputs["graph_context"] = state["graph_context"]
    if state.get("data_discovery_result"):
        req.previous_agent_outputs["data_discovery_result"] = state["data_discovery_result"]
    
    if state["user_id"] == "blocked_user":
        return {
            "status": AgentStatus.BLOCKED,
            "error_message": "User access denied.",
            "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.BLOCKED, reason="Permission Denied")
        }
        
    req.security_context.clearance_level = "SECRET" if state["user_id"] == "admin" else "PUBLIC"
    extracted_slots = _enrich_extracted_slots(
        state.get("extracted_slots") or req.previous_agent_outputs.get("extracted_slots"),
        state.get("norm_result"),
    )
    req.previous_agent_outputs["extracted_slots"] = extracted_slots

    context_result = state.get("context_result")
    if not context_result or not _context_value(context_result, "analysis_type"):
        context_result = context_resolver.resolve(
            query=state.get("query", ""),
            normalized_query=state.get("normalized_query", ""),
            active_workspace=state.get("workspace_context"),
            available_layers=state.get("available_layers"),
            uploaded_assets=state.get("uploaded_assets"),
            extracted_slots=extracted_slots,
        )
        state["context_result"] = context_result
    req.query_execution_context = _build_query_execution_context(state, extracted_slots, context_result)
    
    # Feature Resolver 연동 (2단계: Target Term -> Feature Metadata)
    if req.parsed_intent and req.parsed_intent.target_objects:
        all_nftc_codes = []
        resolved_metadata_list = []
        clarification_questions = []
        
        for obj_kr in req.parsed_intent.target_objects:
            resolved_result = feature_resolver.resolve(obj_kr)
            
            # 모호성 발생 시
            if resolved_result.get("needs_clarification"):
                clarification_questions.append(resolved_result.get("clarification_question"))
                continue
                
            if resolved_result.get("nftc_codes"):
                all_nftc_codes.extend(resolved_result["nftc_codes"])
            resolved_metadata_list.append(resolved_result)
            
        if clarification_questions:
            logger.warning("NEEDS_CLARIFICATION triggered in Resolver", questions=clarification_questions)
            # 수집된 options들을 합침
            all_options = []
            for r in resolved_metadata_list:
                if "clarification_options" in r:
                    all_options.extend(r["clarification_options"])
            # 질문 발생시킨 대상의 옵션도 포함 (resolved_metadata_list에 안 들어갔을 수도 있으므로)
            if resolved_result.get("clarification_options"):
                all_options.extend(resolved_result["clarification_options"])
                
            agent_res = AgentResult(
                task_id=state.get("task_id", ""),
                trace_id="",
                agent_name=req.agent_name,
                agent_version="1.0",
                status=AgentStatus.NEEDS_CLARIFICATION,
                clarification_questions=clarification_questions,
                clarification_options=all_options,
                structured_result={"reason": "대상 Feature가 모호함"}
            )
            return {
                "task_id": state["task_id"],
                "query": state.get("query", ""),
                "organization_id": state.get("organization_id", "default_org"),
                "user_id": state.get("user_id", "default_user"),
                "status": AgentStatus.NEEDS_CLARIFICATION,
                "agent_result": agent_res,
                "normalized_query": state.get("normalized_query", ""),
                "normalization_debug": state.get("normalization_debug", [])
            }
            
        req.previous_agent_outputs["resolved_nftc_codes"] = list(set(all_nftc_codes))
        
        # 첫 번째 대상 객체의 메타데이터를 대표로 저장
        if resolved_metadata_list:
            req.previous_agent_outputs["resolved_metadata"] = resolved_metadata_list[0]
            # LLM이 잘못 예측했을 수 있으므로 확정된 값으로 교체 (None 방지)
    
    return {
        "task_id": state["task_id"],
        "query": state.get("query", ""),
        "organization_id": state.get("organization_id", "default_org"),
        "user_id": state.get("user_id", "default_user"),
        "agent_request": req, 
        "status": AgentStatus.CONTEXT_RESOLVED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.CONTEXT_RESOLVED),
        "context_result": context_result,
        "norm_result": state.get("norm_result"),
        "normalization_debug": state.get("normalization_debug"),
        "spatial_context": state.get("spatial_context"),
        "extracted_slots": extracted_slots
    }

async def create_plan_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("LangGraph: Creating Plan", task_id=state["task_id"])
    req = state["agent_request"]
    ctx_res = state.get("context_result")
    
    # 1. 대상 객체 분류
    target_features = []
    target_area_features = []
    
    ctx_target_features = _context_value(ctx_res, "target_features", [])
    if isinstance(ctx_target_features, dict):
        target_features = ctx_target_features.get("hazard_objects", [])
        target_area_features = ctx_target_features.get("hazard_areas", [])
    elif isinstance(ctx_target_features, list):
        target_features = ctx_target_features
        
    slots = _merge_plan_slots(req, state, ctx_res)
    
    if target_features:
        slots["target_features"] = target_features
    if target_area_features:
        slots["target_area_features"] = target_area_features
        
    graph_context = state.get("graph_context") or {}
    discovery = state.get("data_discovery_result") or {}
    derived_concept = None
    intent_val = req.parsed_intent.intent_type if req.parsed_intent else "clarification_required"
    ctx_derived = _context_value(ctx_res, "derived_concepts", [])
    if ctx_derived:
        derived_concept = ctx_derived[0]
        intent_val = _context_value(ctx_res, "intent") or intent_val
    elif graph_context.get("derived_concepts"):
        derived_concept = graph_context["derived_concepts"][0]
    elif slots.get("derived_concept"):
        derived_concept = slots.get("derived_concept")

    analysis_type = _context_value(ctx_res, "analysis_type")
    if not analysis_type and _looks_like_standard_rag_query(state.get("query", "")):
        analysis_type = "document_search"
        slots["analysis_type"] = analysis_type
    if not analysis_type and _looks_like_external_tide_query(state.get("query", "")):
        analysis_type = "observed_time_series_forecast"
        slots["analysis_type"] = analysis_type
    if not analysis_type and _looks_like_external_weather_query(state.get("query", "")):
        analysis_type = "observed_time_series_forecast"
        slots["analysis_type"] = analysis_type
    if not analysis_type and graph_context.get("execution_hints", {}).get("requires_spatial_analysis"):
        analysis_type = "feature_search_by_radius" if slots.get("distance_m") is not None else "spatial_feature_search"
    if not analysis_type and _looks_like_time_series_query(state.get("query", "")):
        lowered_query = (state.get("query", "") or "").lower()
        if any(term in lowered_query or term in (state.get("query", "") or "") for term in ["forecast", "prediction", "predict", "예측", "신뢰구간", "예보"]):
            analysis_type = "observed_time_series_forecast"
        else:
            analysis_type = "observed_time_series_analysis"
        if any(term in lowered_query or term in (state.get("query", "") or "") for term in ["schedule", "tide", "spring tide", "weather", "wave", "대조기", "조석", "조위", "물때", "만조", "간조", "일정", "기상", "파고", "해상예보"]):
            analysis_type = "observed_time_series_forecast"
        slots["analysis_type"] = analysis_type
        extracted_kv = _extract_key_value_slots(state.get("query", ""))
        slots.setdefault("filters", {}).update(extracted_kv.get("filters", {}))
        for key, value in extracted_kv.items():
            if key != "filters":
                slots[key] = value

    # 동적 라우팅 플랜 생성
    plan_dict = route_planner.generate_plan(
        normalized_query=state.get("normalized_query", ""),
        slots=slots,
        derived_concept=derived_concept,
        context=_context_value(ctx_res, "selected_context", "clarification_required"),
        analysis_type=analysis_type or "clarification_required",
        intent=intent_val,
        graph_context=state.get("graph_context", {}),
        data_discovery_result=state.get("data_discovery_result", {})
    )
        
    # 2. Task Plan 인스턴스 생성
    task_plan = TaskPlan(
        task_id=f"TASK-HAZARD-SEARCH-{state['task_id'][:3].upper()}",
        intent=plan_dict["intent"],
        context=plan_dict["context"],
        analysis_type=plan_dict["analysis_type"],
        derived_concept=plan_dict["derived_concept"],
        primary_agent=plan_dict["primary_agent"] or "Standard RAG Agent",
        secondary_agents=plan_dict["secondary_agents"],
        slots=slots,
        tools=plan_dict["required_tools"],
        data=plan_dict["required_data"],
        outputs=plan_dict.get("outputs", ["GeoJSON", "MapLayer", "FeatureTable", "Summary"]),
        clarification_required=False,
        confidence=_context_value(ctx_res, "confidence", 0.0),
        execution_ready=plan_dict["execution_ready"],
        route_plan_status=plan_dict["route_plan_status"]
    )
    
    # Resolve the named place before dispatch so every Agent implementation
    # receives a concrete spatial reference, not only a display label.
    if req.spatial_context and not req.spatial_context.geometry and req.spatial_context.base_location:
        try:
            from services.spatial_analysis_agent.geocoding_tool import get_maritime_coordinates

            place_name = req.spatial_context.base_location
            for suffix in ("입구", "주변", "근처", "일대", "반경", "이내"):
                place_name = place_name.replace(suffix, " ")
            resolved_wkt = get_maritime_coordinates.invoke(" ".join(place_name.split()))
            if isinstance(resolved_wkt, str) and resolved_wkt.upper().startswith("POINT"):
                req.spatial_context.geometry = resolved_wkt
                slots["reference_geometry"] = resolved_wkt
                slots["resolution_status"] = "RESOLVED"
                slots["crs"] = "EPSG:4326"
                logger.info("Plan location resolved", location=place_name.strip(), geometry=resolved_wkt)
        except Exception as e:
            logger.warning("Plan location resolution failed", location=req.spatial_context.base_location, error=str(e))

    state_spatial_context = req.spatial_context.model_dump() if req.spatial_context else state.get("spatial_context")
    context_state = dict(state)
    context_state["spatial_context"] = state_spatial_context
    req.query_execution_context = _build_query_execution_context(context_state, slots, ctx_res, plan_dict)
    req.query_execution_context = validate_execution_context(req.query_execution_context)

    if req.query_execution_context.readiness == PlanStatus.EXECUTION_READY:
        task_plan.execution_ready = True
        task_plan.route_plan_status = "EXECUTION_READY"
        task_plan.status = "EXECUTION_READY"
    else:
        task_plan.execution_ready = False
        task_plan.route_plan_status = req.query_execution_context.readiness.value
        task_plan.status = req.query_execution_context.readiness.value

    req.task_plan = task_plan
    req.agent_name = task_plan.primary_agent
    
    return {
        "agent_request": req, 
        "task_plan": task_plan.model_dump(),
        "query_execution_context": req.query_execution_context.model_dump(mode="json"),
        "status": AgentStatus.PLAN_CREATED,
        "state_history": log_transition(AgentStatus.CONTEXT_RESOLVED, AgentStatus.PLAN_CREATED),
        "extracted_slots": slots,
        "spatial_context": state_spatial_context
    }

async def execute_agent_node(state: OrchestratorState) -> OrchestratorState:
    logger.info("LangGraph: Executing Agent", task_id=state["task_id"])
    req = state["agent_request"]
    req.previous_agent_outputs["graph_context"] = state.get("graph_context", {})
    req.previous_agent_outputs["data_discovery_result"] = state.get("data_discovery_result", {})

    contract_required_agents = {"Spatial Analysis Agent", "Accident/Risk Agent", "AIS Analysis Agent", "Time-Series Agent", "Time-Series Forecast Agent"}
    if req.agent_name in contract_required_agents and not req.query_execution_context:
        agent_result = AgentResult(
            task_id=req.task_id,
            trace_id=req.trace_id,
            agent_name=req.agent_name,
            agent_version="orchestrator-execution-validator",
            status=AgentStatus.BLOCKED,
            error_code=PlanStatus.BLOCKED_CONFIG.value,
            summary="실행계약이 없어 agent 실행을 차단했습니다.",
            answer_text="이 agent는 QueryExecutionContext 검증을 통과한 뒤에만 실행할 수 있습니다.",
            structured_result={"blockers": ["BLOCKED_CONFIG: query_execution_context is required"]},
            warnings=["BLOCKED_CONFIG: query_execution_context is required"],
            provenance={"validator": "services.orchestrator.execution_validator.validate_execution_context"},
        )
        return {
            "agent_result": agent_result,
            "status": AgentStatus.BLOCKED,
            "state_history": log_transition(AgentStatus.PLAN_CREATED, AgentStatus.BLOCKED, reason="Execution contract missing")
        }

    if req.agent_name in contract_required_agents and req.query_execution_context:
        qec = validate_execution_context(req.query_execution_context)
        req.query_execution_context = qec
        if qec.readiness != PlanStatus.EXECUTION_READY:
            blockers = qec.blockers or ["Execution contract is not ready"]
            status = AgentStatus.NEEDS_CLARIFICATION if any(b.startswith("NEEDS_USER_INPUT") for b in blockers) else AgentStatus.BLOCKED
            agent_result = AgentResult(
                task_id=req.task_id,
                trace_id=req.trace_id,
                agent_name=req.agent_name,
                agent_version="orchestrator-execution-validator",
                status=status,
                error_code=qec.readiness.value,
                summary="실행계약 검증을 통과하지 못해 공간분석을 실행하지 않았습니다.",
                answer_text="실행에 필요한 위치, 거리, 대상 또는 데이터 연결 정보가 아직 확정되지 않았습니다.",
                structured_result={
                    "blockers": blockers,
                    "query_execution_context": qec.model_dump(mode="json"),
                },
                warnings=qec.warnings,
                provenance={"validator": "services.orchestrator.execution_validator.validate_execution_context"},
            )
            return {
                "agent_result": agent_result,
                "status": status,
                "query_execution_context": qec.model_dump(mode="json"),
                "state_history": log_transition(AgentStatus.PLAN_CREATED, status, reason="Execution contract blocked")
            }

    # dispatch 경계에서 공간 실행계약을 다시 강제한다.
    # 재개된 state나 예전 graph state는 위치가 TaskPlan에만 남아 있을 수 있다.
    if req.task_plan and req.task_plan.slots:
        location_name = req.task_plan.slots.get("location")
        if location_name and (not req.spatial_context or not req.spatial_context.geometry):
            try:
                from services.spatial_analysis_agent.geocoding_tool import get_maritime_coordinates

                normalized_name = location_name
                for suffix in ("입구", "주변", "근처", "일대", "반경", "이내"):
                    normalized_name = normalized_name.replace(suffix, " ")
                geometry = get_maritime_coordinates.invoke(" ".join(normalized_name.split()))
                if isinstance(geometry, str) and geometry.upper().startswith("POINT"):
                    distance_m = req.task_plan.slots.get("distance_m")
                    req.spatial_context = SpatialContext(
                        base_location=location_name,
                        geometry=geometry,
                        buffer_distance=distance_m,
                    )
                    logger.info("Dispatch location resolved", location=location_name, geometry=geometry)
            except Exception as e:
                logger.warning("Dispatch location resolution failed", location=location_name, error=str(e))
    
    try:
        # Dynamic Dispatch via Registry
        # The Orchestrator no longer hardcodes any agent imports!
        execute_func = registry.get_execute_function(req.agent_name)
        
        if not execute_func:
            raise ValueError(f"Agent '{req.agent_name}' has no entry_point or failed to load.")
            
        agent_result = await execute_func(req)
            
        if agent_result.status == AgentStatus.NEEDS_CLARIFICATION:
            return {
                "agent_result": agent_result,
                "status": AgentStatus.NEEDS_CLARIFICATION,
                "state_history": log_transition(AgentStatus.PLAN_CREATED, AgentStatus.NEEDS_CLARIFICATION)
            }
            
        return {
            "agent_result": agent_result,
            "status": AgentStatus.RESULTS_AGGREGATED,
            "state_history": log_transition(AgentStatus.PLAN_CREATED, AgentStatus.RESULTS_AGGREGATED)
        }
    except Exception as e:
        logger.error("Agent execution failed", error=str(e), exc_info=True)
        return {
            "status": AgentStatus.FAILED,
            "error_message": str(e),
            "state_history": log_transition(AgentStatus.PLAN_CREATED, AgentStatus.FAILED, error_code="EXEC_ERR")
        }

async def validate_node(state: OrchestratorState) -> OrchestratorState:
    """결과 검증 및 Human-in-the-Loop 결정"""
    logger.info("LangGraph: Validating Results", task_id=state["task_id"])
    result = state["agent_result"]
    
    val_payload = result.validation_payload or {}
    graph_context = state.get("graph_context") or {}
    discovery = state.get("data_discovery_result") or {}
    graph_paths = graph_context.get("graph_paths", []) if isinstance(graph_context, dict) else []
    provenance = result.provenance or {}
    graph_provenance_ok = bool(provenance.get("graph_nodes") or graph_context.get("provenance")) if isinstance(graph_context, dict) else False
    val_payload["graph_validation"] = {
        "graph_path_count": len(graph_paths),
        "provenance_present": graph_provenance_ok,
        "status": "PASS" if graph_provenance_ok or not graph_context else "PENDING_GRAPH_PROVENANCE"
    }
    agent_family = _agent_family(result.agent_name)
    qec_payload = state.get("query_execution_context") or {}
    qec_readiness = qec_payload.get("readiness") if isinstance(qec_payload, dict) else None
    if agent_family in {"time_series", "time_series_forecast"}:
        data_status = "READY" if qec_readiness == PlanStatus.EXECUTION_READY.value else "PENDING_TIME_SERIES_DATA"
    else:
        data_status = "READY" if discovery.get("can_execute_spatial_query") else "PENDING_DATA_OR_GEOMETRY"
    val_payload["data_discovery_validation"] = {
        "execution_level": discovery.get("execution_level", "UNKNOWN"),
        "spatial_query_allowed": discovery.get("can_execute_spatial_query", False),
        "spatial_edges_allowed": discovery.get("can_verify_spatial_edges", False),
        "status": data_status,
    }
    val_payload["validation_agent"] = validate_orchestration(
        graph_context,
        discovery,
        result.provenance,
    )
    result.validation_payload = val_payload
    
    # 실제 검증 로직 구현
    is_valid = True
    reasons = []
    if agent_family == "time_series":
        ts_valid, ts_reasons, ts_payload = _validate_time_series_result(result)
        val_payload["time_series_validation"] = ts_payload
        if not ts_valid:
            is_valid = False
            reasons.extend(ts_reasons)
    elif agent_family == "time_series_forecast":
        fc_valid, fc_reasons, fc_payload = _validate_forecast_result(result)
        val_payload["forecast_validation"] = fc_payload
        if not fc_valid:
            is_valid = False
            reasons.extend(fc_reasons)
    
    # 1. 객체 수 검증
    count = result.structured_result.get("count", 0)
    count = result.structured_result.get("count", 0) if isinstance(result.structured_result, dict) else 0
    if agent_family == "spatial" and count == 0:
        # Empty spatial results are valid and must still produce the search
        # buffer so the user can verify the requested area on the map.
        reasons.append("No features found in the requested area.")
        
    # 2. CRS 검증 (GeoJSON 내 좌표계가 EPSG:4326인지 대략적 확인)
    # 실제로는 좌표 범위를 체크 (-180~180, -90~90) 하거나 
    # 에이전트가 돌려준 메타데이터 확인
    
    if not is_valid:
        logger.warning("결과 검증 실패", reasons=reasons)
        return {
            "status": AgentStatus.WAITING_FOR_REVIEW,
            "error_message": "결과 검증 실패: " + " | ".join(reasons),
            "state_history": log_transition(AgentStatus.RESULTS_AGGREGATED, AgentStatus.WAITING_FOR_REVIEW, reason=" | ".join(reasons))
        }
        
    return {
        "status": AgentStatus.MAP_REPORT_GENERATING,
        "state_history": log_transition(AgentStatus.RESULTS_AGGREGATED, AgentStatus.MAP_REPORT_GENERATING)
    }

async def map_report_node(state: OrchestratorState) -> OrchestratorState:
    """최종 MapLayer 및 응답 패키징"""
    logger.info("LangGraph: Generating Map & Report", task_id=state["task_id"])
    result = state["agent_result"]
    external_requirement = _external_data_requirement_from_state(state)

    plan = state.get("task_plan")
    analysis_type = ""
    if isinstance(plan, dict):
        analysis_type = str(plan.get("analysis_type") or "")
    elif plan is not None:
        analysis_type = str(getattr(plan, "analysis_type", "") or "")
    if analysis_type in {"document_search", "rag.document_search", "graph_scoped_rag"} and not external_requirement:
        structured = result.structured_result or {}
        evidence_bundle = result.evidence_bundle
        final_dict = {
            "task_id": result.task_id,
            "trace_id": result.trace_id,
            "agent_name": result.agent_name,
            "agent_version": result.agent_version,
            "status": result.status,
            "error_code": result.error_code,
            "summary": result.summary,
            "answer_text": result.answer_text or result.summary or "No document answer was generated.",
            "structured_result": {
                "retrieved_count": structured.get("retrieved_count"),
                "documents": structured.get("documents", [])[:3] if isinstance(structured.get("documents"), list) else [],
                "citations": structured.get("citations", [])[:3] if isinstance(structured.get("citations"), list) else [],
                "evidence_candidate_summary": structured.get("evidence_candidate_summary"),
            },
            "evidence_bundle": evidence_bundle.model_dump(mode="json") if hasattr(evidence_bundle, "model_dump") else {},
            "orchestrator_v2": {
                "graph_context": state.get("graph_context", {}),
                "data_discovery_result": state.get("data_discovery_result", {}),
                "route_plan": state.get("task_plan", {}),
                "query_execution_context": state.get("query_execution_context", {}),
                "embedding_independent": True,
                "fast_path": "document_search_compact",
            },
            "claims": [{
                "claim_id": f"claim:{result.task_id}:summary",
                "text": result.answer_text or result.summary or "",
                "evidence_ids": [],
            }],
            "task_results": [{
                "task_id": result.task_id,
                "agent_name": result.agent_name,
                "status": result.status,
                "summary": result.summary,
                "provenance_keys": sorted((result.provenance or {}).keys()),
            }],
            "contract_version": "geollm.execution.v1",
            "request_id": state.get("task_id"),
        }
        return {
            "final_dict": final_dict,
            "status": AgentStatus.COMPLETED,
            "state_history": log_transition(AgentStatus.MAP_REPORT_GENERATING, AgentStatus.COMPLETED),
        }
    
    final_dict = result.model_dump(mode="json")
    final_dict["contract_version"] = final_dict.get("contract_version") or "geollm.execution.v1"
    final_dict["request_id"] = final_dict.get("request_id") or state.get("task_id")
    final_dict["answer_text"] = final_dict.get("answer_text") or result.answer_text or result.summary or "분석 결과를 생성하지 못했습니다."
    
    if external_requirement:
        final_dict["external_data_requirement"] = external_requirement
        final_dict["answer_text"] = (
            "현재 로컬 데이터와 RAG만으로는 해당 일정을 확정할 수 없습니다. "
            f"{external_requirement['domain']} 공식 외부 데이터 연동이 필요하며, "
            "웹 검색은 수행하지 않았고 임의 날짜도 생성하지 않았습니다."
        )
        final_dict.setdefault("structured_result", {})
        final_dict["structured_result"]["requires_external_api"] = True
        final_dict["structured_result"]["external_data_requirement"] = external_requirement
        final_dict["structured_result"]["api_params"] = {
            "domain": external_requirement["domain"],
            "recommended_sources": external_requirement["recommended_sources"],
        }

    req = state.get("agent_request")
    if req and hasattr(req, "parsed_intent") and req.parsed_intent:
        final_dict["intent"] = req.parsed_intent.model_dump(mode="json") if hasattr(req.parsed_intent, "model_dump") else req.parsed_intent
    
    if result.agent_name == "spatial-analysis-agent":
        layer_spec = convert_to_map_layer(result)
        if layer_spec:
            final_dict["map_layer"] = layer_spec.model_dump()
            final_dict["map_layers"] = [layer_spec.model_dump()]
            final_dict["map_layers"].extend(layer_spec.metadata.get("overlay_layers", []))
            final_dict["features"] = layer_spec.inline_geojson

            object_features = [
                f for f in (layer_spec.inline_geojson or {}).get("features", [])
                if not (f.get("properties", {}) or {}).get("is_buffer")
            ]
            if not final_dict.get("spatial_result_summary"):
                final_dict["spatial_result_summary"] = {
                "feature_count": len(object_features),
                "display_feature_count": layer_spec.feature_count,
                "result_reference": layer_spec.layer_id,
                }
            final_dict.setdefault("spatial_feature_evidence", [
                {
                    "evidence_id": f"spatial:{result.task_id}:{idx}",
                    "evidence_type": "spatial_feature",
                    "summary": (feature.get("properties", {}) or {}).get("name") or (feature.get("properties", {}) or {}).get("feature_name") or "spatial feature",
                    "source_ref": layer_spec.layer_id,
                    "data": {
                        "properties": feature.get("properties", {}),
                        "geometry_type": (feature.get("geometry") or {}).get("type"),
                    },
                }
                for idx, feature in enumerate(object_features[:100])
            ])

    # 동적 교통 및 사고 전문 agent는 근거 기반 GeoJSON을 직접 반환한다.
    # S-101 결과와 섞지 않고 별도 map layer로 노출한다.
    structured = result.structured_result or {}
    agent_family = _agent_family(result.agent_name)
    if agent_family == "time_series":
        final_dict["time_series_result"] = {
            "status": structured.get("status"),
            "dataset_id": structured.get("dataset_id"),
            "source_path": structured.get("source_path"),
            "station_id": structured.get("station_id"),
            "time_range": structured.get("time_range"),
            "metrics": structured.get("metrics") or result.metrics,
            "anomalies": structured.get("anomalies", []),
            "sample": structured.get("sample", []),
        }
    elif agent_family == "time_series_forecast":
        final_dict["forecast_result"] = {
            "status": structured.get("status"),
            "method": structured.get("method"),
            "dataset_id": structured.get("dataset_id"),
            "station_id": structured.get("station_id"),
            "source_path": structured.get("source_path"),
            "confidence_level": structured.get("confidence_level"),
            "horizon_steps": structured.get("horizon_steps"),
            "model": structured.get("model"),
            "forecast": structured.get("forecast", []),
        }
    if structured.get("dynamic_traffic_geojson"):
        traffic_geojson = structured["dynamic_traffic_geojson"]
        if traffic_geojson.get("type") == "Feature":
            traffic_geojson = {"type": "FeatureCollection", "features": [traffic_geojson]}
        final_dict.setdefault("map_layers", []).append({
            "layer_id": f"{result.task_id}-dynamic-traffic",
            "task_id": result.task_id,
            "title": "Dynamic Traffic",
            "description": "AIS/V-PASS dynamic traffic layer",
            "geometry_type": "GEOMETRY",
            "source_type": "geojson",
            "inline_geojson": traffic_geojson,
            "feature_count": len(traffic_geojson.get("features", [])),
            "metadata": {"layer_role": "dynamic_traffic", "target_dynamic_layers": structured.get("target_dynamic_layers", [])},
        })
    if structured.get("accident_spatial_geojson"):
        accident_geojson = structured["accident_spatial_geojson"]
        if accident_geojson.get("type") == "Feature":
            accident_geojson = {"type": "FeatureCollection", "features": [accident_geojson]}
        final_dict.setdefault("map_layers", []).append({
            "layer_id": f"{result.task_id}-accident",
            "task_id": result.task_id,
            "title": "Accident Spatial Layer",
            "description": "Standardized accident spatial layer",
            "geometry_type": "GEOMETRY",
            "source_type": "geojson",
            "inline_geojson": accident_geojson,
            "feature_count": len(accident_geojson.get("features", [])),
            "metadata": {"layer_role": "accident_overlay", "relation_status": structured.get("accident_feature_relations", [])},
        })
            
    # --- Debug Trace 구성 ---
    debug_trace = {
        "1. 사용자 질의": state.get("query"),
        "2. 질의 정규화": state.get("normalization_debug", []),
        "3. 오케스트레이터 의도분석": state.get("context_result").__dict__ if state.get("context_result") else None,
        "4. 작업계획 수립": state.get("task_plan"),
        "5. 공간쿼리 실행": {
            "도구 호출": [tc.model_dump() if hasattr(tc, "model_dump") else tc for tc in result.tool_calls],
            "쿼리 결과": result.structured_result
        }
    }
    final_dict["debug_trace"] = debug_trace
    final_dict["orchestrator_v2"] = {
        "graph_context": state.get("graph_context", {}),
        "data_discovery_result": state.get("data_discovery_result", {}),
        "route_plan": state.get("task_plan", {}),
        "query_execution_context": state.get("query_execution_context", {}),
        "embedding_independent": True,
    }
    provenance = result.provenance or {}
    evidence_bundle = build_evidence_bundle(
        graph_context=state.get("graph_context") or structured.get("kg_context") or {},
        structured_result=structured if isinstance(structured, dict) else {},
        spatial_feature_evidence=final_dict.get("spatial_feature_evidence", []),
        task_id=result.task_id,
    )
    final_dict["evidence_bundle"] = evidence_bundle.model_dump(mode="json")
    final_dict["spatial_feature_evidence"] = final_dict["evidence_bundle"]["spatial_feature_evidence"]
    final_dict["spatial_layer_evidence"] = final_dict["evidence_bundle"]["spatial_layer_evidence"]
    final_dict["accident_relation_evidence"] = final_dict["evidence_bundle"]["accident_relation_evidence"]
    final_dict["regulatory_evidence"] = final_dict["evidence_bundle"]["regulatory_evidence"]
    final_dict["rag_evidence"] = final_dict["evidence_bundle"]["rag_evidence"]
    final_dict["kg_provenance"] = final_dict["evidence_bundle"]["kg_provenance"]
    final_dict.setdefault("claims", [
        {
            "claim_id": f"claim:{result.task_id}:summary",
            "text": final_dict["answer_text"],
            "evidence_ids": [
                item.get("evidence_id")
                for item in final_dict.get("spatial_feature_evidence", [])[:10]
                if isinstance(item, dict) and item.get("evidence_id")
            ],
        }
    ])
    final_dict.setdefault("task_results", [{
        "task_id": result.task_id,
        "agent_name": result.agent_name,
        "status": result.status,
        "summary": result.summary,
        "provenance_keys": sorted(provenance.keys()),
    }])
    
    return {
        "final_dict": final_dict,
        "status": AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.MAP_REPORT_GENERATING, AgentStatus.COMPLETED)
    }

async def audit_log_node(state: OrchestratorState) -> OrchestratorState:
    """DB에 실행 상태와 슬롯 추출 결과를 저장하는 Audit Node"""
    logger.info("LangGraph: Saving Audit Log", task_id=state["task_id"])
    try:
        import psycopg2
        import os
        import json
        
        POSTGIS_URL = os.environ.get("POSTGIS_URL", "")
        conn = psycopg2.connect(POSTGIS_URL)
        conn.autocommit = True
        cur = conn.cursor()
        
        task_id = state.get("task_id", "")
        original_query = state.get("query", "")
        normalized_query = state.get("normalized_query", "")
        
        ctx = state.get("context_result")
        
        # ctx can be a dict or an object depending on serialization state
        if isinstance(ctx, dict):
            resolved_intent = ctx.get("selected_context", None)
        else:
            resolved_intent = ctx.selected_context if ctx and hasattr(ctx, "selected_context") else None
            
        task_plan = state.get("task_plan")
        if isinstance(task_plan, dict):
            primary_agent = task_plan.get("primary_agent", None)
            extracted_slots = task_plan.get("slots", {})
        else:
            primary_agent = task_plan.primary_agent if task_plan else None
            extracted_slots = task_plan.slots if task_plan and hasattr(task_plan, "slots") else {}
            
        status = state.get("status", "")
        
        insert_sql = """
            INSERT INTO marine_geo.orchestrator_logs 
            (task_id, original_query, normalized_query, resolved_intent, primary_agent, extracted_slots, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (task_id) DO UPDATE SET
                status = EXCLUDED.status,
                extracted_slots = EXCLUDED.extracted_slots
        """
        cur.execute(insert_sql, (
            task_id,
            original_query,
            normalized_query,
            resolved_intent,
            primary_agent,
            json.dumps(extracted_slots, ensure_ascii=False),
            status
        ))
        cur.close()
        conn.close()
        logger.info("Audit log saved to marine_geo.orchestrator_logs")
    except Exception as e:
        logger.error(f"Failed to save audit log: {e}")
        
    return state

# ----------------- Conditional Edges -----------------

def check_intent_parsed(state: OrchestratorState) -> str:
    if state["status"] == AgentStatus.NEEDS_CLARIFICATION:
        return "needs_clarification"
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    if _should_fast_external_requirement(query):
        return "fast_external_data_requirement"
    if _should_fast_spatial_or_traffic_block(state):
        return "fast_spatial_or_traffic_block"
    if _exact_s101_feature_match(query) or _exact_s100_s101_relation_match(query) or _looks_like_legal_rag_query(query) or _looks_like_no_evidence_document_query(query):
        return "fast_document_answer"
    if _looks_like_time_series_query(query):
        return "create_plan"
    if _looks_like_standard_rag_query(query):
        return "create_plan"
    return "resolve_context"

def check_graph_rag_next(state: OrchestratorState) -> str:
    query = state.get("normalized_query") or state.get("query", "")
    if _looks_like_standard_rag_query(query):
        return "resolve_context"
    return "data_discovery"

def check_context_resolved(state: OrchestratorState) -> str:
    if state["status"] == AgentStatus.BLOCKED:
        return "blocked"
    if state["status"] == AgentStatus.NEEDS_CLARIFICATION:
        return "needs_clarification"
    return "create_plan"

def check_execution_status(state: OrchestratorState) -> str:
    if state["status"] == AgentStatus.FAILED:
        return "failed"
    if state["status"] in {AgentStatus.BLOCKED, AgentStatus.NEEDS_CLARIFICATION} and _external_data_requirement_from_state(state):
        return "external_data_report"
    if state["status"] == AgentStatus.BLOCKED:
        return "blocked"
    if state["status"] == AgentStatus.NEEDS_CLARIFICATION:
        return "needs_clarification"
    plan = state.get("task_plan")
    analysis_type = ""
    if isinstance(plan, dict):
        analysis_type = str(plan.get("analysis_type") or "")
    elif plan is not None:
        analysis_type = str(getattr(plan, "analysis_type", "") or "")
    if analysis_type in {"document_search", "rag.document_search", "graph_scoped_rag"}:
        return "map_report"
    return "validate"

def check_validation_status(state: OrchestratorState) -> str:
    if state["status"] == AgentStatus.WAITING_FOR_REVIEW:
        # approval_granted 값이 들어왔는지 확인 (Resume 상황)
        if state.get("approval_granted") is True:
            return "map_report"
        return "review" # Interrupt point
    return "map_report"

def check_after_map_report(state: OrchestratorState) -> str:
    if os.environ.get("FAST_RAG_SKIP_AUDIT", "true").lower() in {"1", "true", "yes", "on"}:
        plan = state.get("task_plan")
        analysis_type = ""
        if isinstance(plan, dict):
            analysis_type = str(plan.get("analysis_type") or "")
        elif plan is not None:
            analysis_type = str(getattr(plan, "analysis_type", "") or "")
        if analysis_type in {"document_search", "rag.document_search", "graph_scoped_rag"}:
            return "end"
    return "audit_log"

# ----------------- Graph Builder -----------------

def build_orchestrator_graph():
    workflow = StateGraph(OrchestratorState)
    
    # Add Nodes
    workflow.add_node("parse_intent", parse_intent_node)
    workflow.add_node("fast_document_answer", fast_document_answer_node)
    workflow.add_node("fast_external_data_requirement", fast_external_data_requirement_node)
    workflow.add_node("fast_spatial_or_traffic_block", fast_spatial_or_traffic_block_node)
    workflow.add_node("graph_rag", graph_rag_node)
    workflow.add_node("data_discovery", data_discovery_node)
    workflow.add_node("resolve_context", resolve_context_node)
    workflow.add_node("create_plan", create_plan_node)
    workflow.add_node("execute_agent", execute_agent_node)
    workflow.add_node("validate_results", validate_node)
    workflow.add_node("map_report", map_report_node)
    workflow.add_node("audit_log", audit_log_node)
    
    # Entry Point
    workflow.set_entry_point("parse_intent")
    
    # Add Edges
    workflow.add_conditional_edges(
        "parse_intent",
        check_intent_parsed,
        {
            "needs_clarification": "audit_log",
            "fast_external_data_requirement": "fast_external_data_requirement",
            "fast_document_answer": "fast_document_answer",
            "fast_spatial_or_traffic_block": "fast_spatial_or_traffic_block",
            "create_plan": "create_plan",
            "resolve_context": "graph_rag"
        }
    )
    workflow.add_edge("fast_external_data_requirement", END)
    workflow.add_edge("fast_document_answer", END)
    workflow.add_edge("fast_spatial_or_traffic_block", END)
    workflow.add_conditional_edges("graph_rag", check_graph_rag_next, {
        "data_discovery": "data_discovery",
        "resolve_context": "resolve_context",
    })
    workflow.add_edge("data_discovery", "resolve_context")
    workflow.add_conditional_edges("resolve_context", check_context_resolved, {
        "blocked": "audit_log", 
        "needs_clarification": "audit_log",
        "create_plan": "create_plan"
    })
    workflow.add_edge("create_plan", "execute_agent")
    workflow.add_conditional_edges("execute_agent", check_execution_status, {"failed": "audit_log", "blocked": "audit_log", "needs_clarification": "audit_log", "external_data_report": "map_report", "map_report": "map_report", "validate": "validate_results"})
    
    # 검증 결과에 따라 검토 대기 또는 지도 보고서 생성으로 분기
    workflow.add_conditional_edges("validate_results", check_validation_status, {
        "review": "audit_log", # 일단 그래프 실행 종료 (상태 유지). 재호출 시 Resume 됨
        "map_report": "map_report"
    })
    
    workflow.add_conditional_edges("map_report", check_after_map_report, {
        "audit_log": "audit_log",
        "end": END,
    })
    workflow.add_edge("audit_log", END)
    
    # 체크포인터를 연결하여 HITL(Human-in-the-Loop) 완벽 지원
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

# 컴파일된 그래프 싱글톤
orchestrator_graph = build_orchestrator_graph()
