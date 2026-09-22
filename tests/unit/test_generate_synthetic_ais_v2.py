import csv
import json
from datetime import datetime

from scripts.generate_synthetic_ais_v2 import SCENARIOS, generate


def test_reproducible_labeled_multi_voyage_dataset(tmp_path):
    first, second = tmp_path / "first.csv", tmp_path / "second.csv"
    result = generate(first, vessels=5, voyages_per_vessel=2, observations=12, seed=7)
    generate(second, vessels=5, voyages_per_vessel=2, observations=12, seed=7)
    assert result["rows"] == 120
    assert first.read_bytes() == second.read_bytes()
    rows = list(csv.DictReader(first.open(encoding="utf-8")))
    assert len({row["voyage_id"] for row in rows}) == 10
    assert {row["scenario"] for row in rows} == set(SCENARIOS)
    assert {row["source_type"] for row in rows} == {"SYNTHETIC_SIMULATION"}
    assert all(datetime.fromisoformat(row["observed_at"].replace("Z", "+00:00")).tzinfo for row in rows)
    assert all(int(row["minutes_to_arrival"]) > 0 for row in rows)
    manifest = json.loads(first.with_suffix(".csv.manifest.json").read_text(encoding="utf-8"))
    assert manifest["operational_use_allowed"] is False
