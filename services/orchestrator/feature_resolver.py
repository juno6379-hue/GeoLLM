import os
import yaml
import json
from shared.observability.logger import get_logger

logger = get_logger("orchestrator.feature_resolver")

class FeatureResolver:
    def __init__(self):
        self.marine_terms = {}
        self.aliases_map = {}
        self.feature_to_nftc_map = {}
        self.feature_policies = {}
        self.load_dictionary()

    def load_dictionary(self):
        object_dict_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "marine_object_dictionary.yaml")
        s101_feature_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "s101_feature_dictionary.yaml")
        catalog_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "s101_catalogue.json")
        
        # 1. Load Marine Object Dictionary (NLU -> Canonical)
        if os.path.exists(object_dict_path):
            try:
                with open(object_dict_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "marine_objects" in data:
                        for key, term_info in data["marine_objects"].items():
                            self.aliases_map[key] = key
                            for alias in term_info.get("aliases", []):
                                self.aliases_map[alias] = key
                logger.info(f"FeatureResolver loaded Marine Object Dictionary from {object_dict_path}")
            except Exception as e:
                logger.error("Failed to load Marine Object Dictionary", error=str(e))
                
        # 2. Load S-101 Feature Dictionary (Canonical -> Features)
        if os.path.exists(s101_feature_path):
            try:
                with open(s101_feature_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "s101_features" in data:
                        self.marine_terms = data["s101_features"]
                    if data and "feature_policies" in data:
                        self.feature_policies = data["feature_policies"]
                logger.info(f"FeatureResolver loaded S-101 Feature Dictionary from {s101_feature_path}")
            except Exception as e:
                logger.error("Failed to load S-101 Feature Dictionary", error=str(e))
                
        # 3. Load S-101 Feature NFTC mapping from Database (public.codeinformation)
        self._load_nftc_from_db()

    def _load_nftc_from_db(self):
        loaded_from_db = False
        try:
            import psycopg2
            postgis_url = os.environ.get("POSTGIS_URL", "")
            conn = psycopg2.connect(postgis_url)
            cur = conn.cursor()
            cur.execute("SELECT name, code FROM public.codeinformation WHERE type = 0")
            rows = cur.fetchall()
            for name, code in rows:
                self.feature_to_nftc_map[name] = code
            loaded_from_db = bool(rows)
            conn.close()
            logger.info("FeatureResolver loaded NFTC mappings from Database")
        except Exception as e:
            logger.error("Failed to load NFTC mapping from Database", error=str(e))
            logger.warning("Falling back to local S-101 catalogue for NFTC mappings")

        # Development databases can have an empty codeinformation table. Keep
        # the local catalogue as a supplement instead of resolving to code 0.
        catalog_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "s101_catalogue.json")
        if os.path.exists(catalog_path):
            try:
                with open(catalog_path, "r", encoding="utf-8") as f:
                    catalog_data = json.load(f)
                for item in catalog_data:
                    if "name" in item and "nftc" in item and item["name"] not in self.feature_to_nftc_map:
                        self.feature_to_nftc_map[item["name"]] = item["nftc"]
                logger.info("Loaded local S-101 catalogue", extra={"from_db": loaded_from_db})
            except Exception as ex:
                logger.error("Failed to load local S-101 catalogue", error=str(ex))

    def resolve(self, input_term: str) -> dict:
        """
        입력된 용어를 기반으로 매칭되는 Marine Term Dictionary 항목을 찾아
        GBENC Feature 및 메타데이터, NFTC 코드를 반환합니다.
        """
        result = {
            "input_term": input_term,
            "canonical_term": input_term,
            "resolved_features": [],
            "selected_feature": None,
            "geometry_types": [],
            "default_query_template": None,
            "risk_context": [],
            "nftc_codes": [],
            "needs_clarification": False
        }
        
        # 1. Dictionary Lookup (Alias 포함)
        dict_key = self.aliases_map.get(input_term)
        term_info = self.marine_terms.get(dict_key) if dict_key else None
        
        if not term_info:
            return result
            
        result["canonical_term"] = term_info.get("canonical_term", input_term)
        result["geometry_types"] = term_info.get("geometry_types", [])
        result["default_query_template"] = term_info.get("default_query_template")
        result["risk_context"] = term_info.get("risk_context", [])
        
        candidates = term_info.get("feature_candidates", [])
        policy = term_info.get("ambiguity_policy", "")
        
        # 2. Assign Confidence & Resolve Features
        if not candidates:
            return result
            
        # 단일 Feature인 경우 100% 확정
        if len(candidates) == 1:
            result["resolved_features"].append({
                "feature_name": candidates[0],
                "confidence": 0.99,
                "source": "dictionary"
            })
            result["selected_feature"] = candidates[0]
            
        # 다수 Feature인 경우 Ambiguity 검사
        else:
            if policy == "request_user_clarification_if_multiple":
                result["resolved_features"] = [{"feature_name": c, "confidence": 0.5, "source": "dictionary"} for c in candidates]
                result["needs_clarification"] = True
                result["clarification_question"] = f"'{input_term}' 관련 객체가 여러 개 존재합니다. 다음 중 어느 것을 찾으시나요?"
                result["clarification_options"] = [{"label": c, "value": c} for c in candidates]
            elif policy == "resolve_by_gbenc_codeinformation" or policy == "verify_with_gbenc_codeinformation":
                # '선석'의 경우 임시로 Berth에 높은 가중치 부여 로직
                if "Berth" in candidates:
                    result["resolved_features"].append({
                        "feature_name": "Berth",
                        "confidence": 0.92,
                        "source": "GBENC codeinformation"
                    })
                    for c in candidates:
                        if c != "Berth":
                            result["resolved_features"].append({
                                "feature_name": c,
                                "confidence": 0.67,
                                "source": "GBENC candidate match"
                            })
                    result["selected_feature"] = "Berth"
                else:
                    # Berth가 없다면 명확성을 위해 사용자에게 질문
                    result["resolved_features"] = [{"feature_name": c, "confidence": 0.5, "source": "dictionary"} for c in candidates]
                    result["needs_clarification"] = True
                    result["clarification_question"] = f"'{input_term}'을(를) 어느 기준으로 찾을까요? ({', '.join(candidates[:3])} 등)"
            elif policy == "allow_multiple_candidates":
                # 여러 객체를 콤보로 쿼리해도 되는 경우 (예: 부표들)
                result["resolved_features"] = [{"feature_name": c, "confidence": 0.9, "source": "dictionary"} for c in candidates]
                # 여기서 selected_feature에 리스트를 콤마로 넣거나 첫번째만 넣음
                # 후속 로직에서 candidates 리스트 자체를 순회할 수 있으므로, 대표값으로 첫 번째 할당
                result["selected_feature"] = candidates[0] 
            else:
                # 기본 처리
                result["resolved_features"] = [{"feature_name": c, "confidence": 0.8, "source": "dictionary"} for c in candidates]
                result["selected_feature"] = candidates[0]
        
        # 3. 매칭된 Feature들의 NFTC 코드 추출
        nftc_set = set()
        feature_policies_result = {}
        for f in result["resolved_features"]:
            fname = f["feature_name"]
            if fname in self.feature_to_nftc_map:
                nftc_set.add(self.feature_to_nftc_map[fname])
            if fname in self.feature_policies:
                feature_policies_result[fname] = self.feature_policies[fname]
                
        result["nftc_codes"] = list(nftc_set)
        result["feature_policies"] = feature_policies_result
        
        return result

feature_resolver = FeatureResolver()
