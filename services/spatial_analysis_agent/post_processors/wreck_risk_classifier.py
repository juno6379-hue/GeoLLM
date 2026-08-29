from typing import Dict, Any
from .base_processor import BaseProcessor

class WreckRiskClassifier(BaseProcessor):
    def process(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        침선(Wreck)의 valsou(수심) 기반 위험도 평가
        """
        try:
            valsou = properties.get("valsou")
            if valsou is not None:
                valsou = float(valsou)
                if valsou < 20.0:
                    properties["risk_level"] = "고위험 (저수심 침선)"
                else:
                    properties["risk_level"] = "저위험"
            else:
                properties["risk_level"] = "수심 정보 없음"
        except (ValueError, TypeError):
            properties["risk_level"] = "평가 불가"
            
        return properties
