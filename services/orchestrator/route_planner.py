import os
import yaml
from shared.observability.logger import get_logger

logger = get_logger("orchestrator.route_planner")

class RoutePlanner:
    def __init__(self):
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        self.agent_registry = self._load_yaml(os.path.join(data_dir, "agent_capability_registry.yaml"))
        self.tool_registry = self._load_yaml(os.path.join(data_dir, "tool_registry.yaml"))
        self.data_registry = self._load_yaml(os.path.join(data_dir, "data_registry.yaml"))
        v2_path = os.path.join(data_dir, "derived_concept_registry_v2.yaml")
        self.derived_concept_registry = self._load_yaml(v2_path if os.path.exists(v2_path) else os.path.join(data_dir, "derived_concept_registry.yaml"))

    def _load_yaml(self, path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def generate_plan(self, normalized_query: str, slots: dict, derived_concept: str, context: str, analysis_type: str, intent: str, graph_context: dict = None, data_discovery_result: dict = None) -> dict:
        graph_context = graph_context or {}
        data_discovery_result = data_discovery_result or {}
        slots = dict(slots or {})
        slots.setdefault("target_features", graph_context.get("resolved_target_features", []))
        slots.setdefault("target_layers", graph_context.get("resolved_target_layers", []))
        slots.setdefault("target_dynamic_layers", graph_context.get("resolved_target_dynamic_layers", []))
        # 1. infer_intent fallback (from 05_intent_agent_routing_rules.md)
        if intent in (None, "UNKNOWN", "N/A", "clarification_required"):
            intent = self._infer_intent(slots)
            
        # Radius is an operation, not a domain context. Infer it from the
        # spatial slot when callers do not provide an explicit analysis type.
        if not analysis_type and slots.get("distance_m") is not None:
            analysis_type = "feature_search_by_radius"

        route_plan = {
            "intent": intent,
            "context": context,
            "analysis_type": analysis_type,
            "derived_concept": derived_concept,
            "primary_agent": None,
            "secondary_agents": [],
            "required_tools": [],
            "required_data": [],
            "outputs": [],
            "execution_ready": False,
            "route_plan_status": "UNKNOWN",
            "unresolved_slots": []
        }
        route_plan["graph_context"] = graph_context
        route_plan["data_discovery_result"] = data_discovery_result

        # Check unresolved slots (e.g., missing location or target for spatial queries)
        unresolved = []
        if intent in ("spatial_feature_search", "spatial_feature_proximity_search", "spatial_feature_within_area", "spatial_feature_count"):
            if not slots.get("location_text") and not slots.get("location"):
                unresolved.append("location")
            if not slots.get("target_term"):
                unresolved.append("target_term")
        
        if unresolved:
            route_plan["unresolved_slots"] = unresolved
            route_plan["route_plan_status"] = "UNRESOLVED_SLOTS"
            route_plan["primary_agent"] = "ClarificationAgent"
            return route_plan

        agent_cap = self.agent_registry.get("analysis_types", {}).get(analysis_type, {})
        concept_data = {}
        for key, val in self.derived_concept_registry.get("derived_concepts", {}).items():
            if val.get("concept_id") == derived_concept or key == derived_concept:
                concept_data = val
                route_plan["derived_concept"] = val.get("concept_id", derived_concept)
                break

        # Merge Agents
        route_plan["primary_agent"] = agent_cap.get("primary_agent")
        if not route_plan["primary_agent"]:
            # Rule based Agent Routing
            if intent in ("spatial_feature_search", "spatial_feature_proximity_search", "spatial_feature_within_area", "nearest_feature_search"):
                route_plan["primary_agent"] = "SpatialQueryAgent"
            elif intent == "spatial_feature_count":
                route_plan["primary_agent"] = "SpatialStatisticsAgent"
            elif intent in ("spatial_intersection", "spatial_buffer_analysis", "geometry_measurement"):
                route_plan["primary_agent"] = "SpatialAnalysisAgent"
            elif intent == "map_report_generation":
                route_plan["primary_agent"] = "MapReportAgent"
            elif intent == "clarification_required":
                route_plan["primary_agent"] = "ClarificationAgent"
            elif intent == "drone_lidar_change_detection":
                route_plan["primary_agent"] = "Drone LiDAR Analysis Agent"
            else:
                route_plan["primary_agent"] = concept_data.get("default_agent", "ClarificationAgent")
            
        route_plan["secondary_agents"] = agent_cap.get("secondary_agents", [])
        for candidate in graph_context.get("candidate_agents", []):
            if candidate != route_plan["primary_agent"] and candidate not in route_plan["secondary_agents"]:
                route_plan["secondary_agents"].append(candidate)

        # Merge Tools
        tools = set(agent_cap.get("required_tools", []))
        concept_tools = concept_data.get("required_tools", [])
        if concept_tools:
            tools.update(concept_tools)
        if concept_data.get("default_tool"):
            tools.add(concept_data.get("default_tool"))
        route_plan["required_tools"] = list(tools)
        for tool in graph_context.get("verified_tools", []) or graph_context.get("resolved_tools", []):
            if tool not in route_plan["required_tools"]: route_plan["required_tools"].append(tool)
        if analysis_type in {"document_search", "rag.document_search", "graph_scoped_rag"}:
            route_plan["required_tools"] = [
                tool for tool in route_plan["required_tools"]
                if str(tool).startswith("rag.")
            ] or ["rag.graph_scoped_retrieve"]

        # Merge Data
        datasets = set(agent_cap.get("required_data", []))
        concept_data_reqs = concept_data.get("required_data", [])
        if concept_data_reqs:
            datasets.update(concept_data_reqs)
        route_plan["required_data"] = list(datasets)
        route_plan["outputs"] = agent_cap.get("outputs", [])
        route_plan["candidate_query_templates"] = graph_context.get("candidate_query_templates", [])
        route_plan["spatial_execution_available"] = data_discovery_result.get("can_execute_spatial_query", False)

        # Routing is a proposal. Only ExecutionValidator can grant execution readiness.
        if route_plan["primary_agent"] and route_plan["primary_agent"] != "ClarificationAgent":
            route_plan["route_plan_status"] = "PLAN_READY"
        else:
            route_plan["execution_ready"] = False
            route_plan["route_plan_status"] = "NEEDS_CLARIFICATION"

        return route_plan

    def _infer_intent(self, slots: dict) -> str:
        location = slots.get("location_text") or slots.get("location")
        target = slots.get("target_term")
        distance = slots.get("distance_m")
        aggregate = slots.get("aggregate")
        relation = slots.get("spatial_relation")

        if location and target and aggregate == "count":
            return "spatial_feature_count"

        if location and target and distance is not None:
            return "spatial_feature_proximity_search"

        if location and target:
            return "spatial_feature_within_area"

        if target and relation == "nearest":
            return "nearest_feature_search"

        return "clarification_required"
