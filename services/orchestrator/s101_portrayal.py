"""Deterministic S-101 2.0 portrayal selection for map feature instances.

This module selects the official Portrayal Catalogue symbol instruction for
the feature attributes available in the GBHD projection. It does not invent
SVG artwork; the selected instruction is resolved by the frontend against
the bundled catalogue SVG asset.
"""

from __future__ import annotations

from typing import Any


PORTRAYAL_VERSION = "2.0.0"
PORTRAYAL_SOURCE = "S-101 Portrayal Catalogue 2.0.0"
ASSET_ROOT = "/s101-portrayal"


def _value(attrs: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in attrs and attrs[name] not in (None, ""):
            return attrs[name]
    return None


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _asset(symbol: str) -> str:
    return f"{ASSET_ROOT}/{symbol}.svg"


def resolve_s101_portrayal(feature_name: str, geometry_type: str | None, attributes: Any) -> dict[str, Any]:
    """Return the official symbol instruction selected by S-101 rule branches."""
    attrs = attributes if isinstance(attributes, dict) else {}
    code = str(feature_name or "")
    primitive = str(geometry_type or "Point")
    symbol = None
    rule = None
    reason = "default rule branch"

    category_wreck = _int(_value(attrs, "categoryOfWreck", "category_of_wreck"))
    category_obstruction = _int(_value(attrs, "categoryOfObstruction", "category_of_obstruction"))
    water_level = _int(_value(attrs, "waterLevelEffect", "water_level_effect"))
    sounding = _value(attrs, "valueOfSounding", "value_of_sounding")

    if code == "Wreck":
        rule = "Wreck"
        if primitive in {"Polygon", "Surface"}:
            symbol = "WRECKS05"
            reason = "surface portrayal uses WRECKS05 area rule"
        elif category_wreck == 3:
            symbol = "FOULGND1"
            reason = "categoryOfWreck=3"
        elif sounding is not None:
            symbol = "DANGER01"
            reason = "valueOfSounding present; safety-depth context unavailable"
        elif category_wreck == 1 and water_level == 3:
            symbol = "WRECKS04"
            reason = "categoryOfWreck=1 and waterLevelEffect=3"
        elif category_wreck == 2 and water_level == 3:
            symbol = "WRECKS05"
            reason = "categoryOfWreck=2 and waterLevelEffect=3"
        else:
            symbol = "WRECKS05"
    elif code == "Obstruction":
        rule = "Obstruction"
        if primitive in {"LineString", "Curve"}:
            symbol = "OBSTRN01"
            reason = "curve uses OBSTRN07 line branch"
        elif primitive in {"Polygon", "Surface"}:
            symbol = "OBSTRN01"
            reason = "surface uses OBSTRN07 area branch"
        elif category_obstruction in {8, 10}:
            symbol = "FLTHAZ02"
            reason = f"categoryOfObstruction={category_obstruction}"
        elif category_obstruction == 9:
            symbol = "ACHARE02"
            reason = "categoryOfObstruction=9"
        elif category_obstruction == 21:
            symbol = "VOLCANO01"
            reason = "categoryOfObstruction=21"
        elif category_obstruction == 23:
            symbol = "VEGATN04P"
            reason = "categoryOfObstruction=23"
        elif water_level == 7:
            symbol = "FLTHAZ02"
            reason = "waterLevelEffect=7"
        else:
            symbol = "OBSTRN01"
    elif code == "UnderwaterAwashRock":
        rule = "UnderwaterAwashRock"
        symbol = "UWTROC03" if water_level == 3 else "UWTROC04"
        reason = f"waterLevelEffect={water_level}" if water_level is not None else "default OBSTRN07 rock branch"

    if not symbol:
        return {
            "catalogue": PORTRAYAL_SOURCE,
            "catalogue_version": PORTRAYAL_VERSION,
            "status": "UNRESOLVED",
            "rule": None,
        }

    return {
        "catalogue": PORTRAYAL_SOURCE,
        "catalogue_version": PORTRAYAL_VERSION,
        "status": "RESOLVED",
        "rule": rule,
        "symbol": symbol,
        "instruction": f"PointInstruction:{symbol}",
        "asset": _asset(symbol),
        "selection_reason": reason,
    }
