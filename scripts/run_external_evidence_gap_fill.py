"""Run external evidence gap-fill for local spatial evidence misses.

The pipeline is conservative:
1. check local authoritative registries/layers first;
2. expose public authoritative candidates next;
3. expose OSM/RAG candidates as supplemental only;
4. emit promotion candidates that require review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

try:
    import psycopg2
except ImportError:  # pragma: no cover - optional runtime dependency
    psycopg2 = None


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs" / "external_evidence"
REPORTS = ROOT / "outputs" / "reports"
DEFAULT_REGISTRY = DATA / "external_evidence_registry.yaml"
PLACE_REGISTRY = DATA / "place_geometry_registry.yaml"
SPATIAL_REGISTRY = DATA / "spatial_layer_registry.yaml"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def stable_id(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def wkt_point_lon_lat(wkt: str | None) -> tuple[float, float] | None:
    match = re.match(r"\s*POINT\s*\(\s*([0-9.+-]+)\s+([0-9.+-]+)\s*\)\s*$", str(wkt or ""), re.I)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def detect_gap_domain(query: str, registry: dict[str, Any]) -> dict[str, Any] | None:
    lowered = query.lower()
    for domain_id, domain in (registry.get("gap_domains") or {}).items():
        signals = domain.get("query_signals") or []
        if any(str(signal).lower() in lowered for signal in signals):
            return {"domain_id": domain_id, **domain}
    return None


def resolve_anchor_place(query: str, external_registry: dict[str, Any], place_registry: dict[str, Any]) -> dict[str, Any] | None:
    candidates: dict[str, Any] = {}
    for place_id, place in (place_registry.get("places") or {}).items():
        candidates[place_id] = {"place_id": place_id, **place, "source": "data/place_geometry_registry.yaml"}
    for place_id, place in (external_registry.get("places") or {}).items():
        candidates[place_id] = {**candidates.get(place_id, {}), **place, "place_id": place_id, "source": "data/external_evidence_registry.yaml"}

    lowered = query.lower()
    for place in candidates.values():
        aliases = [place.get("canonical_name"), *(place.get("aliases") or [])]
        if any(alias and str(alias).lower() in lowered for alias in aliases):
            lon_lat = wkt_point_lon_lat(place.get("geometry_wkt"))
            return {
                "place_id": place["place_id"],
                "canonical_name": place.get("canonical_name") or place["place_id"],
                "geometry_wkt": place.get("geometry_wkt"),
                "lon": lon_lat[0] if lon_lat else None,
                "lat": lon_lat[1] if lon_lat else None,
                "srid": place.get("srid") or 4326,
                "source": place.get("source"),
            }
    return None


def db_url() -> str:
    return os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL") or "postgresql://postgres:postgres@127.0.0.1:5433/gbhd_s101"


def local_layer_specs(domain: dict[str, Any], spatial_registry: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    layers = spatial_registry.get("layers") or {}
    for layer_id in domain.get("local_layers_checked") or []:
        layer = layers.get(layer_id) or {}
        table = layer.get("physical_table")
        if not table and layer_id == "GBENC_S101_feature":
            table = "projection.s101_feature_current"
        if not table and layer_id.endswith("_current"):
            table = f"serving.{layer_id}"
        if not table and "." in layer_id:
            table = layer_id
        specs.append({
            "layer_id": layer_id,
            "physical_table": table,
            "geometry_column": layer.get("geometry_column") or ("geometry" if table != "projection.s101_feature_current" else "geometry"),
            "execution_status": layer.get("execution_status") or ("executable" if table else "metadata_only"),
            "blocking_match": layer_id in {"protected_sea_area", "serving.protected_area_current"},
        })
    return specs


def check_local_layers(domain: dict[str, Any], anchor: dict[str, Any] | None, spatial_registry: dict[str, Any], radius_m: int, check_db: bool) -> list[dict[str, Any]]:
    checks = []
    for spec in local_layer_specs(domain, spatial_registry):
        result = {
            **spec,
            "radius_m": radius_m,
            "status": "not_checked",
            "match_count": None,
            "reason": None,
        }
        if not anchor:
            result.update({"status": "blocked", "reason": "missing_anchor_place"})
        elif not spec.get("physical_table"):
            result.update({"status": "blocked", "reason": "missing_physical_table"})
        elif not check_db:
            result.update({"status": "declared_check", "reason": "db_check_disabled"})
        elif psycopg2 is None:
            result.update({"status": "blocked", "reason": "psycopg2_not_available"})
        else:
            try:
                with psycopg2.connect(db_url(), connect_timeout=5) as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            f"""
                            SELECT count(*)
                            FROM {spec['physical_table']}
                            WHERE ST_DWithin(
                              {spec['geometry_column']}::geography,
                              ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                              %s
                            )
                            """,
                            (anchor["lon"], anchor["lat"], radius_m),
                        )
                        result.update({"status": "checked", "match_count": int(cur.fetchone()[0])})
            except Exception as exc:  # pragma: no cover - depends on local DB
                result.update({"status": "error", "reason": str(exc)})
        checks.append(result)
    return checks


def local_gap_confirmed(checks: list[dict[str, Any]]) -> bool:
    checked = [row for row in checks if row.get("status") == "checked" and row.get("blocking_match")]
    if not checked:
        return False
    return all(int(row.get("match_count") or 0) == 0 for row in checked)


def external_candidate_generation_allowed(checks: list[dict[str, Any]]) -> bool:
    checked = [row for row in checks if row.get("status") == "checked" and row.get("blocking_match")]
    if any(int(row.get("match_count") or 0) > 0 for row in checked):
        return False
    return True


def public_authoritative_candidates(query: str, domain_id: str, anchor: dict[str, Any] | None, registry: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in registry.get("seed_candidates") or []:
        if item.get("domain") != domain_id:
            continue
        if anchor and item.get("anchor_place_id") != anchor.get("place_id"):
            continue
        geometry = {
            "type": "Point",
            "coordinates": [anchor.get("lon"), anchor.get("lat")] if anchor else None,
            "source": anchor.get("source") if anchor else None,
            "status": item.get("geometry_status") or "needs_review",
            "strategy": item.get("geometry_strategy"),
        }
        payload = {
            "candidate_id": item.get("candidate_id"),
            "query": query,
            "domain": domain_id,
            "name": item.get("name"),
            "category": item.get("category"),
            "anchor": anchor,
            "source_tier": item.get("source_tier"),
            "authority_level": item.get("authority_level"),
            "source_name": item.get("source_name"),
            "authority": item.get("authority"),
            "source_url": item.get("source_url"),
            "geometry": geometry,
            "evidence": {
                "designation": item.get("designation"),
                "designated_on": item.get("designated_on"),
                "area_m2": item.get("area_m2"),
                "location_text": item.get("location_text"),
            },
            "review_required": bool(item.get("review_required", True)),
            "promotion_status": item.get("promotion_status") or "NEEDS_REVIEW",
        }
        rows.append(payload)
    return rows


def osm_supplemental_candidates(query: str, domain_id: str, anchor: dict[str, Any] | None, domain: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in domain.get("osm_candidate_rules") or []:
        payload = {
            "candidate_id": stable_id("extgap.osm_candidate", [query, domain_id, anchor, rule]),
            "query": query,
            "domain": domain_id,
            "name": f"{anchor.get('canonical_name') if anchor else 'unresolved place'} OSM protected-area candidate",
            "category": "supplemental_osm_candidate",
            "anchor": anchor,
            "source_tier": "osm_supplemental",
            "authority_level": "supplemental",
            "source_name": rule.get("source_name"),
            "authority": rule.get("authority"),
            "source_url": "https://www.openstreetmap.org/",
            "geometry": {
                "type": "unknown",
                "coordinates": None,
                "status": "needs_external_fetch",
                "strategy": "overpass_or_nominatim_candidate_only",
            },
            "evidence": {
                "tags": rule.get("tags") or [],
                "use_as_authority": False,
            },
            "review_required": True,
            "promotion_status": "SUPPLEMENTAL_ONLY_NOT_PROMOTABLE",
        }
        rows.append(payload)
    return rows


def promotion_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate.get("authority_level") != "public_authoritative":
            continue
        rows.append({
            "promotion_id": stable_id("extgap.promotion", candidate),
            "candidate_id": candidate.get("candidate_id"),
            "name": candidate.get("name"),
            "target_registry": "data/external_evidence_registry.yaml",
            "target_serving_table": "serving.external_protected_area_candidate",
            "required_reviews": [
                "official_source_url_review",
                "official_polygon_or_boundary_review",
                "authority_metadata_review",
            ],
            "blocked_reason": "official polygon/boundary not yet loaded",
            "promotion_status": "NEEDS_GEOMETRY_REVIEW",
            "source_candidate": candidate,
        })
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, default=str) + "\n" for row in rows), encoding="utf-8")


def write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# External Evidence Gap-Fill Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- query: `{report['query']}`",
        f"- domain: `{report.get('domain_id')}`",
        f"- anchor: `{(report.get('anchor') or {}).get('canonical_name')}`",
        f"- radius_m: `{report['radius_m']}`",
        f"- local_gap_confirmed: `{report['local_gap_confirmed']}`",
        f"- external_candidate_generation_allowed: `{report.get('external_candidate_generation_allowed')}`",
        f"- external_candidate_generation_reason: `{report.get('external_candidate_generation_reason')}`",
        f"- public_authoritative_candidates: `{report['candidate_counts']['public_authoritative']}`",
        f"- supplemental_candidates: `{report['candidate_counts']['supplemental']}`",
        f"- promotion_candidates: `{report['candidate_counts']['promotion']}`",
        "",
        "## Local Checks",
    ]
    for check in report.get("local_checks") or []:
        lines.append(f"- `{check.get('layer_id')}` -> `{check.get('physical_table')}`: `{check.get('status')}`, count=`{check.get('match_count')}`, reason=`{check.get('reason')}`")
    lines.extend(["", "## Candidates"])
    for candidate in report.get("candidates") or []:
        lines.append(f"- `{candidate.get('candidate_id')}` / {candidate.get('name')} / `{candidate.get('authority_level')}` / `{candidate.get('promotion_status')}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_gap_fill(query: str, radius_m: int = 10000, check_db: bool = False) -> dict[str, Any]:
    registry = load_yaml(DEFAULT_REGISTRY)
    place_registry = load_yaml(PLACE_REGISTRY)
    spatial_registry = load_yaml(SPATIAL_REGISTRY)
    domain = detect_gap_domain(query, registry)
    anchor = resolve_anchor_place(query, registry, place_registry)
    if not domain:
        return {
            "status": "BLOCKED_UNSUPPORTED_GAP_DOMAIN",
            "generated_at": utc_now(),
            "query": query,
            "reason": "no gap domain matched",
            "candidates": [],
        }
    local_checks = check_local_layers(domain, anchor, spatial_registry, radius_m, check_db)
    domain_id = domain["domain_id"]
    candidates: list[dict[str, Any]] = []
    allow_external_candidates = external_candidate_generation_allowed(local_checks)
    if allow_external_candidates:
        candidates.extend(public_authoritative_candidates(query, domain_id, anchor, registry))
        candidates.extend(osm_supplemental_candidates(query, domain_id, anchor, domain))
    promotions = promotion_candidates(candidates)
    report = {
        "status": "OK",
        "generated_at": utc_now(),
        "query": query,
        "domain_id": domain_id,
        "domain_label": domain.get("label"),
        "anchor": anchor,
        "radius_m": radius_m,
        "local_checks": local_checks,
        "local_gap_confirmed": local_gap_confirmed(local_checks),
        "external_candidate_generation_allowed": allow_external_candidates,
        "external_candidate_generation_reason": "no_positive_local_match" if allow_external_candidates else "local_authoritative_match_exists",
        "candidate_counts": {
            "total": len(candidates),
            "public_authoritative": sum(1 for item in candidates if item.get("authority_level") == "public_authoritative"),
            "supplemental": sum(1 for item in candidates if item.get("authority_level") == "supplemental"),
            "promotion": len(promotions),
        },
        "candidates": candidates,
        "promotion_candidates": promotions,
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="독도 부근 천연보호구역을 찾아줘")
    parser.add_argument("--radius-m", type=int, default=10000)
    parser.add_argument("--check-db", action="store_true")
    args = parser.parse_args()

    report = run_gap_fill(args.query, radius_m=args.radius_m, check_db=args.check_db)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    write_json(OUTPUTS / "gap_fill_report.json", report)
    write_jsonl(OUTPUTS / "gap_fill_candidates.jsonl", report.get("candidates") or [])
    write_jsonl(OUTPUTS / "promotion_candidates.jsonl", report.get("promotion_candidates") or [])
    write_markdown(REPORTS / "external_evidence_gap_fill.md", report)
    print(json.dumps({
        "status": report.get("status"),
        "query": args.query,
        "domain_id": report.get("domain_id"),
        "candidate_counts": report.get("candidate_counts"),
        "report": "outputs/external_evidence/gap_fill_report.json",
    }, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
