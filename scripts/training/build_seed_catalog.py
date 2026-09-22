from __future__ import annotations

import copy
from pathlib import Path

import yaml

from training.pipeline import ROOT, read_jsonl, registry_snapshot, write_jsonl


def main() -> int:
    template = read_jsonl(ROOT / "training/seeds/canonical_seeds.jsonl")[0]
    output = []
    for path in sorted((ROOT / "training/seed").glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
        domain = document["domain"]
        for spec in document["cases"]:
            row = copy.deepcopy(template)
            row["case_id"] = spec["case_id"]
            row["input"]["user_query"] = spec["query"]
            row["domain_labels"] = [domain]
            row["review_status"] = spec["review_status"]
            row["registry_snapshot"] = registry_snapshot()
            row["lineage"]["generation_batch_id"] = "seed-catalog-v1"
            row["expected_routing"]["required_capabilities"] = [
                "resolver.place_registry",
                "resolver.s101_feature_dictionary",
                "tool.spatial_radius_search",
                "agent.spatial_analysis",
                "ontology.navigation_hazard_object",
            ]
            if spec["review_status"] == "APPROVED":
                row["expected_slots"]["location_text"]["value"] = spec["location"]
                row["expected_slots"]["distance_m"]["value"] = spec["distance_m"]
                row["expected_slots"]["target_term"]["value"] = spec["target_term"]
                row["expected_semantics"]["normalized_query"] = spec["query"]
            if spec["review_status"] != "APPROVED":
                row["quality"]["human_verified"] = False
                row["quality"]["reviewer"] = None
                row["quality"]["review_notes"] = [
                    "Authoring seed only: golden execution labels must be reviewed before expansion."
                ]
            output.append(row)
    target = ROOT / "training/generated/seed_cases.jsonl"
    write_jsonl(target, output)
    print(f"seed_cases={len(output)} approved={sum(r['review_status'] == 'APPROVED' for r in output)} target={target}")
    return 0 if len(output) == 30 else 1


if __name__ == "__main__":
    raise SystemExit(main())
