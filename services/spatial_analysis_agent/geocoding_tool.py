"""Compatibility tool backed by the same resolver as interactive query services."""

from langchain_core.tools import tool

from services.spatial_analysis_agent.place_resolver import PlaceResolutionProblem, resolve_location


def _clean_place_name(place_name: str) -> str:
    return " ".join((place_name or "").split())


@tool
def get_maritime_coordinates(place_name: str) -> str:
    """Resolve an unambiguous dataset place to WKT; request clarification otherwise.

    Spatial qualifiers such as port entrance are retained. No arbitrary first
    match, external geocoding fallback, or write to the source dictionary occurs.
    """
    try:
        geometry, _, _, _ = resolve_location(place_name, {"base_location": _clean_place_name(place_name)})
        return geometry
    except PlaceResolutionProblem as exc:
        labels = ", ".join(f"{item['label']} ({item['longitude']:.6f}, {item['latitude']:.6f})" for item in exc.candidates[:10])
        return f"ERROR: {exc.code}: {exc}" + (f" 후보: {labels}" if labels else "")
