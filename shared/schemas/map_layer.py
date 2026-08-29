from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class MapLegendItem(BaseModel):
    label: str
    color: str

class MapLegend(BaseModel):
    title: str
    items: List[MapLegendItem]

class MapLayerStyle(BaseModel):
    fill_color: Optional[str] = None
    stroke_color: Optional[str] = None
    marker_symbol: Optional[str] = None
    opacity: float = 1.0

class MapLayerSpecification(BaseModel):
    layer_id: str
    task_id: str
    title: str
    description: str
    geometry_type: str  # POINT, LINESTRING, POLYGON
    source_type: str    # GEOJSON, MVT, etc.
    source_uri: Optional[str] = None
    inline_geojson: Optional[Dict[str, Any]] = None
    source_crs: str = "EPSG:4326"
    display_crs: str = "EPSG:3857"
    style: MapLayerStyle = Field(default_factory=MapLayerStyle)
    legend: Optional[MapLegend] = None
    popup_fields: List[str] = Field(default_factory=list)
    label_field: Optional[str] = None
    min_zoom: int = 0
    max_zoom: int = 22
    visibility: bool = True
    z_index: int = 0
    valid_time: Optional[datetime] = None
    dataset_version: Optional[str] = None
    provenance: Optional[str] = None
