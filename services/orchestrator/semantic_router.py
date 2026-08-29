import os
import json
import re
import yaml
import numpy as np
import requests
from typing import Dict, Any, Tuple, Optional, List
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from shared.observability.logger import get_logger
from services.orchestrator.feature_resolver import feature_resolver
from services.llm_config import ollama_base_url

logger = get_logger("orchestrator.semantic_router")

def load_route_definitions() -> Dict[str, list]:
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "intent_dataset.json")
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            routes = {}
            if isinstance(data, list):
                for item in data:
                    cat = item.get("category", "UNKNOWN")
                    if cat not in routes:
                        routes[cat] = []
                    routes[cat].append(item.get("query", ""))
            else:
                for intent, details in data.items():
                    routes[intent] = []
                    sub_types = details.get("sub_types", {})
                    for stype, utterances in sub_types.items():
                        routes[intent].extend(utterances)
            return routes
    except Exception as e:
        logger.error(f"Failed to load intent_dataset.json: {e}")
        return {}

ROUTE_DEFINITIONS = load_route_definitions()

class SemanticRouter:
    def __init__(self):
        self.embed_model = os.environ.get("EMBEDDING_MODEL", "bge-m3")
        try:
            self.embeddings = OllamaEmbeddings(
                model=self.embed_model,
                base_url=ollama_base_url()
            )
            logger.info(f"SemanticRouter initialized with {self.embed_model}")
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            self.embeddings = None
            
        self._route_vectors = {}
        self._initialize_route_vectors()
        
    def _initialize_route_vectors(self):
        # [긴급 테스트용] 3.5분 걸리는 임베딩 스킵 (어차피 정규식으로 통과함)
        return

    def route_query(self, query: str, threshold: float = 0.65) -> str:
        """
        질문(query)을 임베딩하고 가장 유사한 Intent Route를 반환합니다.
        """
        # 1. 정규식 우선 매칭 (FAISS 바이패스)
        extractor = DynamicSlotExtractor()
        regex_intent = extractor.guess_intent_by_regex(query)
        if regex_intent:
            return regex_intent
            
        # 2. FAISS 기반 시맨틱 라우팅
        if not self.embeddings or not self._route_vectors:
            return "clarification_required"
            
        try:
            query_vec = np.array(self.embeddings.embed_query(query))
            best_intent = "clarification_required"
            best_score = -1.0
            
            for intent, items in self._route_vectors.items():
                for item in items:
                    route_vec = item["vector"]
                    # 코사인 유사도 계산
                    score = np.dot(query_vec, route_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(route_vec))
                    if score > best_score:
                        best_score = score
                        best_intent = intent
                        
            logger.info(f"Semantic Routing match: {best_intent} (Score: {best_score:.3f})")
            
            if best_score >= threshold:
                return best_intent
            return "clarification_required"
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return "clarification_required"


# =========================================================================
# 2. Semantic Cache (FAISS 기반 영속 캐시)
# =========================================================================
class SemanticCache:
    def __init__(self):
        self.cache_dir = os.path.join(os.environ.get("APP_DATA_DIR", "/tmp"), "geollm_cache")
        self.index_path = os.path.join(self.cache_dir, "semantic_cache")
        self.embeddings = OllamaEmbeddings(
            model=os.environ.get("EMBEDDING_MODEL", "bge-m3"),
            base_url=ollama_base_url()
        )
        self.vectorstore = None
        self._load_cache()

    def _load_cache(self):
        os.makedirs(self.cache_dir, exist_ok=True)
        if os.path.exists(os.path.join(self.index_path, "index.faiss")):
            try:
                self.vectorstore = FAISS.load_local(self.index_path, self.embeddings, allow_dangerous_deserialization=True)
                logger.info(f"Loaded Semantic Cache from {self.index_path}")
            except Exception as e:
                logger.error(f"Failed to load Semantic Cache: {e}")
                self.vectorstore = None
        else:
            logger.info("Semantic Cache index not found. Will be created on first cache miss.")

    def check_cache(self, query: str, threshold: float = 0.95) -> Optional[Dict[str, Any]]:
        """
        캐시를 검색하여 95% 이상 일치하는 과거 질문이 있다면 파싱 결과를 반환합니다.
        """
        if not self.vectorstore:
            return None
            
        try:
            docs_and_scores = self.vectorstore.similarity_search_with_relevance_scores(query, k=1)
            if docs_and_scores:
                doc, score = docs_and_scores[0]
                logger.info(f"Cache check: Best match score={score:.3f} for query '{doc.page_content}'")
                # bge-m3 등에서 코사인 유사도가 score로 반환된다고 가정
                if score >= threshold:
                    logger.info(f"🔥 Semantic Cache Hit! (Score: {score:.3f})")
                    return json.loads(doc.metadata["parsed_result"])
        except Exception as e:
            logger.error(f"Cache check failed: {e}")
            
        return None

    def add_to_cache(self, query: str, parsed_result: Dict[str, Any]):
        """
        새로운 파싱 결과를 캐시에 저장합니다.
        """
        try:
            doc = Document(
                page_content=query,
                metadata={"parsed_result": json.dumps(parsed_result, ensure_ascii=False)}
            )
            
            if self.vectorstore is None:
                self.vectorstore = FAISS.from_documents([doc], self.embeddings)
            else:
                self.vectorstore.add_documents([doc])
                
            self.vectorstore.save_local(self.index_path)
            logger.info(f"Added to Semantic Cache: '{query}'")
        except Exception as e:
            logger.error(f"Failed to add to cache: {e}")

# 싱글톤 인스턴스
router = SemanticRouter()
cache = SemanticCache()

class DynamicSlotExtractor:
    def __init__(self):
        self.default_distance_policy = {
            "부근": 3000,
            "주변": 3000,
            "인근": 3000,
            "근처": 3000,
            "가까운": 1000
        }
        # 인텐트별 정규식 패턴 및 슬롯 매핑 정의
        self.patterns = {
            "spatial_proximity_search": [
                (r'(.*?)\s*(\d+)(km|m)\s*(이내의?|반경)\s*(.+?)(?:[을를이가])?\s*(?:분석|찾아|검색|보여|표시|해줘|해봐|알려|어딨|출력).*$', ["location", "distance_m", "unit", "spatial_relation", "target_term"]),
                (r'(.*?)\s*(주변|근처|인근|부근|가까운)\s*(\d+)(km|m)\s*(이내\s*)?(.+?)(?:[을를이가])?\s*(?:분석|찾아|검색|보여|표시|해줘|해봐|알려|어딨|출력).*$', ["location", "spatial_relation", "distance_m", "unit", "dummy", "target_term"]),
                # 거리 정보가 없는 패턴 ("부산항 주변 선석 보여줘")
                (r'(.*?)\s*(주변|근처|인근|부근|가까운)\s*(.+?)(?:[을를이가])?\s*(?:분석|찾아|검색|보여|표시|해줘|해봐|알려|어딨|출력).*$', ["location", "spatial_relation", "target_term"]),
                # 장소와 대상만 있는 단순 패턴 ("목포항 선석을 찾아줘")
                (r'^([가-힣]+(?:항|도|만|해|앞바다))\s*([가-힣a-zA-Z0-9\s]+?)(?:[을를이가])?\s*(?:분석|찾아|검색|보여|표시|해줘|해봐|알려|어딨|출력).*$', ["location", "target_term"]),
                # 대상만 있는 단순 패턴 ("선석을 찾아줘")
                (r'^([가-힣a-zA-Z0-9\s]+?)(?:[을를이가])?\s*(?:분석|찾아|검색|보여|표시|해줘|해봐|알려|어딨|출력).*$', ["target_term"])
            ],
            "drone_lidar_change_detection": [
                (r'(.*)(?:드론|drone|라이다|lidar|점군|dsm|정사영상).*(?:분석|탐지|불러|로드|보여|해봐|해줘|찾아|비교).*$', ["target_term"])
            ]
        }

    def guess_intent_by_regex(self, query: str) -> Optional[str]:
        for intent, patterns in self.patterns.items():
            for pattern, _ in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    return intent
        return None

    def extract_distance_m(self, query: str) -> Optional[int]:
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(km|킬로|키로)\s*(이내|내|안|반경)?",
            r"반경\s*(\d+(?:\.\d+)?)\s*(km|킬로|키로)",
            r"(\d+(?:\.\d+)?)\s*(m|미터)\s*(이내|내|안|반경)?"
        ]

        for pattern in patterns:
            match = re.search(pattern, query, flags=re.IGNORECASE)
            if match:
                groups = match.groups()
                value = float(groups[0])
                unit = groups[1]

                if unit in ["km", "킬로", "키로"]:
                    return int(value * 1000)
                return int(value)

        return None

    def extract_location_before_distance(self, query: str) -> Optional[str]:
        pattern = r"(.+?)\s*\d+(?:\.\d+)?\s*(?:km|킬로|키로|m|미터)\s*(?:이내|내|안|반경)?"

        match = re.search(pattern, query, flags=re.IGNORECASE)
        if not match:
            return None

        location = match.group(1).strip()

        # 조사/불필요 표현 정리 (문자열 끝에 있는 경우만 제거)
        cleanup_terms = ["에서", "주변", "부근", "근처", "반경"]
        for term in cleanup_terms:
            location = re.sub(rf'\s*{term}$', '', location)

        return location.strip()

    def extract(self, query: str, intent: str) -> Optional[Dict[str, Any]]:
        slots = {
            "location": self.extract_location_before_distance(query),
            "spatial_relation": None,
            "distance_m": self.extract_distance_m(query),
            "target_term": None,
            "derived_concept": None,
            "context": None,
            "action": None,
            "target_feature_candidates": [],
            "analysis_type": None,
            "output_type": [],
            "filter": None,
            "source_preference": None
        }
        
        extracted_from_regex = False
        if intent in self.patterns:
            for pattern, slot_names in self.patterns[intent]:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    extracted_from_regex = True
                    for i, name in enumerate(slot_names):
                        if name == "dummy" or not match.group(i+1):
                            continue
                        val = match.group(i+1).strip()
                        
                        if name == "distance_m" and "unit" in slot_names:
                            unit_idx = slot_names.index("unit") + 1
                            if match.group(unit_idx):
                                unit = match.group(unit_idx).lower()
                                if unit == "km":
                                    val = int(val) * 1000
                                else:
                                    val = int(val)
                        if name not in ["unit", "dummy"]:
                            # robust extraction 결과가 있으면 덮어쓰지 않음
                            if slots.get(name) is None:
                                slots[name] = val
                    break
                
        if not extracted_from_regex and (not slots["location"] or not slots["distance_m"]):
            logger.warning(f"Regex extraction failed for intent {intent}. Using LLM fallback.", query=query)
            llm_slots = self._extract_with_llm(query, intent)
            if llm_slots:
                for k, v in llm_slots.items():
                    if slots.get(k) is None and v is not None:
                        slots[k] = v
                
        # 1. Default distance policy 적용
        if not slots.get("distance_m"):
            rel = slots.get("spatial_relation")
            if rel and rel in self.default_distance_policy:
                slots["distance_m"] = self.default_distance_policy[rel]
            elif slots.get("location"):
                slots["distance_m"] = 1000  # 기본 반경 1000m 적용
                
        # 2. Output type 휴리스틱 파싱
        if "지도" in query or "표시" in query:
            slots["output_type"].append("map_layer")
        if "표" in query or "속성" in query or "조회" in query:
            slots["output_type"].append("attribute_table")
        if "보고서" in query or "정리" in query or "PDF" in query.upper():
            slots["output_type"].append("summary")
        if not slots["output_type"]:
            slots["output_type"] = ["map_layer", "summary"] # 기본값
            
        # 3. Feature Resolver 연동하여 target_feature_candidates 도출
        if slots.get("target_term"):
            resolved = feature_resolver.resolve(slots["target_term"])
            candidates = [f["feature_name"] for f in resolved.get("resolved_features", [])]
            if candidates:
                slots["target_feature_candidates"] = candidates

        return slots

    def _extract_with_llm(self, query: str, intent_type: str) -> Dict[str, Any]:
        prompt = f"""
        Extract the key entities from the following user query for a maritime GIS system.
        Intent: {intent_type}
        
        Expected fields (all optional, omit if not found):
        - location (string)
        - spatial_relation (string, e.g. "부근", "이내")
        - distance_m (integer in meters)
        - target_term (string, e.g. "선석")
        - filter (string, e.g. "사용중")
        - source_preference (string)
        
        Examples:
        Query: "부산항 부근 사용중인 선석을 찾아줘" -> {{"location": "부산항", "spatial_relation": "부근", "target_term": "선석", "filter": "사용중"}}
        
        Query: "{query}"
        Respond ONLY with a valid JSON object.
        """
        try:
            response = requests.post(ollama_base_url() + "/api/generate", json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=5.0)
            
            if response.status_code == 200:
                result_text = response.json().get("response", "{}")
                return json.loads(result_text)
        except Exception as e:
            logger.error("LLM Fallback failed", error=str(e))
        return {}

slot_extractor = DynamicSlotExtractor()

class RuleBasedRouter:
    def __init__(self):
        self.rules_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "routing_rules.yaml")
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "rules" in data:
                    return sorted(data["rules"], key=lambda x: x.get("priority", 0), reverse=True)
        except Exception as e:
            logger.error(f"Failed to load routing_rules.yaml: {e}")
        return []

    def evaluate(self, query: str) -> Dict[str, Any]:
        """
        질문 텍스트를 기반으로 규칙들을 평가하여 라우팅 결과를 반환합니다.
        """
        result = {
            "primary_agent": None,
            "secondary_agents": []
        }
        
        for rule in self.rules:
            conditions = rule.get("conditions", {})
            any_kw = conditions.get("any_keywords", conditions.get("any_terms", []))
            any_act = conditions.get("any_actions", [])
            
            # 키워드 매칭
            kw_match = any(kw in query for kw in any_kw) if any_kw else True
            # 액션 매칭
            act_match = any(act in query for act in any_act) if any_act else True
            
            if kw_match and act_match:
                route = rule.get("route", {})
                if "primary_agent" in route and not result["primary_agent"]:
                    result["primary_agent"] = route["primary_agent"]
                    logger.info(f"Rule match: {rule['rule_id']} -> Primary: {route['primary_agent']}")
                
                # add_agent (string or list)
                add_agent = route.get("add_agent", [])
                if isinstance(add_agent, str):
                    add_agent = [add_agent]
                
                # secondary_agents (list)
                sec_agents = route.get("secondary_agents", [])
                
                for agent in add_agent + sec_agents:
                    if agent not in result["secondary_agents"]:
                        result["secondary_agents"].append(agent)
                        logger.info(f"Rule match: {rule['rule_id']} -> Added Secondary: {agent}")
                        
        return result

rule_router = RuleBasedRouter()
