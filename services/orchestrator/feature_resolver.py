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
        urls = [os.environ.get("S101_DB_URL", ""), os.environ.get("POSTGIS_URL", "")]
        for db_url in [url for url in urls if url]:
            try:
                import psycopg2
                conn = psycopg2.connect(db_url)
                cur = conn.cursor()
                cur.execute("SELECT name, code FROM public.codeinformation WHERE type = 0")
                rows = cur.fetchall()
                for name, code in rows:
                    self.feature_to_nftc_map[name] = code
                loaded_from_db = loaded_from_db or bool(rows)
                conn.close()
                if rows:
                    logger.info("FeatureResolver loaded NFTC mappings from Database", extra={"url": db_url.split("@")[-1]})
                    break
            except Exception as e:
                logger.error("Failed to load NFTC mapping from Database", error=str(e))

        if not loaded_from_db:
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

        # A dictionary match is not calibrated answer accuracy.
        if not candidates:
            return result
        result["resolved_features"] = [
            {"feature_name": c, "confidence": None, "source": "dictionary",
             "evaluation_status": "NOT_EVALUATED"} for c in candidates
        ]
        if len(candidates) == 1:
            result["selected_feature"] = candidates[0]
        elif policy == "allow_multiple_candidates":
            result["selection_mode"] = "all_candidates"
        else:
            result["needs_clarification"] = True
            result["clarification_question"] = f"'{input_term}' 관련 객체가 여러 개입니다. 사용할 객체를 선택해 주세요."
            result["clarification_options"] = [{"label": c, "value": c} for c in candidates]

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
