"""S-101 Feature Catalogue/DCEG 기반 온톨로지 후보 매칭 점수를 계산한다.

Phase 8.4 산출물은 실행 권한이 아니다. 자동 제안 후보가 어떤 S-101
feature/attribute와 가까운지 점수와 근거를 제공하여 Phase 8.3 승인 검토를
보강한다.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs" / "ontology"
REVIEW = ROOT / "outputs" / "review"

DEFAULT_PROPOSALS = OUT / "ontology_binding_proposals.jsonl"
DEFAULT_PROFILES = OUT / "dataset_profiles.jsonl"
DEFAULT_OUTPUT = OUT / "s101_dceg_match_scores.jsonl"
DEFAULT_SUMMARY = OUT / "s101_dceg_match_summary.json"
DEFAULT_REVIEW = REVIEW / "s101_dceg_match_needs_review.jsonl"


LAYER_FEATURE_HINTS = {
    "hazard_object": ["Wreck", "Obstruction", "UnderwaterAwashRock", "FoulGround"],
    "regulated_area": [
        "RestrictedArea",
        "MilitaryPracticeArea",
        "TrafficSeparationScheme",
        "TrafficSeparationSchemeBoundary",
    ],
    "protected_area": ["RestrictedArea"],
    "traffic_activity": ["Fairway", "RecommendedTrack", "TrafficSeparationScheme", "VesselTrafficServiceArea"],
    "place_gazetteer": ["SeaAreaNamedWaterArea", "LandArea", "HarbourAreaAdministrative"],
    "hydrographic_observation": ["TidalStreamPanelData", "CurrentNonGravitational", "WaterLevelTrend"],
}

MISSING_FEATURE_ALIASES = {
    "Rock": ["UnderwaterAwashRock"],
    "MarineProtectedArea": ["RestrictedArea"],
}

PRIMITIVE_BY_SHAPE = {
    "POINT": "point",
    "POINTZ": "point",
    "MULTIPOINT": "point",
    "POLYLINE": "curve",
    "POLYLINEZ": "curve",
    "POLYGON": "surface",
    "POLYGONZ": "surface",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_json_or_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return yaml.safe_load(text) or {}


def normalize_tokens(value: Any) -> set[str]:
    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value or "")
    words = re.findall(r"[\w/-]+", text.lower(), flags=re.UNICODE)
    tokens: set[str] = set()
    for word in words:
        tokens.add(word)
        for part in re.split(r"[_/-]+", word):
            if len(part) >= 2:
                tokens.add(part)
    return tokens


def camel_tokens(text: str) -> set[str]:
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|[0-9]+", text or "")
    return {part.lower() for part in parts if len(part) >= 2}


def feature_tokens(feature: dict[str, Any]) -> set[str]:
    tokens = normalize_tokens([feature.get("code"), feature.get("name"), feature.get("aliases"), feature.get("definition")])
    tokens.update(camel_tokens(feature.get("code") or ""))
    return tokens


def profile_text_signals(profile: dict[str, Any] | None) -> list[Any]:
    if not profile:
        return []
    signals: list[Any] = []
    signals.extend(profile.get("text_signals") or [])
    spatial = profile.get("spatial_profile") or {}
    signals.extend(spatial.get("fields") or [])
    signals.extend(spatial.get("shape_types") or [])
    signals.append(profile.get("source_asset"))
    signals.append(profile.get("file_name"))
    return signals


def proposal_tokens(proposal: dict[str, Any], profile: dict[str, Any] | None) -> set[str]:
    values: list[Any] = [
        proposal.get("dataset_id"),
        proposal.get("source_asset"),
        proposal.get("suggested_binding"),
        proposal.get("best_rule"),
    ]
    values.extend(profile_text_signals(profile))
    return normalize_tokens(values)


def expected_primitives(profile: dict[str, Any] | None) -> set[str]:
    if not profile:
        return set()
    spatial = profile.get("spatial_profile") or {}
    primitives = set()
    for shape_type in spatial.get("shape_types") or []:
        primitive = PRIMITIVE_BY_SHAPE.get(str(shape_type).upper())
        if primitive:
            primitives.add(primitive)
    return primitives


def dceg_index(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        return {}
    index: dict[str, list[dict[str, Any]]] = {}
    for row in load_jsonl(path):
        text = row.get("text") or ""
        metadata = row.get("metadata") or {}
        related = metadata.get("related_features") or []
        keys = set(str(item).lower() for item in related)
        keys.update(token for token in camel_tokens(text) if len(token) > 4)
        entry = {
            "chunk_id": row.get("chunk_id"),
            "page_no": metadata.get("page_no"),
            "source_file": metadata.get("source_file"),
            "section": metadata.get("section"),
        }
        for key in keys:
            index.setdefault(key, []).append(entry)
    return index


def dceg_evidence_for(feature: dict[str, Any], index: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    keys = {str(feature.get("name") or "").lower(), str(feature.get("code") or "").lower()}
    keys.update(str(alias).lower() for alias in feature.get("aliases") or [])
    keys.update(camel_tokens(feature.get("code") or ""))
    evidence: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in keys:
        for item in index.get(key, [])[:3]:
            marker = str(item.get("chunk_id"))
            if marker in seen:
                continue
            seen.add(marker)
            evidence.append(item)
            if len(evidence) >= 3:
                return evidence
    return evidence


def candidate_feature_codes(proposal: dict[str, Any], semantic_mappings: dict[str, Any]) -> set[str]:
    binding = proposal.get("suggested_binding") or {}
    codes: set[str] = set()
    mapping_name = binding.get("semantic_mapping")
    if mapping_name and mapping_name in semantic_mappings:
        codes.update(semantic_mappings[mapping_name].get("feature_candidates") or [])
    layer_type = binding.get("layer_type")
    codes.update(LAYER_FEATURE_HINTS.get(layer_type, []))
    expanded = set(codes)
    for code in codes:
        expanded.update(MISSING_FEATURE_ALIASES.get(code, []))
    return expanded


def lexical_score(query_tokens: set[str], candidate_tokens: set[str]) -> float:
    if not query_tokens or not candidate_tokens:
        return 0.0
    overlap = query_tokens & candidate_tokens
    if not overlap:
        return 0.0
    return min(1.0, len(overlap) / math.sqrt(len(candidate_tokens)))


def primitive_score(profile: dict[str, Any] | None, feature: dict[str, Any]) -> float:
    expected = expected_primitives(profile)
    primitives = set(str(item).lower() for item in feature.get("primitives") or feature.get("permitted_primitives") or [])
    if not expected or not primitives:
        return 0.0
    return 1.0 if expected & primitives else 0.0


def attribute_matches(profile: dict[str, Any] | None, attributes: list[dict[str, Any]], query_tokens: set[str]) -> list[dict[str, Any]]:
    fields = set()
    if profile:
        spatial = profile.get("spatial_profile") or {}
        fields.update(str(item).lower() for item in spatial.get("fields") or [])
    matches: list[dict[str, Any]] = []
    for attr in attributes:
        aliases = set(str(item).lower() for item in attr.get("alias") or [])
        attr_tokens = normalize_tokens([attr.get("code"), attr.get("name"), attr.get("definition"), attr.get("alias")])
        exact = bool(fields & aliases) or str(attr.get("code") or "").lower() in fields
        lexical = lexical_score(query_tokens, attr_tokens)
        score = (0.8 if exact else 0.0) + min(0.2, lexical * 0.2)
        if score > 0:
            matches.append(
                {
                    "attribute_code": attr.get("code"),
                    "attribute_name": attr.get("name"),
                    "aliases": attr.get("alias") or [],
                    "score": round(score, 4),
                    "match_basis": {"exact_field_or_alias": exact, "lexical_score": round(lexical, 4)},
                }
            )
    matches.sort(key=lambda item: item["score"], reverse=True)
    return matches[:5]


def score_feature(
    proposal: dict[str, Any],
    profile: dict[str, Any] | None,
    feature: dict[str, Any],
    query_tokens: set[str],
    hinted_codes: set[str],
    dceg_index_doc: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    code = feature.get("code")
    exact_hint = code in hinted_codes
    lexical = lexical_score(query_tokens, feature_tokens(feature))
    primitive = primitive_score(profile, feature)
    dceg_evidence = dceg_evidence_for(feature, dceg_index_doc)
    dceg = 1.0 if dceg_evidence else 0.0
    score = min(1.0, (0.55 if exact_hint else 0.0) + lexical * 0.25 + primitive * 0.1 + dceg * 0.1)
    return {
        "feature_code": code,
        "feature_name": feature.get("name"),
        "aliases": feature.get("aliases") or [],
        "primitives": feature.get("primitives") or feature.get("permitted_primitives") or [],
        "score": round(score, 4),
        "confidence": "HIGH" if score >= 0.65 else ("MEDIUM" if score >= 0.4 else "LOW"),
        "basis": {
            "semantic_or_layer_hint": exact_hint,
            "lexical_score": round(lexical, 4),
            "primitive_score": primitive,
            "dceg_score": dceg,
        },
        "dceg_evidence": dceg_evidence,
    }


def match_proposal(
    proposal: dict[str, Any],
    profile: dict[str, Any] | None,
    features: list[dict[str, Any]],
    attributes: list[dict[str, Any]],
    semantic_mappings: dict[str, Any],
    dceg_index_doc: dict[str, list[dict[str, Any]]],
    top_n: int,
) -> dict[str, Any]:
    query = proposal_tokens(proposal, profile)
    hinted = candidate_feature_codes(proposal, semantic_mappings)
    feature_rows = [
        score_feature(proposal, profile, feature, query, hinted, dceg_index_doc)
        for feature in features
    ]
    feature_rows.sort(key=lambda item: item["score"], reverse=True)
    top_features = [item for item in feature_rows if item["score"] > 0][:top_n]
    missing_hint_codes = sorted(code for code in hinted if code not in {feature.get("code") for feature in features})
    top_score = top_features[0]["score"] if top_features else 0.0
    binding = proposal.get("suggested_binding") or {}
    product_candidates = binding.get("product_candidates") or []
    layer_type = binding.get("layer_type")
    s101_applicable = "S-101" in product_candidates and layer_type not in {
        "document_reference",
        "accident_event",
        "hydrographic_observation",
        "unclassified",
    }
    review_required = top_score < 0.65 or bool(missing_hint_codes) or not s101_applicable
    return {
        "proposal_id": proposal["proposal_id"],
        "dataset_id": proposal["dataset_id"],
        "source_asset": proposal["source_asset"],
        "suggested_binding": binding,
        "s101_product_applicable": s101_applicable,
        "top_feature_matches": top_features,
        "top_attribute_matches": attribute_matches(profile, attributes, query),
        "missing_catalogue_hints": missing_hint_codes,
        "match_status": "MATCHED" if top_score >= 0.4 else "NEEDS_REVIEW",
        "review_required": review_required,
        "review_reasons": [
            reason
            for reason, active in [
                ("top_score_below_high_confidence", top_score < 0.65),
                ("catalogue_hint_missing", bool(missing_hint_codes)),
                ("not_primary_s101_layer", not s101_applicable),
            ]
            if active
        ],
        "provenance": {
            "feature_catalogue": "data/s101_feature_dictionary_v2.yaml",
            "attribute_catalogue": "data/s101_attribute_dictionary_v2.yaml",
            "dceg_chunks": "outputs/rag/s101_dceg_chunks.jsonl",
            "proposal_source": "outputs/ontology/ontology_binding_proposals.jsonl",
            "profile_source": "outputs/ontology/dataset_profiles.jsonl",
        },
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="S-101 Feature Catalogue/DCEG 기반 매칭 점수를 계산한다.")
    parser.add_argument("--proposals", type=Path, default=DEFAULT_PROPOSALS)
    parser.add_argument("--profiles", type=Path, default=DEFAULT_PROFILES)
    parser.add_argument("--features", type=Path, default=DATA / "s101_feature_dictionary_v2.yaml")
    parser.add_argument("--attributes", type=Path, default=DATA / "s101_attribute_dictionary_v2.yaml")
    parser.add_argument("--mapping", type=Path, default=DATA / "s100_s101_mapping_registry.yaml")
    parser.add_argument("--dceg-chunks", type=Path, default=ROOT / "outputs" / "rag" / "s101_dceg_chunks.jsonl")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--review", type=Path, default=DEFAULT_REVIEW)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()

    proposals = load_jsonl(args.proposals)
    profiles = {row["dataset_id"]: row for row in load_jsonl(args.profiles)}
    feature_doc = load_json_or_yaml(args.features)
    attribute_doc = load_json_or_yaml(args.attributes)
    mapping_doc = load_json_or_yaml(args.mapping)
    dceg = dceg_index(args.dceg_chunks)

    features = feature_doc.get("features") or []
    attributes = attribute_doc.get("attributes") or []
    semantic_mappings = mapping_doc.get("semantic_mappings") or {}
    rows = [
        match_proposal(
            proposal,
            profiles.get(proposal["dataset_id"]),
            features,
            attributes,
            semantic_mappings,
            dceg,
            args.top_n,
        )
        for proposal in proposals
    ]
    review_rows = [row for row in rows if row["review_required"]]
    summary = {
        "version": "0.1",
        "phase": "8.4",
        "proposal_count": len(rows),
        "matched_count": sum(1 for row in rows if row["match_status"] == "MATCHED"),
        "review_required_count": len(review_rows),
        "high_confidence_count": sum(
            1
            for row in rows
            if row["top_feature_matches"] and row["top_feature_matches"][0]["confidence"] == "HIGH"
        ),
        "medium_confidence_count": sum(
            1
            for row in rows
            if row["top_feature_matches"] and row["top_feature_matches"][0]["confidence"] == "MEDIUM"
        ),
        "low_or_unmatched_count": sum(
            1
            for row in rows
            if not row["top_feature_matches"] or row["top_feature_matches"][0]["confidence"] == "LOW"
        ),
    }

    write_jsonl(args.output, rows)
    write_jsonl(args.review, review_rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({**summary, "output": str(args.output), "review": str(args.review)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
