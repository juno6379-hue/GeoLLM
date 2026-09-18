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
        self.compound_terms = set()
        
        self.load_marine_term_dictionary()
        self.load_derived_concepts()
        self.build_compound_terms()
        
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

    def build_compound_terms(self):
        """Build a domain lexicon for compact Korean query segmentation."""
        seed_terms = {
            "\ub3c5\ub3c4",
            "\ubd80\uc0b0\ud56d",
            "\uc778\ucc9c\ud56d",
            "\uc785\uad6c",
            "\ubd80\uadfc",
            "\uadfc\ucc98",
            "\uc8fc\ubcc0",
            "\uc774\ub0b4",
            "\ubc18\uacbd",
            "\uac70\ub9ac",
            "\ud574\uc800\uc9c0\uba85",
            "\ud574\uc591\uc9c0\uba85",
            "\ub3c4\uc11c\uc9c0\uba85",
            "\uc9c0\uba85",
            "\uc704\ud5d8\uac1d\uccb4",
            "\uc7a5\uc560\ubb3c",
            "\uce68\uc120",
            "\uac04\ucd9c\uc554",
            "\ub178\ucd9c\uc554",
            "\ud56d\ub85c\ud45c\uc9c0",
            "\ubd80\ud45c",
            "\ub4f1\ud45c",
            "\ub4f1\ub300",
            "\uc815\ubc15\uc9c0",
            "\uc77c\ubc18\ud56d\ub85c",
            "\ud1b5\ud56d\ubd84\ub9ac",
            "\uc9c4\uc785\uc81c\ud55c",
            "\uc18d\ub3c4\uc81c\ud55c",
            "\ud1b5\ud56d\ub7c9",
            "\uc0ac\uace0\uc774\ub825",
            "\uc0ac\uace0\ub0b4\uc5ed",
            "\uc0ac\uace0",
            "\uc774\ub825",
            "\ud574\uc0c1\uc870\ub09c",
            "\uc870\ub09c\uc0ac\uace0",
            "\ud574\uc591\uc0ac\uace0",
            "\uc120\ubc15\uc0ac\uace0",
        }
        terms = set(seed_terms)
        terms.update(str(term) for term in self.synonyms.keys())
        terms.update(str(term) for term in self.synonyms.values())
        self.compound_terms = {
            term.strip()
            for term in terms
            if isinstance(term, str)
            and 2 <= len(term.strip()) <= 20
            and " " not in term.strip()
            and re.search(r"[\uac00-\ud7a3]", term)
        }
                
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

    def split_compound_korean(self, text: str) -> tuple[str, list[dict]]:
        """Split compact Korean tokens by longest domain lexicon match."""
        changes = []
        terms = sorted(self.compound_terms, key=len, reverse=True)
        if not terms:
            return text, changes

        def split_run(match: re.Match[str]) -> str:
            token = match.group(0)
            if len(token) < 5:
                return token
            parts = []
            index = 0
            while index < len(token):
                matched = next((term for term in terms if token.startswith(term, index)), None)
                if matched:
                    parts.append(matched)
                    index += len(matched)
                    continue
                next_known = len(token)
                for probe in range(index + 1, len(token)):
                    if any(token.startswith(term, probe) for term in terms):
                        next_known = probe
                        break
                parts.append(token[index:next_known])
                index = next_known
            split_value = " ".join(part for part in parts if part)
            if split_value != token and len(parts) > 1:
                changes.append({
                    "type": "compound_spacing",
                    "from": token,
                    "to": split_value,
                    "parts": parts,
                    "confidence": 0.9,
                })
                return split_value
            return token

        return re.sub(r"[\uac00-\ud7a3]{5,}", split_run, text), changes

    @staticmethod
    def _jamo_signature(text: str) -> str:
        choseong = [
            "\u3131", "\u3132", "\u3134", "\u3137", "\u3138", "\u3139", "\u3141", "\u3142", "\u3143",
            "\u3145", "\u3146", "\u3147", "\u3148", "\u3149", "\u314a", "\u314b", "\u314c", "\u314d", "\u314e",
        ]
        jungseong = [
            "\u314f", "\u3150", "\u3151", "\u3152", "\u3153", "\u3154", "\u3155", "\u3156", "\u3157", "\u3158",
            "\u3159", "\u315a", "\u315b", "\u315c", "\u315d", "\u315e", "\u315f", "\u3160", "\u3161", "\u3162", "\u3163",
        ]
        jongseong = [
            "", "\u3131", "\u3132", "\u3133", "\u3134", "\u3135", "\u3136", "\u3137", "\u3139", "\u313a",
            "\u313b", "\u313c", "\u313d", "\u313e", "\u313f", "\u3140", "\u3141", "\u3142", "\u3144", "\u3145",
            "\u3146", "\u3147", "\u3148", "\u314a", "\u314b", "\u314c", "\u314d", "\u314e",
        ]
        result = []
        for char in text:
            code = ord(char) - 0xAC00
            if 0 <= code <= 11171:
                result.append(choseong[code // 588])
                result.append(jungseong[(code % 588) // 28])
                final = jongseong[code % 28]
                if final:
                    result.append(final)
            else:
                result.append(char)
        return "".join(result)

    @staticmethod
    def _edit_distance(left: str, right: str) -> int:
        previous = list(range(len(right) + 1))
        for i, left_char in enumerate(left, 1):
            current = [i]
            for j, right_char in enumerate(right, 1):
                current.append(min(
                    previous[j] + 1,
                    current[j - 1] + 1,
                    previous[j - 1] + (0 if left_char == right_char else 1),
                ))
            previous = current
        return previous[-1]

    def correct_domain_typos(self, text: str) -> tuple[str, list[dict]]:
        """Correct high-confidence typos after compound spacing."""
        correction_candidates = ["\ubd80\uadfc", "\uadfc\ucc98", "\uc8fc\ubcc0"]
        exact_terms = set(self.compound_terms) | set(correction_candidates)
        corrections = []
        tokens = text.split()
        corrected_tokens = []
        context = set(tokens)
        for token in tokens:
            if token in exact_terms or not re.fullmatch(r"[\uac00-\ud7a3]{2,8}", token):
                corrected_tokens.append(token)
                continue
            ranked = []
            token_jamo = self._jamo_signature(token)
            for candidate in correction_candidates:
                distance = self._edit_distance(token_jamo, self._jamo_signature(candidate))
                confidence = max(0.0, 1.0 - (distance / max(len(token_jamo), len(candidate) * 3, 1)))
                if "\ub3c5\ub3c4" in context and "\ud574\uc800\uc9c0\uba85" in context and candidate == "\ubd80\uadfc":
                    confidence += 0.08
                ranked.append((confidence, distance, candidate))
            ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
            confidence, distance, candidate = ranked[0]
            if distance <= 2 and confidence >= 0.78:
                corrected_tokens.append(candidate)
                corrections.append({
                    "type": "typo_correction",
                    "from": token,
                    "to": candidate,
                    "reason": "domain_term_jamo_edit_distance",
                    "confidence": round(min(confidence, 0.99), 2),
                    "candidates": [item[2] for item in ranked[:3]],
                })
            else:
                corrected_tokens.append(token)
        return " ".join(corrected_tokens), corrections

    def domain_term_confidences(self, normalized_query: str, corrections: list[dict]) -> list[dict]:
        correction_terms = {
            item.get("to"): item
            for item in corrections
            if item.get("type") == "typo_correction" and item.get("to")
        }
        tracked_terms = [
            "\ub3c5\ub3c4",
            "\ubd80\uadfc",
            "\uadfc\ucc98",
            "\uc8fc\ubcc0",
            "\ud574\uc800\uc9c0\uba85",
            "\ud574\uc591\uc9c0\uba85",
            "\ub3c4\uc11c\uc9c0\uba85",
            "\uc0ac\uace0\uc774\ub825",
            "\uc0ac\uace0",
            "\uc774\ub825",
        ]
        tokens = set(normalized_query.split())
        result = []
        for term in tracked_terms:
            if term not in tokens:
                continue
            correction = correction_terms.get(term)
            if correction:
                result.append({
                    "term": term,
                    "source": correction.get("from"),
                    "match_type": "typo_correction",
                    "confidence": correction.get("confidence", 0.0),
                    "reason": correction.get("reason"),
                })
            else:
                result.append({
                    "term": term,
                    "source": term,
                    "match_type": "exact",
                    "confidence": 1.0,
                })
        return result

    def normalize_with_debug(self, query: str) -> dict:
        if not query:
            return {
                "original_query": "",
                "normalized_query": "",
                "canonical_terms": [],
                "candidate_contexts": [],
                "matched_rules": [],
                "corrections": [],
                "term_confidences": [],
                "normalization_confidence": 1.0,
                "requires_confirmation": False
            }
            
        original_query = query
        matched_rules = []
        corrections = []
        canonical_terms_found = set()
        
        # 1. 띄어쓰기 보정 (Spacing correction)
        # 1. 띄어쓰기 보정 (Spacing correction)
        q = query.strip()
        q, compound_changes = self.split_compound_korean(q)
        corrections.extend(compound_changes)
        for change in compound_changes:
            matched_rules.append(f"Compound Korean spacing: '{change['from']}' -> '{change['to']}'")
        q, typo_corrections = self.correct_domain_typos(q)
        corrections.extend(typo_corrections)
        for change in typo_corrections:
            matched_rules.append(
                f"Domain typo correction: '{change['from']}' -> '{change['to']}' "
                f"(confidence={change['confidence']})"
            )
        
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
        term_confidences = self.domain_term_confidences(normalized_q, corrections)
        for item in term_confidences:
            canonical_terms_found.add(item["term"])
        confidence_values = [float(item.get("confidence", 1.0)) for item in corrections]
        normalization_confidence = min(confidence_values) if confidence_values else 1.0
        
        return {
            "original_query": original_query,
            "normalized_query": normalized_q,
            "canonical_terms": list(canonical_terms_found),
            "candidate_contexts": list(candidate_contexts),
            "matched_rules": matched_rules,
            "corrections": corrections,
            "term_confidences": term_confidences,
            "normalization_confidence": round(normalization_confidence, 2),
            "requires_confirmation": normalization_confidence < 0.75
        }

# Singleton instance
normalizer = QueryNormalizer()
