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
import urllib.error
import urllib.parse
import urllib.request
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
OSM_CACHE = OUTPUTS / "cache" / "osm"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def stable_id(prefix: str, payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:16]}"


def read_json_cache(path: Path) -> Any | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def write_json_cache(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def fetch_json_url(url: str, user_agent: str, timeout_sec: int = 20) -> Any:
    req = urllib.request.Request(url, headers={
        "User-Agent": user_agent,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout_sec) as response:
        return json.load(response)


def post_json_url(url: str, body: str, user_agent: str, timeout_sec: int = 30) -> Any:
    req = urllib.request.Request(
        url,
        data=body.encode("utf-8"),
        headers={
            "User-Agent": user_agent,
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as response:
        return json.load(response)


def wkt_point_lon_lat(wkt: str | None) -> tuple[float, float] | None:
    match = re.match(r"\s*POINT\s*\(\s*([0-9.+-]+)\s+([0-9.+-]+)\s*\)\s*$", str(wkt or ""), re.I)
    if not match:
        return None
    return float(match.group(1)), float(match.group(2))


def detect_gap_domain(query: str, registry: dict[str, Any]) -> dict[str, Any] | None:
    lowered = query.lower()
    for domain_id, domain in (registry.get("gap_domains") or {}).items():
        signals = domain.get("query_signals") or []
        for signal in signals:
            signal_text = str(signal)
            if signal_text.startswith("regex:"):
                if re.search(signal_text.removeprefix("regex:"), query, re.I):
                    return {"domain_id": domain_id, **domain}
                continue
            if signal_text.lower() in lowered:
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
        if not table and layer_id == "marine_gazetteer":
            table = "public.maritime_gazetteer_khoa"
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
        names = [item.get("name"), *(item.get("aliases") or [])]
        if not any(name and str(name).lower() in query.lower() for name in names):
            if not anchor or item.get("anchor_place_id") != anchor.get("place_id"):
                continue
        if anchor and item.get("anchor_place_id") != anchor.get("place_id"):
            continue
        item_geometry = item.get("geometry") if isinstance(item.get("geometry"), dict) else {}
        coordinates = item_geometry.get("coordinates")
        if not coordinates and anchor:
            coordinates = [anchor.get("lon"), anchor.get("lat")]
        geometry = {
            "type": item_geometry.get("type") or "Point",
            "coordinates": coordinates,
            "source": anchor.get("source") if anchor else item.get("source_name"),
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
                "description": item.get("description"),
            },
            "review_required": bool(item.get("review_required", True)),
            "promotion_status": item.get("promotion_status") or "NEEDS_REVIEW",
        }
        rows.append(payload)
    return rows


def osm_supplemental_candidates(query: str, domain_id: str, anchor: dict[str, Any] | None, domain: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rule in domain.get("osm_candidate_rules") or []:
        is_admin_place = domain_id == "administrative_place_lookup"
        payload = {
            "candidate_id": stable_id("extgap.osm_candidate", [query, domain_id, anchor, rule]),
            "query": query,
            "domain": domain_id,
            "name": f"{anchor.get('canonical_name') if anchor else query} OSM {'administrative-place' if is_admin_place else 'protected-area'} candidate",
            "category": "supplemental_osm_administrative_candidate" if is_admin_place else "supplemental_osm_candidate",
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


def nominatim_candidate_query(query: str, anchor: dict[str, Any] | None, domain: dict[str, Any]) -> str:
    if anchor and domain.get("domain_id") == "natural_heritage_protected_area":
        return f"{anchor.get('canonical_name')} 천연보호구역"
    return query


def fetch_osm_live_candidates(query: str, domain_id: str, anchor: dict[str, Any] | None, domain: dict[str, Any], radius_m: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    user_agent = os.getenv("GEOLLM_OSM_USER_AGENT")
    if not user_agent:
        return [], {
            "enabled": True,
            "status": "blocked",
            "reason": "GEOLLM_OSM_USER_AGENT is required by OSM/Nominatim usage policy",
        }

    cache_key = stable_id("osm_fetch", [query, domain_id, anchor, radius_m])
    cache_path = OSM_CACHE / f"{cache_key.replace(':', '_')}.json"
    cached = read_json_cache(cache_path)
    if cached:
        return cached.get("candidates") or [], {**(cached.get("diagnostics") or {}), "cache_hit": True}

    diagnostics: dict[str, Any] = {
        "enabled": True,
        "status": "OK",
        "cache_hit": False,
        "policy": {
            "nominatim": "max 1 request/sec, valid User-Agent or Referer, cache results, no autocomplete or bulk geocoding",
            "overpass": "small supplemental queries only; cache and rate-limit; use self-hosted/paid service for regular use",
        },
    }
    candidates: list[dict[str, Any]] = []
    try:
        search_query = nominatim_candidate_query(query, anchor, domain)
        params = urllib.parse.urlencode({
            "format": "jsonv2",
            "q": search_query,
            "limit": "5",
            "addressdetails": "1",
            "extratags": "1",
            "polygon_geojson": "1",
        })
        nominatim_url = f"https://nominatim.openstreetmap.org/search?{params}"
        nominatim_rows = fetch_json_url(nominatim_url, user_agent)
        diagnostics["nominatim_result_count"] = len(nominatim_rows) if isinstance(nominatim_rows, list) else 0
        for row in nominatim_rows if isinstance(nominatim_rows, list) else []:
            name = row.get("display_name") or row.get("name") or search_query
            candidates.append({
                "candidate_id": stable_id("extgap.osm_nominatim", row),
                "query": query,
                "domain": domain_id,
                "name": name,
                "category": "supplemental_osm_nominatim_candidate",
                "anchor": anchor,
                "source_tier": "osm_supplemental",
                "authority_level": "supplemental",
                "source_name": "OpenStreetMap Nominatim",
                "authority": "OpenStreetMap contributors",
                "source_url": "https://nominatim.openstreetmap.org/",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["lon"]), float(row["lat"])] if row.get("lon") and row.get("lat") else None,
                    "status": "osm_candidate_unverified",
                    "strategy": "nominatim_search_candidate",
                    "geojson": row.get("geojson"),
                },
                "evidence": {
                    "osm_type": row.get("osm_type"),
                    "osm_id": row.get("osm_id"),
                    "class": row.get("class"),
                    "type": row.get("type"),
                    "importance": row.get("importance"),
                    "address": row.get("address"),
                    "extratags": row.get("extratags"),
                    "use_as_authority": False,
                },
                "review_required": True,
                "promotion_status": "SUPPLEMENTAL_ONLY_NOT_PROMOTABLE",
            })

        if anchor and anchor.get("lat") is not None and anchor.get("lon") is not None:
            overpass_query = "\n".join([
                "[out:json][timeout:25];",
                "(",
                f'  node(around:{radius_m},{anchor["lat"]},{anchor["lon"]})["boundary"="protected_area"];',
                f'  way(around:{radius_m},{anchor["lat"]},{anchor["lon"]})["boundary"="protected_area"];',
                f'  relation(around:{radius_m},{anchor["lat"]},{anchor["lon"]})["boundary"="protected_area"];',
                f'  node(around:{radius_m},{anchor["lat"]},{anchor["lon"]})["heritage"];',
                f'  way(around:{radius_m},{anchor["lat"]},{anchor["lon"]})["heritage"];',
                f'  relation(around:{radius_m},{anchor["lat"]},{anchor["lon"]})["heritage"];',
                ");",
                "out center tags 25;",
            ])
            body = urllib.parse.urlencode({"data": overpass_query})
            overpass_rows = post_json_url("https://overpass-api.de/api/interpreter", body, user_agent)
            elements = overpass_rows.get("elements") if isinstance(overpass_rows, dict) else []
            diagnostics["overpass_result_count"] = len(elements or [])
            for row in (elements or [])[:25]:
                tags = row.get("tags") or {}
                center = row.get("center") or {}
                lon = row.get("lon") or center.get("lon")
                lat = row.get("lat") or center.get("lat")
                candidates.append({
                    "candidate_id": stable_id("extgap.osm_overpass", row),
                    "query": query,
                    "domain": domain_id,
                    "name": tags.get("name") or tags.get("name:ko") or f"OSM {row.get('type')} {row.get('id')}",
                    "category": "supplemental_osm_overpass_candidate",
                    "anchor": anchor,
                    "source_tier": "osm_supplemental",
                    "authority_level": "supplemental",
                    "source_name": "OpenStreetMap Overpass",
                    "authority": "OpenStreetMap contributors",
                    "source_url": "https://overpass-api.de/api/interpreter",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [float(lon), float(lat)] if lon is not None and lat is not None else None,
                        "status": "osm_candidate_unverified",
                        "strategy": "overpass_around_candidate",
                    },
                    "evidence": {
                        "osm_type": row.get("type"),
                        "osm_id": row.get("id"),
                        "tags": tags,
                        "use_as_authority": False,
                    },
                    "review_required": True,
                    "promotion_status": "SUPPLEMENTAL_ONLY_NOT_PROMOTABLE",
                })
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        diagnostics.update({"status": "error", "reason": str(exc)})

    payload = {"diagnostics": diagnostics, "candidates": candidates}
    write_json_cache(cache_path, payload)
    return candidates, diagnostics


def ollama_ambiguity_review(query: str, domain: dict[str, Any] | None, anchor: dict[str, Any] | None, enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"enabled": False, "status": "skipped", "reason": "ask_ollama_disabled"}
    endpoint = os.getenv("OLLAMA_GENERATE_URL", os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/") + "/api/generate")
    model = os.getenv("GEOLLM_OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "llama3.1"))
    prompt = "\n".join([
        "You are an ambiguity reviewer for a Korean maritime GeoLLM router.",
        "Do not assert facts, coordinates, laws, or counts.",
        "Return compact JSON with keys: ambiguity, likely_intents, missing_slots, notes.",
        f"query: {query}",
        f"detected_domain: {(domain or {}).get('domain_id')}",
        f"detected_anchor: {(anchor or {}).get('place_id')}",
    ])
    body = json.dumps({"model": model, "prompt": prompt, "stream": False}, ensure_ascii=False).encode("utf-8")
    try:
        req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=int(os.getenv("OLLAMA_TIMEOUT_SEC", "45"))) as response:
            payload = json.load(response)
        return {
            "enabled": True,
            "status": "OK",
            "model": model,
            "role": "ambiguity_resolver_only",
            "raw_response": payload.get("response"),
        }
    except Exception as exc:  # pragma: no cover - depends on local Ollama
        return {
            "enabled": True,
            "status": "error",
            "model": model,
            "role": "ambiguity_resolver_only",
            "reason": str(exc),
        }


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
        f"- ollama_ambiguity_review: `{(report.get('ollama_ambiguity_review') or {}).get('status')}`",
        f"- osm_fetch: `{(report.get('osm_fetch_diagnostics') or {}).get('status')}`",
        f"- public_authoritative_candidates: `{report['candidate_counts']['public_authoritative']}`",
        f"- supplemental_candidates: `{report['candidate_counts']['supplemental']}`",
        f"- osm_live_candidates: `{report['candidate_counts'].get('osm_live')}`",
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


def run_gap_fill(query: str, radius_m: int = 10000, check_db: bool = False, fetch_osm: bool = False, ask_ollama: bool = False) -> dict[str, Any]:
    registry = load_yaml(DEFAULT_REGISTRY)
    place_registry = load_yaml(PLACE_REGISTRY)
    spatial_registry = load_yaml(SPATIAL_REGISTRY)
    domain = detect_gap_domain(query, registry)
    anchor = resolve_anchor_place(query, registry, place_registry)
    ollama_review = ollama_ambiguity_review(query, domain, anchor, ask_ollama)
    if not domain:
        return {
            "status": "BLOCKED_UNSUPPORTED_GAP_DOMAIN",
            "generated_at": utc_now(),
            "query": query,
            "radius_m": radius_m,
            "reason": "no gap domain matched",
            "ollama_ambiguity_review": ollama_review,
            "osm_fetch_diagnostics": {"enabled": False, "status": "skipped", "reason": "unsupported_gap_domain"},
            "candidate_counts": {
                "total": 0,
                "public_authoritative": 0,
                "supplemental": 0,
                "osm_live": 0,
                "promotion": 0,
            },
            "candidates": [],
            "promotion_candidates": [],
        }
    local_checks = check_local_layers(domain, anchor, spatial_registry, radius_m, check_db)
    domain_id = domain["domain_id"]
    candidates: list[dict[str, Any]] = []
    allow_external_candidates = external_candidate_generation_allowed(local_checks)
    if allow_external_candidates:
        candidates.extend(public_authoritative_candidates(query, domain_id, anchor, registry))
        candidates.extend(osm_supplemental_candidates(query, domain_id, anchor, domain))
    osm_live_candidates, osm_fetch_diagnostics = ([], {"enabled": False, "status": "skipped", "reason": "fetch_osm_disabled"})
    if allow_external_candidates and fetch_osm:
        osm_live_candidates, osm_fetch_diagnostics = fetch_osm_live_candidates(query, domain_id, anchor, domain, radius_m)
        candidates.extend(osm_live_candidates)
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
        "ollama_ambiguity_review": ollama_review,
        "osm_fetch_diagnostics": osm_fetch_diagnostics,
        "candidate_counts": {
            "total": len(candidates),
            "public_authoritative": sum(1 for item in candidates if item.get("authority_level") == "public_authoritative"),
            "supplemental": sum(1 for item in candidates if item.get("authority_level") == "supplemental"),
            "osm_live": len(osm_live_candidates),
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
    parser.add_argument("--fetch-osm", action="store_true")
    parser.add_argument("--ask-ollama", action="store_true")
    args = parser.parse_args()

    report = run_gap_fill(args.query, radius_m=args.radius_m, check_db=args.check_db, fetch_osm=args.fetch_osm, ask_ollama=args.ask_ollama)
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
