import logging
import hashlib

logger = logging.getLogger('spatial_analysis_agent.overlay_highlighter')

def apply_overlay_highlight(feature: dict, target_layer: str) -> dict:
    """
    Applies highlight styles to the feature properties based on the target layer.
    """
    if "properties" not in feature:
        feature["properties"] = {}
        
    props = feature["properties"]
    
    # Just apply some default styling based on geometry or target_layer
    if target_layer == "gbenc_feature":
        props["marker-color"] = "#ff0000"
        props["marker-symbol"] = "cross"
        props["stroke"] = "#ff0000"
        props["stroke-width"] = 3
        props["fill"] = "#ff0000"
        props["fill-opacity"] = 0.2
    else:
        props["marker-color"] = "#ff8c00"
        props["stroke"] = "#ff8c00"
        
    return feature
