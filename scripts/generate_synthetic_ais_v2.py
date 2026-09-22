"""Generate reproducible multi-voyage AIS simulations for ETA pipeline tests."""

import argparse
import csv
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

SOURCE = "SYNTHETIC_SIMULATION"
SCENARIOS = ("NORMAL_APPROACH", "SLOWDOWN", "ANCHORAGE_WAIT", "OBSERVATION_GAP", "POSITION_NOISE")
FIELDS = (
    "MMSI", "voyage_id", "port_id", "observed_at", "received_at", "arrival_at",
    "minutes_to_arrival", "longitude", "latitude", "sog_knots", "cog_degrees",
    "heading_degrees", "navigation_status", "vessel_type", "scenario", "quality_flag",
    "source_type", "dataset_id", "mmsiNo", "lat", "lot", "sog", "updtTm",
)


def _progress(step, count, scenario):
    value = step / (count - 1)
    if scenario == "SLOWDOWN":
        return 1 - (1 - value) ** 1.35
    if scenario == "ANCHORAGE_WAIT" and 0.48 <= value <= 0.68:
        return 0.58
    if scenario == "ANCHORAGE_WAIT" and value > 0.68:
        return 0.58 + (value - 0.68) / 0.32 * 0.42
    return value


def _voyage(vessel, voyage, count, rng, dataset_id, port_id):
    scenario = SCENARIOS[(vessel + voyage) % len(SCENARIOS)]
    vessel_type = ("CONTAINER", "TANKER", "BULK_CARRIER", "GENERAL_CARGO")[vessel % 4]
    mmsi = f"999{vessel:06d}"
    start = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(days=vessel * 4 + voyage)
    voyage_id = f"SYN-{start:%Y%m%d}-{mmsi}-{voyage + 1:02d}"
    cadence = 10 + voyage % 3 * 5
    times, current = [], start
    for step in range(count):
        times.append(current)
        multiplier = 6 if scenario == "OBSERVATION_GAP" and step == count // 2 else 1
        current += timedelta(minutes=cadence * multiplier)
    arrival = times[-1] + timedelta(minutes=30 + (vessel * 7 + voyage * 13) % 91)
    end_lat, end_lon = 35.50 + vessel % 5 * 0.006, 129.38 + vessel % 7 * 0.006
    start_lat, start_lon = end_lat - 0.18 - vessel % 5 * 0.012, end_lon + (-0.22 if vessel % 2 else 0.22)
    for step, observed in enumerate(times):
        progress = _progress(step, count, scenario)
        curve = math.sin(progress * math.pi) * (0.012 if vessel % 2 else -0.012)
        lat = start_lat + (end_lat - start_lat) * progress + curve
        lon = start_lon + (end_lon - start_lon) * progress - curve * 0.7
        quality = "OK"
        if scenario == "POSITION_NOISE" and step % 9 == 4:
            lat += rng.uniform(-0.006, 0.006)
            lon += rng.uniform(-0.006, 0.006)
            quality = "INJECTED_POSITION_NOISE"
        elif scenario == "OBSERVATION_GAP" and step == count // 2 + 1:
            quality = "AFTER_INJECTED_GAP"
        base_speed = 7 + vessel % 9
        speed = base_speed * (1 - 0.55 * progress) + rng.uniform(-0.35, 0.35)
        if scenario == "SLOWDOWN" and progress > 0.55:
            speed *= 0.45
        if scenario == "ANCHORAGE_WAIT" and 0.55 <= progress <= 0.65:
            speed, quality = 0.15, "SYNTHETIC_ANCHORAGE"
        speed = max(0.0, speed)
        bearing = (315 if start_lon > end_lon else 45) + rng.uniform(-2, 2)
        received = observed + timedelta(seconds=rng.randint(3, 90))
        yield {
            "MMSI": mmsi, "voyage_id": voyage_id, "port_id": port_id,
            "observed_at": observed.isoformat().replace("+00:00", "Z"),
            "received_at": received.isoformat().replace("+00:00", "Z"),
            "arrival_at": arrival.isoformat().replace("+00:00", "Z"),
            "minutes_to_arrival": int((arrival - observed).total_seconds() / 60),
            "longitude": f"{lon:.6f}", "latitude": f"{lat:.6f}",
            "sog_knots": f"{speed:.2f}", "cog_degrees": f"{bearing % 360:.1f}",
            "heading_degrees": round(bearing) % 360,
            "navigation_status": "AT_ANCHOR" if speed < 0.5 else ("MANEUVERING" if speed < 4 else "UNDER_WAY"),
            "vessel_type": vessel_type, "scenario": scenario, "quality_flag": quality,
            "source_type": SOURCE, "dataset_id": dataset_id, "mmsiNo": mmsi,
            "lat": f"{lat:.6f}", "lot": f"{lon:.6f}", "sog": f"{speed:.2f}", "updtTm": "",
        }


def generate(output, vessels=30, voyages_per_vessel=2, observations=48,
             seed=20260922, dataset_id="uport-synthetic-ais-v2", port_id="KRUSN"):
    if not 1 <= vessels <= 1000 or not 1 <= voyages_per_vessel <= 100 or not 4 <= observations <= 1000:
        raise ValueError("vessels 1..1000, voyages 1..100, observations 4..1000 required")
    output, rng = Path(output), random.Random(seed)
    output.parent.mkdir(parents=True, exist_ok=True)
    scenarios = {name: 0 for name in SCENARIOS}
    rows = 0
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for vessel in range(vessels):
            for voyage in range(voyages_per_vessel):
                batch = list(_voyage(vessel, voyage, observations, rng, dataset_id, port_id))
                writer.writerows(batch)
                scenarios[batch[0]["scenario"]] += 1
                rows += len(batch)
    manifest = {
        "dataset_id": dataset_id, "source_type": SOURCE, "generator_version": 2,
        "seed": seed, "port_id": port_id, "vessels": vessels,
        "voyages": vessels * voyages_per_vessel, "observations_per_voyage": observations,
        "rows": rows, "scenarios": scenarios, "operational_use_allowed": False,
        "purpose": "engineering and model-pipeline testing only",
    }
    output.with_suffix(output.suffix + ".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--vessels", type=int, default=30)
    parser.add_argument("--voyages-per-vessel", type=int, default=2)
    parser.add_argument("--observations", type=int, default=48)
    parser.add_argument("--seed", type=int, default=20260922)
    parser.add_argument("--dataset-id", default="uport-synthetic-ais-v2")
    parser.add_argument("--port-id", default="KRUSN")
    args = parser.parse_args()
    result = generate(args.output, args.vessels, args.voyages_per_vessel,
                      args.observations, args.seed, args.dataset_id, args.port_id)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
