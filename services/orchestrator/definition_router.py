from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"


def normalize_term(value: Any) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", str(value or "").casefold())


def definition_subject(query: str) -> str:
    mapping = catalogue_mapping_subject(query)
    if mapping:
        return mapping
    text = str(query or "").strip().strip("\"'“”‘’").rstrip("?!. ").strip()
    suffix = re.fullmatch(r"(.+?)(?:이란|란)", text)
    if suffix:
        return suffix.group(1).strip()
    explicit = re.fullmatch(
        r"(.+?)(?:의)?\s*(?:정의|뜻|의미|개념)(?:은|는|이|가|을|를)?"
        r"(?:\s*(?:무엇|뭐야|알려줘|설명해줘))?",
        text,
    )
    if explicit:
        return explicit.group(1).strip()
    what_is = re.fullmatch(r"(.+?)(?:은|는|이|가)?\s*(?:무엇|뭐야|뭔가)", text)
    return what_is.group(1).strip() if what_is else text


def has_operational_slots(query: str) -> bool:
    text = str(query or "")
    lowered = text.casefold()
    temporal = re.search(
        r"오늘|내일|모레|현재|실시간|최신|최근|일정|시간표|"
        r"\d{1,4}\s*(?:년|월|일|시)|\d{4}[-./]\d{1,2}(?:[-./]\d{1,2})?",
        text,
    )
    spatial = re.search(
        r"인천|부산|목포|울산|여수|제주|독도|[가-힣A-Za-z]+항(?:\s*입구)?|"
        r"앞바다|연안|해역|근처|주변|반경|\d+(?:\.\d+)?\s*(?:km|m|킬로|미터)",
        text,
        re.I,
    )
    execution = any(
        term in lowered
        for term in (
            "만조", "간조", "조위 예측", "예측값", "관측값", "시계열",
            "forecast value", "조회해", "검색해", "계산해", "분석해",
            "시간 알려", "일정 알려", "찾아줘", "보여줘", "표시해줘",
        )
    )
    return bool(temporal or spatial or execution)


def _add(entries: dict[str, dict[str, Any]], entry: dict[str, Any], values: list[Any]) -> None:
    for value in values:
        key = normalize_term(value)
        if key and key not in entries:
            entries[key] = entry


@lru_cache(maxsize=1)
def definition_entries() -> dict[str, dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    products_path = DATA / "s100_product_registry.yaml"
    if products_path.exists():
        products = (yaml.safe_load(products_path.read_text(encoding="utf-8")) or {}).get("products") or {}
        for product_id, product in products.items():
            if not isinstance(product, dict) or not product.get("name"):
                continue
            name = str(product["name"])
            entry = {"term_id": product_id, "canonical_term": product_id,
                     "aliases": [product_id.replace("-", "")],
                     "definition_ko": f"현재 연결된 제품 레지스트리에 {name}로 등록된 S-100 계열 표준입니다. 등록 버전은 {product.get('version', '미기록')}이며, 자료 유형은 {product.get('data_type', '미기록')}입니다.",
                     "source_title": "로컬 S-100 제품 레지스트리",
                     "source_ref": f"data/s100_product_registry.yaml#products/{product_id}",
                     "context": "standard", "verification_status": "LOCAL_PRODUCT_REGISTRY",
                     "source_kind": "s100_product_registry"}
            _add(entries, entry, [product_id, *entry["aliases"]])
    curated = yaml.safe_load((DATA / "definition_term_registry.yaml").read_text(encoding="utf-8")) or {}
    for term_id, raw in (curated.get("terms") or {}).items():
        if not isinstance(raw, dict) or raw.get("verification_status") != "VERIFIED":
            continue
        entry = {"term_id": term_id, "source_kind": "verified_definition_registry", **raw}
        _add(entries, entry, [entry.get("canonical_term"), *(entry.get("aliases") or [])])

    dictionary_path = ROOT / "outputs/dictionaries/marine_term_dictionary.yaml"
    if dictionary_path.exists():
        dictionary = yaml.safe_load(dictionary_path.read_text(encoding="utf-8")) or {}
        for term_id, raw in (dictionary.get("terms") or {}).items():
            definitions = raw.get("definitions") or [] if isinstance(raw, dict) else []
            if not definitions:
                continue
            canonical = str(raw.get("canonical_term") or term_id)
            entry = {
                "term_id": str(term_id), "canonical_term": canonical,
                "aliases": raw.get("aliases") or [], "definition_ko": str(definitions[0]),
                "source_title": "해양수산 용어사전",
                "source_ref": "outputs/dictionaries/marine_term_dictionary.yaml",
                "context": (raw.get("contexts") or ["maritime_domain"])[0],
                "verification_status": raw.get("verification_status") or "DICTIONARY_SOURCE",
                "source_kind": "marine_term_dictionary",
            }
            _add(entries, entry, [canonical, term_id, *(entry["aliases"] or [])])

    catalogue_path = DATA / "s101_catalogue.json"
    if catalogue_path.exists():
        document = json.loads(catalogue_path.read_text(encoding="utf-8"))
        features = document.get("features") if isinstance(document, dict) else document
        for raw in features or []:
            code = str(raw.get("code") or "")
            name = str(raw.get("name") or code)
            definition = str(raw.get("definition") or "")
            if not code or not definition:
                continue
            aliases = [code, *(raw.get("aliases") or [])]
            entry = {
                "term_id": code, "canonical_term": name, "aliases": aliases,
                "definition_ko": definition,
                "source_title": "S-101 Feature Catalogue 2.0.0",
                "source_ref": raw.get("source") or "data/s101_catalogue.json",
                "context": "standard", "verification_status": "CATALOGUE_SOURCE",
                "source_kind": "s101_feature_catalogue",
            }
            _add(entries, entry, [code, name, *aliases])
    # Korean semantic aliases live separately from the parsed FC. Bind only
    # unique feature mappings; broad/multi-feature concepts stay unresolved.
    mapping_path = DATA / "s101_feature_dictionary.yaml"
    if mapping_path.exists():
        mappings = (yaml.safe_load(mapping_path.read_text(encoding="utf-8")) or {}).get("s101_features") or {}
        for label, mapping in mappings.items():
            candidates = mapping.get("feature_candidates") or [] if isinstance(mapping, dict) else []
            if len(candidates) != 1:
                continue
            entry = entries.get(normalize_term(candidates[0]))
            if entry:
                _add(entries, {**entry, "alias_binding_ref": f"data/s101_feature_dictionary.yaml#s101_features/{label}"}, [label])
    return entries


def catalogue_mapping_subject(query: str) -> str | None:
    match = re.fullmatch(
        r"\s*(.+?)(?:은|는|이|가)?\s*S-?101(?:에서|의)?\s*(?:어떤|무슨)\s*(?:Feature|피처|객체)(?:야|인가|인가요|인지)?[?!.\s]*",
        str(query or ""), re.I,
    )
    return match.group(1).strip() if match else None


def resolve_definition(query: str) -> dict[str, Any] | None:
    # Compare two registered concepts only when no executable spatial/time
    # obligation exists. Preserve each source; do not infer a spatial result.
    if not has_operational_slots(query):
        comparison = re.fullmatch(r"\s*(.+?)(?:과|와|하고|\s+vs\.?\s+)\s*(.+?)(?:의)?\s*차이(?:점)?(?:를)?(?:\s*(?:알려줘|설명해줘))?[?!.\s]*", query, re.I)
        if comparison:
            entries = [resolve_definition(part.strip()) for part in comparison.groups()]
            if all(entries) and entries[0]["term_id"] != entries[1]["term_id"]:
                return {**entries[0], "source_kind": "definition_comparison",
                        "canonical_term": " / ".join(item["canonical_term"] for item in entries),
                        "comparison_entries": entries}
    from services.orchestrator.marine_terminology import resolve_label_request
    label_request = resolve_label_request(query)
    if label_request:
        return label_request
    subject = catalogue_mapping_subject(query)
    if subject:
        registry = yaml.safe_load((DATA / "s101_feature_dictionary.yaml").read_text(encoding="utf-8")) or {}
        mapping = (registry.get("s101_features") or {}).get(subject) or {}
        candidates = mapping.get("feature_candidates") or []
        # Multi-feature terms require clarification; never choose the first alias.
        if len(candidates) == 1:
            return definition_entries().get(normalize_term(candidates[0]))
        return None
    return definition_entries().get(normalize_term(definition_subject(query)))


def is_definition_query(query: str) -> bool:
    text = str(query or "").strip()
    if not text or has_operational_slots(text) or len(normalize_term(definition_subject(text))) < 2:
        return False
    entry = resolve_definition(text)
    if not entry:
        return False
    if entry['source_kind'] == 'mof_terminology_relation':
        return True
    if entry['source_kind'] == 'definition_comparison':
        return True
    lowered = text.casefold()
    explicit = any(token in lowered for token in ("definition", "meaning", "what is", "정의", "뜻", "의미", "무엇", "뭐야", "뭔가", "개념"))
    suffix = re.search(r"(?:이란|란)\??$", text) is not None
    bare_term = normalize_term(text) == normalize_term(entry["canonical_term"]) or any(
        normalize_term(text) == normalize_term(alias) for alias in entry.get("aliases") or []
    )
    return bool(explicit or suffix or bare_term or catalogue_mapping_subject(text))
