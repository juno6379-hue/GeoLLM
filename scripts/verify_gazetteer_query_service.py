"""Verify live place resolution and radius results against independent source SQL."""

import argparse
from collections import Counter, defaultdict
from contextlib import ExitStack
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg2
from psycopg2 import sql
from shapely import wkt
import yaml

from verify_s101_radius_service import Checks, VerificationError, read_policy, safe_error, stream_request


ROOT = Path(__file__).resolve().parents[1]
RADIUS = 3000
LIMIT = 30


def normalized(value):
    return re.sub(r"\s+", "", str(value or "")).casefold()


def point_key(geometry):
    point = wkt.loads(geometry)
    return round(point.x, 6), round(point.y, 6)


def post_json(args, payload):
    request = Request(args.base_url.rstrip("/") + "/api/v1/places/resolve",
                      data=json.dumps(payload).encode("utf-8"),
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=args.timeout) as response:
        return json.load(response)


def readonly_connection(stack, env, args):
    if not os.getenv(env):
        raise VerificationError("Required database environment variable is missing: " + env)
    connection = psycopg2.connect(os.environ[env], connect_timeout=5)
    stack.callback(connection.close)
    connection.set_session(readonly=True, isolation_level="REPEATABLE READ")
    with connection.cursor() as cursor:
        cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(args.sql_timeout_ms),))
        cursor.execute("SET LOCAL lock_timeout = '1000ms'")
    return connection


def source_rows(island_connection, khoa_connection):
    sources = [
        (island_connection, "serving.island_gazetteer_current", """
            SELECT source_id::text, name, properties->>'NP_ENM', ST_AsText(geometry),
                   ST_SRID(geometry), source_asset, source_member
            FROM serving.island_gazetteer_current ORDER BY source_id
        """),
        (khoa_connection, "public.maritime_gazetteer_khoa", """
            SELECT gid::text, korn_nm, eng_nm, ST_AsText(geometry), ST_SRID(geometry),
                   ancmnt_yr, ancmnt_inf
            FROM public.maritime_gazetteer_khoa ORDER BY gid
        """),
    ]
    rows = []
    for connection, source, statement in sources:
        with connection.cursor() as cursor:
            cursor.execute(statement)
            for identifier, name, english, geometry, srid, origin, version in cursor.fetchall():
                if srid != 4326 or not name or "\ufffd" in name:
                    continue
                point = wkt.loads(geometry)
                if point.geom_type != "Point" or point.is_empty or not point.is_valid:
                    continue
                rows.append({"source_ref": source, "source_id": identifier, "name": name,
                             "english": english, "geometry": geometry, "origin": origin, "version": version})
    return rows


def group_sources(rows):
    locations, names, aliases = defaultdict(list), defaultdict(list), defaultdict(set)
    for row in rows:
        locations[(normalized(row["name"]), point_key(row["geometry"]))].append(row)
    groups = list(locations.values())
    for index, group in enumerate(groups):
        names[normalized(group[0]["name"])].append(index)
        for row in group:
            for name in (row["name"], row["english"]):
                if name:
                    aliases[normalized(name)].add(index)
    return groups, names, aliases


def hazard_rows(connection, layer, profile, geometry):
    statement = sql.SQL("""
        SELECT f.{identifier}::text, f.{name}, ST_Distance(f.{geometry}::geography, p.geom::geography)
        FROM {relation} AS f CROSS JOIN (SELECT ST_GeomFromText(%s, 4326) AS geom) AS p
        WHERE f.{code} = ANY(%s) AND f.{name} = ANY(%s) AND f.{geometry} IS NOT NULL
          AND ST_DWithin(f.{geometry}::geography, p.geom::geography, %s)
        ORDER BY ST_Distance(f.{geometry}::geography, p.geom::geography), f.{identifier}
    """).format(identifier=sql.Identifier(layer["id_column"]), name=sql.Identifier(layer["name_column"]),
                code=sql.Identifier(layer["code_column"]), geometry=sql.Identifier(layer["geometry_column"]),
                relation=sql.Identifier(*layer["physical_table"].split(".")))
    targets = profile["target_features"]
    with connection.cursor() as cursor:
        cursor.execute(statement, (geometry, [profile["feature_code_map"][name] for name in targets], targets, RADIUS))
        return [{"id": identifier, "name": name, "distance_m": float(distance)} for identifier, name, distance in cursor.fetchall()]


def choose_examples(connection, layer, profile, groups, names, aliases):
    registry = yaml.safe_load((ROOT / "data/place_geometry_registry.yaml").read_text(encoding="utf-8"))
    reserved = {normalized(alias) for item in registry["places"].values()
                for alias in [item.get("canonical_name"), *(item.get("aliases") or [])]}
    unique = [group for group in groups if len(names[normalized(group[0]["name"])] ) == 1
              and normalized(group[0]["name"]) not in reserved and group[0]["english"]
              and len(aliases[normalized(group[0]["english"])]) == 1]
    statement = sql.SQL("""
        SELECT ST_AsText(ST_PointOnSurface({geometry})) FROM {relation}
        WHERE {code} = ANY(%s) AND {geometry} IS NOT NULL ORDER BY {identifier} LIMIT 1
    """).format(geometry=sql.Identifier(layer["geometry_column"]), relation=sql.Identifier(*layer["physical_table"].split(".")),
                code=sql.Identifier(layer["code_column"]), identifier=sql.Identifier(layer["id_column"]))
    with connection.cursor() as cursor:
        cursor.execute(statement, (list(profile["feature_code_map"].values()),))
        row = cursor.fetchone()
    if not row:
        raise VerificationError("The S101 source has no hazard geometry for a populated acceptance case")
    anchor = wkt.loads(row[0])
    unique.sort(key=lambda group: wkt.loads(group[0]["geometry"]).distance(anchor))
    selected, oracle = None, []
    for group in unique[:30]:
        oracle = hazard_rows(connection, layer, profile, group[0]["geometry"])
        if oracle:
            selected = group
            break
    if not selected:
        raise VerificationError("No unique source place near the sampled hazards has a populated 3000m result")
    duplicate = next((group for group in unique if len(group) > 1), None)
    ambiguous_indices = next((indices for name, indices in sorted(names.items()) if len(indices) == 2 and name not in reserved), None)
    if duplicate is None or ambiguous_indices is None:
        raise VerificationError("The source lacks required duplicate or ambiguous acceptance examples")
    return selected, oracle, duplicate, [groups[index] for index in ambiguous_indices]


def verify_source_point(response, group, checks, expected_status="RESOLVED_GAZETTEER"):
    checks.equal("resolved", response.get("status"), "RESOLVED")
    checks.equal("crs", response.get("crs"), "EPSG:4326")
    checks.equal("source_coordinates", point_key(response["geometry"]), point_key(group[0]["geometry"]))
    checks.require("geometry_matches_source_precisely", wkt.loads(response["geometry"]).equals_exact(wkt.loads(group[0]["geometry"]), 1e-8))
    checks.require("place_id_present", bool(response.get("place_id")))
    checks.require("place_version_present", bool(response.get("place_version")))
    resolution = response.get("location_resolution") or {}
    checks.equal("resolution_status", resolution.get("status"), expected_status)
    observed = {(row.get("source_ref"), str(row.get("source_id"))) for row in resolution.get("source_records", [])}
    expected = {(row["source_ref"], row["source_id"]) for row in group}
    checks.equal("source_records", sorted(observed), sorted(expected))


def verify_radius(result, oracle, group, checks, *, limit=LIMIT, offset=0, resolution_status="RESOLVED_GAZETTEER"):
    structured, summary = result.get("structured_result", {}), result.get("spatial_result_summary", {})
    rows, page = structured.get("features", []), oracle[offset:offset + limit]
    ids = [row["id"] for row in page]
    checks.equal("completed", result.get("status"), "COMPLETED")
    checks.equal("success", structured.get("status"), "SUCCESS")
    checks.equal("reference_source_point", point_key(structured["reference_geometry"]), point_key(group[0]["geometry"]))
    checks.equal("radius_m", structured.get("distance_m"), RADIUS)
    checks.equal("source_resolved", structured.get("location_resolution", {}).get("status"), resolution_status)
    checks.equal("result_limit", structured.get("result_limit"), limit)
    checks.equal("page_offset", structured.get("offset"), offset)
    expectations = {"count": len(oracle), "total_count": len(oracle), "returned_count": len(page), "feature_ids": ids,
                    "total_counts_by_type": dict(Counter(row["name"] for row in oracle)),
                    "returned_counts_by_type": dict(Counter(row["name"] for row in page))}
    for key, expected in expectations.items():
        checks.equal("structured_" + key, structured.get(key), expected)
        checks.equal("summary_" + key, summary.get(key), expected)
    checks.equal("table_ids", [str(row.get("feature_instance_id")) for row in rows], ids)
    matched = [layer for layer in result.get("map_layers", []) if layer.get("metadata", {}).get("role") == "matched_features"]
    areas = [layer for layer in result.get("map_layers", []) if layer.get("metadata", {}).get("role") == "search_area"]
    checks.equal("one_matched_layer", len(matched), 1)
    checks.equal("one_search_area_layer", len(areas), 1)
    features = [feature for layer in matched for feature in layer.get("inline_geojson", {}).get("features", [])]
    checks.equal("map_ids", [str(feature.get("id")) for feature in features], ids)
    checks.equal("map_properties_match_table", [feature.get("properties") for feature in features], rows)
    checks.equal("object_count_excludes_search_area", sum(layer.get("feature_count", -1) for layer in matched), len(page))
    bundle = result.get("evidence_bundle", {})
    items = bundle.get("spatial_feature_evidence", [])
    summaries = bundle.get("spatial_layer_evidence", [])
    checks.equal("evidence_ids", [str(item.get("data", {}).get("feature_instance_id")) for item in items], ids)
    checks.equal("evidence_data_matches_table", [item.get("data") for item in items], rows)
    checks.equal("typed_summary_evidence", len(summaries), 1)
    for key, expected in expectations.items():
        checks.equal("evidence_summary_" + key, summaries[0].get("data", {}).get(key) if summaries else None, expected)
    evidence_ids = {item.get("evidence_id") for item in [*items, *summaries]}
    claims = {identifier for claim in result.get("claims", []) for identifier in claim.get("evidence_ids", [])}
    checks.equal("claim_evidence_links", sorted(claims), sorted(evidence_ids))
    text = result.get("summary") or ""
    checks.require("summary_text_total_count", bool(re.search(r"(?<!\d)" + str(len(oracle)) + r"\s*\uac74", text)))
    checks.require("summary_text_returned_count", bool(re.search(r"(?<!\d)" + str(len(page)) + r"\s*\uac74", text)))
    for index, (actual, expected) in enumerate(zip(rows, page)):
        distance = actual.get("distance_m")
        checks.require("distance_" + str(index), isinstance(distance, (int, float)) and math.isfinite(distance)
                       and 0 <= distance <= RADIUS and abs(distance - expected["distance_m"]) <= 0.001)
    return {"total_count": structured.get("total_count"), "returned_count": len(rows), "feature_ids": ids,
            "query_execution_id": structured.get("query_execution_id")}


def verify_place_stream(result, group, checks, *, resolution_status="RESOLVED_GAZETTEER"):
    structured = result.get("structured_result") or {}
    checks.equal("place_lookup_completed", result.get("status"), "COMPLETED")
    checks.equal("place_lookup_analysis", structured.get("analysis_type"), "place_lookup")
    verify_source_point(structured, group, checks, resolution_status)
    checks.equal("place_count", structured.get("count"), 1)
    checks.equal("place_returned_count", structured.get("returned_count"), 1)
    features = structured.get("geojson", {}).get("features", [])
    checks.equal("place_geojson_count", len(features), 1)
    if features:
        checks.equal("place_geojson_id", features[0].get("id"), structured.get("place_id"))
        checks.equal("place_geojson_type", features[0].get("geometry", {}).get("type"), "Point")
        source = wkt.loads(group[0]["geometry"])
        coordinates = features[0].get("geometry", {}).get("coordinates", [])
        checks.require("place_geojson_source_coordinates", len(coordinates) == 2
                       and abs(coordinates[0] - source.x) <= 1e-8 and abs(coordinates[1] - source.y) <= 1e-8)
    layers = result.get("map_layers", [])
    checks.equal("place_map_count", len(layers), 1)
    checks.equal("place_map_equals_geojson", layers[0].get("inline_geojson", {}).get("features") if layers else None, features)
    checks.equal("place_result_equals_geojson", result.get("features", {}).get("features"), features)
    evidence = result.get("evidence_bundle", {}).get("spatial_feature_evidence", [])
    checks.equal("place_evidence_count", len(evidence), 1)
    if evidence:
        checks.equal("place_evidence_type", evidence[0].get("evidence_type"), "place_reference")
        checks.equal("place_evidence_identity", evidence[0].get("data", {}).get("place_id"), structured.get("place_id"))
        checks.equal("place_evidence_provenance", evidence[0].get("data", {}).get("location_resolution"), structured.get("location_resolution"))
        checks.equal("place_evidence_link", features[0].get("properties", {}).get("evidence_id") if features else None, evidence[0].get("evidence_id"))
    return {"status": result.get("status"), "place_id": structured.get("place_id"),
            "place_version": structured.get("place_version"), "geometry": structured.get("geometry")}


def run(args, report):
    deadline = time.monotonic() + args.startup_timeout
    while True:
        try:
            with urlopen(args.base_url.rstrip("/") + "/health", timeout=2) as response:
                if response.status == 200:
                    break
        except Exception:
            pass
        if time.monotonic() >= deadline:
            raise VerificationError("Backend health was not ready within startup timeout")
        time.sleep(1)
    profile, layer = read_policy()
    with ExitStack() as stack:
        island = readonly_connection(stack, "S101_DB_URL", args)
        khoa = readonly_connection(stack, "POSTGIS_URL", args)
        sources = source_rows(island, khoa)
        groups, names, aliases = group_sources(sources)
        selected, oracle, duplicate, ambiguous = choose_examples(island, layer, profile, groups, names, aliases)
        report["source_audit"] = {"source_rows": len(sources), "grouped_locations": len(groups),
                                  "unique_example": selected, "duplicate_example": duplicate,
                                  "ambiguous_examples": ambiguous,
                                  "oracle_total_count": len(oracle), "predicate": "ST_DWithin geography; no bbox prefilter"}

        def case(name, callback):
            checks, started = Checks(), time.monotonic()
            entry = {"name": name, "validation_kind": "actual_api_and_database"}
            report["cases"].append(entry)
            response = None
            try:
                response = callback(checks)
                entry["observed"] = response
            except Exception as exc:
                entry["error"] = safe_error(exc)
                checks.require("completed_without_error", False)
            entry.update(passed=checks.passed, assertions=checks.items, duration_ms=round((time.monotonic() - started) * 1000))
            print(("PASS " if checks.passed else "FAIL ") + name, flush=True)
            return response

        def stream(payload, checks):
            event, _ = stream_request(args.base_url, payload, args.timeout)
            result = event.get("final_result") or {}
            checks.require("stream_has_final_result", bool(result))
            checks.equal("stream_terminal_matches_result", event.get("status"), result.get("status"))
            return result

        def resolve_group(group, alias, checks):
            response = post_json(args, {"query": alias, "spatial_context": {"base_location": alias}})
            verify_source_point(response, group, checks)
            return response

        korean = case("unique_korean_source_point", lambda checks: resolve_group(selected, selected[0]["name"], checks))
        english = case("unique_english_same_source_point", lambda checks: resolve_group(selected, selected[0]["english"], checks))
        case("duplicate_rows_one_location", lambda checks: resolve_group(duplicate, duplicate[0]["name"], checks))

        def ambiguity(checks):
            response = post_json(args, {"query": ambiguous[0][0]["name"], "spatial_context": {"base_location": ambiguous[0][0]["name"]}})
            checks.equal("clarification_required", response.get("status"), "NEEDS_CLARIFICATION")
            candidates = response.get("location_candidates", [])
            checks.equal("distinct_source_locations", sorted(point_key(item["geometry"]) for item in candidates), sorted(point_key(group[0]["geometry"]) for group in ambiguous))
            checks.require("candidate_versions_present", all(item.get("place_id") and item.get("place_version") for item in candidates))
            return response

        ambiguous_response = case("distinct_same_name_requires_selection", ambiguity)
        candidate = ((ambiguous_response or {}).get("location_candidates") or [{}])[0]

        def selection(checks, *, stale=False, conflict=False):
            spatial = {"place_id": candidate["place_id"], "place_version": candidate["place_version"]}
            if stale:
                spatial["place_version"] = "expired-fixture-version"
            if conflict:
                spatial.update(geometry="POINT(0 0)", crs="EPSG:4326")
            response = post_json(args, {"query": candidate["label"], "spatial_context": spatial})
            if stale or conflict:
                checks.equal("selection_rejected", response.get("status"), "NEEDS_CLARIFICATION")
                checks.equal("selection_error", response.get("error_code"), "STALE_PLACE_SELECTION" if stale else "CONFLICTING_LOCATION")
                checks.require("no_resolved_geometry", not response.get("geometry"))
            else:
                group = next(group for group in ambiguous if point_key(group[0]["geometry"]) == point_key(candidate["geometry"]))
                verify_source_point(response, group, checks, "CONFIRMED_SELECTION")
                checks.equal("selected_id_preserved", response.get("place_id"), candidate["place_id"])
            return response

        case("select_current_candidate", selection)
        case("stale_candidate_version_rejected", lambda checks: selection(checks, stale=True))
        case("selected_candidate_conflicting_geometry_rejected", lambda checks: selection(checks, conflict=True))

        def qualifier(checks):
            query = selected[0]["name"] + " \uc785\uad6c"
            response = post_json(args, {"query": query, "spatial_context": {"base_location": query}})
            checks.equal("entrance_is_not_parent_point", response.get("status"), "NEEDS_CLARIFICATION")
            checks.require("parent_point_offered_as_candidate", any(point_key(item["geometry"]) == point_key(selected[0]["geometry"]) for item in response.get("location_candidates", [])))
            return response

        case("unresolved_entrance_modifier", qualifier)

        direct_task = "gazetteer-direct-" + str(uuid4())
        ambiguous_task = "gazetteer-selection-" + str(uuid4())

        def direct_place(checks):
            result = stream({"query": selected[0]["name"] + " \uc704\uce58", "task_id": direct_task}, checks)
            return verify_place_stream(result, selected, checks)

        case("stream_unique_place_lookup", direct_place)

        def stream_ambiguous(checks):
            result = stream({"query": ambiguous[0][0]["name"] + " \uc704\uce58", "task_id": ambiguous_task}, checks)
            checks.equal("stream_place_ambiguity", result.get("status"), "NEEDS_CLARIFICATION")
            checks.equal("stream_place_analysis", result.get("structured_result", {}).get("analysis_type"), "place_lookup")
            candidates = result.get("clarification_options") or []
            checks.equal("stream_candidates_match_source_locations", sorted(point_key(item["geometry"]) for item in candidates), sorted(point_key(group[0]["geometry"]) for group in ambiguous))
            checks.require("stream_candidate_versions_present", all(item.get("place_id") and item.get("place_version") for item in candidates))
            return {"status": result.get("status"), "candidates": candidates}

        stream_candidates = case("stream_ambiguous_place_lookup", stream_ambiguous)
        stream_candidate = ((stream_candidates or {}).get("candidates") or [{}])[0]

        def stream_selected(checks, *, stale=False):
            spatial = {"place_id": stream_candidate["place_id"], "place_version": stream_candidate["place_version"]}
            if stale:
                spatial["place_version"] = "expired-stream-selection-version"
            result = stream({"query": ambiguous[0][0]["name"] + " \uc704\uce58", "task_id": ambiguous_task, "spatial_context": spatial}, checks)
            if stale:
                checks.equal("completed_task_stale_selection_rejected", result.get("status"), "NEEDS_CLARIFICATION")
                checks.equal("stale_selection_error", result.get("error_code"), "STALE_PLACE_SELECTION")
                checks.equal("stale_selection_no_map", result.get("map_layers"), [])
                checks.equal("stale_selection_no_evidence", result.get("evidence_bundle", {}).get("spatial_feature_evidence"), [])
                return {"status": result.get("status"), "error_code": result.get("error_code")}
            group = next(group for group in ambiguous if point_key(group[0]["geometry"]) == point_key(stream_candidate["geometry"]))
            return verify_place_stream(result, group, checks, resolution_status="CONFIRMED_SELECTION")

        case("stream_same_task_candidate_confirmation", stream_selected)
        case("stream_completed_task_stale_selection_rejected", lambda checks: stream_selected(checks, stale=True))

        def radius_query(checks):
            payload = {"query": selected[0]["name"] + " 3km \uc774\ub0b4 \uc704\ud5d8\uac1d\uccb4\ub97c \ucc3e\uc544\uc918",
                       "task_id": "gazetteer-oracle-" + str(uuid4()),
                       "spatial_context": {"base_location": selected[0]["name"], "result_limit": LIMIT}}
            event, _ = stream_request(args.base_url, payload, args.timeout)
            result = event.get("final_result") or {}
            checks.equal("terminal_status", event.get("status"), result.get("status"))
            return verify_radius(result, oracle, selected, checks)

        case("source_resolved_3000m_hazards_vs_independent_sql", radius_query)

        page_task = "gazetteer-page-" + str(uuid4())
        type_counts = Counter(row["name"] for row in oracle)
        page_targets = sorted(name for name, count in type_counts.items() if count >= 2) or sorted(type_counts)
        page_exclusions = [name for name in profile["target_features"] if name not in page_targets]
        page_oracle = [row for row in oracle if row["name"] in page_targets]

        def named_page(checks, offset):
            checks.require("populated_source_supports_page_two", len(page_oracle) >= 2)
            spatial = {"offset": offset}
            if offset == 0:
                spatial.update(base_location=selected[0]["name"], place_id=korean["place_id"],
                               place_version=korean["place_version"], result_limit=1,
                               target_features=page_targets, exclusions=page_exclusions)
            result = stream({"query": selected[0]["name"] + " 3km \uc774\ub0b4 \uc704\ud5d8\uac1d\uccb4\ub97c \ucc3e\uc544\uc918",
                             "task_id": page_task, "spatial_context": spatial}, checks)
            structured = result.get("structured_result") or {}
            checks.equal("pagination_place_id_preserved", structured.get("place_id"), korean["place_id"])
            checks.equal("pagination_place_version_preserved", structured.get("place_version"), korean["place_version"])
            checks.equal("pagination_targets_preserved", sorted(structured.get("target_features") or []), page_targets)
            checks.equal("pagination_exclusions_preserved", sorted(structured.get("exclusions") or []), sorted(page_exclusions))
            return verify_radius(result, page_oracle, selected, checks, limit=1, offset=offset, resolution_status="CONFIRMED_SELECTION")

        first_page = case("stream_named_radius_filtered_first_page", lambda checks: named_page(checks, 0))
        second_page = case("stream_same_task_radius_next_page", lambda checks: named_page(checks, 1))

        def cross_request(checks):
            checks.equal("korean_english_id", (korean or {}).get("place_id"), (english or {}).get("place_id"))
            checks.equal("korean_english_version", (korean or {}).get("place_version"), (english or {}).get("place_version"))
            checks.require("named_radius_pages_completed", bool(first_page) and bool(second_page))
            checks.equal("named_radius_page_total_unchanged", (first_page or {}).get("total_count"), (second_page or {}).get("total_count"))
            checks.equal("named_radius_pages_disjoint", sorted(set((first_page or {}).get("feature_ids", [])) & set((second_page or {}).get("feature_ids", []))), [])
            checks.require("named_radius_execution_identity_changes", (first_page or {}).get("query_execution_id") != (second_page or {}).get("query_execution_id"))
            island.commit()
            khoa.commit()
            for connection in (island, khoa):
                with connection.cursor() as cursor:
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(args.sql_timeout_ms),))
                    cursor.execute("SET LOCAL lock_timeout = '1000ms'")
            checks.equal("source_rows_unchanged", source_rows(island, khoa), sources)
            checks.equal("hazard_source_unchanged", hazard_rows(island, layer, profile, selected[0]["geometry"]), oracle)
            return {"oracle_total_count": len(oracle)}

        case("source_and_cross_request_consistency", cross_request)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--startup-timeout", type=float, default=120)
    parser.add_argument("--sql-timeout-ms", type=int, default=20000)
    args = parser.parse_args()
    url = urlsplit(args.base_url)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error("--base-url must be HTTP(S) without credentials, query, or fragment")
    if min(args.timeout, args.startup_timeout, args.sql_timeout_ms) <= 0:
        parser.error("timeouts must be positive")
    report = {"schema_version": "1.0", "validation_kind": "actual_api_and_database",
              "started_at": datetime.now(timezone.utc).isoformat(), "cases": [],
              "synthetic_tests": {"status": "not_run"}, "api_base_url": args.base_url}
    try:
        run(args, report)
    except Exception as exc:
        report["error"] = safe_error(exc)
    report["passed"] = bool(report["cases"]) and "error" not in report and all(case["passed"] for case in report["cases"])
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["summary"] = {"total": len(report["cases"]), "passed": sum(case["passed"] for case in report["cases"])}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "summary": report["summary"], "report": str(args.output)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
