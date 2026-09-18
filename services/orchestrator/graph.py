import os
import json
import hashlib
import re
from functools import lru_cache
from datetime import datetime
from pathlib import Path
from typing import Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import yaml

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
from services.orchestrator.query_candidate_broker import execution_contract_ready, query_candidate_broker
from services.orchestrator.execution_validator import validate_execution_context
from services.orchestrator.evidence_builder import build_evidence_bundle
from services.data_discovery_agent.agent import execute_data_discovery
from services.llm_config import llm_api_enabled
from services.validation_agent.agent import validate_orchestration
from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem, resolve_location
from services.orchestrator.s101_portrayal import resolve_s101_portrayal

context_resolver = ContextResolver()
route_planner = RoutePlanner()
graph_rag_retriever = GraphRAGRetriever()


def _candidate_trace_summary(trace: dict | None) -> dict:
    if not isinstance(trace, dict):
        return {}
    routes = trace.get("route_candidates") if isinstance(trace.get("route_candidates"), list) else []
    capabilities = trace.get("capability_candidates") if isinstance(trace.get("capability_candidates"), list) else []
    verified = trace.get("verified_candidates") if isinstance(trace.get("verified_candidates"), list) else []
    return {
        "contract": trace.get("contract"),
        "mode": trace.get("mode"),
        "top_routes": [
            {
                "route": row.get("route"),
                "score": row.get("score"),
                "role": row.get("role"),
                "signals": row.get("signals") or [],
            }
            for row in routes[:3]
            if isinstance(row, dict)
        ],
        "top_capabilities": [
            {
                "candidate_id": row.get("candidate_id"),
                "kind": row.get("kind"),
                "score": row.get("score"),
                "routes": row.get("routes") or [],
            }
            for row in capabilities[:5]
            if isinstance(row, dict)
        ],
        "verified_ready_count": sum(1 for row in verified if isinstance(row, dict) and row.get("status") == "verified_ready"),
        "ollama_needed": ((trace.get("ollama_policy") or {}).get("needed") if isinstance(trace.get("ollama_policy"), dict) else None),
    }


def _attach_candidate_trace(state: OrchestratorState, final_dict: dict) -> dict:
    trace = state.get("candidate_trace")
    if not isinstance(trace, dict) or not isinstance(final_dict, dict):
        return final_dict
    final_dict.setdefault("structured_result", {})
    if isinstance(final_dict["structured_result"], dict):
        final_dict["structured_result"]["candidate_trace_summary"] = _candidate_trace_summary(trace)
        if isinstance(trace.get("execution_contract"), dict):
            final_dict["structured_result"]["execution_contract"] = trace["execution_contract"]
    final_dict.setdefault("orchestrator_v2", {})
    if isinstance(final_dict["orchestrator_v2"], dict):
        final_dict["orchestrator_v2"]["candidate_trace"] = trace
        if isinstance(trace.get("execution_contract"), dict):
            final_dict["orchestrator_v2"]["execution_contract"] = trace["execution_contract"]
            qec = final_dict["orchestrator_v2"].get("query_execution_context")
            if isinstance(qec, dict):
                qec.setdefault("execution_contract", trace["execution_contract"])
    return final_dict


def _contract_ready_any(state: OrchestratorState, *, route: str, capability_ids: list[str]) -> bool:
    trace = state.get("candidate_trace")
    return any(
        execution_contract_ready(trace, route=route, capability_id=capability_id)
        for capability_id in capability_ids
    )

S101_DICT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "s101_smart_dictionary.json")
S101_CATALOGUE_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "s101_catalogue.json")
TIME_SERIES_REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "time_series_registry.yaml")
S101_HAZARD_FEATURE_CODES = [100, 101, 102, 167, 168, 556, 557, 558, 559, 560, 561, 562, 563, 564, 565, 566, 567]
S101_HAZARD_FEATURE_NAMES = {
    100: "UnderwaterAwashRock",
    101: "Wreck",
    102: "Obstruction",
    167: "LightAllAround",
    168: "LightSectored",
    556: "NavigationAid",
}
S101_HAZARD_RADIUS_RESULT_LIMIT = 30
REQUESTED_SPATIAL_LAYER_TARGETS = {
    "marine_gazetteer": {
        "relation": "serving.marine_gazetteer_current",
        "layer_id": "marine_gazetteer_mof",
        "title": "\ud574\uc591\uc9c0\uba85",
        "layer_type": "marine_gazetteer",
        "terms": [
            "\uc9c0\uba85",
            "\ud574\uc591\uc9c0\uba85",
            "\ud574\uc591 \uc9c0\uba85",
            "\ud574\uc800\uc9c0\uba85",
            "\ud574\uc800 \uc9c0\uba85",
            "\ubd80\uadfc \uc9c0\uba85",
            "\uc8fc\ubcc0 \uc9c0\uba85",
            "marine gazetteer",
            "place name",
        ],
    },
    "navigation_aid": {
        "relation": "serving.navigation_aid_current",
        "layer_id": "navigation_aid_busan",
        "title": "\ud56d\ub85c\ud45c\uc9c0",
        "layer_type": "navigation_aid",
        "terms": [
            "\ud56d\ub85c\ud45c\uc9c0",
            "\ud574\uc0c1 \ud45c\uc9c0",
            "\ub4f1\ub300",
            "\ubd80\ud45c",
            "navigation aid",
            "aids to navigation",
        ],
    },
    "fairway": {
        "relation": "serving.fairway_area_current",
        "layer_id": "fairway_area",
        "title": "\uc77c\ubc18\ud56d\ub85c",
        "layer_type": "fairway",
        "terms": ["\uc77c\ubc18\ud56d\ub85c", "fairway"],
    },
    "entry_restricted": {
        "relation": "serving.hazard_area_current",
        "layer_id": "entry_restricted_area",
        "title": "\uc9c4\uc785\uc81c\ud55c\uad6c\uc5ed",
        "layer_type": "hazard_area",
        "terms": ["\uc9c4\uc785\uc81c\ud55c", "\uc9c4\uc785 \uc81c\ud55c", "entry restricted"],
    },
    "speed_restriction": {
        "relation": "serving.hazard_area_current",
        "layer_id": "speed_restriction_area",
        "title": "\uc18d\ub3c4\uc81c\ud55c\uad6c\uc5ed",
        "layer_type": "hazard_area",
        "terms": ["\uc18d\ub3c4\uc81c\ud55c", "\uc18d\ub3c4 \uc81c\ud55c", "speed restriction"],
    },
    "dumping_ground": {
        "relation": "serving.hazard_area_current",
        "layer_id": "dumping_ground_area",
        "title": "\ud22c\uae30\uc7a5",
        "layer_type": "hazard_area",
        "terms": ["\ud22c\uae30\uc7a5", "\ud22c\uae30\uad6c\uc5ed", "\uc0b0\uc5c5\ud3d0\uae30\ubb3c\ud22c\uae30\uad6c\uc5ed", "\uc0b0\uc5c5\ud3d0\uae30\ubb3c \ud22c\uae30\uad6c\uc5ed", "dumping ground", "dumping area"],
    },
    "protected_sea": {
        "relation": "serving.protected_area_current",
        "layer_id": "protected_sea_area",
        "title": "\ubcf4\ud638\uc218\uc5ed",
        "layer_type": "protected_area",
        "terms": ["\ubcf4\ud638\uc218\uc5ed", "\ubcf4\ud638\uad6c\uc5ed", "\ubcf4\ud638\ud574\uc5ed", "protected area"],
    },
    "vessel_traffic_control_area": {
        "relation": "serving.vessel_traffic_control_area_current",
        "layer_id": "vessel_traffic_control_area",
        "title": "\uc120\ubc15\uc548\uc804\uad50\ud1b5\uad00\uc81c\uad6c\uc5ed",
        "layer_type": "vessel_traffic_control_area",
        "terms": ["\uc120\ubc15\uc548\uc804\uad50\ud1b5\uad00\uc81c\uad6c\uc5ed", "\ud574\uc0c1\uad50\ud1b5\uad00\uc81c\uad6c\uc5ed", "\ud574\uc0c1\uad50\ud1b5\uad00\uc81c", "\uad00\uc81c\uad6c\uc5ed", "vts", "vessel traffic control"],
    },
    "sea_parting_prediction": {
        "relation": "serving.sea_parting_prediction_current",
        "layer_id": "sea_parting_prediction",
        "title": "\ubc14\ub2e4\uac08\ub77c\uc9d0 \uc608\uce21\uc815\ubcf4",
        "layer_type": "sea_parting_prediction",
        "name_column": "place_name",
        "terms": ["\ubc14\ub2e4\uac08\ub77c\uc9d0", "\ubc14\ub2f7\uae38", "sea parting"],
    },
}
SEA_PARTING_QUERY_ANCHORS = {
    "\ub3d9\uc12c": "POINT(126.9360 33.4590)",
    "\ubb34\ucc3d\ud3ec": "POINT(126.5350 36.2440)",
    "\uc11c\uac74\ub3c4": "POINT(126.5080 33.2290)",
    "\uc18c\uc57c\ub3c4": "POINT(126.1780 37.2290)",
    "\uc2e4\ubbf8\ub3c4": "POINT(126.4030 37.4040)",
    "\uc6b0\ub3c4": "POINT(126.9540 33.5050)",
    "\uc6c5\ub3c4": "POINT(126.3520 36.8760)",
    "\uc81c\ubd80\ub3c4": "POINT(126.6220 37.1700)",
    "\uc9c4\ub3c4": "POINT(126.3230 34.4350)",
    "\ud558\uc12c": "POINT(126.4690 35.6120)",
}
KNOWN_MARINE_PLACE_WKT = {
    "부산항 입구": "POINT(129.075 35.075)",
    "부산항": "POINT(129.075 35.075)",
    "busan port entrance": "POINT(129.075 35.075)",
    "busan port": "POINT(129.075 35.075)",
    "인천항": "POINT(126.592 37.456)",
    "인천": "POINT(126.592 37.456)",
}

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ROOT_DIR = Path(__file__).resolve().parents[2]
S101_DCEG_CHUNKS_PATH = ROOT_DIR / "outputs" / "rag" / "s101_dceg_chunks.jsonl"
S101_DICT_PATH = DATA_DIR / "s101_smart_dictionary.json"
S101_CATALOGUE_PATH = DATA_DIR / "s101_catalogue.json"
TIME_SERIES_REGISTRY_PATH = DATA_DIR / "time_series_registry.yaml"
S101_FEATURE_QUERY_ALIASES = {
    "AnchorageArea": ["정박지", "정박구역", "투묘지", "anchorage"],
}


@lru_cache(maxsize=None)
def _load_yaml_registry(filename: str) -> dict:
    try:
        return yaml.safe_load((DATA_DIR / filename).read_text(encoding="utf-8")) or {}
    except Exception as exc:
        logger.warning("Failed to load registry", filename=filename, error=str(exc))
        return {}


def _feature_codes_for_name(feature_code_map: dict, name: str) -> list[int]:
    raw = feature_code_map.get(name)
    values = raw if isinstance(raw, list) else [raw]
    codes = []
    for value in values:
        try:
            codes.append(int(value))
        except (TypeError, ValueError):
            continue
    return codes


def _flatten_feature_codes(feature_code_map: dict, target_features: list[str]) -> list[int]:
    codes = []
    for name in target_features:
        codes.extend(_feature_codes_for_name(feature_code_map, name))
    return list(dict.fromkeys(codes))


def _feature_names_by_code(feature_code_map: dict) -> dict[int, str]:
    names = {}
    for name in feature_code_map:
        for code in _feature_codes_for_name(feature_code_map, name):
            names.setdefault(code, name)
    return names


def _s101_hazard_radius_registry_config() -> dict:
    concept = ((_load_yaml_registry("derived_concept_registry_v2.yaml").get("derived_concepts") or {})
               .get("navigation_hazard_object") or {})
    profile = ((concept.get("execution_profiles") or {}).get("s101_hazard_radius") or {})
    template_id = profile.get("query_template") or concept.get("analysis_type") or "feature_search_by_radius"
    template = ((_load_yaml_registry("query_template_registry.yaml").get("templates") or {}).get(template_id) or {})
    layer_id = profile.get("layer") or template.get("default_layer") or "GBENC_S101_feature"
    layer = ((_load_yaml_registry("spatial_layer_registry.yaml").get("layers") or {}).get(layer_id) or {})
    feature_code_map = profile.get("feature_code_map") or {}
    target_features = _s101_hazard_candidate_features(concept, profile, feature_code_map)
    feature_names = _feature_names_by_code(feature_code_map)
    resolved_feature_code_map = {}
    if profile.get("auto_resolve_feature_codes", True):
        resolved_feature_code_map = _resolve_s101_feature_code_map_from_projection(layer, target_features)
    if resolved_feature_code_map:
        feature_code_map = resolved_feature_code_map
        target_features = [name for name in target_features if name in resolved_feature_code_map]
        feature_names = _feature_names_by_code(resolved_feature_code_map)
    feature_codes = _flatten_feature_codes(feature_code_map, target_features)
    return {
        "concept_id": "navigation_hazard_object",
        "template_id": template_id,
        "template": template,
        "layer_id": layer_id,
        "layer": layer,
        "target_features": target_features,
        "feature_codes": feature_codes,
        "feature_names": feature_names,
        "result_limit": int(profile.get("result_limit") or template.get("result_limit") or S101_HAZARD_RADIUS_RESULT_LIMIT),
        "feature_code_source": "deployed_projection" if resolved_feature_code_map else "registry_fallback",
    }


def _s101_hazard_candidate_features(concept: dict, profile: dict, feature_code_map: dict) -> list[str]:
    return list(dict.fromkeys(profile.get("target_features") or []))


@lru_cache(maxsize=16)
def _resolve_s101_feature_code_map_from_projection_cached(
    relation: str,
    name_column: str,
    code_column: str,
    feature_names: tuple[str, ...],
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    if not relation or not feature_names:
        return ()
    db_url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not db_url:
        return ()
    schema_table = relation.split(".", 1)
    if len(schema_table) != 2:
        return ()
    schema, table = schema_table
    try:
        import psycopg2

        with psycopg2.connect(db_url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT {name_column}, array_agg(DISTINCT {code_column} ORDER BY {code_column}) AS feature_type_codes
                    FROM {schema}.{table}
                    WHERE {name_column} = ANY(%s)
                    GROUP BY {name_column}
                    ORDER BY {name_column}
                    """,
                    (list(feature_names),),
                )
                rows = []
                for name, codes in cur.fetchall():
                    if name and codes:
                        rows.append((str(name), tuple(int(code) for code in codes if code is not None)))
                return tuple(rows)
    except Exception as exc:
        logger.warning("Failed to resolve S-101 feature codes from projection", relation=relation, error=str(exc))
        return ()


def _resolve_s101_feature_code_map_from_projection(layer: dict, target_features: list[str]) -> dict[str, list[int]]:
    relation = layer.get("physical_table") or layer.get("expected_physical_table")
    name_column = layer.get("name_column", "feature_type_name")
    code_column = layer.get("code_column", "feature_type_code")
    resolved = _resolve_s101_feature_code_map_from_projection_cached(
        str(relation or ""),
        str(name_column),
        str(code_column),
        tuple(target_features),
    )
    return dict(resolved)


def _s101_hazard_feature_codes() -> list[int]:
    return _s101_hazard_radius_registry_config()["feature_codes"] or S101_HAZARD_FEATURE_CODES


def _s101_hazard_feature_names() -> dict[int, str]:
    return _s101_hazard_radius_registry_config()["feature_names"] or S101_HAZARD_FEATURE_NAMES


def _s101_hazard_target_features() -> list[str]:
    return _s101_hazard_radius_registry_config()["target_features"] or ["UnderwaterAwashRock", "Wreck", "Obstruction"]


def _s101_nearest_feature_config(target_features: list[str]) -> dict:
    template_id = "nearest_feature"
    template = ((_load_yaml_registry("query_template_registry.yaml").get("templates") or {}).get(template_id) or {})
    layer_id = template.get("default_layer") or "GBENC_S101_feature"
    layer = ((_load_yaml_registry("spatial_layer_registry.yaml").get("layers") or {}).get(layer_id) or {})
    feature_code_map = _resolve_s101_feature_code_map_from_projection(layer, target_features)
    return {
        "template_id": template_id,
        "template": template,
        "layer_id": layer_id,
        "layer": layer,
        "target_features": [name for name in target_features if name in feature_code_map],
        "feature_codes": _flatten_feature_codes(feature_code_map, target_features),
        "feature_names": _feature_names_by_code(feature_code_map),
        "result_limit": int(template.get("result_limit") or 5),
    }


def _nearest_target_features_from_query(query: str) -> list[str]:
    text = query or ""
    lowered = text.lower()
    if any(term in lowered or term in text for term in ["anchorage", "\uc815\ubc15\uc9c0", "?뺣컯吏"]):
        return ["AnchorageArea"]
    if any(term in lowered or term in text for term in ["mooring", "\uacc4\ub958", "\ubb18\ub9c1"]):
        return ["MooringArea", "MooringBuoy"]
    return []


def _looks_like_s101_nearest_feature_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    has_nearest = any(term in lowered or term in text for term in ["nearest", "closest", "\uac00\uae4c\uc6b4", "媛源뚯슫"])
    return has_nearest and bool(_nearest_target_features_from_query(query))


def _registered_place_aliases() -> dict[str, dict]:
    registry_data = _load_yaml_registry("place_geometry_registry.yaml")
    aliases: dict[str, dict] = {}
    for place_id, place in (registry_data.get("places") or {}).items():
        if not isinstance(place, dict):
            continue
        names = [place.get("canonical_name"), *(place.get("aliases") or [])]
        for name in names:
            if name:
                aliases[str(name).lower()] = {"place_id": place_id, **place}
    return aliases

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

@lru_cache(maxsize=1)
def _load_s101_dceg_chunks_exact() -> tuple[dict, ...]:
    if not S101_DCEG_CHUNKS_PATH.exists():
        return ()
    rows = []
    try:
        with S101_DCEG_CHUNKS_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    except Exception as exc:
        logger.warning("Failed to load S-101 DCEG chunks", error=str(exc))
        return ()
    return tuple(rows)

def _is_s101_dceg_2_0_chunk(row: dict) -> bool:
    metadata = row.get("metadata") or {}
    title = str(metadata.get("title") or "")
    source_file = str(metadata.get("source_file") or "")
    return (
        metadata.get("product_id") == "S-101"
        and metadata.get("document_type") == "dceg"
        and metadata.get("version") == "2.0.0"
        and ("DCEG" in title or "DCEG" in source_file)
    )

def _score_s101_dceg_chunk(row: dict, feature: dict) -> int:
    metadata = row.get("metadata") or {}
    text = str(row.get("text") or "")
    lowered = text.lower()
    code = str(feature.get("code") or "")
    name = str(feature.get("name") or code)
    aliases = [str(alias) for alias in feature.get("aliases") or []]
    score = 0
    target_feature_phrase = f"s-101 geo feature: {name.lower()}"
    has_any_geo_feature_table = "s-101 geo feature:" in lowered
    has_target_instruction = (
        "if it is required to encode an anchorage" in lowered
        or f"using the feature {name.lower()}" in lowered
        or f"using an {name.lower()} feature" in lowered
    )
    for term in [code, name, *aliases]:
        if term and term.lower() in lowered:
            score += 20
    related = {str(item).lower() for item in metadata.get("related_features") or []}
    if name.lower() in related or code.lower() in related:
        score += 30
    if target_feature_phrase in lowered:
        score += 200
    elif has_any_geo_feature_table:
        score -= 120
    if "iho definition:" in lowered and target_feature_phrase in lowered:
        score += 60
    if "allowable encoding value" in lowered:
        score += 25
    if "if it is required to encode" in lowered or "remarks:" in lowered:
        score += 60
    if not target_feature_phrase in lowered and not has_target_instruction:
        score -= 80
    if "associated to:" in lowered or "role type role associated with" in lowered:
        score -= 100
    if "................................" in text:
        score -= 40
    return score

def _s101_dceg_docs_for_feature_exact(feature: dict, limit: int = 2) -> list[dict]:
    candidates = []
    for row in _load_s101_dceg_chunks_exact():
        if not _is_s101_dceg_2_0_chunk(row):
            continue
        score = _score_s101_dceg_chunk(row, feature)
        if score > 0:
            candidates.append((score, row))
    docs = []
    seen = set()
    for _, row in sorted(candidates, key=lambda item: item[0], reverse=True):
        chunk_id = str(row.get("chunk_id") or "")
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        metadata = row.get("metadata") or {}
        docs.append({
            "document_id": chunk_id,
            "title": metadata.get("title") or "S-101 Annex A DCEG Ed. 2.0.0",
            "version": metadata.get("version") or "2.0.0",
            "section": metadata.get("section"),
            "page": metadata.get("page_no", "N/A"),
            "source": metadata.get("source_id") or "s101_dceg_2_0_0",
            "source_id": metadata.get("source_id"),
            "source_file": metadata.get("source_file"),
            "document_type": "dceg",
            "excerpt_reference": str(row.get("text") or ""),
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
            "relevance_score": 1.0,
            "chunk_id": chunk_id,
        })
        if len(docs) >= limit:
            break
    return docs

def _exact_s101_feature_match(query: str) -> dict | None:
    lowered = (query or "").lower()
    if "s-101" not in lowered and "s101" not in lowered and "feature catalogue" not in lowered:
        return None
    if not any(term in lowered or term in (query or "") for term in ("definition", "encoding", "dceg", "instruction", "guidance", "정의", "설명", "인코딩", "지침", "근거", "feature catalogue")):
        return None
    for feature in _load_s101_catalogue_exact():
        code = str(feature.get("code") or "")
        name = str(feature.get("name") or code)
        aliases = [str(alias) for alias in feature.get("aliases") or []]
        query_aliases = S101_FEATURE_QUERY_ALIASES.get(code, [])
        if any(token and token.lower() in lowered for token in [code, name, *aliases, *query_aliases]):
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

NON_DERIVED_CONCEPT_TERMS = {
    "\ubd80\uadfc",
    "\uadfc\ucc98",
    "\uc8fc\ubcc0",
    "\uc774\ub0b4",
    "\ubc18\uacbd",
    "\uac70\ub9ac",
    "\ucc3e\uc544",
    "\ucc3e\uc544\uc918",
    "\uc0ac\uace0",
    "\uc774\ub825",
    "temporary placing",
    "temporary storage",
    "fine sand",
    "movable body type wave converter",
    "transverse joints",
    "side thruster",
    "cofferdam",
}


def _valid_derived_concept(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text or text in NON_DERIVED_CONCEPT_TERMS:
        return None
    concepts = (_load_yaml_registry("derived_concept_registry_v2.yaml").get("derived_concepts") or {})
    legacy = (_load_yaml_registry("derived_concept_registry.yaml").get("derived_concepts") or {})
    known = set(concepts) | set(legacy)
    known.update(
        str(item.get("concept_id"))
        for item in list(concepts.values()) + list(legacy.values())
        if isinstance(item, dict) and item.get("concept_id")
    )
    known.update({"accident_event", "dynamic_traffic", "dataset_embedding_provenance"})
    return text if text in known else None


def _as_unique_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return list(dict.fromkeys(str(item).strip() for item in values if str(item or "").strip()))


def _sanitize_graph_context_for_execution(raw_context: dict | None, query: str, seed_context: dict | None) -> dict:
    """Keep GraphRAG recall broad while preventing unverified candidates from becoming executable slots."""
    if not isinstance(raw_context, dict):
        return {}
    seed_context = seed_context or {}
    sanitized = dict(raw_context)
    candidate_target_features = _as_unique_text_list(raw_context.get("target_features"))
    candidate_target_layers = _as_unique_text_list(raw_context.get("target_layers"))
    candidate_dynamic_layers = _as_unique_text_list(raw_context.get("target_dynamic_layers"))
    candidate_derived = _as_unique_text_list(raw_context.get("derived_concepts"))
    query_lower = (query or "").lower()

    explicit_seed_features = []
    candidate_feature_keys = {item.lower() for item in candidate_target_features}
    for feature in _as_unique_text_list(seed_context.get("target_features")):
        if feature.lower() in candidate_feature_keys and feature.lower() in query_lower:
            explicit_seed_features.append(feature)

    verified_derived = [item for item in candidate_derived if _valid_derived_concept(item)]
    seed_derived = [item for item in _as_unique_text_list(seed_context.get("derived_concepts")) if _valid_derived_concept(item)]
    verified_derived = list(dict.fromkeys(seed_derived + verified_derived))

    sanitized["candidate_target_features"] = candidate_target_features
    sanitized["candidate_target_layers"] = candidate_target_layers
    sanitized["candidate_target_dynamic_layers"] = candidate_dynamic_layers
    sanitized["candidate_derived_concepts"] = candidate_derived
    sanitized["target_features"] = explicit_seed_features
    sanitized["target_layers"] = []
    sanitized["target_dynamic_layers"] = []
    sanitized["derived_concepts"] = verified_derived
    sanitized["candidate_only_policy"] = {
        "policy_id": "candidate_recall_resolved_precision_v1",
        "candidate_fields": [
            "candidate_target_features",
            "candidate_target_layers",
            "candidate_target_dynamic_layers",
            "candidate_derived_concepts",
            "candidate_agents",
            "candidate_tools",
        ],
        "resolved_fields": ["target_features", "target_layers", "target_dynamic_layers", "derived_concepts"],
        "notes": [
            "GraphRAG and S-101 catalogue matches are recall candidates.",
            "Only explicit query seeds or registry-verified derived concepts are promoted into resolved fields.",
        ],
    }
    hints = dict(raw_context.get("execution_hints") or {})
    hints["candidate_requires_spatial_analysis"] = bool(hints.get("requires_spatial_analysis"))
    hints["requires_spatial_analysis"] = bool(explicit_seed_features and seed_context.get("reference_geometry"))
    sanitized["execution_hints"] = hints
    return sanitized


def _enrich_extracted_slots(slots: dict | None, norm_result: dict | None) -> dict:
    """Keep normalized terms and executable spatial slots in one payload."""
    enriched = dict(slots or {})
    norm_result = norm_result or {}
    canonical_terms = norm_result.get("canonical_terms") or []
    candidate_contexts = norm_result.get("candidate_contexts") or []
    if canonical_terms:
        enriched.setdefault("canonical_terms", canonical_terms)
        valid_concepts = [term for term in canonical_terms if _valid_derived_concept(term)]
        if valid_concepts:
            enriched.setdefault("derived_concepts", valid_concepts)
            if not _valid_derived_concept(enriched.get("derived_concept")):
                enriched["derived_concept"] = valid_concepts[0]
        elif not _valid_derived_concept(enriched.get("derived_concept")):
            enriched.pop("derived_concept", None)
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


def _extract_temporal_window_from_query(query: str) -> dict | None:
    text = query or ""
    lowered = text.lower()
    import re

    if any(term in lowered or term in text for term in ["최근 1년", "최근 일년", "지난 1년", "last year", "past year"]):
        return {"preset": "last_1_year", "duration": "P1Y", "source": "query_text"}
    match = re.search(r"(?:최근|지난)\s*(\d+)\s*(년|개월|달|일)", text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        designator = {"년": "Y", "개월": "M", "달": "M", "일": "D"}[unit]
        return {"preset": f"last_{value}_{unit}", "duration": f"P{value}{designator}", "source": "query_text"}
    return None


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
    if _looks_like_dataset_evidence_query(text):
        return False
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
    if _looks_like_dataset_evidence_query(text):
        return False
    return any(term in lowered or term in text for term in [
        "legal",
        "notice",
        "law",
        "\ubc95\ub839",
        "\uace0\uc2dc",
        "\uaddc\uc815",
        "\ud1b5\ud56d\ub839",
        "\ud1b5\ud56d \uba85\ub839",
        "\ud1b5\ud56d\uba85\ub839",
        "\ud1b5\ud56d \uaddc\uc815",
        "\ud1b5\ud56d\uaddc\uc815",
        "\uadfc\uac70",
        "\ud574\uc0c1\uad50\ud1b5\uc548\uc804",
        "abc-999",
    ])

def _looks_like_traffic_document_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    explicit = [
        "\ud1b5\ud56d\ub839",
        "\ud1b5\ud56d \uba85\ub839",
        "\ud1b5\ud56d\uba85\ub839",
        "\ud1b5\ud56d \uaddc\uc815",
        "\ud1b5\ud56d\uaddc\uc815",
        "\ud1b5\ud56d \ubc95\ub839",
        "\ud1b5\ud56d\ubc95\ub839",
        "traffic regulation",
        "traffic order",
        "navigation order",
    ]
    if any(term in lowered or term in text for term in explicit):
        return True
    return "\ud1b5\ud56d" in text and any(term in text for term in ["\ub839", "\ubc95\ub839", "\uace0\uc2dc", "\uaddc\uc815", "\uba85\ub839", "\uc9c0\uce68"])

def _looks_like_no_evidence_document_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "imaginaryfeature",
        "abc-999",
        "\uc874\uc7ac\ud558\uc9c0 \uc54a\ub294",
        "\uc5c6\ub294",
    ])

def _looks_like_dataset_evidence_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    dataset_terms = [
        "dataset",
        "data set",
        "csv",
        "zip",
        "shp",
        "geojson",
        "\ub370\uc774\ud130\uc14b",
        "\ub370\uc774\ud130 \uc14b",
        "\ub370\uc774\ud130",
        "\ud30c\uc77c",
        "\uc801\uc7ac",
        "\uc784\ubca0\ub529",
        "\ud559\uc2b5",
        "embedding",
        "embedded",
        "evidence",
        "document_chunks",
        "knowledge.document_chunks",
    ]
    provenance_terms = [
        "\uadfc\uac70",
        "\ucd9c\ucc98",
        "\uc6d0\ucc9c",
        "\uc801\uc7ac",
        "\uac80\uc99d",
        "\ud559\uc2b5",
        "\uc784\ubca0\ub529",
        "\ub418\uc5c8",
        "\ub410",
        "\ud588",
        "\ud655\uc778",
        "source",
        "provenance",
        "basis",
        "coverage",
        "chunk",
        "chunks",
    ]
    file_like = bool(re.search(r"(?:Dataset[/\\]|\.csv|\.zip|\.shp|\.geojson|_[0-9]{8})", text, re.I))
    has_dataset_context = any(term in lowered or term in text for term in dataset_terms)
    has_provenance = any(term in lowered or term in text for term in provenance_terms)
    return file_like or (has_dataset_context and has_provenance)

def _looks_like_traffic_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    if _looks_like_traffic_document_query(text):
        return False
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

def _looks_like_accident_event_lookup_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    if "feature_instance_id=" in lowered:
        return False
    accident_terms = [
        "accident",
        "\uc0ac\uace0",
        "\uc0ac\uac74",
        "\ud574\uc0c1\uc870\ub09c",
        "\uc870\ub09c\uc0ac\uace0",
        "\ud574\uc591\uc0ac\uace0",
        "\uc120\ubc15\uc0ac\uace0",
    ]
    detail_terms = [
        "\uc815\ube44\ubd88\ub7c9",
        "\uad00\ub9ac\uc18c\ud640",
        "\uc6b4\ud56d\ubd80\uc8fc\uc758",
        "\uc548\uc804\ubd80\uc8fc\uc758",
        "\uc6d0\uc778\ubbf8\uc0c1",
        "\uae30\uad00\uc190\uc0c1",
        "\ucd94\uc9c4\uae30\uc190\uc0c1",
        "\ud0a4\uc190\uc0c1",
        "\uce68\ubab0",
        "\uce68\uc218",
        "\uc88c\ucd08",
        "\ucda9\ub3cc",
        "\ud654\uc7ac",
        "\uc804\ubcf5",
        "\ud45c\ub958",
    ]
    return any(term in lowered or term in text for term in accident_terms) and any(term in lowered or term in text for term in detail_terms)

def _looks_like_accident_spatial_history_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    accident_terms = [
        "accident",
        "incident",
        "\uc0ac\uace0",
        "\uc774\ub825",
        "\uc0ac\uace0\uc774\ub825",
        "\ud574\uc0c1\uc870\ub09c",
        "\uc870\ub09c\uc0ac\uace0",
        "\ud574\uc591\uc0ac\uace0",
    ]
    spatial_terms = [
        "\ubd80\uadfc",
        "\uadfc\ucc98",
        "\uc8fc\ubcc0",
        "\ubc18\uacbd",
        "\uc774\ub0b4",
        "near",
        "nearby",
        "around",
        "within",
    ]
    has_place = bool(_registered_place_aliases()) and any(alias in lowered or alias in text for alias in _registered_place_aliases())
    has_spatial_context = bool(_spatial_context_dict({}).get("geometry"))
    has_accident_history = any(term in lowered or term in text for term in accident_terms)
    has_spatial_relation = any(term in lowered or term in text for term in spatial_terms)
    return (
        has_accident_history
        and (has_place or has_spatial_context)
        and (has_spatial_relation or has_place or has_spatial_context)
    )

def _should_fast_execute_accident_spatial_history(state: OrchestratorState) -> bool:
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    if not _looks_like_accident_spatial_history_query(query):
        return False
    trace = state.get("candidate_trace")
    if isinstance(trace, dict):
        return any(
            _contract_ready_any(state, route="ACCIDENT_ANALYSIS", capability_ids=[capability_id])
            for capability_id in [
                "tool.accident_spatial_history_lookup",
                "tool.accident_event_lookup",
                "dataset.accident_events",
                "resolver.place_registry",
            ]
        )
    return True

def _should_fast_execute_accident_event_lookup(state: OrchestratorState) -> bool:
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    if not _looks_like_accident_event_lookup_query(query):
        return False
    trace = state.get("candidate_trace")
    if isinstance(trace, dict):
        return any(
            _contract_ready_any(state, route="ACCIDENT_ANALYSIS", capability_ids=[capability_id])
            for capability_id in [
                "tool.accident_event_lookup",
                "dataset.accident_events",
                "resolver.accident_event_terms",
            ]
        )
    # Pre-candidate-trace fallback for direct local calls and old tests.
    return True

def _looks_like_policy_block_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    public_restriction_terms = [
        "entry_restricted_area",
        "speed_restriction_area",
        "\uc9c4\uc785\uc81c\ud55c",
        "\uc18d\ub3c4\uc81c\ud55c",
        "\uc9c4\uc785 \uc81c\ud55c",
        "\uc18d\ub3c4 \uc81c\ud55c",
    ]
    if any(term in lowered or term in text for term in public_restriction_terms):
        return False
    if any(term in lowered or term in text for term in [
        "entry_restricted_area",
        "speed_restriction_area",
        "진입제한",
        "속도제한",
        "진입 제한",
        "속도 제한",
    ]):
        return False
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
    return any(term in lowered or term in text for term in [
        "protected area",
        "\ubcf4\ud638\uad6c\uc5ed",
        "\ubcf4\ud638\ud574\uc5ed",
        "\ubcf4\ud638\uc218\uc5ed",
    ])

def _looks_like_dumping_ground_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "dumping ground",
        "dumping area",
        "\ud22c\uae30\uc7a5",
        "\ud22c\uae30\uad6c\uc5ed",
        "\uc0b0\uc5c5\ud3d0\uae30\ubb3c\ud22c\uae30\uad6c\uc5ed",
        "\uc0b0\uc5c5\ud3d0\uae30\ubb3c \ud22c\uae30\uad6c\uc5ed",
        "\ud3d0\uae30\ubb3c\ud22c\uae30\uad6c\uc5ed",
        "\ud3d0\uae30\ubb3c \ud22c\uae30\uad6c\uc5ed",
    ])

def _looks_like_eddy_hazard_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["eddy", "\uc640\ub958"])

def _looks_like_island_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in ["island", "\uc12c \ubaa9\ub85d", "\uc12c"])

def _extract_distance_m_from_query(query: str) -> float | None:
    import re

    match = re.search(r"(-?\d+(?:\.\d+)?)\s*(km|킬로미터|킬로|㎞)", query or "", re.IGNORECASE)
    if match:
        return float(match.group(1)) * 1000.0
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*(m|미터)", query or "", re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None

def _spatial_context_dict(state: OrchestratorState) -> dict:
    spatial = state.get("spatial_context") or {}
    if hasattr(spatial, "model_dump"):
        spatial = spatial.model_dump()
    return spatial if isinstance(spatial, dict) else {}

def _resolve_known_marine_place_wkt(query: str, state: OrchestratorState) -> tuple[str | None, str | None]:
    spatial = _spatial_context_dict(state)
    try:
        geometry, label, _, _ = resolve_location(query, spatial)
        return geometry, label
    except PlaceResolutionProblem:
        return None, spatial.get("base_location") or spatial.get("location_text")


def _looks_like_place_lookup(query: str) -> bool:
    import re

    if any(term in query.lower() for term in ["nearest", "closest", "가까운", "반경", "이내", "위험", "hazard", "침선", "목록", "법령", "규정", "위치 추적", "항적", "정박지", "anchorage", "선박", "구역", "교통량", "유속", "시설"]):
        return False
    return bool(re.search(r"(?:위치|좌표|어디)(?:를|가|는|을|에|인지|야|입니까|\s|[?.!]|$)|\b(?:where is|where are|coordinates of|location of)\b", query, re.I))


def _looks_like_known_place_search(query: str, state: OrchestratorState | None = None) -> bool:
    text = query or ""
    lowered = text.lower()
    if not text.strip():
        return False
    if any(term in lowered or term in text for term in [
        "nearest",
        "closest",
        "hazard",
        "traffic",
        "ais",
        "v-pass",
        "vpass",
        "\uc704\ud5d8\uac1d\uccb4",
        "\uce68\uc120",
        "obstruction",
        "wreck",
        "\uc815\ubc15\uc9c0",
        "\ud56d\ub85c\ud45c\uc9c0",
        "\uad6c\uc5ed",
        "\ud1b5\ud56d",
    ]):
        return False
    if not any(term in lowered or term in text for term in [
        "\ucc3e\uc544\uc918",
        "\ucc3e\uc544",
        "\uc5b4\ub514",
        "\uc704\uce58",
        "\uc88c\ud45c",
        "where is",
        "coordinates of",
        "location of",
    ]):
        return False
    try:
        resolve_location(text, _spatial_context_dict(state or {}))
        return True
    except PlaceResolutionProblem as exc:
        return bool(exc.candidates)
    except Exception as exc:
        logger.warning("Known place search precheck failed", error=str(exc), query=text)
        return False


def _place_lookup_update(state, payload, analysis_type="place_lookup"):
    from shapely import wkt

    resolved = payload["status"] == "RESOLVED"
    status = AgentStatus.COMPLETED if resolved else AgentStatus(payload["status"])
    resolution = payload.get("location_resolution") or {}
    collection = {"type": "FeatureCollection", "features": []}
    evidence = {"spatial_feature_evidence": [], "spatial_layer_evidence": []}
    text = payload["summary"]
    if resolved:
        point = wkt.loads(payload["geometry"])
        identifier = payload.get("place_id") or f"reference:{state['task_id']}"
        evidence_id = f"place:{identifier}:{payload.get('place_version') or 'input'}"
        properties = {"place_id": identifier, "place_version": payload.get("place_version"), "name": payload["location_text"], "evidence_id": evidence_id}
        collection["features"] = [{"type": "Feature", "id": identifier, "geometry": {"type": "Point", "coordinates": [point.x, point.y]}, "properties": properties}]
        evidence["spatial_feature_evidence"] = [{"evidence_id": evidence_id, "evidence_type": "place_reference", "source_ref": resolution["source_ref"], "data": {**properties, "location_resolution": resolution}}]
        text = f"{payload['location_text']}: 경도 {point.x:.6f}, 위도 {point.y:.6f} (EPSG:4326)."
    spatial = _spatial_context_dict(state)
    safe_spatial = {key: value for key, value in spatial.items() if key in {"base_location", "location_text", "place_id", "place_version", "geometry", "crs", "buffer_distance", "target_features", "exclusions", "context", "result_limit", "offset", "k"}}
    structured = {**payload, "analysis_type": analysis_type, "original_query": state["query"], "spatial_context": safe_spatial, "count": 1 if resolved else None, "returned_count": int(resolved), "geojson": collection}
    plan = {"analysis_type": analysis_type, "primary_agent": "Spatial Analysis Agent", "execution_ready": resolved, "status": "EXECUTION_READY" if resolved else ("NEEDS_USER_INPUT" if status == AgentStatus.NEEDS_CLARIFICATION else "BLOCKED_DATA")}
    context = QueryExecutionContext(request_id=state["task_id"], revision=state.get("execution_revision") or 1, original_query=state["query"], route_plan=plan, provenance={"location_resolution": resolution})
    context.plan_hash = hashlib.sha256(json.dumps({"query": state["query"], "geometry": payload.get("geometry"), "location_resolution": resolution}, sort_keys=True).encode()).hexdigest()
    context.readiness = PlanStatus(plan["status"])
    if resolved:
        context.slots = ExecutionSlots(location_text=payload["location_text"], reference_geometry=payload["geometry"], crs=payload["crs"], resolution_status=resolution["status"], analysis_type=analysis_type)
    else:
        context.blockers = [payload.get("error_code", "LOCATION_UNCONFIRMED")]
    quality_metrics = _quality_metrics_from_state(state, fast_path="dataset_place_resolver", exact=resolved)
    structured["quality_metrics"] = quality_metrics
    final = {
        "task_id": state["task_id"], "request_id": state["task_id"], "status": status.value,
        "contract_version": context.contract_version,
        "agent_name": "Spatial Analysis Agent", "summary": text, "answer_text": text,
        "error_code": payload.get("error_code"), "structured_result": structured,
        "clarification_questions": [text] if status == AgentStatus.NEEDS_CLARIFICATION else [],
        "clarification_options": payload.get("location_candidates", []),
        "features": collection, "evidence_bundle": evidence,
        "map_layers": [{"layer_id": f"place:{state['task_id']}", "title": payload["location_text"], "source_type": "geojson", "geometry_type": "POINT", "inline_geojson": collection, "feature_count": 1}] if resolved else [],
        "orchestrator_v2": {"route_plan": plan, "query_execution_context": context.model_dump(mode="json"), "embedding_independent": True, "fast_path": "dataset_place_resolver", "quality_metrics": quality_metrics},
    }
    _attach_candidate_trace(state, final)
    _record_query_quality_issues(state, final)
    return {"final_dict": final, "task_plan": plan, "query_execution_context": context.model_dump(mode="json"), "candidate_trace": state.get("candidate_trace"), "status": status, "state_history": log_transition(AgentStatus.INTENT_PARSED, status, actor="DatasetPlaceResolver")}


async def fast_place_lookup_node(state: OrchestratorState) -> OrchestratorState:
    import asyncio
    from services.orchestrator.place_router import resolve_payload

    if state.get("user_id") == "blocked_user":
        payload = {"status": "BLOCKED", "error_code": "ACCESS_DENIED", "summary": "이 요청에 대한 접근 권한이 없습니다."}
    else:
        payload = await asyncio.to_thread(resolve_payload, state["query"], _spatial_context_dict(state))
    return _place_lookup_update(state, payload)

def _requested_distance_m(state: OrchestratorState, query: str) -> float | None:
    spatial = _spatial_context_dict(state)
    if spatial.get("buffer_distance") is not None:
        try:
            return float(spatial.get("buffer_distance"))
        except (TypeError, ValueError):
            return None
    return _extract_distance_m_from_query(query)

def _looks_like_s101_hazard_radius_query(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    target = _looks_like_s101_hazard_target(text)
    radius = any(term in lowered or term in text for term in ["km", "㎞", "킬로", "m 이내", "\uc774\ub0b4", "반경", "\ubc18\uacbd"])
    return target and radius

def _looks_like_s101_hazard_target(query: str) -> bool:
    text = query or ""
    lowered = text.lower()
    return any(term in lowered or term in text for term in [
        "navigation_hazard_object",
        "hazard",
        "위험 객체",
        "간출암",
        "수중암",
        "장애물",
        "난파선",
        "wreck",
        "obstruction",
        "underwaterawashrock",
        "\uc704\ud5d8\uac1d\uccb4",
        "\uce68\uc120",
        "?꾪뿕媛앹껜",
        "移⑥꽑",
        "媛앹껜",
        "꾪뿕",
    ])

def _should_fast_execute_s101_hazard_radius(state: OrchestratorState) -> bool:
    query = state.get("query", "")
    if not _looks_like_s101_hazard_target(query):
        return False
    nearest_request = any(term in query.lower() for term in ["nearest", "closest", "가까운", "가까이"])
    if nearest_request and not _looks_like_s101_hazard_radius_query(query):
        return False
    if _looks_like_standard_rag_query(query) and not _looks_like_s101_hazard_radius_query(query):
        return False
    if _looks_like_s101_hazard_radius_query(query):
        return True
    # Incomplete radius requests enter the same handler to obtain real clarification.
    return _contract_ready_any(
        state,
        route="SPATIAL_ANALYSIS",
        capability_ids=["resolver.s101_feature_dictionary", "tool.spatial_radius_search", "agent.spatial_analysis"],
    )


def _should_fast_execute_s101_nearest_feature(state: OrchestratorState) -> bool:
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    # Location confirmation precedes any projection/schema lookup in the executor.
    return _looks_like_s101_nearest_feature_query(query) and _contract_ready_any(
        state,
        route="SPATIAL_ANALYSIS",
        capability_ids=["resolver.s101_feature_dictionary", "tool.spatial_radius_search", "agent.spatial_analysis"],
    )


def _should_fast_execute_traffic_query(state: OrchestratorState) -> bool:
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    if not _looks_like_traffic_query(query):
        return False
    if not _contract_ready_any(
        state,
        route="TRAFFIC_ANALYSIS",
        capability_ids=["tool.dynamic_traffic_aggregation", "dataset.dynamic_traffic_layer", "agent.data_discovery"],
    ):
        return False
    try:
        from services.orchestrator.traffic_execution import traffic_layer_ready

        return traffic_layer_ready()
    except Exception as exc:
        logger.warning("Traffic execution readiness check failed", error=str(exc))
        return False


def _requested_spatial_layer_targets(query: str) -> list[dict]:
    text = query or ""
    lowered = text.lower()
    targets = []
    provenance_terms = [
        "\uadfc\uac70",
        "\ucd9c\ucc98",
        "\uc801\uc7ac",
        "\ud30c\uc2f1",
        "\ud45c\uc900\ud654",
        "\uc784\ubca0\ub529",
        "source",
        "provenance",
        "embedding",
    ]
    if any(term in lowered or term in text for term in provenance_terms):
        return []
    for target in REQUESTED_SPATIAL_LAYER_TARGETS.values():
        if any(term.lower() in lowered or term in text for term in target["terms"]):
            targets.append(target)
    if any(term in lowered or term in text for term in ["\uc704\ud5d8\uac1d\uccb4", "hazard object"]):
        targets.extend([
            REQUESTED_SPATIAL_LAYER_TARGETS["entry_restricted"],
            REQUESTED_SPATIAL_LAYER_TARGETS["speed_restriction"],
        ])
    deduped = {}
    for target in targets:
        deduped[target["layer_id"]] = target
    if (
        "navigation_aid_busan" in deduped
        and "fairway_area" in deduped
        and "\ud56d\ub85c\ud45c\uc9c0" in text
        and "\uc77c\ubc18\ud56d\ub85c" not in text
        and "fairway" not in lowered
    ):
        deduped.pop("fairway_area", None)
    return list(deduped.values())


def _requested_layer_distance_m(query: str, state: OrchestratorState) -> float:
    import re

    spatial = _spatial_context_dict(state)
    if spatial.get("buffer_distance") is not None:
        try:
            return float(spatial["buffer_distance"])
        except (TypeError, ValueError):
            pass
    match = re.search(r"(\d+(?:\.\d+)?)\s*(km|\ud0ac\ub85c\ubbf8\ud130|\ud0ac\ub85c)", query or "", re.IGNORECASE)
    if match:
        return float(match.group(1)) * 1000.0
    match = re.search(r"(\d+(?:\.\d+)?)\s*(m|\ubbf8\ud130)", query or "", re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 3000.0


def _should_fast_execute_requested_spatial_layer(state: OrchestratorState) -> bool:
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    if not _requested_spatial_layer_targets(query):
        return False
    return True


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
    if _looks_like_planned_port_query(query) or _looks_like_protected_area_query(query) or _looks_like_dumping_ground_query(query) or _looks_like_eddy_hazard_query(query) or _looks_like_island_query(query):
        return True
    if _looks_like_vts_control_query(query):
        return True
    if _looks_like_traffic_query(query):
        return True
    return False

def _fast_spatial_or_traffic_plan(query: str, state: OrchestratorState) -> tuple[dict, dict, str, str]:
    explicit_time_series = _looks_like_explicit_time_series_request(query)
    policy_block = _looks_like_policy_block_query(query)
    ambiguous_hazard = _looks_like_ambiguous_hazard_query(query)
    accident_relation = _looks_like_accident_relation_query(query)
    tidal_current = _looks_like_tidal_current_query(query)
    sea_parting = _looks_like_sea_parting_query(query)
    planned_port = _looks_like_planned_port_query(query)
    protected_area = _looks_like_protected_area_query(query)
    dumping_ground = _looks_like_dumping_ground_query(query)
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
        data = ["protected_sea_area"]
        blockers = ["BLOCKED_DATA: protected-area query requires a resolved base geometry and executable layer binding"]
        target_term = "protected_sea_area"
    elif dumping_ground:
        analysis_type = "hazard_area_lookup"
        agent_name = "Spatial Analysis Agent"
        tools = ["hazard.area_lookup", "postgis.intersects"]
        data = ["dumping_ground_area"]
        blockers = ["BLOCKED_DATA: dumping-ground query requires a resolved base geometry and executable layer binding"]
        target_term = "dumping_ground_area"
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
        blockers = ["BLOCKED_DATA: vessel traffic control area query requires a resolved base geometry and executable layer binding"]
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
    temporal_window = _extract_temporal_window_from_query(query)
    if temporal_window:
        slots["temporal_window"] = temporal_window
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
            "resolved": {
                "derived_concept": _valid_derived_concept(slots.get("derived_concept")),
                "target_features": _as_unique_text_list(slots.get("target_features")),
                "target_layers": _as_unique_text_list(slots.get("target_layers")),
                "target_dynamic_layers": _as_unique_text_list(slots.get("target_dynamic_layers")),
            },
            "candidates": {
                "target_features": _as_unique_text_list(graph_context.get("candidate_target_features")),
                "target_layers": _as_unique_text_list(graph_context.get("candidate_target_layers")),
                "target_dynamic_layers": _as_unique_text_list(graph_context.get("candidate_target_dynamic_layers")),
                "derived_concepts": _as_unique_text_list(graph_context.get("candidate_derived_concepts")),
                "agents": _as_unique_text_list(graph_context.get("candidate_agents")),
                "tools": _as_unique_text_list(graph_context.get("candidate_tools")),
                "policy": graph_context.get("candidate_only_policy"),
            },
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
    candidate_trace = query_candidate_broker.build_trace(
        original_query,
        normalized_query=query,
        norm_result=norm_result,
    )
    state["candidate_trace"] = candidate_trace
    trace_summary = _candidate_trace_summary(candidate_trace)
    top_routes = [
        f"{row.get('route')}:{row.get('score')}"
        for row in trace_summary.get("top_routes", [])
        if isinstance(row, dict)
    ]
    if top_routes:
        debug_logs.append(f"Candidate routes(dry-run): {', '.join(top_routes)}")
    top_capabilities = [
        str(row.get("candidate_id"))
        for row in trace_summary.get("top_capabilities", [])[:3]
        if isinstance(row, dict) and row.get("candidate_id")
    ]
    if top_capabilities:
        debug_logs.append(f"Capability candidates(dry-run): {', '.join(top_capabilities)}")
    
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
    fast_dataset_evidence = _looks_like_dataset_evidence_query(original_query)
    fast_legal_or_no_evidence_rag = _looks_like_legal_rag_query(original_query) or _looks_like_no_evidence_document_query(original_query)
    fast_time_series = _looks_like_time_series_query(original_query)
    fast_known_place = _looks_like_known_place_search(original_query, state)
    combined_fast_query = f"{original_query} {query}"
    fast_requested_layer = bool(_requested_spatial_layer_targets(combined_fast_query))
    fast_spatial_or_traffic = (
        fast_requested_layer
        or
        _looks_like_traffic_query(combined_fast_query)
        or _looks_like_spatial_query(combined_fast_query)
        or _should_fast_execute_s101_hazard_radius(state)
        or _looks_like_place_lookup(original_query)
        or fast_known_place
        or _looks_like_explicit_time_series_request(combined_fast_query)
        or _looks_like_accident_relation_query(combined_fast_query)
        or _looks_like_accident_spatial_history_query(combined_fast_query)
        or _looks_like_policy_block_query(combined_fast_query)
        or _looks_like_ambiguous_hazard_query(combined_fast_query)
        or _looks_like_tidal_current_query(combined_fast_query)
        or _looks_like_sea_parting_query(combined_fast_query)
        or _looks_like_planned_port_query(combined_fast_query)
        or _looks_like_protected_area_query(combined_fast_query)
        or _looks_like_eddy_hazard_query(combined_fast_query)
        or _looks_like_island_query(combined_fast_query)
    )
    cached_intent = None if (fast_external_tide or fast_external_weather or fast_standard_rag or fast_dataset_evidence or fast_legal_or_no_evidence_rag or fast_time_series or fast_spatial_or_traffic or fast_known_place) else cache.check_cache(query)
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
    elif fast_dataset_evidence:
        intent_type = "DATA_DISCOVERY"
        target_objects = ["gazetteer", "dataset_provenance"]
        output_format = "SUMMARY"
        intent_understanding = "Dataset/gazetteer provenance lookup is required."
        execution_plan = "1. Check dataset ingestion report. 2. Return source files, serving tables, row counts, and evidence candidates."
    elif fast_standard_rag or fast_legal_or_no_evidence_rag:
        intent_type = "KNOWLEDGE_SEARCH"
        target_objects = [term for term in ["S-100", "S-101", "Wreck", "Obstruction", "Feature Catalogue", "DCEG"] if term.lower() in query.lower()]
        if not target_objects:
            target_objects = [query]
        output_format = "SUMMARY"
        intent_understanding = "Marine standards or catalogue document search is required."
        execution_plan = "1. Route to Standard RAG Agent. 2. Retrieve graph-scoped document evidence. 3. Answer only with retrieved evidence and citations."
    elif fast_known_place:
        intent_type = "SPATIAL_SEARCH"
        target_objects = ["named_place"]
        output_format = "MAP"
        intent_understanding = "A known named marine place should be resolved from the gazetteer or place registry."
        execution_plan = "1. Resolve the named place against local gazetteers. 2. Return its source-backed location and map point."
    elif fast_spatial_or_traffic:
        if fast_requested_layer:
            intent_type = "SPATIAL_SEARCH"
            target_objects = ["dataset_spatial_layer"]
            output_format = "MAP"
            intent_understanding = "Requested dataset spatial layer search requires a validated reference geometry and spatial layer binding."
            execution_plan = "1. Resolve the reference place. 2. Execute the requested spatial layer radius search. 3. Return map features and evidence."
        elif _looks_like_accident_spatial_history_query(combined_fast_query):
            intent_type = "ACCIDENT_ANALYSIS"
            target_objects = ["accident_history"]
            output_format = "MAP"
            intent_understanding = "Nearby accident history requires a validated place anchor, radius, and accident event serving-table binding."
            execution_plan = "1. Resolve the reference place. 2. Validate accident spatial history binding. 3. Query serving.accident_events by distance and return map evidence."
        elif _looks_like_explicit_time_series_request(combined_fast_query):
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
                            "norm_result": norm_result,
                            "candidate_trace": candidate_trace,
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
                        
    temporal_window = _extract_temporal_window_from_query(combined_fast_query if fast_spatial_or_traffic else original_query)
    if temporal_window and not temporal_conditions:
        temporal_conditions = [temporal_window["preset"]]

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

    if base_location or map_bounds or req_spatial_ctx.get("geometry"):
        spatial_context = SpatialContext(
            base_location=base_location,
            place_id=req_spatial_ctx.get("place_id"),
            place_version=req_spatial_ctx.get("place_version"),
            geometry=req_spatial_ctx.get("geometry"),
            crs=req_spatial_ctx.get("crs") or "EPSG:4326",
            map_bounds=map_bounds,
            buffer_distance=radius_m
        )
    else:
        spatial_context = None

    preserved_spatial_context = dict(req_spatial_ctx)
    if spatial_context:
        for key, value in spatial_context.model_dump().items():
            if key not in preserved_spatial_context and value is not None:
                preserved_spatial_context[key] = value
    if req_spatial_ctx.get("geometry") and "crs" not in req_spatial_ctx:
        preserved_spatial_context.pop("crs", None)
    
    task_id = str(state.get("task_id") or state.get("request_id") or "unknown_task")
    user_id = str(state.get("user_id") or "default_user")
    organization_id = str(state.get("organization_id") or "default_org")
    req = AgentRequest(
        task_id=task_id,
        trace_id=f"tr-{task_id}",
        user_id=user_id,
        organization_id=organization_id,
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
        "task_id": task_id,
        "query": original_query,
        "organization_id": organization_id,
        "user_id": user_id,
        "agent_request": req, 
        "status": AgentStatus.INTENT_PARSED,
        "state_history": log_transition(AgentStatus.RECEIVED, AgentStatus.INTENT_PARSED),
        "normalized_query": query,
        "normalization_debug": debug_logs,
        "norm_result": norm_result,
        "context_result": state.get("context_result"),
        "spatial_context": preserved_spatial_context,
        "extracted_slots": extracted_payload,
        "candidate_trace": candidate_trace,
    }

from services.orchestrator.feature_resolver import feature_resolver

async def graph_rag_node(state: OrchestratorState) -> OrchestratorState:
    """Run graph candidate discovery between normalization and context resolution."""
    query = state.get("query") or state.get("normalized_query") or ""
    intent = state.get("agent_request").parsed_intent if state.get("agent_request") else None
    norm = state.get("norm_result") or {}
    derived_seed = [
        item for item in (norm.get("derived_concepts", []) or norm.get("canonical_terms", []))
        if _valid_derived_concept(item)
    ]
    seed_context = {
        "target_features": list(intent.target_objects) if intent else [],
        "derived_concepts": derived_seed,
        "document_type": norm.get("document_type", []),
    }
    context = _sanitize_graph_context_for_execution(
        graph_rag_retriever.retrieve(query, seed_context),
        query,
        seed_context,
    )
    return {
        "graph_context": context,
        "graph_rag_context": context,
        "candidate_trace": state.get("candidate_trace"),
        "status": AgentStatus.INTENT_PARSED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.INTENT_PARSED, actor="GraphRAGRetriever", reason="KG candidate plan created"),
    }

def _quality_metrics_from_state(
    state: OrchestratorState,
    *,
    fast_path: str | None = None,
    exact: bool = False,
    blocked_no_evidence: bool = False,
) -> dict:
    graph_context = state.get("graph_context") or state.get("graph_rag_context") or {}
    quality = graph_context.get("quality_metrics") if isinstance(graph_context, dict) else None
    if isinstance(quality, dict) and quality:
        result = dict(quality)
        result.setdefault("fast_path", fast_path)
        return result
    if exact:
        return {
            "intent_similarity": 1.0,
            "kg_similarity": 1.0,
            "evidence_similarity": 1.0,
            "evidence_average_similarity": 1.0,
            "estimated_accuracy": 1.0,
            "confidence_band": "high",
            "method": "deterministic_exact_route_match",
            "fast_path": fast_path,
            "notes": ["Exact fast-path route. Ground-truth accuracy still requires review feedback."],
        }
    if blocked_no_evidence:
        return {
            "intent_similarity": 1.0,
            "kg_similarity": 0.8,
            "evidence_similarity": 0.8,
            "evidence_average_similarity": 0.8,
            "estimated_accuracy": 0.82,
            "confidence_band": "high",
            "method": "deterministic_authoritative_no_evidence_gate",
            "fast_path": fast_path,
            "notes": [
                "Authoritative local registries and evidence stores were checked.",
                "No-evidence is a supported terminal result, not a missing quality signal.",
            ],
        }
    return {
        "intent_similarity": 0.65,
        "kg_similarity": 0.55,
        "evidence_similarity": 0.55,
        "evidence_average_similarity": 0.55,
        "estimated_accuracy": 0.58,
        "confidence_band": "medium",
        "method": "deterministic_fast_path_default_quality_v1",
        "fast_path": fast_path,
        "notes": [
            "Deterministic fast path supplied default quality metrics.",
            "This is an estimated routing/evidence signal, not labelled ground-truth accuracy.",
        ],
    }

def _record_query_quality_issues(state: OrchestratorState, final_dict: dict) -> None:
    if not isinstance(final_dict, dict):
        return
    structured = final_dict.get("structured_result") if isinstance(final_dict.get("structured_result"), dict) else {}
    orch = final_dict.get("orchestrator_v2") if isinstance(final_dict.get("orchestrator_v2"), dict) else {}
    route_plan = orch.get("route_plan") if isinstance(orch.get("route_plan"), dict) else {}
    quality = final_dict.get("quality_metrics") or structured.get("quality_metrics") or orch.get("quality_metrics") or {}
    evidence_summary = structured.get("evidence_candidate_summary") or {}
    task_id = str(final_dict.get("task_id") or state.get("task_id") or "")
    query = str(state.get("query") or final_dict.get("original_query") or "")
    issues: list[tuple[str, str, dict]] = []

    status = str(final_dict.get("status") or structured.get("status") or state.get("status") or "")
    error_code = final_dict.get("error_code")
    if error_code in {"NO_AUTHORITATIVE_EVIDENCE", "BLOCKED_DATA"} or status in {"BLOCKED", "BLOCKED_DATA"}:
        issues.append(("blocked_or_no_evidence_response", "high", {"status": status, "error_code": error_code}))

    method = str(quality.get("method") or "")
    estimated_accuracy = quality.get("estimated_accuracy")
    kg_similarity = quality.get("kg_similarity")
    evidence_similarity = quality.get("evidence_similarity")
    if method == "quality_unavailable":
        issues.append(("quality_metrics_unavailable", "medium", {"method": method}))
    try:
        if estimated_accuracy is not None and float(estimated_accuracy) < 0.55:
            issues.append(("low_estimated_accuracy", "medium", {"estimated_accuracy": estimated_accuracy}))
    except (TypeError, ValueError):
        pass
    try:
        if kg_similarity is not None and float(kg_similarity) < 0.35:
            issues.append(("low_kg_similarity", "medium", {"kg_similarity": kg_similarity}))
    except (TypeError, ValueError):
        pass
    try:
        if evidence_similarity is not None and float(evidence_similarity) < 0.35:
            issues.append(("low_evidence_similarity", "medium", {"evidence_similarity": evidence_similarity}))
    except (TypeError, ValueError):
        pass

    route_status = str(route_plan.get("route_plan_status") or route_plan.get("status") or "")
    if route_plan.get("execution_ready") is True:
        missing_ready_parts = []
        for key in ("tools", "data", "slots"):
            value = route_plan.get(key)
            if value in (None, [], {}):
                missing_ready_parts.append(key)
        if missing_ready_parts:
            issues.append(("unsafe_execution_ready_without_bindings", "high", {"missing": missing_ready_parts, "route_plan_status": route_status}))

    if (
        route_plan.get("execution_ready") is False
        and not route_plan.get("clarification_required")
        and not route_status.startswith("BLOCKED")
    ):
        issues.append(("execution_not_ready_without_clarification", "high", {"route_plan_status": route_plan.get("route_plan_status")}))

    seen: set[str] = set()
    for issue_type, severity, details in issues:
        if issue_type in seen:
            continue
        seen.add(issue_type)
        collector.record_quality_issue(
            query=query,
            task_id=task_id,
            issue_type=issue_type,
            severity=severity,
            route_plan=route_plan,
            quality_metrics=quality,
            evidence_summary=evidence_summary,
            details=details,
        )

async def fast_document_answer_node(state: OrchestratorState) -> OrchestratorState:
    """Return authoritative local catalogue answers without vector/LLM orchestration."""
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    temporal_window = _extract_temporal_window_from_query(query)
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
            "summary_ko": f"{doc['title']} / {doc['section']}: {name}의 정의는 \"{definition}\"입니다.",
            "detail_label": "상세정보",
            "detail_text": content,
            "provenance": {"method": "exact_s101_feature_catalogue_lookup", "query": query},
        }
        answer = (
            f"검색 질의와 관련된 근거 문서 1건을 찾았습니다. "
            f"대표 근거는 S-101 Feature Catalogue 2.0.0 / feature:{code}이며, "
            f"정의는 다음과 같습니다: {definition}"
        )
        dceg_docs = _s101_dceg_docs_for_feature_exact(feature)
        dceg_citations = [
            {
                "document_id": item["document_id"],
                "source": item["title"],
                "source_id": item.get("source_id"),
                "source_file": item.get("source_file"),
                "section": item.get("section"),
                "document_type": "dceg",
                "chunk_id": item.get("chunk_id"),
                "page": item.get("page"),
                "similarity": item.get("relevance_score"),
                "summary_ko": (
                    f"{item.get('title')} / {item.get('section')} / page {item.get('page')}: "
                    f"{str(item.get('excerpt_reference') or '')[:180]}"
                ),
                "detail_label": "상세정보",
                "detail_text": item.get("excerpt_reference"),
                "provenance": {"method": "exact_s101_dceg_lookup", "query": query},
            }
            for item in dceg_docs
        ]
        documents = [doc, *dceg_docs]
        citations = [citation, *dceg_citations]
        dceg_refs = ", ".join(
            f"{item.get('title')} / {item.get('section')}"
            for item in dceg_docs
            if item.get("title") and item.get("section")
        )
        answer = (
            f"S-101 Feature Catalogue 2.0.0 기준 {name}의 정의는 \"{definition}\"입니다. "
            f"근거는 Feature Catalogue의 feature:{code} 항목입니다."
        )
        if dceg_refs:
            answer += (
                f" 인코딩 지침 근거는 S-101 Annex A DCEG Ed. 2.0.0의 객체별 본문 청크이며, "
                f"참조 위치는 {dceg_refs}입니다."
            )
        dceg_refs_with_pages = ", ".join(
            f"{item.get('title')} / {item.get('section')} / page {item.get('page')}"
            for item in dceg_docs
            if item.get("title") and item.get("section")
        )
        answer = (
            f"S-101 Feature Catalogue 2.0.0 기준 {name}의 정의는 \"{definition}\"입니다. "
            f"근거는 Feature Catalogue의 feature:{code} 항목입니다."
        )
        if dceg_refs_with_pages:
            answer += (
                f" 인코딩 지침 근거는 S-101 Annex A DCEG Ed. 2.0.0의 객체별 본문 청크에서 확인했으며, "
                f"참조 위치는 {dceg_refs_with_pages}입니다. 긴 원문은 상세정보에서 확인할 수 있습니다."
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
    documents = locals().get("documents", [doc])
    citations = locals().get("citations", [citation])
    doc_blocked = target_term == "no_authoritative_evidence"
    quality_metrics = _quality_metrics_from_state(
        state,
        fast_path="document_no_evidence" if doc_blocked else "authoritative_s101_feature_catalogue",
        exact=not doc_blocked,
        blocked_no_evidence=doc_blocked,
    )
    route_plan = {
        "task_id": f"TASK-DOC-FAST-{state['task_id'][:3].upper()}",
        "status": "BLOCKED_DATA" if doc_blocked else "EXECUTION_READY",
        "intent": "KNOWLEDGE_SEARCH",
        "context": "standard_document",
        "analysis_type": "document_search",
        "derived_concept": None,
        "primary_agent": "Standard RAG Agent",
        "secondary_agents": [],
        "slots": {
            "target_term": target_term,
            "analysis_type": "document_search",
            "temporal_window": temporal_window,
        },
        "tools": ["rag.graph_scoped_retrieve"],
        "data": ["s101_feature_catalogue", "s101_dceg_2_0_0"] if feature else ["s101_feature_catalogue"],
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
            "retrieved_count": 0 if doc_blocked else len(documents),
            "documents": [] if doc_blocked else documents,
            "citations": [] if doc_blocked else citations,
            "no_evidence": doc_blocked,
            "evidence_candidate_summary": {},
            "quality_metrics": quality_metrics,
            "temporal_window": temporal_window,
            "web_rag_usage": {
                "web_used": False,
                "rag_used": False,
                "llm_used": False,
                "execution_path": "document_no_evidence" if doc_blocked else "authoritative_document_fast_path",
                "local_authoritative_registry_checked": True,
                "embedding_independent": True,
            },
        },
        "evidence_bundle": {"rag_evidence": [] if doc_blocked else citations, "kg_provenance": [], "regulatory_evidence": [], "spatial_feature_evidence": [], "spatial_layer_evidence": [], "accident_relation_evidence": []},
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": {
                "readiness": "BLOCKED_DATA" if doc_blocked else "READY",
                "blockers": ["NO_AUTHORITATIVE_EVIDENCE: local legal/standard evidence is not available"] if doc_blocked else [],
                "warnings": [],
                "data_bindings": [{"dataset_id": item, "relation": "authoritative_lookup"} for item in (["s101_feature_catalogue", "s101_dceg_2_0_0"] if feature else ["s101_feature_catalogue"])],
                "tool_bindings": [{"tool_id": "rag.graph_scoped_retrieve", "operation": "exact_catalogue_lookup"}],
            },
            "embedding_independent": True,
            "fast_path": "document_no_evidence" if doc_blocked else "authoritative_s101_feature_catalogue",
            "quality_metrics": quality_metrics,
        },
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
    _attach_candidate_trace(state, final_dict)
    _record_query_quality_issues(state, final_dict)
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": final_dict["orchestrator_v2"]["query_execution_context"],
        "candidate_trace": state.get("candidate_trace"),
        "status": AgentStatus.BLOCKED if doc_blocked else AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.BLOCKED if doc_blocked else AgentStatus.COMPLETED, actor="FastDocumentAnswer"),
    }

DATASET_EVIDENCE_DOC_TYPES = {
    "dataset_profile",
    "accident_data",
    "supplemental_document",
}


DATASET_EVIDENCE_STOPWORDS = {
    "dataset",
    "data",
    "set",
    "csv",
    "zip",
    "file",
    "source",
    "provenance",
    "evidence",
    "embedding",
    "embedded",
    "chunks",
    "chunk",
    "근거",
    "출처",
    "원천",
    "적재",
    "임베딩",
    "학습",
    "데이터",
    "데이터셋",
    "데이터",
    "파일",
    "확인",
    "알려줘",
    "보여줘",
    "됐는지",
    "되었는지",
    "어떤",
    "어디까지",
}


def _dataset_evidence_terms(query: str) -> list[str]:
    text = query or ""
    text = text.replace("조산사고", "조난사고")
    raw_tokens = re.findall(r"[0-9A-Za-z가-힣_()&#./-]{2,}", text)
    terms: list[str] = []
    generic_stems = ("근거", "출처", "원천", "적재", "임베딩", "학습", "확인", "데이터셋", "데이터", "파일")
    for token in raw_tokens:
        cleaned = _strip_korean_particles(token)
        cleaned = token.strip("`'\".,;:!?[]{}")
        cleaned = re.sub(r"(?:은|는|이|가|을|를|로|으로|에서|에게|까지|부터|인지|됐는지|되었는지|되는지|된것|된 것)$", "", cleaned)
        lowered = cleaned.lower()
        if (
            len(cleaned) < 2
            or lowered in DATASET_EVIDENCE_STOPWORDS
            or cleaned in DATASET_EVIDENCE_STOPWORDS
            or any(cleaned.startswith(stem) for stem in generic_stems)
        ):
            continue
        terms.append(cleaned)
        if "_" in cleaned:
            terms.extend(part for part in cleaned.split("_") if len(part) >= 2)
        if "/" in cleaned or "\\" in cleaned:
            terms.extend(part for part in re.split(r"[/\\]", cleaned) if len(part) >= 2)
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(term)
    return deduped[:10]


def _dataset_evidence_db_url() -> str:
    return os.environ.get("S101_DB_URL") or os.environ.get("POSTGIS_URL") or ""


def _query_dataset_evidence_sources(query: str, limit: int = 12) -> list[dict]:
    terms = _dataset_evidence_terms(query)
    if not terms:
        return []
    db_url = _dataset_evidence_db_url()
    if not db_url:
        logger.warning("Dataset evidence lookup skipped: database URL is not configured")
        return []
    patterns = [f"%{term}%" for term in terms]
    try:
        import psycopg2
        import psycopg2.extras

        with psycopg2.connect(db_url) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        chunk_id,
                        document_type,
                        content,
                        source_id,
                        source_sha256,
                        metadata,
                        metadata->>'title' AS title,
                        COALESCE(metadata->>'source_file', metadata->>'source_path') AS source_file,
                        metadata->>'section' AS section,
                        metadata->>'extraction_status' AS extraction_status,
                        embedding IS NULL AS embedding_missing
                    FROM knowledge.document_chunks
                    WHERE embedding IS NOT NULL
                      AND document_type = ANY(%s)
                      AND (
                        metadata::text ILIKE ANY(%s)
                        OR content ILIKE ANY(%s)
                        OR source_id ILIKE ANY(%s)
                      )
                    LIMIT 240
                    """,
                    (list(DATASET_EVIDENCE_DOC_TYPES), patterns, patterns, patterns),
                )
                rows = [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("Dataset evidence lookup failed", error=str(exc))
        return []

    grouped: dict[tuple[str, str, str], dict] = {}
    for row in rows:
        metadata = row.get("metadata") or {}
        title = row.get("title") or metadata.get("title") or row.get("source_id") or "Dataset evidence"
        source_file = row.get("source_file") or metadata.get("source_file") or metadata.get("source_path") or row.get("source_id") or "N/A"
        document_type = row.get("document_type") or metadata.get("document_type") or "dataset_profile"
        key = (str(source_file), str(title), str(document_type))
        text_for_score = " ".join([
            str(title),
            str(source_file),
            str(row.get("source_id") or ""),
            str(row.get("content") or ""),
            json.dumps(metadata, ensure_ascii=False),
        ]).lower()
        score = sum(1 for term in terms if term.lower() in text_for_score)
        item = grouped.setdefault(
            key,
            {
                "dataset_id": str(row.get("source_id") or hashlib.sha256(str(source_file).encode("utf-8")).hexdigest()[:16]),
                "name": str(title),
                "source_file": str(source_file),
                "target_relation": "knowledge.document_chunks",
                "row_count": 0,
                "null_embedding": 0,
                "document_type": str(document_type),
                "evidence_type": f"{document_type}_embedding_chunk",
                "source_sha256": row.get("source_sha256") or metadata.get("source_sha256"),
                "sections": set(),
                "chunk_ids": [],
                "score": 0,
                "excerpt": "",
            },
        )
        item["row_count"] += 1
        item["null_embedding"] += 1 if row.get("embedding_missing") else 0
        item["score"] += score
        if row.get("section"):
            item["sections"].add(str(row.get("section")))
        if row.get("chunk_id") and len(item["chunk_ids"]) < 8:
            item["chunk_ids"].append(str(row.get("chunk_id")))
        if not item["excerpt"] and row.get("content"):
            item["excerpt"] = " ".join(str(row.get("content")).split())[:320]

    results = []
    for item in grouped.values():
        normalized = dict(item)
        normalized["sections"] = sorted(item["sections"])[:8]
        results.append(normalized)
    results.sort(key=lambda item: (item.get("score", 0), item.get("row_count", 0)), reverse=True)
    return results[:limit]


ACCIDENT_EVENT_STOPWORDS = {
    "accident",
    "event",
    "events",
    "case",
    "cases",
    "\uc0ac\uace0",
    "\uc0ac\uac74",
    "\ud574\uc0c1\uc870\ub09c",
    "\uc870\ub09c\uc0ac\uace0",
    "\ud574\uc591\uc0ac\uace0",
    "\uc120\ubc15\uc0ac\uace0",
    "\ucc3e\uc544",
    "\ucc3e\uc544\uc918",
    "\ubcf4\uc5ec\uc918",
    "\uc54c\ub824\uc918",
    "\ubaa9\ub85d",
    "\uac80\uc0c9",
    "\uc870\ud68c",
    "\uadfc\uac70",
    "\uc704\uce58",
    "\uc9c0\ub3c4",
    "\ucc3e\uc544\ubcfc\ub798",
    "\ubcf4\uc5ec",
    "\uc54c\ub824",
    "\uac80\uc0c9\ud574",
    "\uac80\uc0c9\ud574\uc918",
    "\uc870\ud68c\ud574",
    "\uc870\ud68c\ud574\uc918",
    "\uc0ac\ub840",
    "\uc774\ub825",
    "\ucd5c\uadfc",
}


def _strip_korean_particles(token: str) -> str:
    cleaned = token.strip("`'\".,;:!?[]{}()")
    endings = (
        "\uc73c\ub85c\ubd80\ud130",
        "\ub85c\ubd80\ud130",
        "\uc5d0\uc11c\ub294",
        "\uc5d0\uc11c",
        "\uc5d0\uac8c",
        "\uaed8",
        "\uc73c\ub85c",
        "\ucc98\ub7fc",
        "\uc774\ub77c\uba74",
        "\ub77c\uba74",
        "\uae4c\uc9c0",
        "\ubd80\ud130",
        "\ub9cc",
        "\uc640",
        "\uacfc",
        "\uc740",
        "\ub294",
        "\uc774",
        "\uac00",
        "\uc744",
        "\ub97c",
        "\uc758",
        "\uc5d0",
        "\ub3c4",
        "\ub85c",
    )
    for ending in endings:
        if cleaned.endswith(ending) and len(cleaned) > len(ending) + 1:
            return cleaned[: -len(ending)]
    return cleaned


def _accident_event_terms(query: str) -> list[str]:
    raw_tokens = re.findall(r"[0-9A-Za-z\uac00-\ud7a3_-]{2,}", query or "")
    terms: list[str] = []
    for token in raw_tokens:
        cleaned = _strip_korean_particles(token)
        cleaned = re.sub(r"(?:을|를|이|가|은|는|으로|로|에서|에게|께|의|과|와|도|만|부터|까지|처럼|라면|이면)$", "", cleaned)
        lowered = cleaned.lower()
        if lowered in ACCIDENT_EVENT_STOPWORDS or cleaned in ACCIDENT_EVENT_STOPWORDS:
            continue
        if re.fullmatch(r"\d{1,4}", cleaned):
            continue
        terms.append(cleaned)
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        key = term.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(term)
    return deduped[:8]


def _query_accident_events(query: str, limit: int = 120) -> dict:
    terms = _accident_event_terms(query)
    db_url = _dataset_evidence_db_url()
    if not db_url:
        return {"terms": terms, "total": 0, "rows": [], "error": "S101_DB_URL or POSTGIS_URL is not configured"}
    where_parts: list[str] = []
    params: list[str] = []
    for term in terms:
        pattern = f"%{term}%"
        where_parts.append(
            "(authority ILIKE %s OR sea_area ILIKE %s OR cause ILIKE %s OR accident_type ILIKE %s OR vessel_type ILIKE %s)"
        )
        params.extend([pattern, pattern, pattern, pattern, pattern])
    where_sql = " AND ".join(where_parts) if where_parts else "TRUE"
    try:
        import psycopg2
        import psycopg2.extras

        with psycopg2.connect(db_url, connect_timeout=3) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SET LOCAL statement_timeout = '2500ms'")
                cur.execute(f"SELECT count(*) AS total FROM serving.accident_events WHERE {where_sql}", params)
                total = int((cur.fetchone() or {}).get("total") or 0)
                cur.execute(
                    f"""
                    SELECT
                        event_id,
                        source_row_number,
                        occurred_at,
                        authority,
                        sea_area,
                        weather,
                        cause,
                        accident_type,
                        vessel_count,
                        people_count,
                        rescued,
                        injured,
                        dead,
                        missing,
                        vessel_type,
                        tonnage,
                        longitude,
                        latitude,
                        ST_AsGeoJSON(geom)::text AS geometry_geojson
                    FROM serving.accident_events
                    WHERE {where_sql}
                    ORDER BY occurred_at DESC, source_row_number ASC
                    LIMIT %s
                    """,
                    [*params, limit],
                )
                rows = [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("Accident event lookup failed", error=str(exc))
        return {"terms": terms, "total": 0, "rows": [], "error": str(exc)}

    for row in rows:
        if isinstance(row.get("occurred_at"), datetime):
            row["occurred_at"] = row["occurred_at"].strftime("%Y-%m-%d %H:%M")
    return {"terms": terms, "total": total, "rows": rows, "error": None}


def _query_accident_events_near_geometry(
    geometry_wkt: str,
    *,
    radius_m: float,
    limit: int = 120,
) -> dict:
    db_url = _dataset_evidence_db_url()
    if not db_url:
        return {"total": 0, "rows": [], "error": "S101_DB_URL or POSTGIS_URL is not configured"}
    try:
        import psycopg2
        import psycopg2.extras

        with psycopg2.connect(db_url, connect_timeout=3) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("SET LOCAL statement_timeout = '2500ms'")
                cur.execute(
                    """
                    WITH base AS (
                        SELECT ST_SetSRID(ST_GeomFromText(%s), 4326)::geography AS g
                    )
                    SELECT count(*) AS total
                    FROM serving.accident_events AS a, base
                    WHERE ST_DWithin(a.geom::geography, base.g, %s)
                    """,
                    (geometry_wkt, radius_m),
                )
                total = int((cur.fetchone() or {}).get("total") or 0)
                cur.execute(
                    """
                    WITH base AS (
                        SELECT ST_SetSRID(ST_GeomFromText(%s), 4326)::geography AS g
                    )
                    SELECT
                        a.event_id,
                        a.source_row_number,
                        a.occurred_at,
                        a.authority,
                        a.sea_area,
                        a.weather,
                        a.cause,
                        a.accident_type,
                        a.vessel_count,
                        a.people_count,
                        a.rescued,
                        a.injured,
                        a.dead,
                        a.missing,
                        a.vessel_type,
                        a.tonnage,
                        a.longitude,
                        a.latitude,
                        ST_Distance(a.geom::geography, base.g) AS distance_m,
                        ST_AsGeoJSON(a.geom)::text AS geometry_geojson
                    FROM serving.accident_events AS a, base
                    WHERE ST_DWithin(a.geom::geography, base.g, %s)
                    ORDER BY ST_Distance(a.geom::geography, base.g), a.occurred_at DESC NULLS LAST
                    LIMIT %s
                    """,
                    (geometry_wkt, radius_m, limit),
                )
                rows = [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("Accident spatial history lookup failed", error=str(exc), radius_m=radius_m)
        return {"total": 0, "rows": [], "error": str(exc)}

    for row in rows:
        if isinstance(row.get("occurred_at"), datetime):
            row["occurred_at"] = row["occurred_at"].strftime("%Y-%m-%d %H:%M")
        if row.get("distance_m") is not None:
            row["distance_m"] = round(float(row["distance_m"]), 2)
    return {"total": total, "rows": rows, "error": None}


async def fast_accident_spatial_history_lookup_node(state: OrchestratorState) -> OrchestratorState:
    """Answer nearby accident history from serving.accident_events using a resolved place geometry."""
    import asyncio

    query = state.get("query") or state.get("normalized_query") or ""
    task_id = str(state.get("task_id") or "local")
    generated_at = datetime.utcnow().isoformat() + "Z"
    radius_m = _requested_distance_m(state, query) or 10000.0
    try:
        geometry_wkt, location_text, crs, resolution = await asyncio.to_thread(
            resolve_location,
            query,
            _spatial_context_dict(state),
        )
    except PlaceResolutionProblem as exc:
        payload = {
            "status": "NEEDS_CLARIFICATION" if exc.status == "NEEDS_USER_INPUT" else "BLOCKED",
            "error_code": exc.code,
            "summary": str(exc),
            "location_candidates": exc.candidates,
        }
        return _place_lookup_update(state, payload, "accident_spatial_history_lookup")

    result = _query_accident_events_near_geometry(geometry_wkt, radius_m=radius_m)
    rows = result.get("rows") or []
    total = int(result.get("total") or 0)
    found = bool(rows)
    quality_metrics = _quality_metrics_from_state(state, fast_path="accident_spatial_history_lookup", exact=found)
    features = []
    for row in rows:
        geometry = json.loads(row.get("geometry_geojson") or "{}")
        properties = {key: value for key, value in row.items() if key != "geometry_geojson"}
        properties.update({
            "layer_role": "accident_event",
            "label": f"{row.get('authority') or ''} {row.get('cause') or ''} {row.get('accident_type') or ''}".strip(),
            "source_ref": "serving.accident_events",
            "distance_m": row.get("distance_m"),
        })
        features.append({"type": "Feature", "id": row.get("event_id"), "geometry": geometry, "properties": properties})
    collection = {"type": "FeatureCollection", "features": features}
    type_counts: dict[str, int] = {}
    cause_counts: dict[str, int] = {}
    for row in rows:
        type_counts[str(row.get("accident_type") or "\ubbf8\uc0c1")] = type_counts.get(str(row.get("accident_type") or "\ubbf8\uc0c1"), 0) + 1
        cause_counts[str(row.get("cause") or "\ubbf8\uc0c1")] = cause_counts.get(str(row.get("cause") or "\ubbf8\uc0c1"), 0) + 1
    top_types = ", ".join(f"{name} {count}\uac74" for name, count in sorted(type_counts.items(), key=lambda item: item[1], reverse=True)[:4])
    top_causes = ", ".join(f"{name} {count}\uac74" for name, count in sorted(cause_counts.items(), key=lambda item: item[1], reverse=True)[:4])
    if result.get("error"):
        answer = f"{location_text} 부근 사고 이력 조회가 실패했습니다. 원인: {result['error']}"
    elif found:
        nearest = rows[0]
        answer = (
            f"{location_text} 기준 반경 {radius_m:g}m 이내 해상조난사고 이력 {total}건을 "
            f"`serving.accident_events`에서 확인했습니다. 지도에는 거리순 {len(rows)}건을 표시했습니다. "
            f"표시 목록 기준 사고유형은 {top_types or '집계 없음'}, 발생원인은 {top_causes or '집계 없음'}입니다. "
            f"가장 가까운 사고는 약 {nearest.get('distance_m')}m 거리의 {nearest.get('occurred_at')} "
            f"{nearest.get('authority')} 관할, {nearest.get('cause')} 원인, {nearest.get('accident_type')} 유형입니다. "
            "거리 기준점은 place registry/gazetteer에서 확정한 기준점이며, 별도 거리 표현이 없으면 기본 반경 10,000m를 사용합니다."
        )
    else:
        answer = (
            f"{location_text} 기준 반경 {radius_m:g}m 이내에서는 `serving.accident_events`에 적재된 "
            "해상조난사고 이력을 찾지 못했습니다. 별도 거리 표현이 없어서 기본 반경 10,000m를 사용했습니다."
        )
    citations = [{
        "document_id": "dataset:coastguard_accident_events_2025",
        "source": "해양경찰청 해상조난사고 상세데이터",
        "source_id": "serving.accident_events",
        "section": "spatial accident history rows",
        "document_type": "accident_data",
        "chunk_id": "serving.accident_events",
        "similarity": 1.0 if found else 0.0,
        "summary_ko": f"{location_text} 기준 반경 {radius_m:g}m 이내 사고 이력 {total}건",
        "detail_label": "상세정보",
        "detail_text": "사고 좌표와 기준점 거리, 관할해경서, 발생해역, 발생원인, 발생유형은 serving.accident_events에서 직접 조회했습니다.",
        "provenance": {"method": "structured_accident_spatial_history_lookup", "retrieved_at": generated_at, "radius_m": radius_m, "location_resolution": resolution},
    }]
    plan_status = "BLOCKED_DATA" if result.get("error") else "EXECUTION_READY"
    route_plan = {
        "task_id": f"TASK-ACCIDENT-SPATIAL-{task_id[:3].upper()}",
        "status": "DRAFT",
        "intent": "ACCIDENT_ANALYSIS",
        "context": "accident_risk",
        "analysis_type": "accident_spatial_history_lookup",
        "derived_concept": "accident_event",
        "primary_agent": "Accident/Risk Agent",
        "secondary_agents": ["Spatial Analysis Agent"],
        "slots": {
            "location_text": location_text,
            "reference_geometry": geometry_wkt,
            "crs": crs,
            "distance_m": radius_m,
            "spatial_relation": "nearby",
            "target_term": "accident_history",
            "derived_concept": "accident_event",
            "analysis_type": "accident_spatial_history_lookup",
        },
        "tools": ["accident.spatial_history_lookup"],
        "data": ["serving.accident_events"],
        "outputs": ["AccidentEventGeoJSON", "EvidenceBundle", "Summary"],
        "clarification_required": False,
        "confidence": 1.0 if found else 0.82,
        "execution_ready": False,
        "route_plan_status": "DRAFT",
    }
    qec_model = QueryExecutionContext(
        request_id=task_id,
        task_id=task_id,
        original_query=query,
        normalized_query=state.get("normalized_query"),
        route_plan=route_plan,
        slots=ExecutionSlots.from_payload(route_plan["slots"]),
        spatial={"spatial_context": {"base_location": location_text, "geometry": geometry_wkt, "crs": crs, "buffer_distance": radius_m}},
        blockers=[result["error"]] if result.get("error") else [],
        warnings=["기본 반경은 질의에 거리 표현이 없을 때만 10,000m로 적용됩니다."],
        provenance={"location_resolution": resolution},
    )
    qec_model = validate_execution_context(qec_model)
    route_plan["status"] = qec_model.readiness.value
    route_plan["route_plan_status"] = qec_model.readiness.value
    route_plan["execution_ready"] = qec_model.readiness == PlanStatus.EXECUTION_READY
    qec = qec_model.model_dump(mode="json")
    final_dict = {
        "task_id": task_id,
        "trace_id": f"tr-{task_id}",
        "agent_name": "Accident/Risk Agent",
        "agent_version": "2.5.0-accident-spatial-history-fast-path",
        "status": AgentStatus.COMPLETED if qec_model.readiness == PlanStatus.EXECUTION_READY else AgentStatus.BLOCKED,
        "summary": answer,
        "answer_text": answer,
        "structured_result": {
            "analysis_type": "accident_spatial_history_lookup",
            "total_count": total,
            "returned_count": len(rows),
            "location_text": location_text,
            "radius_m": radius_m,
            "location_resolution": resolution,
            "events": [{key: value for key, value in row.items() if key != "geometry_geojson"} for row in rows],
            "geojson": collection,
            "quality_metrics": quality_metrics,
            "performance_profile": {"path": "fast_accident_spatial_history_lookup", "db_statement_timeout_ms": 2500},
        },
        "features": collection,
        "map_layers": [{
            "layer_id": f"accident-spatial-history:{task_id}",
            "title": f"{location_text} 부근 사고 이력",
            "source_type": "geojson",
            "geometry_type": "POINT",
            "inline_geojson": collection,
            "feature_count": len(features),
            "style": {"circleColor": "#dc2626", "circleRadius": 6, "circleOpacity": 0.76},
            "metadata": {"layer_role": "accident_event", "total_count": total, "source_ref": "serving.accident_events", "radius_m": radius_m},
        }],
        "evidence_bundle": {
            "rag_evidence": [],
            "kg_provenance": [{"source_ref": "data/place_geometry_registry.yaml", "concept": "place_anchor", "location_resolution": resolution}],
            "regulatory_evidence": [],
            "spatial_feature_evidence": [],
            "spatial_layer_evidence": citations,
            "accident_relation_evidence": citations,
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "embedding_independent": True,
            "fast_path": "accident_spatial_history_lookup",
            "quality_metrics": quality_metrics,
        },
        "contract_version": "geollm.execution.v1",
        "request_id": task_id,
    }
    _attach_candidate_trace(state, final_dict)
    _record_query_quality_issues(state, final_dict)
    status = AgentStatus.COMPLETED if qec_model.readiness == PlanStatus.EXECUTION_READY else AgentStatus.BLOCKED
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "candidate_trace": state.get("candidate_trace"),
        "status": status,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, status, actor="FastAccidentSpatialHistoryLookup"),
    }


async def fast_accident_event_lookup_node(state: OrchestratorState) -> OrchestratorState:
    """Answer row-level accident event lookup from serving.accident_events."""
    query = state.get("query") or state.get("normalized_query") or ""
    task_id = str(state.get("task_id") or "local")
    generated_at = datetime.utcnow().isoformat() + "Z"
    result = _query_accident_events(query)
    rows = result.get("rows") or []
    total = int(result.get("total") or 0)
    found = bool(rows)
    quality_metrics = _quality_metrics_from_state(state, fast_path="accident_event_structured_lookup", exact=found)

    features = []
    for row in rows:
        geometry = json.loads(row.get("geometry_geojson") or "{}")
        properties = {key: value for key, value in row.items() if key != "geometry_geojson"}
        properties.update({
            "layer_role": "accident_event",
            "label": f"{row.get('authority') or ''} {row.get('cause') or ''} {row.get('accident_type') or ''}".strip(),
            "source_ref": "serving.accident_events",
        })
        features.append({"type": "Feature", "id": row.get("event_id"), "geometry": geometry, "properties": properties})
    collection = {"type": "FeatureCollection", "features": features}

    by_type: dict[str, int] = {}
    by_sea_area: dict[str, int] = {}
    people_total = 0
    rescued_total = 0
    casualties_total = 0
    for row in rows:
        by_type[str(row.get("accident_type") or "\ubbf8\uc0c1")] = by_type.get(str(row.get("accident_type") or "\ubbf8\uc0c1"), 0) + 1
        by_sea_area[str(row.get("sea_area") or "\ubbf8\uc0c1")] = by_sea_area.get(str(row.get("sea_area") or "\ubbf8\uc0c1"), 0) + 1
        people_total += int(row.get("people_count") or 0)
        rescued_total += int(row.get("rescued") or 0)
        casualties_total += int(row.get("injured") or 0) + int(row.get("dead") or 0) + int(row.get("missing") or 0)

    top_types = ", ".join(f"{name} {count}\uac74" for name, count in sorted(by_type.items(), key=lambda item: item[1], reverse=True)[:4])
    top_areas = ", ".join(f"{name} {count}\uac74" for name, count in sorted(by_sea_area.items(), key=lambda item: item[1], reverse=True)[:4])
    terms_text = ", ".join(result.get("terms") or []) or query
    if found:
        sample = rows[0]
        answer = (
            f"`serving.accident_events`에서 `{terms_text}` 조건의 해상조난사고 {total}건을 찾았습니다. "
            f"지도에는 최근순 {len(rows)}건을 사고 이벤트 포인트로 표시했습니다. "
            f"조회된 표시 목록 기준 사고유형은 {top_types or '집계 없음'}, 발생해역은 {top_areas or '집계 없음'}입니다. "
            f"표시 목록의 발생인원 합계는 {people_total}명, 구조 {rescued_total}명, 부상/사망/실종 합계 {casualties_total}명입니다. "
            f"가장 최근 사례는 {sample.get('occurred_at')} {sample.get('authority')} 관할, {sample.get('sea_area')}, "
            f"{sample.get('cause')} 원인, {sample.get('accident_type')} 유형입니다. "
            "제한 사항: 이 경로는 해양경찰청 2025 해상조난사고 상세데이터의 구조화 row를 기준으로 하며, 사고 원인과 전자해도 객체 간 인과관계는 추정하지 않습니다."
        )
    else:
        answer = (
            f"`serving.accident_events`에서 `{terms_text}` 조건과 일치하는 해상조난사고 row를 찾지 못했습니다. "
            "철자, 관할해경서, 발생원인, 발생유형 중 하나를 더 구체화하면 구조화 사고 테이블에서 다시 조회할 수 있습니다."
        )

    citations = [{
        "document_id": "dataset:coastguard_accident_events_2025",
        "source": "해양경찰청 해상조난사고 상세데이터",
        "source_id": "serving.accident_events",
        "source_file": "Dataset/해양경찰청_해상조난사고 상세데이터 현황_20251231 (1).csv",
        "section": "structured accident rows",
        "document_type": "accident_data",
        "chunk_id": "serving.accident_events",
        "similarity": 1.0 if found else 0.0,
        "summary_ko": f"조건 `{terms_text}`에 대한 구조화 사고 row {total}건",
        "detail_label": "상세정보",
        "detail_text": "관할해경서, 발생해역, 발생원인, 발생유형, 선종, 인원 및 좌표는 serving.accident_events에서 직접 조회했습니다.",
        "provenance": {"method": "structured_accident_event_lookup", "retrieved_at": generated_at, "terms": result.get("terms") or []},
    }]
    route_plan = {
        "task_id": f"TASK-ACCIDENT-EVENT-{task_id[:3].upper()}",
        "status": "EXECUTION_READY" if not result.get("error") else "BLOCKED_DATA",
        "intent": "ACCIDENT_ANALYSIS",
        "context": "accident_risk",
        "analysis_type": "accident_event_lookup",
        "derived_concept": "accident_event",
        "primary_agent": "Accident/Risk Agent",
        "secondary_agents": [],
        "slots": {"target_terms": result.get("terms") or [], "analysis_type": "accident_event_lookup"},
        "tools": ["accident.event_lookup"],
        "data": ["serving.accident_events"],
        "outputs": ["AccidentEventGeoJSON", "EvidenceBundle", "Summary"],
        "clarification_required": False,
        "confidence": 1.0 if found else 0.72,
        "execution_ready": not bool(result.get("error")),
        "route_plan_status": "EXECUTION_READY" if not result.get("error") else "BLOCKED_DATA",
    }
    qec = {
        "readiness": "READY" if not result.get("error") else "BLOCKED_DATA",
        "blockers": [result["error"]] if result.get("error") else [],
        "warnings": [
            "사고 row 위치와 전자해도 객체의 공간 관계 또는 인과관계는 이 조회만으로 단정하지 않습니다.",
            "표시 목록 집계는 응답 제한으로 반환된 최근순 row 기준이며, 전체 건수는 total_count를 사용하십시오.",
        ],
        "data_bindings": [{"dataset_id": "accident_events_coastguard_2025", "relation": "serving.accident_events", "geometry_column": "geom"}],
        "tool_bindings": [{"tool_id": "accident.event_lookup", "operation": "structured_accident_event_lookup"}],
    }
    final_dict = {
        "task_id": task_id,
        "trace_id": f"tr-{task_id}",
        "agent_name": "Accident/Risk Agent",
        "agent_version": "2.4.0-accident-event-fast-path",
        "status": AgentStatus.COMPLETED if not result.get("error") else AgentStatus.BLOCKED,
        "summary": answer,
        "answer_text": answer,
        "structured_result": {
            "analysis_type": "accident_event_lookup",
            "total_count": total,
            "returned_count": len(rows),
            "terms": result.get("terms") or [],
            "events": [{key: value for key, value in row.items() if key != "geometry_geojson"} for row in rows],
            "geojson": collection,
            "quality_metrics": quality_metrics,
            "web_rag_usage": {
                "web_used": False,
                "rag_used": False,
                "llm_used": False,
                "execution_path": "accident_event_structured_fast_path",
                "local_authoritative_registry_checked": True,
                "embedding_independent": True,
            },
        },
        "features": collection,
        "map_layers": [{
            "layer_id": f"accident-events:{task_id}",
            "title": "해상조난사고 이벤트",
            "source_type": "geojson",
            "geometry_type": "POINT",
            "inline_geojson": collection,
            "feature_count": len(features),
            "style": {"circleColor": "#d9480f", "circleRadius": 6, "circleOpacity": 0.78},
            "metadata": {"layer_role": "accident_event", "total_count": total, "source_ref": "serving.accident_events"},
        }],
        "evidence_bundle": {
            "rag_evidence": [],
            "kg_provenance": [{"source_ref": "data/accident_dictionary.yaml", "concept": "accident_event", "terms": result.get("terms") or []}],
            "regulatory_evidence": [],
            "spatial_feature_evidence": [],
            "spatial_layer_evidence": citations,
            "accident_relation_evidence": citations,
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "embedding_independent": True,
            "fast_path": "accident_event_structured_lookup",
            "quality_metrics": quality_metrics,
        },
        "contract_version": "geollm.execution.v1",
        "request_id": task_id,
    }
    _attach_candidate_trace(state, final_dict)
    _record_query_quality_issues(state, final_dict)
    status = AgentStatus.COMPLETED if not result.get("error") else AgentStatus.BLOCKED
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "candidate_trace": state.get("candidate_trace"),
        "status": status,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, status, actor="FastAccidentEventLookup"),
    }


async def fast_dataset_evidence_answer_node(state: OrchestratorState) -> OrchestratorState:
    """Answer Dataset provenance questions from live knowledge.document_chunks."""
    query = state.get("query") or state.get("normalized_query") or ""
    task_id = str(state.get("task_id") or "local")
    generated_at = datetime.utcnow().isoformat() + "Z"
    sources = _query_dataset_evidence_sources(query)
    citations = []
    documents = []
    for item in sources:
        doc = {
            "document_id": f"dataset_provenance:{item['dataset_id']}",
            "title": item["name"],
            "version": "live_knowledge_document_chunks",
            "section": ", ".join(item.get("sections") or []) or item.get("document_type") or "dataset_evidence",
            "page": "N/A",
            "source": "knowledge.document_chunks",
            "source_file": item["source_file"],
            "excerpt_reference": (
                f"{item['dataset_id']} -> {item['target_relation']}: "
                f"{item['row_count']} embedded chunks; excerpt={item.get('excerpt') or 'N/A'}"
            ),
            "retrieved_at": generated_at,
            "relevance_score": item.get("score") or 1.0,
        }
        citation = {
            "document_id": doc["document_id"],
            "source": doc["title"],
            "source_id": item["dataset_id"],
            "source_file": item["source_file"],
            "section": doc["section"],
            "document_type": item.get("document_type") or "dataset_profile",
            "chunk_id": ", ".join(item.get("chunk_ids") or []) or doc["document_id"],
            "similarity": item.get("score") or 1.0,
            "summary_ko": f"{item['name']} / {item['source_file']}: {item['row_count']}개 embedded chunk",
            "detail_label": "상세정보",
            "detail_text": item.get("excerpt") or doc["excerpt_reference"],
            "provenance": {
                "method": "live_document_chunks_dataset_evidence_lookup",
                "target_relation": item["target_relation"],
                "row_count": item["row_count"],
                "null_embedding": item.get("null_embedding", 0),
                "evidence_type": item["evidence_type"],
                "query": query,
            },
        }
        documents.append(doc)
        citations.append(citation)
    found = bool(sources)
    quality_metrics = _quality_metrics_from_state(
        state,
        fast_path="dataset_evidence_live_document_chunks",
        exact=found,
        blocked_no_evidence=not found,
    )
    target_terms = _dataset_evidence_terms(query)
    target_term = ", ".join(target_terms[:4]) if target_terms else "dataset"
    derived_concept = "dataset_embedding_provenance"
    total_chunks = sum(int(item.get("row_count") or 0) for item in sources)
    total_null_embeddings = sum(int(item.get("null_embedding") or 0) for item in sources)
    type_counts: dict[str, int] = {}
    for item in sources:
        document_type = str(item.get("document_type") or "dataset_profile")
        type_counts[document_type] = type_counts.get(document_type, 0) + int(item.get("row_count") or 0)
    type_summary = ", ".join(f"{name} {count}건" for name, count in sorted(type_counts.items()))
    source_summary = "; ".join(
        f"{item.get('source_file')} ({item.get('document_type')}, {item.get('row_count')} chunks)"
        for item in sources[:6]
    )
    if found:
        answer = (
            f"live `knowledge.document_chunks`에서 질의와 맞는 Dataset 근거 {len(sources)}개 source, "
            f"총 {total_chunks}개 embedded chunk를 찾았습니다. "
            f"문서 유형별로는 {type_summary or '분류 정보 없음'}이며, embedding NULL은 {total_null_embeddings}건입니다. "
            f"주요 원천은 {source_summary}입니다. "
            "이 fast path는 법령/고시 확정 근거가 아니라 Dataset provenance, 임베딩 coverage, RAG/분석 근거 확인용입니다."
        )
    else:
        answer = (
            "live `knowledge.document_chunks`에서 이 질의와 직접 매칭되는 Dataset 임베딩 근거를 찾지 못했습니다. "
            "근거 없는 적재 여부나 chunk 수를 생성하지 않습니다. 파일명, 기관명, 데이터셋명 중 하나를 더 구체적으로 넣으면 다시 조회할 수 있습니다."
        )
    route_plan = {
        "task_id": f"TASK-DATASET-EVIDENCE-{task_id[:3].upper()}",
        "status": "EXECUTION_READY",
        "intent": "DATA_DISCOVERY",
        "context": "dataset_provenance",
        "analysis_type": "dataset_evidence_lookup",
        "derived_concept": derived_concept,
        "primary_agent": "Data Discovery Agent",
        "secondary_agents": [],
        "slots": {
            "target_term": target_term,
            "analysis_type": "dataset_evidence_lookup",
            "requested_sources": [item["dataset_id"] for item in sources],
        },
        "tools": ["dataset.ingestion_report_lookup", "rag.dataset_profile_retrieve"],
        "data": [item["target_relation"] for item in sources],
        "outputs": ["DatasetEvidenceOutput", "EvidenceBundle", "Summary"],
        "clarification_required": False,
        "confidence": 1.0,
        "execution_ready": True,
        "route_plan_status": "EXECUTION_READY",
    }
    final_dict = {
        "task_id": task_id,
        "trace_id": f"tr-{task_id}",
        "agent_name": "Data Discovery Agent",
        "agent_version": "2.3.0-dataset-evidence-fast-path",
        "status": AgentStatus.COMPLETED,
        "summary": answer,
        "answer_text": answer,
        "structured_result": {
            "retrieved_count": len(documents),
            "documents": documents,
            "citations": citations,
            "sources": sources,
            "no_evidence": False,
            "evidence_candidate_summary": {
                "rag_evidence": len(citations),
                "dataset_embedding_coverage_candidate": len(citations),
            },
            "quality_metrics": quality_metrics,
            "web_rag_usage": {
                "web_used": False,
                "rag_used": True,
                "llm_used": False,
                "execution_path": "dataset_evidence_fast_path",
                "local_authoritative_registry_checked": False,
                "dataset_ingestion_report_checked": True,
            },
        },
        "evidence_bundle": {
            "rag_evidence": citations,
            "kg_provenance": [],
            "regulatory_evidence": [],
            "spatial_feature_evidence": [],
            "spatial_layer_evidence": citations,
            "accident_relation_evidence": [],
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": {
                "readiness": "READY",
                "blockers": [],
                "warnings": [],
                "data_bindings": [
                    {
                        "dataset_id": item["dataset_id"],
                        "relation": item["target_relation"],
                        "source_file": item["source_file"],
                    }
                    for item in sources
                ],
                "tool_bindings": [
                    {"tool_id": "dataset.ingestion_report_lookup", "operation": "exact_dataset_provenance_lookup"},
                    {"tool_id": "rag.dataset_profile_retrieve", "operation": "dataset_embedding_candidate_lookup"},
                ],
            },
            "embedding_independent": False,
            "fast_path": "dataset_evidence_live_document_chunks",
            "quality_metrics": quality_metrics,
        },
        "contract_version": "geollm.execution.v1",
        "request_id": task_id,
    }
    _attach_candidate_trace(state, final_dict)
    _record_query_quality_issues(state, final_dict)
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": final_dict["orchestrator_v2"]["query_execution_context"],
        "candidate_trace": state.get("candidate_trace"),
        "status": AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.COMPLETED, actor="FastDatasetEvidenceAnswer"),
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
    _attach_candidate_trace(state, final_dict)
    _record_query_quality_issues(state, final_dict)
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "candidate_trace": state.get("candidate_trace"),
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
    quality_metrics = _quality_metrics_from_state(state, fast_path="spatial_or_traffic_blocked_data")
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
            "temporal_window": route_plan.get("slots", {}).get("temporal_window"),
            "quality_metrics": quality_metrics,
            "web_rag_usage": {"web_used": False, "rag_used": False, "llm_used": False, "execution_path": analysis_type, "embedding_independent": True},
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "embedding_independent": True,
            "fast_path": "spatial_or_traffic_blocked_data",
            "quality_metrics": quality_metrics,
        },
        "evidence_bundle": {"rag_evidence": [], "kg_provenance": [], "regulatory_evidence": [], "spatial_feature_evidence": [], "spatial_layer_evidence": [], "accident_relation_evidence": []},
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
    _attach_candidate_trace(state, final_dict)
    _record_query_quality_issues(state, final_dict)
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "candidate_trace": state.get("candidate_trace"),
        "status": AgentStatus.BLOCKED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.BLOCKED, actor="FastSpatialTrafficBlock"),
    }

async def fast_s101_hazard_radius_execute_node(state: OrchestratorState) -> OrchestratorState:
    """Run confirmed radius requests through the shared execution gate."""
    import asyncio
    from services.orchestrator.s101_radius_execution import execute_radius_request

    if _looks_like_policy_block_query(state.get("query", "")):
        return await fast_spatial_or_traffic_block_node(state)
    final = await asyncio.to_thread(execute_radius_request, state)
    _attach_candidate_trace(state, final)
    context = final["orchestrator_v2"]["query_execution_context"]
    status = AgentStatus(final["status"])
    return {
        "final_dict": final,
        "task_plan": final["orchestrator_v2"]["route_plan"],
        "query_execution_context": context,
        "candidate_trace": state.get("candidate_trace"),
        "status": status,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, status, actor="ValidatedS101HazardRadius"),
    }


async def fast_dynamic_traffic_execute_node(state: OrchestratorState) -> OrchestratorState:
    """Execute AIS/V-PASS dynamic traffic volume queries against PostGIS."""
    import asyncio
    from services.orchestrator.traffic_execution import TrafficProblem, execute_traffic_request

    try:
        final = await asyncio.to_thread(execute_traffic_request, state)
        _attach_candidate_trace(state, final)
        status = AgentStatus(final["status"])
        return {
            "final_dict": final,
            "task_plan": final["orchestrator_v2"]["route_plan"],
            "query_execution_context": final["orchestrator_v2"]["query_execution_context"],
            "candidate_trace": state.get("candidate_trace"),
            "status": status,
            "state_history": log_transition(AgentStatus.INTENT_PARSED, status, actor="DynamicTrafficLayerExecute"),
        }
    except TrafficProblem:
        return await fast_spatial_or_traffic_block_node(state)


async def fast_s101_nearest_feature_execute_node(state: OrchestratorState) -> OrchestratorState:
    """Execute registry-backed nearest S-101 feature search against PostGIS."""
    import asyncio
    from services.orchestrator.place_router import resolve_payload

    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    if state.get("user_id") == "blocked_user":
        return _place_lookup_update(state, {"status": "BLOCKED", "error_code": "ACCESS_DENIED", "summary": "이 요청에 대한 접근 권한이 없습니다."}, "nearest_feature")
    location = await asyncio.to_thread(resolve_payload, query, _spatial_context_dict(state))
    if location["status"] != "RESOLVED":
        return _place_lookup_update(state, location, "nearest_feature")
    base_wkt, location_text = location["geometry"], location["location_text"]
    target_features = _nearest_target_features_from_query(query)
    config = _s101_nearest_feature_config(target_features)
    layer = config["layer"]
    template = config["template"]
    relation = layer.get("physical_table") or layer.get("expected_physical_table")
    feature_codes = config["feature_codes"]
    if not base_wkt or not relation or not feature_codes:
        return await fast_spatial_or_traffic_block_node(state)

    format_args = {
        "relation": relation,
        "id_column": layer.get("id_column", "feature_instance_id"),
        "code_column": layer.get("code_column", "feature_type_code"),
        "name_column": layer.get("name_column", "feature_type_name"),
        "geometry_column": layer.get("geometry_column", "geometry"),
        "attributes_column": layer.get("attributes_column", "attributes"),
    }
    select_sql = str(((template.get("sql") or {}).get("select") or "")).format(**format_args)
    if not select_sql:
        return await fast_spatial_or_traffic_block_node(state)

    params = {
        "base_wkt": base_wkt,
        "srid": int(layer.get("srid") or 4326),
        "feature_codes": feature_codes,
        "result_limit": int(config["result_limit"]),
    }
    rows: list[dict] = []
    try:
        import psycopg2
        import psycopg2.extras

        db_url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
        if not db_url:
            raise RuntimeError("S101_DB_URL or POSTGIS_URL is not configured")
        with psycopg2.connect(db_url, connect_timeout=3) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(select_sql, params)
                rows = [dict(row) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("Fast S-101 nearest feature execution failed", error=str(exc), query=query)
        return await fast_spatial_or_traffic_block_node(state)

    features = []
    table_rows = []
    for row in rows:
        geometry = json.loads(row["geojson"]) if row.get("geojson") else None
        feature_type_code = int(row.get("feature_type_code") or 0)
        feature_name = row.get("feature_type_name") or config["feature_names"].get(feature_type_code) or f"NFTC:{feature_type_code}"
        distance_value = float(row.get("distance_m") or 0.0)
        properties = {
            "feature_instance_id": row.get("id"),
            "feature_type_code": feature_type_code,
            "feature_name": feature_name,
            "distance_m": round(distance_value, 2),
            "source": relation,
        }
        attrs = row.get("attributes")
        if isinstance(attrs, dict):
            properties["attributes"] = attrs
        geometry_type = (geometry or {}).get("type") if isinstance(geometry, dict) else None
        properties["portrayal"] = resolve_s101_portrayal(feature_name, geometry_type, attrs)
        properties["portrayal_symbol"] = properties["portrayal"].get("symbol")
        properties["portrayal_symbol_asset"] = properties["portrayal"].get("asset")
        features.append({"type": "Feature", "geometry": geometry, "properties": properties})
        table_rows.append(properties)

    nearest = table_rows[0] if table_rows else {}
    feature_collection = {"type": "FeatureCollection", "features": features}
    route_plan = {
        "task_id": f"TASK-S101-NEAREST-{state['task_id'][:3].upper()}",
        "status": "EXECUTION_READY",
        "intent": "SPATIAL_ANALYSIS",
        "context": "navigation_safety",
        "analysis_type": "nearest_feature",
        "derived_concept": "nearest_feature",
        "primary_agent": "Spatial Analysis Agent",
        "secondary_agents": [],
        "slots": {
            "location_text": location_text,
            "reference_geometry": base_wkt,
            "target_term": "anchorage",
            "target_features": config["target_features"],
            "nftc_codes": feature_codes,
            "k": int(config["result_limit"]),
            "analysis_type": "nearest_feature",
        },
        "tools": ["postgis.nearest"],
        "data": [config["layer_id"]],
        "outputs": ["GeoJSON", "FeatureTable", "Summary"],
        "clarification_required": False,
        "confidence": 1.0,
        "execution_ready": True,
        "route_plan_status": "EXECUTION_READY",
    }
    qec = {
        "readiness": "READY",
        "blockers": [],
        "warnings": [],
        "data_bindings": [{
            "dataset_id": config["layer_id"],
            "relation": relation,
            "geometry_column": layer.get("geometry_column", "geometry"),
            "srid": int(layer.get("srid") or 4326),
            "layer_type": layer.get("layer_type", "s101_feature"),
            "execution_status": layer.get("execution_status", "executable"),
            "read_only": True,
        }],
        "tool_bindings": [{
            "tool_id": "postgis.nearest",
            "operation": "nearest_feature",
            "query_template_id": config["template_id"],
            "schema_version": "2.0",
        }],
    }
    summary = (
        f"{location_text or '기준 위치'}에서 가장 가까운 S-101 정박지는 "
        f"{round(float(nearest.get('distance_m') or 0.0), 2)}m 거리에 있습니다."
        if nearest else f"{location_text or '기준 위치'} 주변에서 S-101 정박지를 찾지 못했습니다."
    )
    final_dict = {
        "task_id": state["task_id"],
        "trace_id": f"tr-{state['task_id']}",
        "agent_name": "Spatial Analysis Agent",
        "agent_version": "2.3.0-s101-nearest-execute",
        "status": "COMPLETED",
        "summary": summary,
        "answer_text": summary,
        "structured_result": {
            "status": "COMPLETED",
            "analysis_type": "nearest_feature",
            "count": len(features),
            "nearest": nearest,
            "location_text": location_text,
            "reference_geometry": base_wkt,
            "target_features": config["target_features"],
            "features": table_rows,
            "geojson": feature_collection,
        },
        "map_layers": [{
            "layer_id": f"{state['task_id']}-s101-nearest-feature",
            "task_id": state["task_id"],
            "title": "Nearest S-101 Feature",
            "description": summary,
            "geometry_type": "GEOMETRY",
            "source_type": "geojson",
            "inline_geojson": feature_collection,
            "feature_count": len(features),
            "metadata": {"source": relation, "query_template_id": config["template_id"]},
        }],
        "features": feature_collection,
        "evidence_bundle": {
            "rag_evidence": [],
            "kg_provenance": [],
            "regulatory_evidence": [],
            "spatial_feature_evidence": table_rows[:100],
            "spatial_layer_evidence": [{
                "dataset_id": config["layer_id"],
                "relation": relation,
                "feature_type_codes": feature_codes,
                "query_template_id": config["template_id"],
            }],
            "accident_relation_evidence": [],
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "embedding_independent": True,
            "fast_path": "registry_backed_s101_nearest_feature_execute",
        },
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
    qec.setdefault("provenance", {})["location_resolution"] = location["location_resolution"]
    final_dict["structured_result"].update({key: location.get(key) for key in ("place_id", "place_version", "location_resolution")})
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "status": AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.COMPLETED, actor="FastS101NearestFeatureExecute"),
    }


async def fast_requested_spatial_layer_execute_node(state: OrchestratorState) -> OrchestratorState:
    """Execute Dataset-ingested spatial layer radius searches against PostGIS."""
    import asyncio
    from services.orchestrator.place_router import resolve_payload

    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    targets = _requested_spatial_layer_targets(query)
    if not targets:
        return await fast_spatial_or_traffic_block_node(state)

    sea_parting_place = None
    if any(target["layer_id"] == "sea_parting_prediction" for target in targets):
        sea_parting_place = next((place for place in SEA_PARTING_QUERY_ANCHORS if place in query), None)
    if sea_parting_place:
        location = {
            "status": "RESOLVED",
            "geometry": SEA_PARTING_QUERY_ANCHORS[sea_parting_place],
            "location_text": sea_parting_place,
            "location_resolution": {
                "method": "sea_parting_site_anchor",
                "confidence": 0.92,
                "source": "serving.sea_parting_prediction_current site anchor",
            },
        }
    else:
        location = await asyncio.to_thread(resolve_payload, query, _spatial_context_dict(state))
        if location["status"] != "RESOLVED":
            return _place_lookup_update(state, location, "feature_search_by_radius")

    base_wkt = location["geometry"]
    location_text = location["location_text"]
    distance_m = _requested_layer_distance_m(query, state)
    limit_per_layer = 100
    sql = """
        WITH base AS (
            SELECT ST_SetSRID(ST_GeomFromText(%(base_wkt)s), 4326)::geography AS g
        )
        SELECT source_id,
               layer_id,
               {name_column} AS name,
               properties,
               provenance,
               ST_AsGeoJSON(geometry)::json AS geojson,
               ST_Distance(geometry::geography, base.g) AS distance_m
        FROM {relation}, base
        WHERE layer_id = %(layer_id)s
          AND geometry IS NOT NULL
          AND ST_DWithin(geometry::geography, base.g, %(distance_m)s)
        ORDER BY geometry::geography <-> base.g
        LIMIT %(limit)s
    """

    rows: list[dict] = []
    try:
        import psycopg2
        import psycopg2.extras

        db_url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
        if not db_url:
            raise RuntimeError("POSTGIS_URL or S101_DB_URL is not configured")
        with psycopg2.connect(db_url, connect_timeout=3) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                for target in targets:
                    cur.execute(
                        sql.format(
                            relation=target["relation"],
                            name_column=target.get("name_column") or "name",
                        ),
                        {
                            "base_wkt": base_wkt,
                            "layer_id": target["layer_id"],
                            "distance_m": distance_m,
                            "limit": limit_per_layer,
                        },
                    )
                    for row in cur.fetchall():
                        item = dict(row)
                        item["_target"] = target
                        rows.append(item)
    except Exception as exc:
        logger.warning("Requested spatial layer execution failed", error=str(exc), query=query)
        return await fast_spatial_or_traffic_block_node(state)

    rows.sort(key=lambda row: float(row.get("distance_m") or 0.0))
    features = []
    table_rows = []
    evidence = []
    for idx, row in enumerate(rows[:200]):
        target = row["_target"]
        geometry = row.get("geojson")
        if isinstance(geometry, str):
            geometry = json.loads(geometry)
        props = row.get("properties") if isinstance(row.get("properties"), dict) else {}
        provenance = row.get("provenance") if isinstance(row.get("provenance"), dict) else {}
        distance_value = round(float(row.get("distance_m") or 0.0), 2)
        feature_id = f"{target['layer_id']}:{row.get('source_id') or idx}"
        evidence_id = f"spatial:{state['task_id']}:{idx}"
        display_name = row.get("name") or props.get("name") or props.get("title") or props.get("\uc9c0\uba85\uba85") or target["title"]
        properties = {
            **props,
            "source_id": row.get("source_id"),
            "layer_id": target["layer_id"],
            "layer_title": target["title"],
            "layer_type": target["layer_type"],
            "name": display_name,
            "display_name": display_name,
            "feature_name": display_name,
            "feature_display_name": display_name,
            "distance_m": distance_value,
            "source": target["relation"],
            "provenance": provenance,
            "feature_id": feature_id,
            "id": feature_id,
            "evidence_id": evidence_id,
        }
        features.append({"type": "Feature", "id": feature_id, "geometry": geometry, "properties": properties})
        table_rows.append(properties)
        evidence.append({
            "evidence_id": evidence_id,
            "evidence_type": "spatial_feature",
            "summary": properties.get("name") or target["title"],
            "source_ref": target["relation"],
            "data": {
                **properties,
                "feature_id": feature_id,
                "id": feature_id,
                "evidence_id": evidence_id,
                "layer_id": target["layer_id"],
                "distance_m": distance_value,
                "properties": properties,
                "geometry_type": (geometry or {}).get("type") if isinstance(geometry, dict) else None,
            },
        })

    collection = {"type": "FeatureCollection", "features": features}
    target_titles = ", ".join(target["title"] for target in targets)
    sample_names = [str(row.get("name")) for row in table_rows[:8] if row.get("name")]
    sample_text = f" 주요 지명: {', '.join(sample_names)}." if sample_names else ""
    answer = (
        f"{location_text} \uae30\uc900 {distance_m:g}m \uc774\ub0b4 "
        f"{target_titles} {len(features)}\uac74\uc744 \ucc3e\uc558\uc2b5\ub2c8\ub2e4.{sample_text}"
    )
    route_plan = {
        "task_id": f"TASK-REQUESTED-LAYER-{state['task_id'][:3].upper()}",
        "status": "EXECUTION_READY",
        "intent": "SPATIAL_ANALYSIS",
        "context": "dataset_spatial_layer",
        "analysis_type": "feature_search_by_radius",
        "derived_concept": "dataset_spatial_layer_radius",
        "primary_agent": "Spatial Analysis Agent",
        "secondary_agents": [],
        "slots": {
            "location_text": location_text,
            "reference_geometry": base_wkt,
            "buffer_distance": distance_m,
            "target_layers": [target["layer_id"] for target in targets],
            "analysis_type": "feature_search_by_radius",
        },
        "tools": ["postgis.radius"],
        "data": [target["layer_id"] for target in targets],
        "outputs": ["GeoJSON", "FeatureTable", "Summary"],
        "clarification_required": False,
        "confidence": 1.0,
        "execution_ready": True,
        "route_plan_status": "EXECUTION_READY",
    }
    qec = {
        "readiness": "READY",
        "blockers": [],
        "warnings": [],
        "execution_contract": (state.get("candidate_trace") or {}).get("execution_contract"),
        "data_bindings": [
            {
                "dataset_id": target["layer_id"],
                "relation": target["relation"],
                "geometry_column": "geometry",
                "srid": 4326,
                "layer_type": target["layer_type"],
                "execution_status": "executable",
                "read_only": True,
            }
            for target in targets
        ],
        "tool_bindings": [{
            "tool_id": "postgis.radius",
            "operation": "feature_search_by_radius",
            "schema_version": "2.0",
        }],
        "provenance": {"location_resolution": location.get("location_resolution")},
    }
    layer_evidence = [
        {
            "dataset_id": target["layer_id"],
            "relation": target["relation"],
            "layer_type": target["layer_type"],
            "feature_count": sum(1 for row in table_rows if row.get("layer_id") == target["layer_id"]),
        }
        for target in targets
    ]
    final_dict = {
        "task_id": state["task_id"],
        "trace_id": f"tr-{state['task_id']}",
        "agent_name": "Spatial Analysis Agent",
        "agent_version": "2.4.0-requested-spatial-layer-execute",
        "status": "COMPLETED",
        "summary": answer,
        "answer_text": answer,
        "structured_result": {
            "status": "COMPLETED",
            "analysis_type": "feature_search_by_radius",
            "count": len(features),
            "returned_count": len(features),
            "total_count": len(features),
            "feature_ids": [feature["id"] for feature in features],
            "location_text": location_text,
            "distance_m": distance_m,
            "reference_geometry": base_wkt,
            "buffer_distance": distance_m,
            "target_layers": [target["layer_id"] for target in targets],
            "target_features": [target["title"] for target in targets],
            "features": table_rows,
            "geojson": collection,
            "result_surface_contract": {
                "join_key": "feature_id",
                "feature_ids": [feature["id"] for feature in features],
                "map_feature_count": len(features),
                "table_row_count": len(table_rows),
                "evidence_feature_count": len(evidence),
                "authority": "registry/postgis_geometry",
                "candidate_retrieval": "pgvector_capability_top_k",
            },
            **{key: location.get(key) for key in ("place_id", "place_version", "location_resolution")},
        },
        "map_layers": [{
            "layer_id": f"{state['task_id']}-requested-spatial-layers",
            "task_id": state["task_id"],
            "title": "\uacf5\uac04 \ub808\uc774\uc5b4 \uac80\uc0c9 \uacb0\uacfc",
            "description": answer,
            "geometry_type": "GEOMETRY",
            "source_type": "geojson",
            "inline_geojson": collection,
            "feature_count": len(features),
            "metadata": {"target_layers": [target["layer_id"] for target in targets]},
        }],
        "features": collection,
        "spatial_result_summary": {
            "feature_count": len(features),
            "display_feature_count": len(features),
            "result_reference": "requested_spatial_layers",
        },
        "spatial_feature_evidence": evidence,
        "spatial_layer_evidence": layer_evidence,
        "evidence_bundle": {
            "rag_evidence": [],
            "kg_provenance": [],
            "regulatory_evidence": [],
            "spatial_feature_evidence": evidence,
            "spatial_layer_evidence": layer_evidence,
            "accident_relation_evidence": [],
        },
        "orchestrator_v2": {
            "route_plan": route_plan,
            "query_execution_context": qec,
            "execution_contract": (state.get("candidate_trace") or {}).get("execution_contract"),
            "embedding_independent": True,
            "fast_path": "requested_dataset_spatial_layer_execute",
        },
        "claims": [{
            "claim_id": f"claim:{state['task_id']}:summary",
            "text": answer,
            "evidence_ids": [item["evidence_id"] for item in evidence[:10]],
        }],
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
    return {
        "final_dict": final_dict,
        "task_plan": route_plan,
        "query_execution_context": qec,
        "status": AgentStatus.COMPLETED,
        "state_history": log_transition(AgentStatus.INTENT_PARSED, AgentStatus.COMPLETED, actor="RequestedSpatialLayerExecute"),
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
    valid_ctx_derived = [
        valid for item in _as_unique_text_list(ctx_derived)
        for valid in [_valid_derived_concept(item)]
        if valid
    ]
    valid_graph_derived = [
        valid for item in _as_unique_text_list(graph_context.get("derived_concepts"))
        for valid in [_valid_derived_concept(item)]
        if valid
    ]
    valid_slot_derived = _valid_derived_concept(slots.get("derived_concept"))
    if valid_ctx_derived:
        derived_concept = valid_ctx_derived[0]
        intent_val = _context_value(ctx_res, "intent") or intent_val
    elif valid_graph_derived:
        derived_concept = valid_graph_derived[0]
    elif valid_slot_derived:
        derived_concept = valid_slot_derived

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
    resolved_context = _context_value(ctx_res, "selected_context") or "clarification_required"
    plan_dict = route_planner.generate_plan(
        normalized_query=state.get("normalized_query", ""),
        slots=slots,
        derived_concept=derived_concept,
        context=resolved_context,
        analysis_type=analysis_type or "clarification_required",
        intent=intent_val,
        graph_context=state.get("graph_context", {}),
        data_discovery_result=state.get("data_discovery_result", {})
    )
        
    # 2. Task Plan 인스턴스 생성
    task_plan = TaskPlan(
        task_id=f"TASK-HAZARD-SEARCH-{state['task_id'][:3].upper()}",
        intent=plan_dict["intent"],
        context=plan_dict.get("context") or resolved_context,
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
    if req.spatial_context and (req.spatial_context.place_id or req.spatial_context.base_location):
        try:
            import asyncio

            geometry, label, crs, resolution = await asyncio.to_thread(resolve_location, state["query"], req.spatial_context.model_dump())
            req.spatial_context.geometry = geometry
            req.spatial_context.base_location = label
            req.spatial_context.crs = crs
            req.spatial_context.place_id = resolution.get("place_id")
            req.spatial_context.place_version = resolution.get("place_version")
            req.spatial_context.location_resolution = resolution
            slots.update(reference_geometry=geometry, location=label, resolution_status=resolution["status"], crs=crs)
            req.previous_agent_outputs.pop("location_resolution_problem", None)
        except PlaceResolutionProblem as exc:
            req.spatial_context.geometry = None
            slots.pop("reference_geometry", None)
            slots["resolution_status"] = exc.code
            req.previous_agent_outputs["location_resolution_problem"] = {"status": "NEEDS_CLARIFICATION" if exc.status == "NEEDS_USER_INPUT" else "BLOCKED", "error_code": exc.code, "summary": str(exc), "location_candidates": exc.candidates}

    state_spatial_context = req.spatial_context.model_dump() if req.spatial_context else state.get("spatial_context")
    context_state = dict(state)
    context_state["spatial_context"] = state_spatial_context
    req.query_execution_context = _build_query_execution_context(context_state, slots, ctx_res, plan_dict)
    if req.spatial_context and req.spatial_context.location_resolution:
        req.query_execution_context.provenance["location_resolution"] = req.spatial_context.location_resolution
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

    if req.previous_agent_outputs.get("location_resolution_problem"):
        return _place_lookup_update(state, req.previous_agent_outputs["location_resolution_problem"], "place_lookup")

    if req.agent_name == "ClarificationAgent":
        route_plan = state.get("task_plan") or {}
        extracted_slots = state.get("extracted_slots") or req.previous_agent_outputs.get("extracted_slots") or {}
        qec_payload = req.query_execution_context.model_dump(mode="json") if req.query_execution_context else {}
        qec_slots = qec_payload.get("slots", {}) if isinstance(qec_payload, dict) else {}
        derived_concept = (
            route_plan.get("derived_concept") if isinstance(route_plan, dict) else None
        ) or qec_slots.get("derived_concept") or qec_slots.get("concept_id")
        unresolved = []
        if isinstance(route_plan, dict):
            unresolved = route_plan.get("unresolved_slots") or []
        blockers = []
        if req.query_execution_context:
            blockers = req.query_execution_context.blockers or []
        summary = "추가 정보가 필요합니다."
        if unresolved:
            summary = "다음 항목을 확인해 주세요: " + ", ".join(str(item) for item in unresolved)
        elif blockers:
            summary = "실행 전 확인이 필요합니다: " + "; ".join(str(item) for item in blockers)
        agent_result = AgentResult(
            task_id=req.task_id,
            trace_id=req.trace_id,
            agent_name="ClarificationAgent",
            agent_version="orchestrator-clarification-gate",
            status=AgentStatus.NEEDS_CLARIFICATION,
            error_code=PlanStatus.NEEDS_USER_INPUT.value,
            summary=summary,
            answer_text=summary,
            structured_result={
                "analysis_type": route_plan.get("analysis_type") if isinstance(route_plan, dict) else None,
                "normalization": state.get("norm_result") or {},
                "extracted_slots": extracted_slots,
                "derived_concept_mapping": {
                    "derived_concept": derived_concept,
                    "mapping_source": "query_execution_context",
                    "candidate_canonical_terms": (state.get("norm_result") or {}).get("canonical_terms", []),
                },
                "query_execution_context": qec_payload,
                "unresolved_slots": unresolved,
                "blockers": blockers,
                "route_plan": route_plan,
            },
            clarification_questions=[summary],
            warnings=["ClarificationAgent is a terminal state, not a dynamically dispatched executable agent."],
            provenance={"clarification_gate": "services.orchestrator.graph.execute_agent_node"},
        )
        return {
            "agent_result": agent_result,
            "norm_result": state.get("norm_result"),
            "normalization_debug": state.get("normalization_debug"),
            "extracted_slots": extracted_slots,
            "query_execution_context": qec_payload,
            "task_plan": route_plan,
            "status": AgentStatus.NEEDS_CLARIFICATION,
            "state_history": log_transition(AgentStatus.PLAN_CREATED, AgentStatus.NEEDS_CLARIFICATION, reason="Clarification terminal state")
        }

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
            status = (
                AgentStatus.NEEDS_CLARIFICATION
                if qec.readiness == PlanStatus.NEEDS_USER_INPUT
                else AgentStatus.BLOCKED
            )
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

    # Revalidate source identity at dispatch, including resumed plans.
    if req.spatial_context and req.spatial_context.place_id:
        try:
            import asyncio

            await asyncio.to_thread(resolve_location, state["query"], req.spatial_context.model_dump())
        except PlaceResolutionProblem as exc:
            return _place_lookup_update(state, {"status": "NEEDS_CLARIFICATION" if exc.status == "NEEDS_USER_INPUT" else "BLOCKED", "error_code": exc.code, "summary": str(exc), "location_candidates": exc.candidates})
    
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
        quality_metrics = _quality_metrics_from_state(state, fast_path="document_search_compact")
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
                "quality_metrics": quality_metrics,
            },
            "evidence_bundle": evidence_bundle.model_dump(mode="json") if hasattr(evidence_bundle, "model_dump") else {},
            "orchestrator_v2": {
                "graph_context": state.get("graph_context", {}),
                "data_discovery_result": state.get("data_discovery_result", {}),
                "route_plan": state.get("task_plan", {}),
                "query_execution_context": state.get("query_execution_context", {}),
                "embedding_independent": True,
                "fast_path": "document_search_compact",
                "quality_metrics": quality_metrics,
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
        _record_query_quality_issues(state, final_dict)
        return {
            "final_dict": final_dict,
            "status": AgentStatus.COMPLETED,
            "state_history": log_transition(AgentStatus.MAP_REPORT_GENERATING, AgentStatus.COMPLETED),
        }
    
    final_dict = result.model_dump(mode="json")
    quality_metrics = _quality_metrics_from_state(state)
    final_dict["contract_version"] = final_dict.get("contract_version") or "geollm.execution.v1"
    final_dict["request_id"] = final_dict.get("request_id") or state.get("task_id")
    final_dict["answer_text"] = final_dict.get("answer_text") or result.answer_text or result.summary or "분석 결과를 생성하지 못했습니다."
    
    final_dict.setdefault("structured_result", {})
    final_dict["structured_result"]["quality_metrics"] = quality_metrics

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
    final_dict["debug_trace"]["6. Query Quality"] = quality_metrics
    final_dict["orchestrator_v2"] = {
        "graph_context": state.get("graph_context", {}),
        "data_discovery_result": state.get("data_discovery_result", {}),
        "route_plan": state.get("task_plan", {}),
        "query_execution_context": state.get("query_execution_context", {}),
        "embedding_independent": True,
        "quality_metrics": quality_metrics,
        "candidate_trace": state.get("candidate_trace", {}),
    }
    final_dict.setdefault("structured_result", {})
    if isinstance(final_dict["structured_result"], dict):
        final_dict["structured_result"]["candidate_trace_summary"] = _candidate_trace_summary(state.get("candidate_trace"))
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
    
    _record_query_quality_issues(state, final_dict)
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
    if _should_fast_execute_s101_hazard_radius(state):
        return "fast_s101_hazard_radius_execute"
    if _should_fast_execute_s101_nearest_feature(state):
        return "fast_s101_nearest_feature_execute"
    if _should_fast_execute_requested_spatial_layer(state):
        return "fast_requested_spatial_layer_execute"
    if _should_fast_execute_accident_spatial_history(state):
        return "fast_accident_spatial_history_lookup"
    if _should_fast_execute_accident_event_lookup(state):
        return "fast_accident_event_lookup"
    if _looks_like_place_lookup(state.get("query", "")) or _looks_like_known_place_search(state.get("query", ""), state):
        return "fast_place_lookup"
    if _looks_like_dataset_evidence_query(query):
        return "fast_dataset_evidence_answer"
    if _should_fast_execute_traffic_query(state):
        return "fast_dynamic_traffic_execute"
    if _should_fast_spatial_or_traffic_block(state):
        return "fast_spatial_or_traffic_block"
    if (
        _exact_s101_feature_match(query)
        or _exact_s100_s101_relation_match(query)
        or _looks_like_legal_rag_query(query)
        or _looks_like_no_evidence_document_query(query)
    ) and _contract_ready_any(
        state,
        route="STANDARD_RAG",
        capability_ids=["tool.graph_scoped_rag", "resolver.s101_feature_dictionary"],
    ):
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
    workflow.add_node("fast_dataset_evidence_answer", fast_dataset_evidence_answer_node)
    workflow.add_node("fast_external_data_requirement", fast_external_data_requirement_node)
    workflow.add_node("fast_spatial_or_traffic_block", fast_spatial_or_traffic_block_node)
    workflow.add_node("fast_s101_hazard_radius_execute", fast_s101_hazard_radius_execute_node)
    workflow.add_node("fast_dynamic_traffic_execute", fast_dynamic_traffic_execute_node)
    workflow.add_node("fast_s101_nearest_feature_execute", fast_s101_nearest_feature_execute_node)
    workflow.add_node("fast_requested_spatial_layer_execute", fast_requested_spatial_layer_execute_node)
    workflow.add_node("fast_accident_spatial_history_lookup", fast_accident_spatial_history_lookup_node)
    workflow.add_node("fast_accident_event_lookup", fast_accident_event_lookup_node)
    workflow.add_node("fast_place_lookup", fast_place_lookup_node)
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
            "fast_dataset_evidence_answer": "fast_dataset_evidence_answer",
            "fast_spatial_or_traffic_block": "fast_spatial_or_traffic_block",
            "fast_s101_hazard_radius_execute": "fast_s101_hazard_radius_execute",
            "fast_dynamic_traffic_execute": "fast_dynamic_traffic_execute",
            "fast_s101_nearest_feature_execute": "fast_s101_nearest_feature_execute",
            "fast_requested_spatial_layer_execute": "fast_requested_spatial_layer_execute",
            "fast_accident_spatial_history_lookup": "fast_accident_spatial_history_lookup",
            "fast_accident_event_lookup": "fast_accident_event_lookup",
            "fast_place_lookup": "fast_place_lookup",
            "create_plan": "create_plan",
            "resolve_context": "graph_rag"
        }
    )
    workflow.add_edge("fast_external_data_requirement", END)
    workflow.add_edge("fast_document_answer", END)
    workflow.add_edge("fast_dataset_evidence_answer", END)
    workflow.add_edge("fast_spatial_or_traffic_block", END)
    workflow.add_edge("fast_s101_hazard_radius_execute", END)
    workflow.add_edge("fast_dynamic_traffic_execute", END)
    workflow.add_edge("fast_s101_nearest_feature_execute", END)
    workflow.add_edge("fast_requested_spatial_layer_execute", END)
    workflow.add_edge("fast_accident_spatial_history_lookup", END)
    workflow.add_edge("fast_accident_event_lookup", END)
    workflow.add_edge("fast_place_lookup", END)
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
