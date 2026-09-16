"""Registry-backed AIS/V-PASS traffic volume execution."""

from __future__ import annotations

import json
import math
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
import yaml


DATA_DIR = Path(__file__).resolve().parents[2] / "data"

KNOWN_PLACES = {
    "부산항 입구": ("부산항 입구", "POINT(129.075 35.075)"),
    "부산항": ("부산항", "POINT(129.075 35.075)"),
    "부산": ("부산항", "POINT(129.075 35.075)"),
    "인천항": ("인천항", "POINT(126.592 37.456)"),
    "인천": ("인천항", "POINT(126.592 37.456)"),
    "busan port entrance": ("Busan Port Entrance", "POINT(129.075 35.075)"),
    "busan port": ("Busan Port", "POINT(129.075 35.075)"),
    "incheon port": ("Incheon Port", "POINT(126.592 37.456)"),
}


class TrafficProblem(Exception):
    def __init__(self, status: str, code: str, message: str):
        super().__init__(message)
        self.status = status
        self.code = code


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _registry(filename: str) -> dict:
    try:
        return yaml.safe_load((DATA_DIR / filename).read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise TrafficProblem("BLOCKED_CONFIG", "INVALID_REGISTRY", "Traffic registry is not readable.") from exc


def _db_url() -> str:
    url = os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL")
    if not url:
        raise TrafficProblem("BLOCKED_CONFIG", "DB_NOT_CONFIGURED", "PostGIS connection is not configured.")
    return url


def _traffic_layers() -> list[dict[str, Any]]:
    registry = _registry("traffic_layer_registry.yaml")
    layers = []
    for layer_id, layer in (registry.get("layers") or {}).items():
        if layer.get("execution_status") == "executable" and layer.get("physical_table"):
            layers.append({"layer_id": layer_id, **layer})
    return layers


def _tile_layers() -> list[dict[str, Any]]:
    return [
        layer
        for layer in _traffic_layers()
        if layer.get("layer_type") == "dynamic_traffic_tile" or layer.get("geometry_type") == "raster_tile"
    ]


def traffic_layer_ready() -> bool:
    return bool(_traffic_layers())


def _source_filter(query: str) -> list[str]:
    lowered = (query or "").lower()
    sources = []
    if "ais" in lowered:
        sources.append("AIS")
    if "v-pass" in lowered or "vpass" in lowered or "V-PASS" in query:
        sources.append("V-PASS")
    return sources or ["AIS", "V-PASS"]


def _distance_m(query: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(km|㎞|킬로|m|미터)", query or "", re.I)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2).lower()
    return value * 1000 if unit in {"km", "㎞", "킬로"} else value


def _reference(query: str, state: dict) -> tuple[str | None, str | None, float | None]:
    spatial = state.get("spatial_context") or {}
    if hasattr(spatial, "model_dump"):
        spatial = spatial.model_dump()
    if not isinstance(spatial, dict):
        spatial = {}
    if spatial.get("geometry"):
        return str(spatial["geometry"]), spatial.get("base_location") or spatial.get("location_text") or "request geometry", spatial.get("buffer_distance")
    text = " ".join(str(item or "") for item in [query, spatial.get("base_location"), spatial.get("location_text")]).lower()
    compact_text = re.sub(r"\s+", "", text)
    for alias, (label, wkt) in KNOWN_PLACES.items():
        if alias.lower() in text or re.sub(r"\s+", "", alias.lower()) in compact_text:
            return wkt, label, _distance_m(query) or spatial.get("buffer_distance") or 50000.0
    return None, None, None


def _temporal_window(query: str) -> dict:
    text = query or ""
    if any(term in text.lower() or term in text for term in ["최근 1년", "최근 일년", "지난 1년", "last year", "past year"]):
        return {"preset": "last_1_year", "duration": "P1Y", "source": "query_text"}
    match = re.search(r"(?:최근|지난)\s*(\d+)\s*(년|개월|달|일)", text)
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        designator = {"년": "Y", "개월": "M", "달": "M", "일": "D"}[unit]
        return {"preset": f"last_{value}_{unit}", "duration": f"P{value}{designator}", "source": "query_text"}
    return {"preset": "latest_available", "duration": None, "source": "default"}


def _effective_month_filter(cur, sources: list[str], temporal_window: dict) -> tuple[str, dict]:
    cur.execute(
        """
        SELECT min(observed_month) AS min_month, max(observed_month) AS max_month,
               array_agg(DISTINCT to_char(observed_month, 'YYYYMM') ORDER BY to_char(observed_month, 'YYYYMM')) AS months
        FROM serving.dynamic_traffic_layer
        WHERE layer_source = ANY(%s)
        """,
        (sources,),
    )
    row = cur.fetchone()
    if not row or not row["max_month"]:
        raise TrafficProblem("BLOCKED_DATA", "NO_TRAFFIC_ROWS", "No executable AIS/V-PASS traffic rows are loaded.")
    if temporal_window.get("preset") == "last_1_year":
        where_sql = "observed_month >= (%(max_month)s::date - interval '11 months') AND observed_month <= %(max_month)s::date"
        interpretation = "latest_available_12_months"
    else:
        where_sql = "observed_month <= %(max_month)s::date"
        interpretation = "latest_available"
    metadata = {
        "requested_temporal_window": temporal_window,
        "effective_temporal_window": {
            "interpretation": interpretation,
            "min_available_month": str(row["min_month"]),
            "max_available_month": str(row["max_month"]),
            "available_months": row["months"] or [],
            "warning": "Current-year AIS/V-PASS observations are not loaded; query uses the latest loaded traffic months.",
        },
        "max_month": str(row["max_month"]),
    }
    return where_sql, metadata


def _traffic_tile_summary(cur, sources: list[str]) -> dict[str, Any]:
    tile_layers = _tile_layers()
    cur.execute("SELECT to_regclass('serving.dynamic_traffic_tile_layer') AS relation")
    if not tile_layers or not cur.fetchone()["relation"]:
        return {
            "status": "NOT_LOADED",
            "table": "serving.dynamic_traffic_tile_layer",
            "layers": [],
            "total_tiles": 0,
        }
    cur.execute(
        """
        SELECT layer_id,
               layer_source,
               count(*) AS tile_count,
               min(observed_month) AS min_month,
               max(observed_month) AS max_month,
               array_agg(DISTINCT to_char(observed_month, 'YYYYMM') ORDER BY to_char(observed_month, 'YYYYMM')) AS months,
               array_agg(DISTINCT zoom_level ORDER BY zoom_level) AS zooms,
               sum(tile_size_bytes)::bigint AS total_size_bytes
        FROM serving.dynamic_traffic_tile_layer
        WHERE layer_source = ANY(%s)
        GROUP BY layer_id, layer_source
        ORDER BY layer_id, layer_source
        """,
        (sources,),
    )
    rows = [dict(row) for row in cur.fetchall()]
    return {
        "status": "READY" if rows else "NO_MATCHING_SOURCE",
        "table": "serving.dynamic_traffic_tile_layer",
        "layers": rows,
        "total_tiles": sum(int(row.get("tile_count") or 0) for row in rows),
        "registered_layers": [layer["layer_id"] for layer in tile_layers],
    }


def _fmt_int(value: Any) -> str:
    try:
        return f"{int(value or 0):,}"
    except Exception:
        return "0"


def _month_range_text(months: list[Any]) -> str:
    clean = [str(month) for month in months if month]
    if not clean:
        return "available months"
    if len(clean) == 1:
        return clean[0]
    return f"{clean[0]}-{clean[-1]}"


def _source_total(source_breakdown: dict[str, Any], source: str) -> int:
    row = source_breakdown.get(source) or {}
    try:
        return int(row.get("vessel_count_total") or 0)
    except Exception:
        return 0


def _traffic_analysis_brief(
    *,
    result: dict[str, Any],
    rows: list[dict[str, Any]],
    sources: list[str],
    temporal_metadata: dict[str, Any],
    ref_label: str | None,
    distance_m: float | None,
) -> dict[str, Any]:
    effective = temporal_metadata.get("effective_temporal_window") or {}
    months = effective.get("available_months") or []
    source_breakdown = result.get("source_breakdown") or {}
    monthly_rows = result.get("monthly_breakdown") or []
    top_months: dict[str, int] = {}
    for row in monthly_rows:
        month = str(row.get("month") or "")
        if month:
            top_months[month] = top_months.get(month, 0) + int(row.get("vessel_count_total") or 0)
    ranked_months = sorted(top_months.items(), key=lambda item: item[1], reverse=True)[:3]
    dominant_source = max(source_breakdown, key=lambda source: _source_total(source_breakdown, source)) if source_breakdown else None
    return {
        "analysis_scope": {
            "sources": sources,
            "period": _month_range_text(months),
            "interpretation": effective.get("interpretation"),
            "reference_place": ref_label,
            "distance_m": distance_m,
            "grid_row_count": int(result.get("grid_count") or 0),
            "displayed_cell_count": len(rows),
        },
        "total_traffic_count": int(result.get("vessel_count_total") or 0),
        "source_totals": {
            "AIS": _source_total(source_breakdown, "AIS"),
            "V-PASS": _source_total(source_breakdown, "V-PASS"),
        },
        "dominant_source": dominant_source,
        "top_months": [{"month": month, "traffic": traffic} for month, traffic in ranked_months],
        "top_cells": [
            {
                "rank": idx + 1,
                "grid_id": row.get("grid_id"),
                "month": row.get("observed_month"),
                "traffic": int(row.get("vessel_count_total") or 0),
                "ais": int(((row.get("source_counts") or {}).get("AIS") or {}).get("vessel_count_total") or 0),
                "vpass": int(((row.get("source_counts") or {}).get("V-PASS") or {}).get("vessel_count_total") or 0),
                "day": int(row.get("vessel_count_day") or 0),
                "night": int(row.get("vessel_count_night") or 0),
            }
            for idx, row in enumerate(rows[:5])
        ],
    }


def _fallback_traffic_answer(brief: dict[str, Any]) -> str:
    scope = brief.get("analysis_scope") or {}
    source_totals = brief.get("source_totals") or {}
    top_cells = brief.get("top_cells") or []
    top_months = brief.get("top_months") or []
    place = scope.get("reference_place")
    distance_m = scope.get("distance_m")
    place_text = f"{place} 반경 {float(distance_m) / 1000:.1f}km" if place and distance_m else "조회 구역"
    lines = [
        f"{place_text}의 AIS/V-PASS 통항량은 {scope.get('period')} 기준 총 {_fmt_int(brief.get('total_traffic_count'))}건입니다.",
        f"출처별로는 AIS {_fmt_int(source_totals.get('AIS'))}건, V-PASS {_fmt_int(source_totals.get('V-PASS'))}건이며, V-PASS 비중이 더 크게 나타납니다.",
    ]
    if top_months:
        month_text = ", ".join(f"{item['month']} {_fmt_int(item['traffic'])}건" for item in top_months)
        lines.append(f"월별 피크는 {month_text} 순입니다.")
    if top_cells:
        cell_text = "; ".join(
            f"{cell['rank']}위 격자 {cell.get('grid_id')}({cell.get('month')}) {_fmt_int(cell.get('traffic'))}건"
            for cell in top_cells[:3]
        )
        lines.append(f"상위 혼잡 구역은 {cell_text}으로, 지도에서 해당 격자를 클릭해 AIS/V-PASS 세부 값을 확인할 수 있습니다.")
    lines.append("이 기간은 현재일 기준이 아니라 적재된 최신 가용월 기준 최근 12개월입니다.")
    return "\n".join(lines)


def _try_llm_traffic_answer(query: str, brief: dict[str, Any]) -> tuple[str | None, bool]:
    try:
        from services.llm_config import llm_api_enabled, ollama_base_url

        if os.getenv("ENABLE_TRAFFIC_LLM", "").lower() not in {"1", "true", "yes", "on"}:
            return None, False
        if not llm_api_enabled():
            return None, False
        import requests

        scope = brief.get("analysis_scope") or {}
        source_totals = brief.get("source_totals") or {}
        top_months = brief.get("top_months") or []
        top_cells = brief.get("top_cells") or []
        month_facts = ", ".join(f"{item.get('month')} {_fmt_int(item.get('traffic'))}건" for item in top_months[:3])
        cell_facts = "; ".join(
            f"{cell.get('rank')}위 {cell.get('grid_id')} {cell.get('month')} 총 {_fmt_int(cell.get('traffic'))}건 "
            f"(AIS {_fmt_int(cell.get('ais'))}, V-PASS {_fmt_int(cell.get('vpass'))})"
            for cell in top_cells[:3]
        )
        facts = (
            f"기간 {scope.get('period')}, 총합 {_fmt_int(brief.get('total_traffic_count'))}건, "
            f"AIS {_fmt_int(source_totals.get('AIS'))}건, V-PASS {_fmt_int(source_totals.get('V-PASS'))}건. "
            f"피크월 {month_facts}. 혼잡격자 {cell_facts}. "
            "적재 최신월 기준 최근 12개월."
        )
        prompt = (
            "너는 해상교통 분석가다. 아래 사실만 근거로 한국어 답변을 정확히 2문장 작성하라. "
            "1문장은 기간/총합/AIS와 V-PASS 비중, 2문장은 피크월/상위 혼잡 격자를 설명하라. 각 문장은 마침표로 끝내라.\n"
            f"{facts}"
        )
        response = requests.post(
            ollama_base_url() + "/api/generate",
            json={
                "model": os.getenv("OLLAMA_MODEL") or os.getenv("LLM_MODEL", "gemma2"),
                "prompt": prompt,
                "stream": True,
                "options": {"temperature": 0.2, "num_predict": 150},
            },
            stream=True,
            timeout=(5.0, 120.0),
        )
        if response.status_code != 200:
            return None, False
        chunks: list[str] = []
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            token = payload.get("response")
            if token:
                chunks.append(str(token))
            if payload.get("done") or sum(len(chunk) for chunk in chunks) >= 700:
                break
        answer = "".join(chunks).strip()
        return (answer or None), bool(answer)
    except Exception:
        return None, False


def execute_traffic_request(state: dict) -> dict:
    query = " ".join(str(item or "") for item in [state.get("query", ""), state.get("normalized_query", "")])
    layers = _traffic_layers()
    if not layers:
        raise TrafficProblem("BLOCKED_DATA", "TRAFFIC_LAYER_NOT_EXECUTABLE", "Dynamic traffic layer is not executable.")
    sources = _source_filter(query)
    temporal_window = _temporal_window(query)
    ref_wkt, ref_label, distance_m = _reference(query, state)
    relation = "serving.dynamic_traffic_layer"
    limit = 50
    params: dict[str, Any] = {"sources": sources, "limit": limit}
    spatial_predicate = ""
    if ref_wkt and distance_m and math.isfinite(float(distance_m)):
        spatial_predicate = "AND ST_DWithin(t.geom::geography, ST_SetSRID(ST_GeomFromText(%(ref_wkt)s), 4326)::geography, %(distance_m)s)"
        params.update({"ref_wkt": ref_wkt, "distance_m": float(distance_m)})

    with psycopg2.connect(_db_url(), connect_timeout=5) as conn:
        conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT to_regclass('serving.dynamic_traffic_layer') AS relation")
            if not cur.fetchone()["relation"]:
                raise TrafficProblem("BLOCKED_DATA", "TRAFFIC_TABLE_MISSING", "serving.dynamic_traffic_layer is missing.")
            time_where, temporal_metadata = _effective_month_filter(cur, sources, temporal_window)
            params["max_month"] = temporal_metadata["max_month"]
            cur.execute(
                f"""
                WITH filtered AS MATERIALIZED (
                    SELECT *
                    FROM serving.dynamic_traffic_layer AS t
                    WHERE t.layer_source = ANY(%(sources)s)
                      AND {time_where}
                      {spatial_predicate}
                ),
                by_source AS (
                    SELECT layer_source,
                           count(*) AS grid_count,
                           sum(vessel_count_total) AS vessel_count_total,
                           sum(vessel_count_day) AS vessel_count_day,
                           sum(vessel_count_night) AS vessel_count_night
                    FROM filtered
                    GROUP BY layer_source
                ),
                by_month AS (
                    SELECT to_char(observed_month, 'YYYYMM') AS month,
                           layer_source,
                           sum(vessel_count_total) AS vessel_count_total
                    FROM filtered
                    GROUP BY observed_month, layer_source
                ),
                ranked_cells AS (
                    SELECT
                           concat('traffic-cell:', grid_id, ':', to_char(observed_month, 'YYYYMM')) AS source_id,
                           'dynamic_traffic_combined' AS layer_id,
                           CASE
                               WHEN count(DISTINCT layer_source) > 1 THEN 'AIS/V-PASS'
                               ELSE min(layer_source)
                           END AS layer_source,
                           grid_id,
                           max(grid_level) AS grid_level,
                           to_char(observed_month, 'YYYYMM') AS observed_month,
                           sum(vessel_count_total) AS vessel_count_total,
                           sum(vessel_count_day) AS vessel_count_day,
                           sum(vessel_count_night) AS vessel_count_night,
                           jsonb_object_agg(layer_source, jsonb_build_object(
                               'vessel_count_total', vessel_count_total,
                               'vessel_count_day', vessel_count_day,
                               'vessel_count_night', vessel_count_night
                           )) AS source_counts,
                           min(reference_place_name) AS reference_place_name,
                           min(reference_distance_m) AS reference_distance_m,
                           ST_AsGeoJSON((array_agg(geom ORDER BY layer_source))[1])::jsonb AS geometry
                    FROM filtered
                    GROUP BY grid_id, observed_month
                    ORDER BY sum(vessel_count_total) DESC, grid_id, observed_month
                    LIMIT %(limit)s
                )
                SELECT
                    (SELECT count(*) FROM filtered) AS grid_count,
                    COALESCE((SELECT sum(vessel_count_total) FROM filtered), 0) AS vessel_count_total,
                    COALESCE((SELECT jsonb_object_agg(layer_source, to_jsonb(by_source)) FROM by_source), '{{}}'::jsonb) AS source_breakdown,
                    COALESCE((SELECT jsonb_agg(to_jsonb(by_month) ORDER BY month, layer_source) FROM by_month), '[]'::jsonb) AS monthly_breakdown,
                    COALESCE((SELECT jsonb_agg(to_jsonb(ranked_cells) ORDER BY vessel_count_total DESC, source_id) FROM ranked_cells), '[]'::jsonb) AS rows
                """,
                params,
            )
            result = dict(cur.fetchone())
            result = _json_safe(result)
            tile_summary = _json_safe(_traffic_tile_summary(cur, sources))
            cur.execute("SELECT txid_current_snapshot()::text AS snapshot, transaction_timestamp()::text AS captured_at")
            snapshot = _json_safe(dict(cur.fetchone()))

    rows = result.get("rows") or []
    features = []
    table_rows = []
    for row in rows:
        props = _json_safe({k: v for k, v in row.items() if k != "geometry"})
        props["source"] = relation
        features.append({"type": "Feature", "id": row["source_id"], "geometry": row["geometry"], "properties": props})
        table_rows.append(props)
    feature_collection = {"type": "FeatureCollection", "features": features}
    evidence_counts = {
        "spatial_feature_evidence": len(table_rows),
        "spatial_layer_evidence": 2 if tile_summary.get("status") == "READY" else 1,
    }
    traffic_brief = _traffic_analysis_brief(
        result=result,
        rows=table_rows,
        sources=sources,
        temporal_metadata=temporal_metadata,
        ref_label=ref_label,
        distance_m=distance_m,
    )
    llm_answer, llm_used = _try_llm_traffic_answer(query, traffic_brief)
    summary = llm_answer or _fallback_traffic_answer(traffic_brief)
    route_plan = {
        "task_id": f"TASK-TRAFFIC-{state['task_id'][:3].upper()}",
        "status": "EXECUTION_READY",
        "intent": "TRAFFIC_ANALYSIS",
        "context": "maritime_traffic",
        "analysis_type": "traffic_search_by_time_space",
        "derived_concept": "dynamic_traffic",
        "primary_agent": "AIS Analysis Agent",
        "secondary_agents": ["Spatial Analysis Agent"],
        "slots": {
            "target_term": "dynamic_traffic",
            "analysis_type": "traffic_search_by_time_space",
            "sources": sources,
            "temporal_window": temporal_window,
            "effective_temporal_window": temporal_metadata["effective_temporal_window"],
            "reference_geometry": ref_wkt,
            "location_text": ref_label,
            "distance_m": distance_m,
        },
        "tools": ["traffic.dynamic_layer_search", "postgis.intersects", "postgis.dwithin"],
        "data": ["DynamicTrafficLayer", *[layer["layer_id"] for layer in layers]],
        "outputs": ["TrafficSummary", "GeoJSON", "EvidenceBundle"],
        "clarification_required": False,
        "confidence": 1.0,
        "execution_ready": True,
        "route_plan_status": "EXECUTION_READY",
    }
    qec = {
        "readiness": "READY",
        "blockers": [],
        "warnings": [temporal_metadata["effective_temporal_window"]["warning"]],
        "data_bindings": [{
            "dataset_id": "DynamicTrafficLayer",
            "relation": relation,
            "geometry_column": "geom",
            "temporal_column": "observed_at",
            "count_column": "vessel_count_total",
            "srid": 4326,
            "execution_status": "executable",
            "read_only": True,
        }],
        "tool_bindings": [{"tool_id": "traffic.dynamic_layer_search", "operation": "traffic_search_by_time_space", "query_template_id": "traffic_search_by_time_space"}],
    }
    structured = {
        "status": "COMPLETED",
        "analysis_type": "traffic_search_by_time_space",
        "total_traffic_count": int(result.get("vessel_count_total") or 0),
        "grid_count": int(result.get("grid_count") or 0),
        "source_breakdown": result.get("source_breakdown") or {},
        "monthly_breakdown": result.get("monthly_breakdown") or [],
        "source_layer": {"physical_table": relation, "geometry_column": "geom", "temporal_column": "observed_at", "count_column": "vessel_count_total"},
        "tile_layer_summary": tile_summary,
        "reference_geometry": {"wkt": ref_wkt, "label": ref_label, "distance_m": distance_m},
        "temporal_window": temporal_window,
        "effective_temporal_window": temporal_metadata["effective_temporal_window"],
        "features": table_rows,
        "traffic_analysis_brief": traffic_brief,
        "geojson": feature_collection,
        "geojson_feature_count": len(features),
        "map_layer_count": 1 if features else 0,
        "evidence_bundle_counts": evidence_counts,
        "web_rag_usage": {"web_used": False, "rag_used": False, "llm_used": llm_used, "execution_path": "traffic.dynamic_layer_search", "embedding_independent": True},
    }
    layer_evidence = {
        "dataset_id": "DynamicTrafficLayer",
        "relation": relation,
        "snapshot": snapshot,
        "sources": sources,
        "temporal": temporal_metadata,
        "reference_geometry": structured["reference_geometry"],
    }
    tile_evidence = {
        "dataset_id": "DynamicTrafficTileLayer",
        "relation": tile_summary.get("table"),
        "snapshot": snapshot,
        "sources": sources,
        "summary": tile_summary,
    }
    return {
        "task_id": state["task_id"],
        "trace_id": f"tr-{state['task_id']}",
        "agent_name": "AIS Analysis Agent",
        "agent_version": "1.1.0-dynamic-traffic-layer",
        "status": "COMPLETED",
        "summary": summary,
        "answer_text": summary,
        "structured_result": structured,
        "map_layers": [{
            "layer_id": f"{state['task_id']}-dynamic-traffic",
            "task_id": state["task_id"],
            "title": "AIS/V-PASS Traffic Volume",
            "description": summary,
            "geometry_type": "POLYGON",
            "source_type": "geojson",
            "inline_geojson": feature_collection,
            "feature_count": len(features),
            "metadata": {"source": relation, "query_template_id": "traffic_search_by_time_space"},
        }],
        "features": feature_collection,
        "evidence_bundle": {
            "rag_evidence": [],
            "kg_provenance": [],
            "regulatory_evidence": [],
            "spatial_feature_evidence": table_rows,
            "spatial_layer_evidence": [layer_evidence, tile_evidence] if tile_summary.get("status") == "READY" else [layer_evidence],
            "accident_relation_evidence": [],
        },
        "orchestrator_v2": {"route_plan": route_plan, "query_execution_context": qec, "embedding_independent": True, "fast_path": "dynamic_traffic_layer_execute"},
        "contract_version": "geollm.execution.v1",
        "request_id": state.get("task_id"),
    }
