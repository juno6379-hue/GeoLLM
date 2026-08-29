from typing import Dict, Any
from .base_processor import BaseProcessor

class DepthAreaRiskClassifier(BaseProcessor):
    def process(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        drval1 (최소수심), drval2 (최대수심) 기반 위험도 평가
        """
        try:
            drval1 = float(properties.get("drval1") or 0.0)
            drval2 = float(properties.get("drval2") or 0.0)
            
            # 위험도 로직 (예시: 5m 미만은 고위험)
            if drval1 < 5.0:
                properties["depth_risk"] = "고위험 (저수심)"
            elif drval1 < 10.0:
                properties["depth_risk"] = "주의 (중수심)"
            else:
                properties["depth_risk"] = "안전수심"
                
        except (ValueError, TypeError):
            properties["depth_risk"] = "수심 정보 없음"
            
        return properties
