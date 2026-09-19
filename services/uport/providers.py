"""Source contracts for U-Port map data that GeoLLM has not yet connected.

Implementations must return observed records from a registered provider. A
missing provider is represented by ``None`` at the API boundary; production
code never substitutes fixture vessels or invented berth occupancy.
"""

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field


class AISPosition(BaseModel):
    """One source-attributed vessel observation in WGS84 coordinates."""

    mmsi: str = Field(pattern=r"^[0-9]{9}$")
    longitude: float = Field(ge=-180, le=180)
    latitude: float = Field(ge=-90, le=90)
    observed_at: datetime
    source_dataset_id: str


class AISProvider(Protocol):
    """A live provider must bound results to the requested map viewport."""

    def positions_in_bbox(
        self, west: float, south: float, east: float, north: float
    ) -> list[AISPosition]: ...


def get_ais_provider() -> AISProvider | None:
    """Return the configured provider once an authoritative feed exists.

    The current GeoLLM AIS tool reads historical CSV tracks and cannot satisfy
    a live dashboard position contract. Explicit absence keeps the map honest.
    """

    return None
