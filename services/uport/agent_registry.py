"""Domain specialist lookup layered on GeoLLM's Capability Registry metadata.

Only verified, implemented adapters are registered. Names for future AIS,
prediction, optimization and knowledge specialists can exist in metadata, but
an absent factory cannot be interpreted as an executable Agent.
"""

from services.orchestrator.query_candidate_broker import query_candidate_broker
from services.uport.s101_agent import S101Agent

_IMPLEMENTED_AGENTS = {"S101Agent": S101Agent}


def get_executable_agent(capability_id: str):
    """Resolve an available Capability to an implemented specialist adapter."""
    definition = query_candidate_broker.domain_capability_definitions("uport").get(capability_id)
    if not definition or definition.get("status") != "available":
        return None
    factory = _IMPLEMENTED_AGENTS.get(definition.get("agent"))
    return factory() if factory else None
