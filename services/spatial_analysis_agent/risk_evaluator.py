import os
import yaml
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from shared.observability.logger import get_logger

logger = get_logger("spatial_analysis_agent.risk_evaluator")

class RiskEvaluator:
    def __init__(self, rule_file_path: str = None):
        if rule_file_path is None:
            rule_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "risk_rules.yaml")
        
        self.rules = []
        try:
            with open(rule_file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "risk_rules" in data:
                    self.rules = data["risk_rules"]
            logger.info(f"Loaded {len(self.rules)} risk rules from {rule_file_path}")
        except Exception as e:
            logger.error("Failed to load risk rules", error=str(e))
            
    def evaluate(self, feature: dict, context: dict = None) -> dict:
        """
        Evaluate a single GeoJSON feature dictionary against the loaded rules.
        Returns a dict with 'risk_level' and 'reason', or None if no rules match.
        """
        props = feature.get("properties", {})
        
        feature_name = props.get("name", "")
        nftc = props.get("nftc")
        distance_m = props.get("distance_m", float('inf'))
        depth = props.get("depth", None)
        
        # Context extraction (e.g. vessel draft)
        context = context or {}
        vessel_draft = context.get("vessel_draft", 8.0) # default draft 8.0m for demo
        
        # Determine logical feature name for evaluation based on NFTC or name
        eval_feature = ""
        if nftc == 159 or "Wreck" in feature_name or "침선" in feature_name:
            eval_feature = "Wreck"
        elif nftc == 86 or "Rock" in feature_name or "암초" in feature_name:
            eval_feature = "Rock"
        elif nftc == 153 or "Obstruction" in feature_name or "장애물" in feature_name:
            eval_feature = "Obstruction"
        elif "DepthArea" in feature_name or "수심" in feature_name:
            eval_feature = "DepthArea"
        elif "AIS" in feature_name or "교통밀집" in feature_name:
            eval_feature = "AIS_Density_Layer"
        elif "Hotspot" in feature_name or "사고다발" in feature_name:
            eval_feature = "Accident_Hotspot_Layer"
        
        for rule in self.rules:
            cond = rule.get("condition", {})
            
            if "feature" in cond and cond["feature"] == eval_feature:
                # 1. Logic-based evaluation (e.g. UKC rules)
                if "logic" in cond:
                    logic_str = cond["logic"]
                    if depth is not None:
                        # UKC Violation Critical
                        if "depth <= draft" in logic_str and depth <= vessel_draft:
                            return {"risk_level": rule.get("risk_level", "CRITICAL"), "reason": rule.get("reason", "")}
                        # UKC Violation High
                        if "depth > draft AND depth <" in logic_str:
                            if depth > vessel_draft and depth < (vessel_draft + vessel_draft * 0.10):
                                return {"risk_level": rule.get("risk_level", "HIGH"), "reason": rule.get("reason", "")}
                
                # 2. Distance-based evaluation
                if "operator" in cond and "value_m" in cond:
                    op = cond["operator"]
                    val = float(cond["value_m"])
                    
                    if op == "<=" and distance_m <= val:
                        return {"risk_level": rule.get("risk_level", "UNKNOWN"), "reason": rule.get("reason", "")}
                    elif op == ">=" and distance_m >= val:
                        return {"risk_level": rule.get("risk_level", "UNKNOWN"), "reason": rule.get("reason", "")}
                    elif op == "<" and distance_m < val:
                        return {"risk_level": rule.get("risk_level", "UNKNOWN"), "reason": rule.get("reason", "")}
                    elif op == ">" and distance_m > val:
                        return {"risk_level": rule.get("risk_level", "UNKNOWN"), "reason": rule.get("reason", "")}
                
                # 3. Intersection / Density logic (Simulated for AIS/Hotspot)
                if "density_level" in cond and "intersects_with" in cond:
                    # In a real scenario, this involves a spatial cross-join
                    # Here we simulate if distance is 0 (intersect)
                    if distance_m == 0:
                        return {"risk_level": rule.get("risk_level", "CRITICAL"), "reason": rule.get("reason", "")}

        return None

    async def aevaluate(self, feature: dict, context: dict = None) -> dict:
        """
        Async evaluation wrapper. First attempts fast static YAML evaluation.
        If no rules match (returns None), falls back to LLM-based dynamic reasoning.
        """
        static_result = self.evaluate(feature, context)
        if static_result:
            return static_result
            
        # Fallback to LLM if OPENAI_API_KEY is present
        if "OPENAI_API_KEY" not in os.environ:
            return {"risk_level": "UNKNOWN", "reason": "No matching static rule, and LLM not configured."}
            
        props = feature.get("properties", {})
        feature_name = props.get("name", "Unknown Object")
        distance_m = props.get("distance_m", "Unknown")
        depth = props.get("depth", "Unknown")
        
        try:
            model_name = os.environ.get("LLM_MODEL", "gpt-4o-mini")
            llm = ChatOpenAI(model=model_name, temperature=0, model_kwargs={"response_format": {"type": "json_object"}})
            
            sys_msg = SystemMessage(content='''당신은 해양 항행 안전 전문가입니다. 발견된 해양 객체(Wreck, Obstruction, DepthArea 등)와 선박 간의 거리를 분석하여, 국제해사기구(IMO) 기준, SOLAS 규정, 여유수심(IHO UKC/DUKC) 가이드라인 등 일반적인 해사 안전 기준에 비추어 위험도(HIGH, MEDIUM, LOW)와 그 사유를 반환하세요.
오직 JSON 형식으로만 응답해야 합니다.
예시: {"risk_level": "CRITICAL", "reason": "IHO UKC 가이드라인에 따라 수심이 흘수+10% 미만이므로 좌초 위험 극히 높음"}''')
            
            user_msg = HumanMessage(content=f"발견된 객체: {feature_name}\n추정 거리: {distance_m}m\n수심(Depth): {depth}m\n이 객체에 대한 항행 위험도를 평가하세요.")
            
            res = await llm.ainvoke([sys_msg, user_msg])
            result_json = json.loads(res.content)
            return {
                "risk_level": result_json.get("risk_level", "UNKNOWN"),
                "reason": result_json.get("reason", "LLM 판단 완료")
            }
        except Exception as e:
            logger.error("LLM evaluation failed", error=str(e))
            return {"risk_level": "UNKNOWN", "reason": "LLM evaluation error"}

risk_evaluator = RiskEvaluator()
