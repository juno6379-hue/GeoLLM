"""Inventory AIS/V-PASS dynamic traffic archives and build registry/graph outputs."""
from __future__ import annotations

import csv, hashlib, json, re, tarfile, zipfile
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
OUT = ROOT / "outputs"

TARGETS = {
    "AIS항로분석.zip": ("AIS", "ais_route_analysis"),
    "AIS주요통항로분석.zip": ("AIS", "ais_major_route"),
    "V-PASS항로분석.zip": ("V-PASS", "vpass_route_analysis"),
    "V-PASS주요통항로분석.zip": ("V-PASS", "vpass_major_route"),
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def rel(path): return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def inspect_shapefiles(path, source):
    import geopandas as gpd
    from tempfile import TemporaryDirectory
    row_count = 0; bbox = None; geometry_types = set(); columns = set(); crs = set(); samples = []
    with TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        with zipfile.ZipFile(path) as z:
            shp_names = [x for x in z.namelist() if x.lower().endswith(".shp")]
            for shp_name in shp_names:
                prefix = shp_name[:-4]
                members = [x for x in z.namelist() if x.startswith(prefix) and Path(x).suffix.lower() in {".shp", ".shx", ".dbf", ".prj", ".cpg", ".qpj"}]
                for member in members:
                    target = tmp / Path(member).name; target.write_bytes(z.read(member))
                shp = tmp / Path(shp_name).name
                frame = gpd.read_file(shp)
                row_count += len(frame); columns.update(str(x) for x in frame.columns if x != "geometry")
                geometry_types.update(str(x) for x in frame.geometry.geom_type.dropna().unique())
                if frame.crs: crs.add(str(frame.crs))
                if not frame.empty:
                    bounds = frame.total_bounds.tolist()
                    bbox = bounds if bbox is None else [min(bbox[0], bounds[0]), min(bbox[1], bounds[1]), max(bbox[2], bounds[2]), max(bbox[3], bounds[3])]
                    if not samples: samples = frame.drop(columns=["geometry"], errors="ignore").head(3).to_dict(orient="records")
                for f in tmp.iterdir(): f.unlink()
    lower = {x.lower() for x in columns}
    with zipfile.ZipFile(path) as z:
        member_count = len([x for x in z.namelist() if x.lower().endswith(".shp")])
    return {"row_count": row_count, "geometry_type": sorted(geometry_types), "time_columns": sorted(x for x in columns if any(k in x.lower() for k in ("time", "date", "dt", "ymd"))), "vessel_identifier_columns": sorted(x for x in columns if any(k in x.lower() for k in ("mmsi", "ship", "vessel", "imo", "id"))), "speed_course_columns": sorted(x for x in columns if any(k in x.lower() for k in ("speed", "sog", "course", "cog", "heading"))), "route_density_line_grid": "grid_density", "bbox": bbox, "crs": sorted(crs), "sample_attributes": samples, "member_count": member_count, "archive_type": "shapefile_zip", "source": source}


def inspect_tiles(path, source):
    tar_count = 0; tile_count = 0; samples = []; levels = set()
    with zipfile.ZipFile(path) as z:
        tar_names = [x for x in z.namelist() if x.lower().endswith(".tar")]
        for name in tar_names:
            tar_count += 1
            with z.open(name) as stream:
                with tarfile.open(fileobj=stream, mode="r|*") as tar:
                    for member in tar:
                        if member.isfile() and member.name.lower().endswith(".png"):
                            tile_count += 1
                            match = re.search(r"/L(\d+)/", member.name)
                            if match: levels.add(match.group(1))
                            if len(samples) < 3: samples.append({"member": member.name, "size": member.size})
    return {"row_count": tile_count, "geometry_type": ["raster_tile"], "time_columns": [], "vessel_identifier_columns": [], "speed_course_columns": [], "route_density_line_grid": "major_route_raster_tile", "bbox": None, "crs": [], "sample_attributes": samples, "member_count": tar_count, "tile_levels": sorted(levels), "archive_type": "tar_png_tiles", "source": source}


def main():
    rows = []
    for filename, (source_type, layer_id) in TARGETS.items():
        path = DATASET / filename
        with zipfile.ZipFile(path) as z: is_grid = any(x.lower().endswith(".shp") for x in z.namelist())
        info = inspect_shapefiles(path, rel(path)) if is_grid else inspect_tiles(path, rel(path))
        info.update({"layer_id": layer_id, "source_type": source_type, "source_path": rel(path), "source_sha256": sha256(path), "data_type": "dynamic_traffic_derived"})
        rows.append(info)
    inv = OUT / "inventories/ais_vpass_inventory.csv"; inv.parent.mkdir(parents=True, exist_ok=True)
    fields = ["layer_id", "source_type", "source_path", "source_sha256", "data_type", "archive_type", "member_count", "row_count", "geometry_type", "time_columns", "vessel_identifier_columns", "speed_course_columns", "route_density_line_grid", "bbox", "crs", "tile_levels", "sample_attributes"]
    with inv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for row in rows: w.writerow({k: json.dumps(row.get(k, []), ensure_ascii=False) if isinstance(row.get(k), (list, dict)) else row.get(k, "") for k in fields})
    registry = {"version": "3.0", "layers": {}}
    for row in rows:
        registry["layers"][row["layer_id"]] = {"data_type": row["data_type"], "source": row["source_type"], "source_path": row["source_path"], "geometry_type": row["geometry_type"], "time_columns": row["time_columns"], "vessel_identifier_columns": row["vessel_identifier_columns"], "speed_course_columns": row["speed_course_columns"], "route_density_line_grid": row["route_density_line_grid"], "row_count": row["row_count"], "bbox": row["bbox"], "crs": row["crs"], "related_concepts": (["traffic_density", "collision_risk", "route_risk"] if row["source_type"] == "AIS" else ["small_vessel_traffic", "collision_risk", "rescue_vulnerability"]), "related_agents": (["AIS Analysis Agent", "Spatial Analysis Agent", "Situation Interpretation Agent"] if row["source_type"] == "AIS" else ["V-PASS Analysis Agent", "Spatial Analysis Agent", "Situation Interpretation Agent"]), "provenance": {"source_path": row["source_path"], "source_sha256": row["source_sha256"]}}
    reg = OUT / "registries/traffic_layer_registry.yaml"; reg.parent.mkdir(parents=True, exist_ok=True); reg.write_text(yaml.safe_dump(registry, allow_unicode=True, sort_keys=False), encoding="utf-8")
    dict_out = OUT / "dictionaries/traffic_data_dictionary.yaml"; dict_out.parent.mkdir(parents=True, exist_ok=True); dict_out.write_text(yaml.safe_dump({"version": "3.0", "dynamic_layer": True, "source_types": ["AIS", "V-PASS"], "fields": {"observed_at": {"role": "observation_time", "required": False}, "vessel_identifier": {"role": "vessel_identity", "required": False}, "speed": {"role": "speed", "required": False}, "course": {"role": "course", "required": False}, "geometry": {"role": "route_or_density_geometry", "required": True}}, "layers": registry["layers"]}, allow_unicode=True, sort_keys=False), encoding="utf-8")
    nodes = []; concept_edges = []; overlap_edges = []
    for row in rows:
        node_id = f"dynamic_traffic_layer:{row['layer_id']}"; nodes.append({"id": node_id, "node_type": "DynamicTrafficLayer", "name": row["layer_id"], "properties": row, "provenance": {"source_path": row["source_path"], "source_sha256": row["source_sha256"]}})
        concepts = registry["layers"][row["layer_id"]]["related_concepts"]
        for concept in concepts: concept_edges.append({"id": f"{node_id}|relatedTo|{concept}", "subject_id": node_id, "predicate": "relatedToConcept", "object_id": f"derived_concept:{concept}", "status": "CANDIDATE", "provenance": nodes[-1]["provenance"]})
        overlap_edges.append({"id": f"{node_id}|overlapsLayer|datalayer:gbenc_s101_feature", "subject_id": node_id, "predicate": "overlapsLayer", "object_id": "datalayer:gbenc_s101_feature", "status": "PENDING_SPATIAL_JOIN", "provenance": nodes[-1]["provenance"]})
    graph = OUT / "graph"; graph.mkdir(parents=True, exist_ok=True)
    (graph / "nodes_dynamic_traffic_layers.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in nodes), encoding="utf-8")
    (graph / "edges_traffic_related_to_concept.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in concept_edges), encoding="utf-8")
    (graph / "edges_traffic_overlaps_layer.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in overlap_edges), encoding="utf-8")
    report = OUT / "reports/10_ais_vpass_integration_report.md"
    report.write_text("# AIS/V-PASS Dynamic Traffic Integration\n\n" + "\n".join(f"- `{r['layer_id']}`: {r['source_type']}, {r['archive_type']}, {r['row_count']} rows/tiles, geometry={','.join(r['geometry_type'])}, CRS={','.join(r['crs']) or 'not declared'}" for r in rows) + "\n\nAIS/V-PASS is registered as DynamicTrafficLayer and is not modeled as an S-101 static Feature. Concept relations are CANDIDATE; overlap with S-101 layers remains PENDING_SPATIAL_JOIN until both serving geometries are loaded into a common CRS.\n", encoding="utf-8")
    print(json.dumps({"layers": len(rows), "nodes": len(nodes), "concept_edges": len(concept_edges), "overlap_edges": len(overlap_edges)}))


if __name__ == "__main__": main()
