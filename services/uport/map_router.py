"""Read-only S-101 map features for the U-Port dashboard.

The live AIS source and port-operation berth database have not been registered.
This route therefore exposes only charted S-101 berth geometry; it never
labels those chart features as live berth occupancy or vessel observations.
"""

from __future__ import annotations

import json
import math
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from data.database import get_s101_db
from shared.observability.logger import get_logger
from services.uport.providers import AISProvider, get_ais_provider

router = APIRouter(prefix="/uport", tags=["U-Port Map"])
logger = get_logger("uport.map")
S101_PRODUCT = "INT.IHO.S-101.2.0"
MAX_BBOX_SPAN_DEGREES = 2.0
PAGE_LIMIT = 200


class MapFeatureCollection(BaseModel):
    """GeoJSON plus source metadata needed for honest map labelling."""

    type: str = "FeatureCollection"
    features: list[dict]
    source: str
    product_specification: str
    truncated: bool


def parse_bbox(raw: str) -> tuple[float, float, float, float]:
    """Validate a bounded WGS84 viewport before it reaches a spatial query."""

    try:
        values = tuple(float(part.strip()) for part in raw.split(","))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="bbox must contain four numbers") from exc
    if len(values) != 4 or not all(math.isfinite(value) for value in values):
        raise HTTPException(status_code=422, detail="bbox must contain four finite numbers")
    west, south, east, north = values
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise HTTPException(status_code=422, detail="bbox must be ordered WGS84 coordinates")
    if east - west > MAX_BBOX_SPAN_DEGREES or north - south > MAX_BBOX_SPAN_DEGREES:
        raise HTTPException(status_code=422, detail="bbox is too large for a berth query")
    return west, south, east, north


@router.get("/map/berths", response_model=MapFeatureCollection)
def get_charted_berths(
    bbox: Annotated[str, Query(description="WGS84 west,south,east,north")],
    db: Session | None = Depends(get_s101_db),
) -> MapFeatureCollection:
    """Return charted Berth features in the current viewport, with stable IDs.

    A bound envelope and fixed feature class prevent user input from becoming
    a SQL identifier. The 201st row only signals that the page is truncated.
    """

    west, south, east, north = parse_bbox(bbox)
    if db is None:
        raise HTTPException(status_code=503, detail="S-101 database is not configured")
    statement = text("""
        SELECT feature_instance_id, dataset_id, dataset_version_id,
               ST_AsGeoJSON(geometry)::json AS geometry
        FROM projection.s101_feature_valid
        WHERE product_specification = :product
          AND feature_type_name = 'Berth'
          AND geometry IS NOT NULL
          AND geometry && ST_MakeEnvelope(:west, :south, :east, :north, 4326)
          AND ST_Intersects(geometry, ST_MakeEnvelope(:west, :south, :east, :north, 4326))
        ORDER BY feature_instance_id
        LIMIT :limit
    """)
    try:
        # SET LOCAL limits this read without changing the connection's future
        # requests. A failed or slow spatial query becomes an explicit 503.
        with db.begin():
            db.execute(text("SET LOCAL statement_timeout = '5000ms'"))
            rows = db.execute(statement, {
                "product": S101_PRODUCT, "west": west, "south": south,
                "east": east, "north": north, "limit": PAGE_LIMIT + 1,
            }).mappings().all()
    except (SQLAlchemyError, UnicodeError) as exc:
        logger.error("S-101 berth map query failed", error=str(exc))
        raise HTTPException(status_code=503, detail="S-101 berth layer is unavailable") from exc

    features = []
    for row in rows[:PAGE_LIMIT]:
        # PostgreSQL JSON values may arrive as either decoded objects or text,
        # depending on the DB driver. Both forms are normalized to GeoJSON.
        geometry = row["geometry"]
        if isinstance(geometry, str):
            geometry = json.loads(geometry)
        features.append({
            "type": "Feature", "id": str(row["feature_instance_id"]),
            "geometry": geometry,
            "properties": {
                "feature_type": "Berth",
                "dataset_id": str(row["dataset_id"]),
                "dataset_version_id": str(row["dataset_version_id"]),
            },
        })
    return MapFeatureCollection(
        features=features, source="projection.s101_feature_valid",
        product_specification=S101_PRODUCT, truncated=len(rows) > PAGE_LIMIT,
    )


@router.get("/map/vessels")
def get_vessels(
    bbox: Annotated[str, Query(description="WGS84 west,south,east,north")],
    provider: AISProvider | None = Depends(get_ais_provider),
) -> dict:
    """Expose the live AIS boundary without disguising historical CSV as live.

    Once configured, the provider supplies timestamped MMSI observations. The
    layer remains unavailable until that source is explicitly registered.
    """

    west, south, east, north = parse_bbox(bbox)
    if provider is None:
        raise HTTPException(status_code=503, detail="Live AIS provider is not configured")
    return {"positions": [row.model_dump(mode="json") for row in provider.positions_in_bbox(
        west, south, east, north
    )]}
