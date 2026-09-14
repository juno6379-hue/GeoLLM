"""Parse marine terms and gazetteer sources into provenance-aware dictionaries."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
OUT = ROOT / "outputs"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clean(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def relpath(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def coordinate_decimal(value):
    """Convert decimal or D-M-S coordinate text to decimal degrees."""
    raw = clean(value)
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        pass
    match = re.match(r"^\s*(\d+(?:\.\d+)?)\D+(\d+(?:\.\d+)?)?(?:\D+(\d+(?:\.\d+)?))?\D*([NSEW])\s*$", raw, re.I)
    if not match:
        return None
    degrees = float(match.group(1)); minutes = float(match.group(2) or 0); seconds = float(match.group(3) or 0)
    value = degrees + minutes / 60 + seconds / 3600
    return -value if match.group(4).upper() in {"S", "W"} else value


def read_csv_any(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except (UnicodeDecodeError, LookupError):
            continue
    return pd.read_csv(path, encoding_errors="replace", low_memory=False)


def col_for(columns, patterns):
    for col in columns:
        label = clean(col).lower()
        if any(pattern in label for pattern in patterns):
            return col
    return None


TAXONOMY_RULES = [
    ("accident_term", ("사고", "조난", "충돌", "좌초", "침몰", "전복", "화재", "기관손상", "구조")),
    ("law_regulation_term", ("법령", "시행령", "고시", "규칙", "허가", "금지", "제한", "보호구역", "관할")),
    ("place_term", ("해역", "항만", "어항", "항구", "섬", "수역", "앞바다", "연안", "해안")),
    ("traffic_term", ("항로", "통항", "교통", "항행", "ais", "v-pass", "선박")),
    ("hazard_feature_term", ("침선", "난파", "장애물", "암초", "간출암", "노출암", "침석", "위험", "부표", "표지")),
    ("bathymetry_environment_term", ("수심", "조위", "조류", "해류", "파랑", "와류", "갯골", "준설")),
    ("spatial_layer_term", ("양식장", "어초", "어장", "케이블", "투기", "폐기물", "정박", "계선", "등대", "등표")),
]


def classify_term(term: str, definition: str = "", english: str = "") -> str:
    haystack = f"{term} {english}".lower()
    definition_text = definition.lower()
    for category, needles in TAXONOMY_RULES:
        if any(needle.lower() in haystack for needle in needles):
            return category
    for category, needles in TAXONOMY_RULES:
        long_needles = [needle for needle in needles if len(needle) >= 3]
        if any(needle.lower() in definition_text for needle in long_needles):
            return category
    if re.search(r"[A-Za-z]{2,}", english or term):
        return "technology_or_english_term"
    return "maritime_domain"


def catalogue_index(catalogue):
    features = {}
    by_label = {}
    for item in catalogue.get("features", []):
        code = clean(item.get("code"))
        name = clean(item.get("name"))
        if not code:
            continue
        features[code] = {
            "code": code,
            "name": name,
            "definition": clean(item.get("definition")),
            "permitted_primitives": item.get("permitted_primitives", []),
        }
        for label in (code, name):
            if label:
                by_label[label.lower()] = code
    return features, by_label


def catalogue_match(term: str, english: str, features_by_label: dict[str, str]):
    matched = []
    for value in (term, english):
        lowered = clean(value).lower()
        if lowered in features_by_label:
            matched.append(features_by_label[lowered])
    return list(dict.fromkeys(matched))


def feature_mapping(term: str):
    rules = [
        (("침선", "난파", "침몰선", "wreck"), ["Wreck"], ["navigation_hazard_object"], ["navigation_safety", "grounding_risk"]),
        (("장애물", "obstruction"), ["Obstruction"], ["navigation_hazard_object"], ["navigation_safety", "grounding_risk"]),
        (("암초", "간출암", "노출암", "침석", "rock"), ["UnderwaterAwashRock"], ["navigation_hazard_object"], ["navigation_safety", "grounding_risk"]),
        (("해역", "앞바다", "수역", "sea area"), ["SeaAreaNamedWaterArea"], [], ["navigation_safety", "route_planning"]),
        (("정박", "anchorage"), ["AnchorageArea"], [], ["navigation_safety", "route_planning"]),
        (("항로", "fairway", "통항로"), ["Fairway", "TrafficSeparationScheme", "TrafficSeparationSchemeLanePart"], [], ["navigation_safety", "route_planning"]),
        (("제한", "금지", "restricted", "통항 불가", "못 지나"), ["RestrictedArea", "TrafficSeparationScheme", "TrafficSeparationSchemeLanePart"], ["restricted_navigation_area", "navigation_hazard_area"], ["navigation_safety", "route_planning"]),
    ]
    for needles, features, concepts, contexts in rules:
        if any(x in term.lower() for x in needles):
            return features, concepts, contexts
    return [], [], ["maritime_domain"]


def parse_terms(path: Path, catalogue):
    result = {}
    feature_meta, features_by_label = catalogue_index(catalogue)
    workbook = pd.ExcelFile(path)
    for sheet in workbook.sheet_names:
        frame = pd.read_excel(path, sheet_name=sheet, dtype=str).fillna("")
        term_col = col_for(frame.columns, ("용어", "국문", "한글", "명칭", "term", "name")) or frame.columns[0]
        eng_col = col_for(frame.columns, ("영문", "영어", "english", "eng"))
        definition_col = col_for(frame.columns, ("정의", "설명", "definition", "description"))
        synonym_col = col_for(frame.columns, ("동의어", "synonym", "alias"))
        for _, row in frame.iterrows():
            term = clean(row.get(term_col))
            if not term or len(term) > 200:
                continue
            english = clean(row.get(eng_col)) if eng_col else ""
            definition = clean(row.get(definition_col)) if definition_col else ""
            features, concepts, contexts = feature_mapping(term)
            features = list(dict.fromkeys(features + catalogue_match(term, english, features_by_label)))
            taxonomy_class = classify_term(term, definition, english)
            verification_status = "CANDIDATE" if features or concepts else "UNMAPPED"
            if term == "침석":
                verification_status = "NEEDS_REVIEW"
            key = re.sub(r"[^0-9A-Za-z가-힣]+", "_", term).strip("_") or "term"
            entry = result.setdefault(key, {
                "canonical_term": term, "aliases": [], "definitions": [],
                "maps_to_features": features, "maps_to_concepts": concepts,
                "contexts": contexts,
                "taxonomy_class": taxonomy_class,
                "verification_status": verification_status,
                "s101_feature_catalogue": {},
                "source_records": [],
                "provenance": {"source_path": relpath(path), "source_sha256": sha256(path)},
            })
            for feature in features:
                if feature in feature_meta:
                    entry["s101_feature_catalogue"][feature] = feature_meta[feature]
            synonym_values = re.split(r"[,;/]", clean(row.get(synonym_col)) if synonym_col else "")
            for value in [english, term] + [clean(item) for item in synonym_values]:
                if value and value != entry["canonical_term"] and value not in entry["aliases"]:
                    entry["aliases"].append(value)
            if definition and definition not in entry["definitions"]:
                entry["definitions"].append(definition)
            entry["source_records"].append({"sheet": sheet, "row": int(row.name) + 2})
    # Add explicit operational terms even when the source workbook has no row.
    for term, features, concepts, contexts in [
        ("침선", ["Wreck"], ["navigation_hazard_object"], ["navigation_safety", "grounding_risk"]),
        ("간출암", ["UnderwaterAwashRock"], ["navigation_hazard_object"], ["navigation_safety", "grounding_risk"]),
        ("노출암", ["UnderwaterAwashRock"], ["navigation_hazard_object"], ["navigation_safety", "grounding_risk"]),
        ("침석", ["UnderwaterAwashRock"], ["navigation_hazard_object"], ["navigation_safety", "grounding_risk"]),
        ("해역", ["SeaAreaNamedWaterArea"], [], ["navigation_safety", "route_planning"]),
        ("배가 못 지나가는 곳", ["RestrictedArea", "TrafficSeparationScheme"], ["restricted_navigation_area", "navigation_hazard_area"], ["navigation_safety", "route_planning"]),
    ]:
        key = re.sub(r"[^0-9A-Za-z가-힣]+", "_", term).strip("_")
        result.setdefault(key, {"canonical_term": term, "aliases": [], "definitions": [], "maps_to_features": features, "maps_to_concepts": concepts, "contexts": contexts, "taxonomy_class": classify_term(term), "verification_status": "NEEDS_REVIEW" if term == "침석" else "CANDIDATE", "source_records": [], "provenance": {"source_path": relpath(path), "source_sha256": sha256(path), "derived_from": "operational vocabulary"}})
    return result


def parse_gazetteer(csv_path: Path, island_zip: Path):
    places = []
    frame = read_csv_any(csv_path)
    name_col = col_for(frame.columns, ("지명", "명칭", "name", "명")) or frame.columns[0]
    eng_col = col_for(frame.columns, ("영문", "english", "eng"))
    lon_col = col_for(frame.columns, ("경도", "longitude", "lon", "x"))
    lat_col = col_for(frame.columns, ("위도", "latitude", "lat", "y"))
    type_col = col_for(frame.columns, ("유형", "종류", "type", "구분"))
    for idx, row in frame.iterrows():
        name = clean(row.get(name_col))
        if not name:
            continue
        lon_raw = clean(row.get(lon_col)) if lon_col else ""
        lat_raw = clean(row.get(lat_col)) if lat_col else ""
        lon = coordinate_decimal(lon_raw); lat = coordinate_decimal(lat_raw)
        places.append({"place_id": f"marine_name:{idx + 1}", "name_ko": name, "name_en": clean(row.get(eng_col)) if eng_col else "", "place_type": clean(row.get(type_col)) if type_col else "marine_name", "longitude": lon, "latitude": lat, "coordinate_raw": {"longitude": lon_raw, "latitude": lat_raw}, "geometry_status": "POINT" if lon is not None and lat is not None else "ATTRIBUTE_ONLY", "provenance": {"source_path": relpath(csv_path), "source_sha256": sha256(csv_path), "row": int(idx) + 2}})
    with zipfile.ZipFile(island_zip) as z:
        z.extractall(OUT / "staging/island_gazetteer")
    try:
        import geopandas as gpd
        shp = next((OUT / "staging/island_gazetteer").glob("*.shp"))
        island_frame = gpd.read_file(shp)
        if island_frame.crs:
            island_frame = island_frame.to_crs("EPSG:4326")
        for idx, row in island_frame.iterrows():
            geom = row.geometry
            centroid = geom.centroid if geom is not None else None
            props = {clean(k): clean(v) for k, v in row.items() if k != "geometry" and clean(v)}
            name = next((v for k, v in props.items() if any(x in k.lower() for x in ("name", "지명", "명칭"))), f"island_{idx + 1}")
            places.append({"place_id": f"island:{idx + 1}", "name_ko": name, "name_en": "", "place_type": "island", "longitude": float(centroid.x) if centroid else None, "latitude": float(centroid.y) if centroid else None, "geometry_type": geom.geom_type if geom is not None else None, "properties": props, "geometry_status": "POLYGON", "provenance": {"source_path": relpath(island_zip), "source_sha256": sha256(island_zip), "member": shp.name, "row": int(idx) + 1, "crs": "EPSG:4326"}})
    except ImportError:
        places.append({"place_id": "island_gazetteer:archive", "name_ko": "도서지명", "name_en": "", "place_type": "island_archive", "geometry_status": "ARCHIVE_ONLY", "provenance": {"source_path": relpath(island_zip), "source_sha256": sha256(island_zip), "parser_status": "geopandas_missing"}})
    return places


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--terms", type=Path, default=DATASET / "용어사전.xls")
    ap.add_argument("--names", type=Path, default=DATASET / "해양수산부_공동활용체계_해양지명_20221231.csv")
    ap.add_argument("--islands", type=Path, default=DATASET / "도서지명.zip")
    args = ap.parse_args()
    catalogue = json.loads((ROOT / "data/s101_feature_catalogue_v2_parsed.json").read_text(encoding="utf-8"))
    terms = parse_terms(args.terms, catalogue)
    places = parse_gazetteer(args.names, args.islands)
    out_dict = OUT / "dictionaries"; out_graph = OUT / "graph"; out_dict.mkdir(parents=True, exist_ok=True); out_graph.mkdir(parents=True, exist_ok=True)
    (OUT / "review").mkdir(parents=True, exist_ok=True)
    taxonomy_counts = Counter(v.get("taxonomy_class", "maritime_domain") for v in terms.values())
    review_classes = {"hazard_feature_term", "spatial_layer_term", "accident_term", "traffic_term", "bathymetry_environment_term", "law_regulation_term", "place_term"}
    needs_review = [
        {
            "review_id": f"term_review:{key}",
            "term_key": key,
            "term": value.get("canonical_term"),
            "reason": "unmapped_or_marked_for_review",
            "taxonomy_class": value.get("taxonomy_class"),
            "verification_status": value.get("verification_status"),
            "provenance": value.get("provenance"),
        }
        for key, value in terms.items()
        if value.get("verification_status") == "NEEDS_REVIEW" or (value.get("verification_status") == "UNMAPPED" and value.get("taxonomy_class") in review_classes)
    ]
    (out_dict / "marine_term_dictionary.yaml").write_text(yaml.safe_dump({"version": "3.0", "source": [str(args.terms), "data/s101_feature_catalogue_v2_parsed.json", "data/derived_concept_registry_v2.yaml"], "term_count": len(terms), "terms": terms}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (out_dict / "marine_term_taxonomy.yaml").write_text(yaml.safe_dump({"version": "3.0", "source": "Dataset/용어사전.xls", "taxonomy_counts": dict(taxonomy_counts), "classes": sorted(taxonomy_counts)}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (OUT / "review/kg_needs_review.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in needs_review), encoding="utf-8")
    (out_dict / "location_gazetteer.yaml").write_text(yaml.safe_dump({"version": "3.0", "sources": [relpath(args.names), relpath(args.islands)], "place_count": len(places), "places": places}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    (out_graph / "nodes_marine_terms.jsonl").write_text("".join(json.dumps({"id": f"marine_term:{k}", "node_type": "MarineTerm", "name": v["canonical_term"], "properties": v, "provenance": v["provenance"]}, ensure_ascii=False) + "\n" for k, v in terms.items()), encoding="utf-8")
    (out_graph / "nodes_term_taxonomy.jsonl").write_text("".join(json.dumps({"id": f"taxonomy:{name}", "node_type": "TaxonomyClass", "name": name, "properties": {"term_count": count}, "provenance": {"source_path": relpath(args.terms), "generator": "scripts/parse_marine_terms_gazetteer.py"}}, ensure_ascii=False) + "\n" for name, count in sorted(taxonomy_counts.items())), encoding="utf-8")
    (out_graph / "nodes_places.jsonl").write_text("".join(json.dumps({"id": p["place_id"], "node_type": "Place", "name": p["name_ko"], "properties": p, "provenance": p["provenance"]}, ensure_ascii=False) + "\n" for p in places), encoding="utf-8")
    term_feature = []; term_concept = []
    term_taxonomy = []
    for key, value in terms.items():
        source = f"marine_term:{key}"
        for feature in value["maps_to_features"]:
            term_feature.append({"id": f"{source}|mapsToFeature|{feature}", "subject_id": source, "predicate": "mapsToFeature", "object_id": f"feature:{feature.lower()}", "provenance": value["provenance"]})
        for concept in value["maps_to_concepts"]:
            term_concept.append({"id": f"{source}|mapsToConcept|{concept}", "subject_id": source, "predicate": "mapsToConcept", "object_id": f"derived_concept:{concept}", "provenance": value["provenance"]})
        taxonomy = value.get("taxonomy_class", "maritime_domain")
        term_taxonomy.append({"id": f"taxonomy:{taxonomy}|classifiesTerm|{source}", "subject_id": f"taxonomy:{taxonomy}", "predicate": "classifiesTerm", "object_id": source, "provenance": value["provenance"]})
    (out_graph / "edges_term_maps_to_feature.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in term_feature), encoding="utf-8")
    (out_graph / "edges_term_maps_to_concept.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in term_concept), encoding="utf-8")
    (out_graph / "edges_term_taxonomy.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in term_taxonomy), encoding="utf-8")
    report = OUT / "reports/08_marine_terms_gazetteer.md"
    report.write_text(f"""# Marine Terms and Gazetteer

## Sources

- Term workbook: `{relpath(args.terms)}`
- Marine names CSV: `{relpath(args.names)}`
- Island names Shapefile ZIP: `{relpath(args.islands)}`
- S-101 catalogue enrichment: `data/s101_feature_catalogue_v2_parsed.json`

## Results

- Marine terms: {len(terms)}
- Marine/place CSV records: {sum(1 for p in places if p['place_id'].startswith('marine_name:'))}
- Island polygon records: {sum(1 for p in places if p['place_id'].startswith('island:'))}
- Term-to-Feature edges: {len(term_feature)}
- Term-to-Concept edges: {len(term_concept)}
- Term taxonomy classes: {len(taxonomy_counts)}
- Review queue records: {len(needs_review)}
- Point places: {sum(1 for p in places if p['geometry_status'] == 'POINT')}
- Polygon places: {sum(1 for p in places if p['geometry_status'] == 'POLYGON')}

Each record retains source path, source hash, and source row/member information.
Feature and concept mappings are rule-based and catalogue-backed; unmapped terms
remain in the dictionary without invented semantics.
""", encoding="utf-8")
    print(json.dumps({"terms": len(terms), "places": len(places), "feature_edges": len(term_feature), "concept_edges": len(term_concept), "taxonomy_classes": len(taxonomy_counts), "needs_review": len(needs_review)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
