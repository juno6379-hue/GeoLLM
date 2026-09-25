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
    return entries


def resolve_definition(query: str) -> dict[str, Any] | None:
    return definition_entries().get(normalize_term(definition_subject(query)))


def is_definition_query(query: str) -> bool:
    text = str(query or "").strip()
    if not text or has_operational_slots(text) or len(normalize_term(definition_subject(text))) < 2:
        return False
    entry = resolve_definition(text)
    if not entry:
        return False
    lowered = text.casefold()
    explicit = any(token in lowered for token in ("definition", "meaning", "what is", "정의", "뜻", "의미", "무엇", "뭐야", "뭔가", "개념"))
    suffix = re.search(r"(?:이란|란)\??$", text) is not None
    bare_term = normalize_term(text) == normalize_term(entry["canonical_term"]) or any(
        normalize_term(text) == normalize_term(alias) for alias in entry.get("aliases") or []
    )
    return bool(explicit or suffix or bare_term)
