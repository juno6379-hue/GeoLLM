"""Reconcile the parsed S-101 catalogue with the restored v2 DB inventory."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"

# This is an explicit, reviewed bridge between catalogue identifiers and the
# GBENC numeric code space. Unknown numeric codes remain DB_ONLY.
GBENC_CODES = {
    "AnchorageArea": 4, "Fairway": 46, "RestrictedArea": 112,
    "Wreck": 159, "Obstruction": 86, "UnderwaterAwashRock": 153,
    "CableSubmarine": 27, "PipelineSubmarine": 95, "MarineFarmCulture": 84,
    "FishingFacility": 54, "BeaconCardinal": 14, "BeaconLateral": 16,
    "BeaconSpecialPurpose": 18, "BuoyCardinal": 21, "BuoyLateral": 24,
    "BuoySpecialPurpose": 26, "Landmark": 74, "LandArea": 71,
    "MooringFacility": 85, "TrafficSeparationSchemeLanePart": 129,
    "DredgedArea": 38, "Berth": 10, "HarbourFacility": 64,
    "MooringWarpingFacility": 86,
}


def geometry_primitives(value):
    result = set()
    for item in (value or "").split(","):
        item = item.lower().strip()
        if item in {"point", "multipoint"}:
            result.add("point")
        elif item in {"linestring", "multilinestring", "curve"}:
            result.add("curve")
        elif item in {"polygon", "multipolygon", "surface"}:
            result.add("surface")
        elif item:
            result.add(item)
    return result


def main():
    parsed = json.loads((DATA / "s101_feature_catalogue_v2_parsed.json").read_text(encoding="utf-8"))
    catalogue = {x["code"]: x for x in parsed["features"]}
    with (OUT / "inventories/v2_feature_type_summary.csv").open(encoding="utf-8-sig", newline="") as f:
        db_rows = {int(x["feature_type_code"]): x for x in csv.DictReader(f)}

    rows = []
    edges = []
    mapped_codes = set()
    for code, item in catalogue.items():
        db_code = GBENC_CODES.get(code)
        db = db_rows.get(db_code) if db_code is not None else None
        if not db:
            status = "S101_ONLY"
            reason = "No explicit S-101 catalogue-code to GBENC numeric-code mapping"
            db_code = ""
        else:
            mapped_codes.add(db_code)
            s101_geom = {str(x).lower() for x in item.get("permitted_primitives", [])}
            db_geom = geometry_primitives(db.get("geometry_types"))
            if not db_geom or not (db_geom & s101_geom):
                status = "GEOMETRY_MISMATCH"
                reason = "DB geometry primitive is not permitted by the S-101 catalogue"
            elif int(db.get("attribute_value_count") or 0) == 0 and item.get("bindings"):
                status = "ATTRIBUTE_MISMATCH"
                reason = "S-101 attribute bindings have no DB attribute values"
            elif item.get("bindings"):
                status = "NEEDS_REVIEW"
                reason = "DB attribute values exist, but binding-level name/value reconciliation is pending"
            else:
                status = "MATCHED"
                reason = "Explicit code mapping and compatible geometry"
            edges.append({
                "subject_id": f"feature:{code.lower()}",
                "predicate": "storedIn",
                "object_id": "datalayer:gbenc_s101_feature",
                "properties": {"status": status, "db_feature_type_code": db_code},
                "provenance": {"catalogue": "data/s101_feature_catalogue_v2_parsed.json", "db": "outputs/inventories/v2_feature_inventory.csv"},
            })
        rows.append({
            "status": status, "s101_code": code, "s101_name": item.get("name"),
            "s101_aliases": "|".join(item.get("aliases", [])),
            "db_feature_type_code": db_code,
            "db_feature_count": db.get("feature_count", "") if db else "",
            "s101_primitives": "|".join(item.get("permitted_primitives", [])),
            "db_geometry_types": db.get("geometry_types", "") if db else "",
            "s101_attribute_binding_count": len(item.get("bindings", [])),
            "db_attribute_value_count": db.get("attribute_value_count", "") if db else "",
            "reason": reason,
            "provenance": "data/s101_feature_catalogue_v2_parsed.json;outputs/inventories/v2_feature_type_summary.csv",
        })

    for db_code, db in db_rows.items():
        if db_code in mapped_codes:
            continue
        rows.append({
            "status": "DB_ONLY", "s101_code": "", "s101_name": "", "s101_aliases": "",
            "db_feature_type_code": db_code, "db_feature_count": db["feature_count"],
            "s101_primitives": "", "db_geometry_types": db["geometry_types"],
            "s101_attribute_binding_count": "", "db_attribute_value_count": db.get("attribute_value_count", ""),
            "reason": "DB numeric Feature Type has no explicit catalogue mapping",
            "provenance": "outputs/inventories/v2_feature_type_summary.csv",
        })

    mapping_path = OUT / "mappings/v2_s101_db_feature_mapping.csv"
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with mapping_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(sorted(rows, key=lambda x: (x["status"], x["s101_code"], str(x["db_feature_type_code"]))))
    edge_path = OUT / "graph/edges_feature_stored_in_db.jsonl"
    edge_path.parent.mkdir(parents=True, exist_ok=True)
    edge_path.write_text("".join(json.dumps({"id": f"{e['subject_id']}|storedIn|{e['object_id']}", **e}, ensure_ascii=False) + "\n" for e in edges), encoding="utf-8")

    counts = {}
    for row in rows: counts[row["status"]] = counts.get(row["status"], 0) + 1
    report = OUT / "reports/06_s101_db_gap_report.md"
    report.write_text("# S-101 v2.0 vs Restored DB Feature Gap Report\n\n" +
        "## Reconciliation basis\n\n" +
        "The S-101 XML uses catalogue codes; the database uses numeric `feature_type_code`. "
        "Only explicit reviewed mappings are used. Unknown codes are not inferred.\n\n" +
        "- Catalogue source: `data/s101_feature_catalogue_v2_parsed.json`\n" +
        "- DB source: `projection.s101_feature_current`\n" +
        f"- Catalogue Feature Types: {len(catalogue)}\n- DB Feature Types: {len(db_rows)}\n- DB Feature Instances: {sum(int(x['feature_count']) for x in db_rows.values())}\n\n" +
        "## Status counts\n\n" + "\n".join(f"- `{k}`: {v}" for k, v in sorted(counts.items())) + "\n\n" +
        "## Interpretation\n\n" +
        "`S101_ONLY` and `DB_ONLY` identify code-space gaps. `NEEDS_REVIEW` means "
        "geometry is compatible but binding-level attribute reconciliation is not yet proven. "
        "No NAME_MISMATCH or VERIFIED relation is created without source evidence.\n",
        encoding="utf-8")
    print(json.dumps({"statuses": counts, "mapping": str(mapping_path), "edges": len(edges)}))


if __name__ == "__main__": main()
