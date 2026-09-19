"""Typed map-entity resolution against U-Port's ontology mapping Registry."""

from pathlib import Path
import yaml

from services.uport.planning import MapSelection

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "data" / "uport_resolver_registry.yaml"


def resolve_map_selection(selection: MapSelection) -> dict:
    """Bind UI identity to an ontology class without asserting DB existence.

    The returned status is CANDIDATE because a later execution step must check
    the feature ID against the authoritative PostGIS relation and permission.
    """
    payload = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    matches = [entry for entry in payload.get("resolvers") or []
               if entry.get("entity_type") == selection.entity_type]
    if len(matches) != 1:
        raise ValueError("map entity has no unique ontology resolver")
    entry = matches[0]
    return {
        "resolver_id": entry["id"],
        "ontology_class": entry["ontology_class"],
        "dataset": entry["dataset"],
        "source": entry["source"],
        "id_field": entry["id_field"],
        "feature_id": selection.feature_id,
        "verification_status": "CANDIDATE",
    }
