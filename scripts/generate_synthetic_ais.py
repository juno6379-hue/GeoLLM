"""Generate demo AIS tracks from the existing U-Port position proxy response.

The output is synthetic, even when its anchor positions came from the provider.
"""
import argparse
import csv
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

FIELDS = ("MMSI", "observed_at", "longitude", "latitude", "sog_knots", "source_type",
          "mmsiNo", "lat", "lot", "sog", "updtTm")


def anchors_from_response(payload):
    from scripts.audit_uport_eta_pairs import _rows
    anchors = []
    for row in _rows(payload):
        try:
            lat, lon = float(row["lat"]), float(row["lot"])
            sog = float(row.get("sog") or 0)
        except (KeyError, TypeError, ValueError):
            continue
        if -90 <= lat <= 90 and -180 <= lon <= 180 and 0 <= sog <= 50:
            anchors.append((lat, lon, sog, str(row.get("updtTm") or "")))
    return anchors


def generate(output, vessels=3, observations=12, snapshot=None):
    if not 1 <= vessels <= 100 or not 2 <= observations <= 1000:
        raise ValueError("vessels must be 1..100 and observations 2..1000")
    anchors = anchors_from_response(snapshot) if snapshot is not None else []
    if snapshot is not None and not anchors:
        raise ValueError("snapshot has no usable vessel positions")
    if anchors:
        vessels = min(vessels, len(anchors))
    output.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 9, 21)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for vessel in range(vessels):
            anchor_lat, anchor_lon, sog, update = (anchors[vessel] if anchors else
                (35.40 + vessel * 0.012, 129.15 + vessel * 0.015, 8.0 + vessel * 0.5, ""))
            synthetic_mmsi = f"999{vessel:06d}"
            for step in range(observations):
                offset = observations - 1 - step
                lat, lon = anchor_lat + offset * 0.001, anchor_lon - offset * 0.002
                writer.writerow({
                    "MMSI": synthetic_mmsi,
                    "observed_at": (start + timedelta(minutes=10 * step)).isoformat(),
                    "longitude": f"{lon:.6f}", "latitude": f"{lat:.6f}",
                    "sog_knots": f"{sog:.1f}", "source_type": "SYNTHETIC_SIMULATION",
                    "mmsiNo": synthetic_mmsi, "lat": f"{lat:.6f}",
                    "lot": f"{lon:.6f}", "sog": f"{sog:.1f}", "updtTm": update,
                })
    return vessels * observations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--vessels", type=int, default=3)
    parser.add_argument("--observations", type=int, default=12)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--snapshot-json", type=Path)
    source.add_argument("--api-url")
    args = parser.parse_args()
    snapshot = None
    if args.snapshot_json:
        snapshot = json.loads(args.snapshot_json.read_text(encoding="utf-8-sig"))
    elif args.api_url:
        if not args.api_url.startswith(("http://localhost:", "http://127.0.0.1:")):
            parser.error("--api-url must use localhost or 127.0.0.1")
        with urlopen(args.api_url, timeout=10) as response:
            snapshot = json.load(response)
    count = generate(args.output, args.vessels, args.observations, snapshot)
    print(f"Wrote {count} SYNTHETIC_SIMULATION rows to {args.output}")


if __name__ == "__main__":
    main()
