"""Build accident dictionary, spatial layer metadata, RAG chunks and KG edges."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
OUT = ROOT / "outputs"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def decode_best(raw):
    candidates = []
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            value = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        score = sum(1 for char in value if 0xAC00 <= ord(char) <= 0xD7A3) - value.count("\ufffd") * 10000
        candidates.append((score, encoding, value))
    if not candidates:
        return raw.decode("utf-8", errors="replace"), "utf-8-replace"
    _, encoding, value = max(candidates, key=lambda item: item[0])
    return value, encoding


def read_csv(path):
    text, encoding = decode_best(path.read_bytes())
    rows = list(csv.DictReader(text.splitlines()))
    return rows, encoding


def rel(path):
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def find_files():
    csvs = list(DATASET.glob("*.csv"))
    def first(*terms):
        return next((p for p in csvs if all(term in p.name for term in terms)), None)
    targets = {
        "detailed": first("해상조난사고", "상세데이터"),
        "type_summary": first("해상조난사고", "유형별"),
        "area_summary": first("해상조난사고", "해역별"),
        "central": first("사고정보", "중앙해양"),
    }
    archives = [p for p in DATASET.glob("*.zip") if "선박사고" in p.name or "인명사고" in p.name]
    return targets, archives


def dms(value):
    if value is None:
        return None
    nums = re.findall(r"-?\d+(?:\.\d+)?", str(value))
    if not nums:
        return None
    parts = [float(x) for x in nums[:3]]
    result = abs(parts[0]) + (parts[1] / 60 if len(parts) > 1 else 0) + (parts[2] / 3600 if len(parts) > 2 else 0)
    return -result if parts[0] < 0 else result


def number(value):
    try:
        return int(float(str(value).replace(",", "")))
    except (TypeError, ValueError):
        return None


def shapefile_info(path):
    result = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.lower().endswith(".shp"):
                continue
            raw = archive.read(name)
            shape_type = struct.unpack("<i", raw[32:36])[0] if len(raw) >= 36 else None
            bbox = list(struct.unpack("<4d", raw[36:68])) if len(raw) >= 68 else None
            record_count = 0
            offset = 100
            while offset + 8 <= len(raw):
                words = struct.unpack(">i", raw[offset + 4:offset + 8])[0]
                if words <= 0:
                    break
                record_count += 1
                offset += 8 + words * 2
            dbf_fields = []
            dbf_name = name[:-4] + ".dbf"
            if dbf_name in archive.namelist():
                dbf = archive.read(dbf_name)
                if len(dbf) >= 32:
                    header_len = struct.unpack("<H", dbf[8:10])[0]
                    for position in range(32, min(header_len - 1, len(dbf)), 32):
                        if dbf[position] == 0x0D:
                            break
                        field = dbf[position:position + 11].split(b"\0", 1)[0].decode("ascii", errors="replace")
                        if field:
                            dbf_fields.append(field)
            result.append({"member": name, "shape_type": shape_type, "geometry_type": {1: "Point", 3: "Polyline", 5: "Polygon", 8: "MultiPoint"}.get(shape_type, f"ShapeType_{shape_type}"), "row_count": record_count, "bbox": bbox, "attributes": dbf_fields})
    return result


def yaml_like(value):
    # JSON is valid YAML 1.2 and preserves Korean text and nested provenance exactly.
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def main():
    targets, archives = find_files()
    missing = [name for name, path in targets.items() if path is None]
    detailed_rows, detailed_encoding = read_csv(targets["detailed"]) if targets["detailed"] else ([], None)
    type_rows, type_encoding = read_csv(targets["type_summary"]) if targets["type_summary"] else ([], None)
    area_rows, area_encoding = read_csv(targets["area_summary"]) if targets["area_summary"] else ([], None)
    central_rows, central_encoding = read_csv(targets["central"]) if targets["central"] else ([], None)

    source_files = [path for path in targets.values() if path] + archives
    provenance = lambda path: {"source_path": rel(path), "source_sha256": sha256(path)}
    event_features = []
    skipped_coordinates = 0
    for index, row in enumerate(detailed_rows, 1):
        latitude = dms(row.get("위도")); longitude = dms(row.get("경도"))
        if latitude is None or longitude is None:
            skipped_coordinates += 1
            continue
        event_id = f"accident-event:coastguard-2025-{index:06d}"
        event_features.append({"type": "Feature", "id": event_id, "geometry": {"type": "Point", "coordinates": [longitude, latitude]}, "properties": {"event_id": event_id, "occurred_at": row.get("발생일시"), "area": row.get("발생해역"), "authority": row.get("관할해경서"), "weather": row.get("기상상태"), "cause": row.get("발생원인"), "accident_type": row.get("발생유형"), "vessel_count": number(row.get("사고선박수")), "people": number(row.get("발생인원")), "rescued": number(row.get("구조")), "injured": number(row.get("부상")), "dead": number(row.get("사망")), "missing": number(row.get("실종")), "vessel_type": row.get("선 종"), "tonnage": row.get("톤수")}})

    spatial_path = OUT / "standardized/accident_spatial_layers.geojson"
    spatial_path.parent.mkdir(parents=True, exist_ok=True)
    spatial_path.write_text(json.dumps({"type": "FeatureCollection", "name": "coastguard_accident_events_2025", "crs": {"type": "name", "properties": {"name": "EPSG:4326"}}, "features": event_features}, ensure_ascii=False), encoding="utf-8")

    archive_layers = []
    for path in archives:
        archive_layers.append({"layer_id": "accident_archive:" + path.stem, "source_type": "accident_data", "source_path": rel(path), "archive_sha256": sha256(path), "geometry_source": shapefile_info(path), "standardized_status": "METADATA_AND_SOURCE_ARCHIVE", "crs_policy": "reproject_to_EPSG:4326_during_staging", "provenance": provenance(path)})
    layers = [{"layer_id": "accident_events_coastguard_2025", "layer_type": "AccidentEventLayer", "geometry_type": "Point", "crs": "EPSG:4326", "row_count": len(event_features), "source_path": rel(targets["detailed"]) if targets["detailed"] else None, "provenance": provenance(targets["detailed"]) if targets["detailed"] else {}}] + archive_layers

    type_names = sorted({row.get("발생유형", "").strip() for row in detailed_rows if row.get("발생유형")})
    concept_map = {
        "침몰": ["navigation_hazard_object", "grounding_risk"], "좌초": ["navigation_hazard_object", "grounding_risk"],
        "충돌": ["navigation_hazard_object", "collision_risk"], "접촉": ["navigation_hazard_object", "collision_risk"],
        "전복": ["navigation_hazard_object", "rescue_vulnerability"], "침수": ["navigation_hazard_object", "rescue_vulnerability"],
        "화재": ["navigation_hazard_object", "accident_hotspot"], "기관손상": ["navigation_hazard_object", "accident_hotspot"],
    }
    default_concepts = ["accident_hotspot", "navigation_hazard_object"]
    dictionary = {"version": "2.0", "source_type": "accident_data", "coordinate_policy": "DMS_to_decimal_degrees", "standard_crs": "EPSG:4326", "fields": {"event_id": "stable event identifier", "occurred_at": "event timestamp", "accident_type": "normalized accident type", "geometry": "Point location when available", "provenance": "source path and SHA-256"}, "accident_types": {name: {"aliases": [name], "maps_to_concepts": concept_map.get(name, default_concepts), "source": "해상조난사고 상세데이터"} for name in type_names}, "aggregate_fields": {"type_summary": list(type_rows[0].keys()) if type_rows else [], "area_summary": list(area_rows[0].keys()) if area_rows else [], "central_system": list(central_rows[0].keys()) if central_rows else []}, "source_files": [{"path": rel(path), "sha256": sha256(path)} for path in source_files], "quality": {"detailed_rows": len(detailed_rows), "events_with_geometry": len(event_features), "missing_coordinates": skipped_coordinates, "csv_encodings": {"detailed": detailed_encoding, "type_summary": type_encoding, "area_summary": area_encoding, "central": central_encoding}}}

    (OUT / "dictionaries").mkdir(parents=True, exist_ok=True)
    (OUT / "dictionaries/accident_dictionary.yaml").write_text(yaml_like(dictionary), encoding="utf-8")
    registry = {"version": "2.0", "layers": {layer["layer_id"]: layer for layer in layers}, "derived_concept_relations": {"accident_events_coastguard_2025": ["accident_hotspot", "navigation_hazard_object", "collision_risk", "grounding_risk", "rescue_vulnerability"]}, "related_agents": ["Accident/Risk Agent", "Spatial Analysis Agent", "Validation Agent", "Map Report Agent"], "provenance": {"generator": "scripts/build_accident_artifacts.py", "source_files": [rel(path) for path in source_files]}}
    (OUT / "registries").mkdir(parents=True, exist_ok=True)
    (OUT / "registries/accident_layer_registry.yaml").write_text(yaml_like(registry), encoding="utf-8")

    rag_rows = []
    def add_chunk(source, title, body, encoding=None):
        metadata = {"source_id": "accident:" + source.stem, "source_path": rel(source), "source_type": "accident_data", "source_sha256": sha256(source), "title": title, "extraction_status": "structured_csv_summary", "encoding": encoding, "provenance": provenance(source)}
        for offset in range(0, max(len(body), 1), 1200):
            content = body[offset:offset + 1200]
            rag_rows.append({"chunk_id": hashlib.sha256(f"{metadata['source_id']}:{offset}".encode()).hexdigest()[:24], "text": content, "metadata": dict(metadata, chunk_index=offset // 1200)})
    if targets["detailed"]:
        sample = "\n".join(",".join(str(row.get(key, "")) for key in detailed_rows[0].keys()) for row in detailed_rows[:80]) if detailed_rows else ""
        add_chunk(targets["detailed"], "해상조난사고 상세데이터 표준화 요약", f"사고 이벤트 수: {len(detailed_rows)}\n공간화 이벤트 수: {len(event_features)}\n사고 유형: {', '.join(type_names)}\n샘플 원문:\n{sample}", detailed_encoding)
    for source, title, rows, encoding in ((targets["type_summary"], "해상조난사고 유형별 집계", type_rows, type_encoding), (targets["area_summary"], "해상조난사고 해역별 집계", area_rows, area_encoding), (targets["central"], "해양안전종합정보시스템 사고 집계", central_rows, central_encoding)):
        if source:
            add_chunk(source, title, json.dumps(rows, ensure_ascii=False, indent=2), encoding)
    for archive in archives:
        add_chunk(archive, "사고공간 Shapefile 아카이브 메타데이터", json.dumps(shapefile_info(archive), ensure_ascii=False, indent=2))
    rag_path = OUT / "rag/accident_chunks.jsonl"
    rag_path.parent.mkdir(parents=True, exist_ok=True)
    rag_path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rag_rows), encoding="utf-8")

    nodes_events = [{"id": feature["id"], "node_type": "AccidentEvent", "name": feature["properties"].get("accident_type") or feature["id"], "properties": feature["properties"], "geometry": feature["geometry"], "provenance": provenance(targets["detailed"])} for feature in event_features]
    nodes_types = [{"id": "accident-type:" + name, "node_type": "AccidentType", "name": name, "properties": {"maps_to_concepts": concept_map.get(name, default_concepts)}, "provenance": provenance(targets["detailed"])} for name in type_names]
    graph_dir = OUT / "graph"; graph_dir.mkdir(parents=True, exist_ok=True)
    (graph_dir / "nodes_accident_events.jsonl").write_text("".join(json.dumps(node, ensure_ascii=False) + "\n" for node in nodes_events), encoding="utf-8")
    (graph_dir / "nodes_accident_types.jsonl").write_text("".join(json.dumps(node, ensure_ascii=False) + "\n" for node in nodes_types), encoding="utf-8")
    edges = []
    for node in nodes_types:
        for concept in node["properties"]["maps_to_concepts"]:
            edges.append({"id": f"{node['id']}|mapsToConcept|derived-concept:{concept}", "subject_id": node["id"], "predicate": "mapsToConcept", "object_id": "derived_concept:" + concept, "status": "CANDIDATE", "provenance": node["provenance"]})
    edges.append({"id": "accident-events-coastguard-2025|supportsConcept|derived_concept:accident_hotspot", "subject_id": "accident_events_coastguard_2025", "predicate": "supportsConcept", "object_id": "derived_concept:accident_hotspot", "status": "CANDIDATE", "provenance": provenance(targets["detailed"])})
    (graph_dir / "edges_accident_related_to_concept.jsonl").write_text("".join(json.dumps(edge, ensure_ascii=False) + "\n" for edge in edges), encoding="utf-8")

    report = ["# Accident Data Integration Report", "", f"- 상세사고 원문: {len(detailed_rows)}건", f"- 공간화 이벤트: {len(event_features)}건", f"- 사고 유형: {len(type_names)}종", f"- RAG chunk: {len(rag_rows)}건", f"- 사고 레이어: {len(layers)}개", f"- 좌표 누락: {skipped_coordinates}건", "", "## Derived Concept 연결", "", "사고 유형은 `mapsToConcept` 후보 관계로 `navigation_hazard_object`, `grounding_risk`, `collision_risk`, `rescue_vulnerability`, `accident_hotspot`에 연결했습니다. 공간 기반 `occurredIn`, `nearFeature`, `overlapsFeature`는 사고 위치와 대상 geometry가 함께 검증될 때만 VERIFIED로 승격해야 합니다.", "", "## 처리 보류", "", "누락 파일: " + (", ".join(missing) if missing else "없음"), "ZIP Shapefile은 원본 archive provenance와 DBF/SHP 메타데이터를 등록했으며, EPSG:4326 재투영 및 PostGIS 적재는 Staging 단계의 후속 작업입니다."]
    report_path = OUT / "reports/11_accident_data_report.md"; report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"detailed_rows": len(detailed_rows), "event_nodes": len(nodes_events), "type_nodes": len(nodes_types), "rag_chunks": len(rag_rows), "layers": len(layers), "missing": missing}, ensure_ascii=False))


if __name__ == "__main__":
    main()
