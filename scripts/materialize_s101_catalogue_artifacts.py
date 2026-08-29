"""Materialize Dictionary inputs from the parsed S-101 Feature Catalogue."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main():
    parsed = json.loads((DATA / "s101_feature_catalogue_v2_parsed.json").read_text(encoding="utf-8"))
    # The S-101 XML uses catalogue codes, while GBENC uses a separate numeric
    # code space. Keep only previously validated mappings; never infer values.
    gbenc_codes = {
        "AnchorageArea": 4, "Fairway": 46, "RestrictedArea": 112,
        "Wreck": 159, "Obstruction": 86, "UnderwaterAwashRock": 153,
        "CableSubmarine": 27, "PipelineSubmarine": 95,
        "MarineFarmCulture": 84, "FishingFacility": 54,
        "BeaconCardinal": 14, "BeaconLateral": 16,
        "BeaconSpecialPurpose": 18, "BuoyCardinal": 21,
        "BuoyLateral": 24, "BuoySpecialPurpose": 26,
        "Landmark": 74, "LandArea": 71, "MooringFacility": 85,
        "TrafficSeparationSchemeLanePart": 129, "DredgedArea": 38,
        "Berth": 10, "HarbourFacility": 64, "MooringWarpingFacility": 86,
    }
    features = []
    for item in parsed["features"]:
        features.append({
            "code": item["code"],
            "nftc": gbenc_codes.get(item["code"]),
            "name": item["name"],
            "definition": item.get("definition"),
            "aliases": item.get("aliases", []),
            "primitives": item.get("permitted_primitives", []),
            "attribute_bindings": item.get("bindings", []),
            "source": item["source"],
        })
    (DATA / "s101_catalogue.json").write_text(json.dumps(features, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "s101_feature_dictionary_v2.yaml").write_text(json.dumps({
        "version": "2.0.0", "source": parsed["metadata"], "features": features
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (DATA / "s101_attribute_dictionary_v2.yaml").write_text(json.dumps({
        "version": "2.0.0", "source": parsed["metadata"], "attributes": parsed["attributes"]
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ROOT / "outputs/reports/15_s101_feature_catalogue_parse_report.md"
    report.write_text(f"""# S-101 Feature Catalogue Parse Report

- Source XML: `{parsed['metadata']['source']}`
- SHA-256: `{parsed['metadata']['sha256']}`
- XML namespace handling: local-name based, namespace aware
- Catalogue version: `{parsed['metadata']['versionNumber']}`
- Feature Types parsed: {len(features)}
- Attributes parsed: {len(parsed['attributes'])}
- Listed value collections: {sum(1 for x in parsed['attributes'] if x.get('listed_values'))}
- Feature geometry declarations: {sum(1 for x in features if x.get('primitives'))}
- Feature/Attribute bindings: {sum(len(x.get('attribute_bindings', [])) for x in features)}

The catalogue code is the standard identifier. GBENC numeric `feature_type_code`
mapping remains a separate DB reconciliation step because the XML does not
contain the database's numeric code column.
""", encoding="utf-8")
    print(json.dumps({"features": len(features), "attributes": len(parsed["attributes"])}))


if __name__ == "__main__":
    main()
