from typing import Dict, Any
from .base_processor import BaseProcessor

class LightAttributeInterpreter(BaseProcessor):
    def process(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        등대의 등질(colpat, sigper) 및 광달거리(valnmr) 속성 해석
        """
        # (임시) colpat 등 실제 속성에 따라 해석 로직 고도화 가능
        valnmr = properties.get("valnmr")
        interpreted = []
        
        if valnmr:
            interpreted.append(f"광달거리: {valnmr}해리")
            
        color = properties.get("colpat", "")
        if color == "1":
            interpreted.append("백색")
        elif color == "3":
            interpreted.append("적색")
        elif color == "4":
            interpreted.append("녹색")
            
        if interpreted:
            properties["interpreted_light"] = " / ".join(interpreted)
        else:
            properties["interpreted_light"] = "등질 정보 없음"
            
        return properties
