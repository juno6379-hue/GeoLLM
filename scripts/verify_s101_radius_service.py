"""Verify the running radius service against independent, read-only PostGIS SQL.

Run inside geollm_backend after reloading the backend:
    python scripts/verify_s101_radius_service.py --base-url http://localhost:8000 \
        --output outputs/reports/s101_radius_service.json
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg2
from psycopg2 import sql
import yaml


ROOT = Path(__file__).resolve().parents[1]
BASE_QUERY = "\ubd80\uc0b0\ud56d \uc785\uad6c 3km \uc774\ub0b4 \uc704\ud5d8\uac1d\uccb4\ub97c \ucc3e\uc544\uc918"
BASE_LABEL = "\ubd80\uc0b0\ud56d \uc785\uad6c"
REFERENCE_WKT = "POINT(129.075 35.075)"
DISTANCE_M = 3000
PAGE_SIZE = 30
PROFILE_ID = "navigation_hazard_object.s101_hazard_radius"


class VerificationError(Exception):
    """An error whose message is safe to include in a verification report."""


def safe_error(exc):
    if isinstance(exc, VerificationError):
        return {"type": type(exc).__name__, "message": str(exc)}
    details = {"type": type(exc).__name__}
    if isinstance(exc, HTTPError):
        details["http_status"] = exc.code
    if isinstance(exc, psycopg2.Error) and exc.pgcode:
        details["sqlstate"] = exc.pgcode
    return details


class Checks:
    def __init__(self):
        self.items = []

    def equal(self, name, actual, expected):
        item = {"name": name, "passed": actual == expected}
        if not item["passed"]:
            item.update(actual=actual, expected=expected)
        self.items.append(item)

    def require(self, name, condition):
        self.equal(name, bool(condition), True)

    @property
    def passed(self):
        return bool(self.items) and all(item["passed"] for item in self.items)


def stream_request(base_url, payload, timeout):
    request = Request(
        base_url.rstrip("/") + "/api/v1/tasks/stream",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )
    events, fields = [], []
    started = time.monotonic()
    with urlopen(request, timeout=timeout) as response:
        if "text/event-stream" not in response.headers.get("Content-Type", ""):
            raise VerificationError("The task endpoint did not return an SSE stream")
        for raw_line in response:
            if time.monotonic() - started > timeout:
                raise VerificationError("The SSE request exceeded its total time budget")
            line = raw_line.decode("utf-8").rstrip("\r\n")
            if line.startswith("data:"):
                fields.append(line[5:].lstrip(" "))
            elif not line and fields:
                event = json.loads("\n".join(fields))
                fields.clear()
                events.append(event)
                if event.get("event") == "error":
                    raise VerificationError("The service emitted an SSE error event")
                if event.get("event") == "completed":
                    return event, [item.get("event") for item in events]
    raise VerificationError("The SSE stream ended without a completed event")


def read_policy():
    with (ROOT / "data" / "derived_concept_registry_v2.yaml").open(encoding="utf-8") as handle:
        concepts = yaml.safe_load(handle)
    profile = concepts["derived_concepts"]["navigation_hazard_object"]["execution_profiles"]["s101_hazard_radius"]
    with (ROOT / "data" / "spatial_layer_registry.yaml").open(encoding="utf-8") as handle:
        layer = yaml.safe_load(handle)["layers"][profile["layer"]]
    if profile["context"] != "navigation_safety" or layer["srid"] != 4326:
        raise VerificationError("The radius policy context or coordinate system is unexpected")
    if "Wreck" not in profile["target_features"]:
        raise VerificationError("The approved target policy does not include the Wreck test target")
    return profile, layer


def reference_rows(connection, layer, profile, targets):
    # Deliberately omit the service's bounding box and SQL template. The oracle
    # evaluates the geography predicate over every row with an approved type.
    statement = sql.SQL("""
        SELECT f.{identifier}::text, f.{name}, f.{code},
               ST_Distance(f.{geometry}::geography, p.geom::geography) AS distance_m,
               f.dataset_id::text, f.dataset_version_id::text
        FROM {relation} AS f
        CROSS JOIN (SELECT ST_GeomFromText(%s, 4326) AS geom) AS p
        WHERE f.{code} = ANY(%s)
          AND f.{name} = ANY(%s)
          AND f.{geometry} IS NOT NULL
          AND ST_DWithin(f.{geometry}::geography, p.geom::geography, %s)
        ORDER BY distance_m, f.{identifier}
    """).format(
        identifier=sql.Identifier(layer["id_column"]),
        name=sql.Identifier(layer["name_column"]),
        code=sql.Identifier(layer["code_column"]),
        geometry=sql.Identifier(layer["geometry_column"]),
        relation=sql.Identifier(*layer["physical_table"].split(".")),
    )
    with connection.cursor() as cursor:
        cursor.execute(statement, (
            REFERENCE_WKT, [int(profile["feature_code_map"][target]) for target in targets],
            targets, DISTANCE_M,
        ))
        rows = cursor.fetchall()
    return [
        {"feature_instance_id": row[0], "feature_name": row[1], "feature_type_code": row[2],
         "distance_m": float(row[3]), "source_dataset_id": row[4], "dataset_version_id": row[5]}
        for row in rows
    ]


def source_digest(rows):
    return hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()


def feature_ids(features):
    return [str(feature.get("feature_instance_id")) for feature in features]


def verify_success(result, oracle, targets, offset, checks):
    structured = result.get("structured_result") or {}
    rows = structured.get("features") or []
    page = oracle[offset:offset + PAGE_SIZE]
    expected_ids = feature_ids(page)
    total = len(oracle)
    total_types = dict(Counter(row["feature_name"] for row in oracle))
    page_types = dict(Counter(row["feature_name"] for row in page))
    expected_status = "SUCCESS" if total else "SUCCESS_EMPTY"
    checks.equal("terminal_success_status", result.get("status"), "COMPLETED")
    checks.equal("structured_success_status", structured.get("status"), expected_status)
    checks.equal("requested_radius_m", structured.get("distance_m"), DISTANCE_M)
    checks.equal("requested_targets", sorted(structured.get("target_features") or []), sorted(targets))
    checks.equal("ordered_table_ids_vs_sql", feature_ids(rows), expected_ids)
    checks.equal("table_id_uniqueness", len(set(feature_ids(rows))), len(rows))
    checks.equal("structured_type_counts_vs_sql", structured.get("total_counts_by_type"), total_types)
    checks.equal("table_page_type_counts_vs_sql", structured.get("returned_counts_by_type"), page_types)

    summary = result.get("spatial_result_summary") or {}
    expected_values = {
        "count": total, "total_count": total, "returned_count": len(page),
        "feature_ids": expected_ids, "result_limit": PAGE_SIZE, "offset": offset,
        "total_counts_by_type": total_types, "returned_counts_by_type": page_types,
    }
    for name, value in expected_values.items():
        checks.equal("structured_" + name, structured.get(name), value)
        checks.equal("summary_" + name, summary.get(name), value)

    layers = result.get("map_layers") or []
    matched = [layer for layer in layers if (layer.get("metadata") or {}).get("role") == "matched_features"]
    search_areas = [layer for layer in layers if (layer.get("metadata") or {}).get("role") == "search_area"]
    checks.equal("matched_feature_layer_count", len(matched), 1)
    checks.equal("search_area_layer_count", len(search_areas), 1)
    checks.equal("map_layers_have_explicit_roles", len(matched) + len(search_areas), len(layers))
    map_features = [feature for layer in matched for feature in (layer.get("inline_geojson") or {}).get("features", [])]
    checks.equal("ordered_map_ids_vs_sql", [str(feature.get("id")) for feature in map_features], expected_ids)
    checks.equal("map_properties_equal_table", [feature.get("properties") for feature in map_features], rows)
    checks.require("map_feature_geometries_present", all(feature.get("geometry") for feature in map_features))
    checks.equal("map_object_count_excludes_search_area", sum(layer.get("feature_count", -1) for layer in matched), len(page))
    if matched:
        for name, value in expected_values.items():
            checks.equal("map_metadata_" + name, matched[0].get("metadata", {}).get(name), value)
    checks.equal("structured_geojson_matches_map", structured.get("geojson", {}).get("features"), map_features)
    checks.equal("result_geojson_matches_map", result.get("features", {}).get("features"), map_features)

    evidence = result.get("evidence_bundle") or {}
    feature_evidence = evidence.get("spatial_feature_evidence") or []
    layer_evidence = evidence.get("spatial_layer_evidence") or []
    checks.equal("typed_evidence_count", len(feature_evidence), len(page))
    checks.equal("ordered_evidence_data_ids_vs_sql", feature_ids([item.get("data", {}) for item in feature_evidence]), expected_ids)
    checks.equal("evidence_data_equal_table", [item.get("data") for item in feature_evidence], rows)
    checks.require("typed_feature_evidence", all(item.get("evidence_type") == "spatial_feature" for item in feature_evidence))
    checks.equal("summary_evidence_count", len(layer_evidence), 1)
    if layer_evidence:
        checks.equal("typed_summary_evidence", layer_evidence[0].get("evidence_type"), "spatial_query_summary")
        for name, value in expected_values.items():
            checks.equal("evidence_summary_" + name, layer_evidence[0].get("data", {}).get(name), value)
    evidence_ids = [item.get("evidence_id") for item in [*feature_evidence, *layer_evidence]]
    checks.require("evidence_ids_present_and_unique", all(evidence_ids) and len(set(evidence_ids)) == len(evidence_ids))
    checks.equal("table_evidence_links", [row.get("evidence_id") for row in rows], [item.get("evidence_id") for item in feature_evidence])
    claim_ids = {identifier for claim in (result.get("claims") or []) for identifier in claim.get("evidence_ids", [])}
    checks.equal("claim_links_cover_exact_evidence", sorted(claim_ids), sorted(evidence_ids))

    for index, (row, expected) in enumerate(zip(rows, page)):
        for field in ("feature_type_code", "feature_name", "source_dataset_id", "dataset_version_id"):
            checks.equal("row_{}_{}".format(index, field), str(row.get(field)), str(expected[field]))
        distance = row.get("distance_m")
        checks.require("row_{}_distance_matches_sql".format(index),
                       isinstance(distance, (int, float)) and math.isfinite(distance)
                       and 0 <= distance <= DISTANCE_M and abs(distance - expected["distance_m"]) <= 0.001)
        checks.equal("row_{}_result_id".format(index), row.get("result_id"), summary.get("result_id"))
        checks.equal("row_{}_execution_id".format(index), row.get("query_execution_id"), summary.get("query_execution_id"))

    qec = result.get("orchestrator_v2", {}).get("query_execution_context", {})
    checks.equal("execution_context_ready", qec.get("readiness"), "EXECUTION_READY")
    checks.equal("approved_context", qec.get("slots", {}).get("context"), "navigation_safety")
    checks.equal("approved_target_policy", qec.get("semantic_resolution", {}).get("target_policy"), PROFILE_ID)
    checks.equal("confirmed_location", structured.get("location_resolution", {}).get("status"), "CONFIRMED_INPUT")
    checks.require("execution_snapshot_recorded", bool(qec.get("snapshot_versions", {}).get("data_snapshot")))
    text = result.get("summary") or ""
    checks.require("summary_text_total_count", bool(re.search(r"(?<!\d)" + str(total) + r"\s*\uac74", text)))
    checks.require("summary_text_returned_count", bool(re.search(r"(?<!\d)" + str(len(page)) + r"\s*\uac74", text)))
    return {
        "status": structured.get("status"), "total_count": structured.get("total_count"),
        "returned_count": structured.get("returned_count"), "ordered_feature_ids": feature_ids(rows),
        "total_counts_by_type": structured.get("total_counts_by_type"),
        "oracle_total_count": total, "oracle_ordered_feature_ids": expected_ids,
        "oracle_total_counts_by_type": total_types,
        "oracle_sha256": source_digest(oracle),
    }


def verify_no_execution(result, expected_status, require_candidate, checks):
    checks.equal("terminal_status", result.get("status"), expected_status)
    structured = result.get("structured_result") or {}
    checks.equal("structured_status", structured.get("status"), expected_status)
    checks.equal("no_asserted_result_count", structured.get("count"), None)
    checks.equal("no_returned_objects", structured.get("returned_count"), 0)
    checks.equal("no_map_objects", result.get("map_layers"), [])
    checks.equal("no_spatial_feature_evidence", result.get("evidence_bundle", {}).get("spatial_feature_evidence"), [])
    qec = result.get("orchestrator_v2", {}).get("query_execution_context", {})
    checks.equal("execution_ready_false", qec.get("route_plan", {}).get("execution_ready"), False)
    if expected_status == "NEEDS_CLARIFICATION":
        checks.require("clarification_prompt_present", bool(result.get("clarification_questions")))
        candidates = result.get("clarification_options") or []
        if require_candidate:
            checks.require("location_candidate_present", bool(candidates))
            checks.require("candidate_requires_confirmation", all(item.get("requires_confirmation") is True for item in candidates))
        else:
            checks.equal("unknown_place_no_fabricated_candidate", candidates, [])
    else:
        checks.equal("policy_readiness", qec.get("readiness"), "BLOCKED_POLICY")
        checks.equal("policy_error", result.get("error_code"), "ACCESS_DENIED")
    return {"status": result.get("status"), "error_code": result.get("error_code")}


def confirmed_context(**overrides):
    return {"base_location": BASE_LABEL, "geometry": REFERENCE_WKT, "crs": "EPSG:4326",
            "buffer_distance": DISTANCE_M, "result_limit": PAGE_SIZE, **overrides}


def run(args, report):
    deadline = time.monotonic() + args.startup_timeout
    while True:
        try:
            with urlopen(args.base_url.rstrip("/") + "/health", timeout=2) as response:
                if json.load(response).get("status") == "ok":
                    break
        except (URLError, OSError, ValueError):
            pass
        if time.monotonic() >= deadline:
            raise VerificationError("The service did not become healthy before the startup deadline")
        time.sleep(1)
    profile, layer = read_policy()
    targets = list(profile["target_features"])
    remaining = [target for target in targets if target != "Wreck"]
    dsn = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not dsn:
        raise VerificationError("Neither S101_DB_URL nor POSTGIS_URL is configured")
    resume_id = "radius-verification-" + str(uuid4())
    cases = [
        {"name": "raw_query_requires_location_confirmation", "query": BASE_QUERY, "task_id": resume_id,
         "expected_status": "NEEDS_CLARIFICATION", "require_candidate": True},
        {"name": "confirm_candidate_same_task", "query": BASE_QUERY, "task_id": resume_id,
         "spatial_context": confirmed_context(), "targets": targets},
        {"name": "confirmed_reference_first_page", "query": BASE_QUERY,
         "spatial_context": confirmed_context(), "targets": targets},
        {"name": "confirmed_reference_next_page", "query": BASE_QUERY,
         "spatial_context": confirmed_context(offset=PAGE_SIZE), "targets": targets},
        {"name": "wreck_only_natural_language",
         "query": BASE_LABEL + " 3km \uc774\ub0b4 \uce68\uc120\ub9cc \ucc3e\uc544\uc918",
         "spatial_context": confirmed_context(), "targets": ["Wreck"]},
        {"name": "exclude_wreck_natural_language",
         "query": BASE_LABEL + " 3km \uc774\ub0b4 \uc704\ud5d8\uac1d\uccb4 \uc911 \uce68\uc120\uc744 \uc81c\uc678\ud558\uace0 \ucc3e\uc544\uc918",
         "spatial_context": confirmed_context(), "targets": remaining},
        {"name": "explicit_wreck_target", "query": BASE_QUERY,
         "spatial_context": confirmed_context(target_features=["Wreck"]), "targets": ["Wreck"]},
        {"name": "explicit_wreck_exclusion", "query": BASE_QUERY,
         "spatial_context": confirmed_context(exclusions=["Wreck"]), "targets": remaining},
        {"name": "unknown_place_requires_clarification",
         "query": "\ubbf8\ub4f1\ub85d\ud14c\uc2a4\ud2b8\ud56d \uc785\uad6c 3km \uc774\ub0b4 \uc704\ud5d8\uac1d\uccb4\ub97c \ucc3e\uc544\uc918",
         "expected_status": "NEEDS_CLARIFICATION", "require_candidate": False},
        {"name": "policy_denied_user", "query": BASE_QUERY, "user_id": "blocked_user",
         "spatial_context": confirmed_context(), "expected_status": "BLOCKED"},
    ]
    report.update(
        reference={"label": BASE_LABEL, "geometry": REFERENCE_WKT, "crs": "EPSG:4326",
                   "radius_m": DISTANCE_M, "authorization": "explicit_test_request_geometry"},
        policy={"context": profile["context"], "target_policy": PROFILE_ID,
                "policy_version": profile.get("policy_version"), "target_features": targets,
                "feature_code_map": profile["feature_code_map"]},
        oracle={"source_relation": layer["physical_table"], "predicate": "ST_DWithin(geography, geography, 3000)",
                "bounding_box_prefilter": False, "order_by": ["distance_m", layer["id_column"]],
                "transaction": "READ ONLY REPEATABLE READ", "statement_timeout_ms": args.sql_timeout_ms,
                "count_source": "independent SQL result length; no hardcoded expected count",
                "snapshot_note": "API requests use separate snapshots; source fingerprint is checked again after all requests."},
    )
    with psycopg2.connect(dsn, connect_timeout=5) as connection:
        connection.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(args.sql_timeout_ms),))
            cursor.execute("SELECT set_config('lock_timeout', '1000', true)")
            cursor.execute("SELECT txid_current_snapshot()::text, transaction_timestamp()::text")
            snapshot, captured_at = cursor.fetchone()
        report["oracle"].update(snapshot=snapshot, captured_at=captured_at)
        initial_rows = reference_rows(connection, layer, profile, targets)
        report["oracle"].update(total_count=len(initial_rows), source_sha256=source_digest(initial_rows))
        if not initial_rows:
            raise VerificationError("The confirmed reference has no real hazard features; this live acceptance scenario requires a populated source")
        for case in cases:
            checks, started = Checks(), time.monotonic()
            payload = {key: case[key] for key in ("query", "task_id", "spatial_context", "user_id") if key in case}
            payload.setdefault("task_id", "radius-verification-" + str(uuid4()))
            entry = {"name": case["name"], "validation_kind": "actual_api_and_database", "request": payload}
            report["cases"].append(entry)
            try:
                event, event_names = stream_request(args.base_url, payload, args.timeout)
                checks.require("completed_has_final_result", isinstance(event.get("final_result"), dict))
                result = event.get("final_result") or {}
                checks.equal("outer_terminal_status_matches_result", event.get("status"), result.get("status"))
                entry["sse_events"] = event_names
                if "expected_status" in case:
                    entry["result"] = verify_no_execution(result, case["expected_status"], case.get("require_candidate", False), checks)
                else:
                    oracle = reference_rows(connection, layer, profile, case["targets"])
                    entry["result"] = verify_success(result, oracle, case["targets"], payload["spatial_context"].get("offset", 0), checks)
            except Exception as exc:
                entry["error"] = safe_error(exc)
                checks.require("case_execution_completed", False)
            entry.update(passed=checks.passed, assertions=checks.items, duration_ms=round((time.monotonic() - started) * 1000))
            print("{} {}".format("PASS" if entry["passed"] else "FAIL", case["name"]), flush=True)
        connection.commit()
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(args.sql_timeout_ms),))
            cursor.execute("SELECT set_config('lock_timeout', '1000', true)")
        final_rows = reference_rows(connection, layer, profile, targets)
        consistency = Checks()
        consistency.equal("source_stable_across_api_requests", source_digest(final_rows), source_digest(initial_rows))
        pages = {item["name"]: item.get("result", {}) for item in report["cases"]}
        first, second = pages["confirmed_reference_first_page"], pages["confirmed_reference_next_page"]
        consistency.require("pagination_cases_succeeded", bool(first.get("status", "").startswith("SUCCESS")) and bool(second.get("status", "").startswith("SUCCESS")))
        consistency.equal("pagination_total_unchanged", first.get("total_count"), second.get("total_count"))
        consistency.equal("pagination_disjoint_ids", sorted(set(first.get("ordered_feature_ids", [])) & set(second.get("ordered_feature_ids", []))), [])
        report["cases"].append({"name": "cross_request_consistency", "validation_kind": "actual_api_and_database", "passed": consistency.passed, "assertions": consistency.items})


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--startup-timeout", type=float, default=120)
    parser.add_argument("--sql-timeout-ms", type=int, default=20000)
    args = parser.parse_args(argv)
    url = urlsplit(args.base_url)
    if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
        parser.error("--base-url must be an HTTP(S) URL without credentials, query, or fragment")
    if not math.isfinite(args.timeout) or not math.isfinite(args.startup_timeout) or args.timeout <= 0 or args.startup_timeout <= 0 or args.sql_timeout_ms <= 0:
        parser.error("timeouts must be positive")
    report = {"schema_version": "1.0", "started_at": datetime.now(timezone.utc).isoformat(),
              "validation_kind": "actual_api_and_database", "api_base_url": args.base_url,
              "synthetic_tests": {"status": "not_run", "reason": "This verifier only checks the running API and actual PostGIS source."},
              "cases": []}
    try:
        run(args, report)
    except Exception as exc:
        report["error"] = safe_error(exc)
    report["passed"] = bool(report["cases"]) and "error" not in report and all(case["passed"] for case in report["cases"])
    report["summary"] = {"cases": len(report["cases"]), "passed": sum(case["passed"] for case in report["cases"]),
                         "failed": sum(not case["passed"] for case in report["cases"])}
    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "summary": report["summary"], "report": str(args.output)}, ensure_ascii=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
