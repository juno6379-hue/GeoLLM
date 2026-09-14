import os
import yaml
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from shared.observability.logger import get_logger
from services.llm_config import ollama_base_url

logger = get_logger("orchestrator.context_resolver")

from dataclasses import dataclass, field

@dataclass
class ContextResult:
    status: str = "UNKNOWN"
    intent: Optional[str] = None
    selected_context: Optional[str] = None
    confidence: float = 0.0
    candidate_contexts: List[Dict[str, Any]] = field(default_factory=list)
    derived_concepts: List[str] = field(default_factory=list)
    target_features: Any = field(default_factory=list)
    selected_agents: List[str] = field(default_factory=list)
    clarification_questions: List[str] = field(default_factory=list)
    selected_tool: Optional[str] = None
    query_template: Optional[str] = None
    analysis_type: Optional[str] = None
    reason: str = ""
    debug_scores: Dict[str, float] = field(default_factory=dict)

class ContextResolver:
    def __init__(self):
        self.contexts = {}
        self.derived_concepts = {}
        self.synonyms = {}
        self.eval_dataset = []
        self.vector_store = None
        
        self.embed_model = os.environ.get("EMBEDDING_MODEL", "bge-m3")
        try:
            self.embeddings = OllamaEmbeddings(
                model=self.embed_model,
                base_url=ollama_base_url()
            )
        except Exception as e:
            logger.error(f"Failed to initialize embeddings: {e}")
            self.embeddings = None
            
        self.load_assets()
        self.build_vector_store()

    def load_assets(self):
        data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        
        # 1. Context Dictionary (New Format)
        dict_path = os.path.join(data_dir, "context_dictionary.yaml")
        if os.path.exists(dict_path):
            with open(dict_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "contexts" in data:
                    self.contexts = data["contexts"]
                    
        # 2. Derived Concept Registry
        concept_path = os.path.join(data_dir, "derived_concept_registry.yaml")
        if os.path.exists(concept_path):
            with open(concept_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "derived_concepts" in data:
                    self.derived_concepts = data["derived_concepts"]
                    
        # 3. Synonyms Dictionary
        syn_path = os.path.join(data_dir, "context_synonyms.yaml")
        if os.path.exists(syn_path):
            with open(syn_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "synonyms" in data:
                    self.synonyms = data["synonyms"]
                    
        # 4. Eval Dataset
        eval_path = os.path.join(data_dir, "context_evaluation_dataset.jsonl")
        if os.path.exists(eval_path):
            with open(eval_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        self.eval_dataset.append(json.loads(line))

    def build_vector_store(self):
        if not self.embeddings or not self.eval_dataset:
            return
            
        docs = []
        for item in self.eval_dataset:
            expected_context = item.get("context_id") or item.get("expected_context")
            doc = Document(
                page_content=item["query"], 
                metadata={"context_id": expected_context, "reason": item.get("reason", "")}
            )
            docs.append(doc)
            
        if docs:
            try:
                self.vector_store = FAISS.from_documents(docs, self.embeddings)
                logger.info("ContextResolver vector store built successfully.")
            except Exception as e:
                logger.error(f"Failed to build FAISS index for ContextResolver: {e}")

    def resolve(self, query: str, normalized_query: str = "", active_workspace: dict = None, available_layers: list = None, uploaded_assets: list = None, extracted_slots: dict = None) -> ContextResult:
        """
        다단계 컨텍스트 해석 파이프라인
        """
        derived_concepts = self._extract_derived_concepts(query, normalized_query, extracted_slots or {})
                
        target = derived_concepts[0] if derived_concepts else ""

        # --- 1. Rule-based Score & Evidence Calculation ---
        rule_scores = {}
        evidences = {}
        for context_id, cfg in self.contexts.items():
            r_score = 0
            ev_list = []
            # 1. 핵심 파생 개념 / 도메인 키워드 매칭
            has_domain_concept = False
            for dc in derived_concepts:
                if self.derived_concepts.get(dc, {}).get("default_context") == context_id:
                    has_domain_concept = True
                    r_score += 0.35
                    ev_list.append(f"핵심 파생개념({dc})")
                    break
            
            # 파생개념이 없다면 일반 키워드 매칭 확인 (가중치 보정)
            if not has_domain_concept:
                matched_phrases = [ph for ph in cfg.get("phrases", []) if ph in query or ph in normalized_query]
                matched_kws = [kw for kw in cfg.get("keywords", []) if kw in query or kw in normalized_query]
                if matched_phrases:
                    r_score += 0.35
                    ev_list.append(f"핵심 구문({matched_phrases[0]})")
                elif matched_kws:
                    r_score += 0.20
                    ev_list.append(f"도메인 키워드({matched_kws[0]})")
                    
            # 2 & 3. 슬롯 조건 (공간 검색 질의인 경우 위치/거리가 있으면 가점)
            if extracted_slots:
                if extracted_slots.get("location"):
                    r_score += 0.20
                    ev_list.append("위치 슬롯")
                if extracted_slots.get("distance_m"):
                    r_score += 0.20
                    ev_list.append("거리 슬롯")
                    
            # 4. 공간검색 행위
            search_actions = ["찾아줘", "검색", "보여줘", "표시", "조회"]
            if any(action in query for action in search_actions):
                r_score += 0.10
                ev_list.append("검색 행위")
                
            # 5. 공간분석 힌트
            spatial_terms = ["이내", "주변", "부근", "근처", "반경", "거리"]
            if any(term in query for term in spatial_terms):
                r_score += 0.10
                ev_list.append("공간분석 힌트")
                
            # 6. 지도 출력 암시
            if any(term in query for term in ["지도", "레이어"]):
                r_score += 0.05
                ev_list.append("지도 출력")
                
            normalized_r_score = min(r_score, 1.0)
            rule_scores[context_id] = normalized_r_score
            evidences[context_id] = list(set(ev_list))
            
        # --- 2. Embedding-based Score Calculation ---
        embed_scores = {}
        if self.vector_store:
            try:
                search_q = normalized_query if normalized_query else query
                results = self.vector_store.similarity_search_with_score(search_q, k=5)
                for doc, dist in results:
                    ctx = doc.metadata.get("context_id")
                    if ctx:
                        sim_score = max(0.0, 1.0 - (dist / 2.0))
                        if ctx not in embed_scores or sim_score > embed_scores[ctx]:
                            embed_scores[ctx] = sim_score
            except Exception as e:
                logger.error(f"Embedding search failed: {e}")
                
        # --- 3. Score Combination ---
        candidates = []
        for ctx_id in self.contexts.keys():
            r_score = rule_scores.get(ctx_id, 0.0)
            e_score = embed_scores.get(ctx_id, 0.0)
            
            # Derived Concept Score
            derived_concept_score = 0.0
            req_slots = []
            if target:
                concept_data = self.derived_concepts.get(target, {})
                if concept_data.get("default_context") == ctx_id:
                    derived_concept_score = 1.0
                    req_slots = concept_data.get("required_slots", [])
            
            # Slot Score (실행 가능성 체크)
            slot_score = 0.0
            if req_slots:
                filled_slots = sum(1 for s in req_slots if extracted_slots and extracted_slots.get(s))
                slot_score = filled_slots / len(req_slots)
            else:
                # 특별히 요구되는 슬롯이 없거나, 타겟이 없을 때
                slot_score = 1.0
                
            # Data Availability Score
            data_availability_score = 0.0
            active_module = ""
            loaded_layers = []
            
            if active_workspace:
                active_module = active_workspace.get("current_module", "")
                loaded_layers = active_workspace.get("loaded_layers", [])
                
            if available_layers:
                loaded_layers.extend(available_layers)
                
            if ctx_id == "navigation_safety" and active_module == "전자해도/S-101":
                data_availability_score = 1.0
                evidences.setdefault(ctx_id, []).append("전자해도 모듈 활성화")
            
            if ctx_id == "offshore_wind_site" and "offshore_wind_candidate" in loaded_layers:
                data_availability_score = 1.0
                evidences.setdefault(ctx_id, []).append("풍력단지 레이어 활성화")
                
            if ctx_id == "accident_prevention" and "accident_points" in loaded_layers:
                data_availability_score = 1.0
                evidences.setdefault(ctx_id, []).append("사고 레이어 활성화")
            
            # 신규 가중치 공식 적용
            final_score = (
                r_score * 0.35 +
                slot_score * 0.30 +
                derived_concept_score * 0.20 +
                e_score * 0.10 +
                data_availability_score * 0.05
            )
            
            if final_score > 0.2: # Minimum threshold
                candidates.append({
                    "context_id": ctx_id,
                    "score": round(final_score, 2),
                    "evidence": evidences.get(ctx_id, []),
                    "debug_scores": {
                        "rule_score": round(r_score, 2),
                        "slot_score": round(slot_score, 2),
                        "derived_concept_score": round(derived_concept_score, 2),
                        "embedding_score": round(e_score, 2),
                        "data_availability_score": round(data_availability_score, 2),
                        "final_confidence": round(final_score, 2)
                    }
                })
                
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        matched_context = candidates[0]["context_id"] if candidates else None
        confidence = candidates[0]["score"] if candidates else 0.0
        
        target_features = []
        selected_agents = []
        
        if matched_context:
            ctx_def = self.contexts.get(matched_context, {})
            selected_agents = ctx_def.get("default_agents", [])
            
        # --- 4. Derived Concept Direct Expansion ---
        clarification = []
        reason = ""
        selected_tool = None
        query_template = None
        analysis_type = None
        
        if derived_concepts:
            for concept_key, concept_data in self.derived_concepts.items():
                if concept_key in derived_concepts:
                    ambiguity_type = concept_data.get("ambiguity")
                    default_context = concept_data.get("default_context")
                    
                    if ambiguity_type == "conditional":
                        
                        def check_required_slots(concept: dict, slots: dict) -> dict:
                            required_slots = concept.get("required_slots", [])
                            slot_aliases = concept.get("slot_aliases", {})
                            filled_slots_res = {}
                            
                            def has_slot(required_slot: str) -> bool:
                                if slots.get(required_slot):
                                    filled_slots_res[required_slot] = slots.get(required_slot)
                                    return True
                        
                                aliases = slot_aliases.get(required_slot, [])
                                for alias in aliases:
                                    if slots.get(alias):
                                        filled_slots_res[required_slot] = slots.get(alias)
                                        return True
                                return False
                        
                            missing = [
                                slot for slot in required_slots
                                if not has_slot(slot)
                            ]
                        
                            return {
                                "required_slots": required_slots,
                                "filled_slots": filled_slots_res,
                                "missing_slots": missing,
                                "can_execute": len(missing) == 0
                            }
                            
                        # 슬롯 조건 검사 실행
                        slot_check_result = check_required_slots(concept_data, extracted_slots or {})
                        
                        has_all_req_slots = slot_check_result["can_execute"]
                        
                        if has_all_req_slots and concept_data.get("auto_execute_when_required_slots_present", False):
                            # Early Return (사용자 요청 로직)
                            target_features = concept_data.get("target_feature_groups", {}).get("hazard_objects", []) + concept_data.get("target_feature_groups", {}).get("hazard_areas", [])
                            if not target_features:
                                tf = concept_data.get("target_features", [])
                                if isinstance(tf, dict):
                                    target_features = tf
                                else:
                                    target_features = tf
                                    
                            mapped_dc = [self.derived_concepts.get(dc, {}).get("concept_id", dc) for dc in derived_concepts]
                                    
                            return ContextResult(
                                status="RESOLVED",
                                intent="marine_hazard_feature_search",
                                selected_context=default_context,
                                confidence=0.90,
                                candidate_contexts=candidates,
                                derived_concepts=mapped_dc,
                                target_features=list(set(target_features)) if isinstance(target_features, list) else target_features,
                                selected_agents=[concept_data.get("default_agent", "Spatial Analysis Agent")],
                                clarification_questions=[],
                                selected_tool=self._tool_for_analysis_type(
                                    concept_data.get("default_analysis_type"),
                                    concept_data.get("default_tool"),
                                ),
                                query_template=concept_data.get("default_query_template"),
                                analysis_type=concept_data.get("default_analysis_type"),
                                reason="Derived Concept의 필수 Slot이 충족되어 기본 Context를 적용",
                                debug_scores={"slot_check_result": slot_check_result}
                            )
                            
                        elif has_all_req_slots:
                            matched_context = default_context
                            confidence = 1.0
                        else:
                            if not extracted_slots or not extracted_slots.get("location"):
                                clarification.append(f"어느 위치(예: 부산항)를 기준으로 '{concept_key}'을(를) 검색할까요?")
                                reason_msg = "위치 정보 누락"
                            else:
                                clarification.append(f"'{concept_key}' 검색을 위해 추가 정보(거리 또는 영역)가 필요합니다. (예: 부산항 입구 3km 이내)")
                                reason_msg = "거리/영역 정보 누락"
                                
                            return ContextResult(
                                status="NEEDS_CLARIFICATION",
                                selected_context=None,
                                confidence=0.0,
                                candidate_contexts=candidates,
                                derived_concepts=[self.derived_concepts.get(dc, {}).get("concept_id", dc) for dc in derived_concepts],
                                target_features=[],
                                selected_agents=[],
                                clarification_questions=clarification,
                                selected_tool=None,
                                query_template=None,
                                analysis_type=None,
                                reason=f"모호성 해소 필요: {reason_msg}"
                            )
                            
                    # Registry에 정의된 실행 계획 요소를 즉각 주입
                    tf = concept_data.get("target_features", [])
                    tfg = concept_data.get("target_feature_groups", {})
                    
                    if tfg:
                        # flatten groups
                        for v in tfg.values():
                            target_features.extend(v)
                    elif isinstance(tf, dict):
                        target_features = tf
                    else:
                        target_features.extend(tf)
                    
                    da = concept_data.get("default_agent")
                    if da:
                        selected_agents.append(da)
                        
                    selected_tool = self._tool_for_analysis_type(
                        concept_data.get("default_analysis_type"),
                        concept_data.get("default_tool"),
                    )
                    query_template = concept_data.get("default_query_template")
                    analysis_type = concept_data.get("default_analysis_type")
                    
                    desc = concept_data.get("description", "")
                    reason = f"파생개념 '{concept_key}' 기반 Direct Expansion -> {matched_context}: {desc}"

        mapped_derived_concepts = []
        for dc in derived_concepts:
            dc_id = self.derived_concepts.get(dc, {}).get("concept_id", dc)
            mapped_derived_concepts.append(dc_id)
            
        if not reason and matched_context:
            reason = f"가장 높은 점수 획득 ({confidence})"

        if matched_context:
            best_candidate = candidates[0] if candidates else {}
            debug_scores = best_candidate.get("debug_scores", {})
            return ContextResult(
                status="RESOLVED",
                selected_context=matched_context,
                confidence=confidence,
                candidate_contexts=candidates,
                derived_concepts=mapped_derived_concepts,
                target_features=list(set(target_features)) if isinstance(target_features, list) else target_features,
                selected_agents=list(set(selected_agents)),
                clarification_questions=[],
                selected_tool=selected_tool,
                query_template=query_template,
                analysis_type=analysis_type,
                reason=reason,
                debug_scores=debug_scores
            )
            
        # 5. Global Fallback
        clarification.append("검색 기준(안전, 입지 제약 등)을 명확히 말씀해 주시겠어요?")
        return ContextResult(
            status="NEEDS_CLARIFICATION",
            selected_context=None,
            confidence=0.0,
            candidate_contexts=candidates,
            derived_concepts=mapped_derived_concepts,
            target_features=[],
            selected_agents=[],
            clarification_questions=clarification,
            selected_tool=None,
            query_template=None,
            analysis_type=None,
            reason="점수를 넘는 컨텍스트가 없음"
        )

    @staticmethod
    def _tool_for_analysis_type(analysis_type: Optional[str], fallback: Optional[str]) -> Optional[str]:
        """Keep operation selection separate from domain-context selection."""
        if analysis_type == "feature_search_by_radius":
            return "gbenc.s101_feature_search_by_radius"
        return fallback

    def _extract_derived_concepts(self, query: str, normalized_query: str, extracted_slots: dict) -> List[str]:
        """Resolve concept keys from raw text, normalized text, aliases, or canonical IDs."""
        haystack = f"{query or ''} {normalized_query or ''}"
        supplied = []
        for key in ("derived_concept", "derived_concepts", "canonical_terms"):
            value = extracted_slots.get(key)
            if not value:
                continue
            supplied.extend(value if isinstance(value, list) else [value])

        result = []
        for concept_key, concept_data in self.derived_concepts.items():
            concept_id = concept_data.get("concept_id", concept_key)
            aliases = concept_data.get("aliases", [])
            candidates = [concept_key, concept_id, *aliases]
            if any(candidate and candidate in haystack for candidate in candidates):
                result.append(concept_key)
                continue
            if any(item == concept_key or item == concept_id or item in aliases for item in supplied):
                result.append(concept_key)

        return list(dict.fromkeys(result))

context_resolver = ContextResolver()
