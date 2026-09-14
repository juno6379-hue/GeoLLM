import os
import re
import json
import yaml
from shared.observability.logger import get_logger

logger = get_logger("orchestrator.normalizer")

class QueryNormalizer:
    def __init__(self):
        self.synonyms = {}
        self.synonym_meta = {}
        self.marine_terms = {}
        self.derived_concepts = {}
        
        self.load_marine_term_dictionary()
        self.load_derived_concepts()
        
    def load_marine_term_dictionary(self):
        """
        Dynamically load synonyms from the Marine Term Dictionary (YAML).
        """
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        dict_paths = [
            os.path.join(root, "outputs", "dictionaries", "marine_term_dictionary.yaml"),
            os.path.join(root, "data", "marine_term_dictionary.yaml"),
        ]
        for dict_path in dict_paths:
            if not os.path.exists(dict_path):
                continue
            try:
                with open(dict_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and ("marine_terms" in data or "terms" in data):
                        terms = data.get("marine_terms") or data.get("terms") or {}
                        self.marine_terms.update(terms)
                        for surface_term, term_info in terms.items():
                            canonical_term = term_info.get("canonical_id") or term_info.get("canonical_term") or surface_term
                            self.synonyms[surface_term] = canonical_term
                            self.synonym_meta[surface_term] = term_info
                            aliases = term_info.get("aliases", [])
                            for alias in aliases:
                                self.synonyms[alias] = canonical_term
                                self.synonym_meta[alias] = term_info
                logger.info(f"Normalizer loaded Marine Term Dictionary from {dict_path}")
            except Exception as e:
                logger.error("Failed to load Marine Term Dictionary", error=str(e))
                
    def load_derived_concepts(self):
        """
        Load derived concepts to map canonical terms to candidate contexts.
        """
        concept_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "derived_concept_registry.yaml")
        if os.path.exists(concept_path):
            try:
                with open(concept_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if data and "derived_concepts" in data:
                        self.derived_concepts = data["derived_concepts"]
            except Exception as e:
                logger.error(f"Failed to load derived_concept_registry: {e}")

    def normalize(self, query: str) -> str:
        res = self.normalize_with_debug(query)
        return res["normalized_query"]

    def normalize_with_debug(self, query: str) -> dict:
        if not query:
            return {
                "original_query": "",
                "normalized_query": "",
                "canonical_terms": [],
                "candidate_contexts": [],
                "matched_rules": []
            }
            
        original_query = query
        matched_rules = []
        canonical_terms_found = set()
        
        # 1. 띄어쓰기 보정 (Spacing correction)
        # 1. 띄어쓰기 보정 (Spacing correction)
        q = query.strip()
        
        # 반경, 킬로 등을 km/m 이내 형식으로 정규화
        q = re.sub(r'반경\s*(\d+)\s*(km|m)', r'\1\2 이내', q)
        q = re.sub(r'(\d+)\s*킬로\s*이내', r'\1km 이내', q)
        q = re.sub(r'(\d+)\s*(km|m)\s*이내', r'\1\2 이내', q)
        
        # 다중 공백을 단일 공백으로 치환
        q = re.sub(r'\s+', ' ', q)
        
        # 숫자와 단위 사이의 공백 제거 (예: 3 km -> 3km)
        q = re.sub(r'(\d+)\s+(km|m|킬로|키로)', r'\1\2', q)
        
        # 2. 조사 제거 (Particle removal) - 공백 유지하며 조사만 제거
        q = re.sub(r'(을|를|이|가|은|는)\s+(찾아|보여|알려|검색)', r' \2', q)
        
        # 3. Synonym/Canonical term replacement
        sorted_syns = sorted(self.synonyms.keys(), key=len, reverse=True)
        for syn in sorted_syns:
            if syn in q:
                canonical = self.synonyms[syn]
                term_meta = self.synonym_meta.get(syn, {})
                if term_meta.get("replace_in_query", True):
                    q = q.replace(syn, canonical)
                    matched_rules.append(f"Dictionary 기반 canonical term 변환: '{syn}' -> '{canonical}'")
                else:
                    matched_rules.append(f"Dictionary 기반 canonical term 인식: '{syn}' -> '{canonical}'")
                canonical_terms_found.add(canonical)
                
        # Check if derived concepts (like "위험객체") are in the query explicitly
        for concept_name, concept_data in self.derived_concepts.items():
            aliases = concept_data.get("aliases", [concept_name])
            for alias in aliases:
                if alias in q:
                    concept_id = concept_data.get("concept_id", concept_name)
                    canonical_terms_found.add(concept_id)
                    matched_rules.append(f"Derived Concept 매핑: '{alias}' -> '{concept_id}'")
                    break
                
        # 4. Candidate Contexts lookup
        candidate_contexts = set()
        for term in canonical_terms_found:
            for c_name, c_data in self.derived_concepts.items():
                if c_data.get("concept_id") == term or c_name == term:
                    default_ctx = c_data.get("default_context")
                    if default_ctx:
                        candidate_contexts.add(default_ctx)
                    
        # Cleanup
        normalized_q = re.sub(r'\s+', ' ', q).strip()
        
        return {
            "original_query": original_query,
            "normalized_query": normalized_q,
            "canonical_terms": list(canonical_terms_found),
            "candidate_contexts": list(candidate_contexts),
            "matched_rules": matched_rules
        }

# Singleton instance
normalizer = QueryNormalizer()
