from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class MapLayerStyle(BaseModel):
    fill_color: Optional[str] = None
    stroke_color: Optional[str] = None
    marker_symbol: Optional[str] = None
    opacity: float = 1.0

    model_config = {"extra": "allow"}

class MapLayerSpecification(BaseModel):
    layer_id: str
    task_id: str
    title: str
    description: str
    geometry_type: str
    source_type: str
    source_uri: Optional[str] = None
    inline_geojson: Optional[Dict[str, Any]] = None
    source_crs: str = "EPSG:4326"
    display_crs: str = "EPSG:4326"
    style: MapLayerStyle = Field(default_factory=MapLayerStyle)
    legend: Dict[str, Any] = Field(default_factory=dict)
    popup_fields: List[str] = Field(default_factory=list)
    label_field: Optional[str] = None
    min_zoom: Optional[int] = None
    max_zoom: Optional[int] = None
    visibility: bool = True
    z_index: int = 0
    valid_time: Optional[str] = None
    dataset_version: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)
    feature_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def layer_type(self) -> str:
        return self.source_type
