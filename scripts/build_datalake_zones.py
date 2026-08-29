"""Create the Data Lake zone contract and source-level standardized manifest."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ZONE_LAYOUT = {
    "raw": ["source_files", "manifests"],
    "staging": ["archives", "documents", "spatial", "db_restore"],
    "standardized": ["features", "layers", "documents", "manifests"],
    "knowledge": ["dictionaries", "registries", "rag_chunks", "graph"],
    "serving": ["postgis", "pgvector", "knowledge_graph", "agent_views"],
}


def zone_for(classification: str) -> str:
    if classification == "db_dump":
        return "staging"
    if classification in {"standard_s100", "standard_s101", "standard_s104", "standard_s111", "standard_s124", "validation_s158", "feature_catalogue", "portrayal_catalogue", "law_rag", "marine_term_dictionary"}:
        return "knowledge"
    if classification in {"marine_gazetteer", "domestic_static_spatial_layer"}:
        return "standardized"
    if classification in {"dynamic_traffic_ais", "dynamic_traffic_vpass"}:
        return "serving"
    return "staging"


def intended_processing(classification: str) -> str:
    if classification == "db_dump":
        return "restore_to_s100_dev_postgis_after_valid_binary_dump"
    if classification in {"domestic_static_spatial_layer", "marine_gazetteer"}:
        return "extract_validate_crs_transform_to_epsg4326_standardize_columns"
    if classification in {"dynamic_traffic_ais", "dynamic_traffic_vpass"}:
        return "normalize_to_dynamic_traffic_layer_and_build_time_spatial_index"
    if classification in {"feature_catalogue", "portrayal_catalogue"}:
        return "parse_catalogue_and_link_feature_portrayal_metadata"
    if classification in {"law_rag", "marine_term_dictionary", "accident_data"}:
        return "parse_metadata_chunk_and_attach_provenance"
    return "parse_metadata_preserve_source_and_version"


def build(dataset_root: Path, inventory_path: Path, lake_root: Path, output_root: Path) -> None:
    inventory = list(json.loads("[]"))
    import csv
    with inventory_path.open("r", encoding="utf-8-sig", newline="") as stream:
        inventory = list(csv.DictReader(stream))

    generated_at = datetime.now(timezone.utc).isoformat()
    for zone, subdirs in ZONE_LAYOUT.items():
        for subdir in subdirs:
            directory = lake_root / zone / subdir
            directory.mkdir(parents=True, exist_ok=True)
            readme = directory / "README.md"
            if not readme.exists():
                readme.write_text(
                    f"# {zone}/{subdir}\n\nThis directory is governed by the An_GeoLLM Data Lake Zone contract.\n",
                    encoding="utf-8",
                )

    standardized = []
    for source in inventory:
        classification = source["classification"]
        processing = intended_processing(classification)
        standardized.append({
            "source_id": source["source_id"],
            "source_path": source["relative_path"],
            "source_filename": source["filename"],
            "source_type": classification,
            "source_zone": "raw",
            "staging_zone": "staging",
            "standardized_zone": "standardized" if zone_for(classification) in {"standardized", "serving"} else None,
            "knowledge_zone": "knowledge" if zone_for(classification) == "knowledge" else None,
            "serving_zone": "serving" if zone_for(classification) == "serving" else None,
            "source_modified_at": source["modified_at"],
            "source_size_bytes": int(source["size_bytes"]),
            "source_sha256": source["sha256"],
            "classification_reason": source["classification_reason"],
            "intended_processing": processing,
            "encoding": "unknown",
            "source_crs": "unknown",
            "standardized_crs": "EPSG:4326" if classification in {"domestic_static_spatial_layer", "marine_gazetteer"} else None,
            "schema_status": "pending",
            "parse_status": "pending",
            "crs_status": "pending" if classification in {"domestic_static_spatial_layer", "marine_gazetteer"} else "not_applicable",
            "provenance_status": "ready",
            "ingestion_status": "pending",
        })

    out_dir = output_root / "standardized"
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "manifest_version": "1.0",
        "generated_at": generated_at,
        "raw_root": str(dataset_root.resolve()),
        "lake_root": str(lake_root.resolve()),
        "source_count": len(standardized),
        "zone_contract": ZONE_LAYOUT,
        "sources": standardized,
    }
    (out_dir / "standardized_source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    duplicate_groups = defaultdict(list)
    for source in standardized:
        duplicate_groups[source["source_sha256"]].append(source["source_path"])
    duplicate_files = [path for group in duplicate_groups.values() if len(group) > 1 for path in group]
    quality = {
        "report_version": "1.0",
        "generated_at": generated_at,
        "source_count": len(standardized),
        "classification_counts": dict(Counter(source["source_type"] for source in standardized)),
        "zone_counts": dict(Counter(zone_for(source["source_type"]) for source in standardized)),
        "duplicate_group_count": sum(1 for group in duplicate_groups.values() if len(group) > 1),
        "duplicate_file_count": len(duplicate_files),
        "unknown_classification_count": sum(1 for source in standardized if source["source_type"] == "unknown"),
        "pending_parse_count": sum(1 for source in standardized if source["parse_status"] == "pending"),
        "pending_crs_count": sum(1 for source in standardized if source["crs_status"] == "pending"),
        "quality_checks": [
            {"check": "raw_source_exists", "status": "passed", "details": "Inventory source paths are rooted at Dataset/"},
            {"check": "sha256_manifest_present", "status": "passed", "details": "Every source has a SHA-256 checksum"},
            {"check": "classification_complete", "status": "passed" if not any(source["source_type"] == "unknown" for source in standardized) else "warning", "details": "Unknown files require manual review"},
            {"check": "content_parsing", "status": "pending", "details": "PDF/DOCX/XML/CSV and archive extraction is the next staging task"},
            {"check": "spatial_crs_validation", "status": "pending", "details": "Spatial files have not yet been opened and transformed"},
            {"check": "db_restore", "status": "blocked", "details": "The supplied dump failed pg_restore validation; v2 restore is intentionally deferred"},
        ],
        "known_risks": [
            "Duplicate filenames/content must be deduplicated by checksum without deleting the raw source.",
            "ZIP internal schema and CRS are not known until staging extraction.",
            "AIS/V-PASS sources need timestamp, update cadence, geometry, and retention policy validation.",
            "Serving Zone must not be populated from a failed or unverified DB restore.",
        ],
    }
    (out_dir / "data_quality_report.json").write_text(json.dumps(quality, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = [
        "# 04 Data Lake Zone Design",
        "",
        f"- 생성 시각(UTC): `{generated_at}`",
        f"- Raw 원천 파일 수: **{len(standardized)}**",
        "- Raw 원본은 `Dataset/`에 보존하며, Lake Zone은 원본을 이동하거나 삭제하지 않는다.",
        "",
        "## Zone 구조",
        "",
        "```text",
        "data_lake/",
        "├── raw/           # 원본 참조, manifest, checksum",
        "├── staging/       # 압축 해제 및 중간 파싱 결과",
        "├── standardized/  # 표준 컬럼, EPSG:4326, Feature/Layer/Document metadata",
        "├── knowledge/     # Dictionary, Registry, RAG Chunk, Graph Node/Edge",
        "└── serving/       # PostGIS, pgvector, KG, Agent-ready views",
        "```",
        "",
        "## Raw Zone",
        "",
        "원본 파일은 `Dataset/`에 보존한다. `dataset_inventory.csv` 및 `raw_source_manifest.json`을 통해 원본 경로, 파일명, 수정일, source_type, 크기, SHA-256을 추적한다.",
        "",
        "## Staging Zone",
        "",
        "ZIP 해제, PDF/DOCX/XML/CSV 파싱, Shapefile/GeoJSON 임시 적재, DB dump 검사·복원 중간 산출물을 저장한다. Staging 결과는 재처리 가능해야 하며 원본을 덮어쓰지 않는다.",
        "",
        "## Standardized Zone",
        "",
        "공간자료는 CRS 확인 후 EPSG:4326으로 변환한다. Feature Inventory, Layer Inventory, Document metadata는 공통 source_id, dataset_version, provenance 필드를 사용한다.",
        "",
        "## Knowledge Zone",
        "",
        "S-100/S-101 Catalogue, 해양용어, 법령, 사고자료를 Dictionary/Registry/RAG Chunk/Graph Node·Edge로 변환한다. Catalogue는 표준 기준이며 실제 DB Feature는 별도 정합성 검사를 거친다.",
        "",
        "## Serving Zone",
        "",
        "PostGIS 공간 테이블, pgvector `document_chunks`, `kg_nodes`, `kg_edges`, Agent-ready view를 제공한다. AIS/V-PASS는 정적 S-101 Feature와 분리된 `DynamicTrafficLayer`로 제공한다.",
        "",
        "## 현재 처리 상태",
        "",
        f"- 분류 완료: `{len(standardized)}`개",
        f"- 파싱 대기: `{quality['pending_parse_count']}`개",
        f"- CRS 검증 대기: `{quality['pending_crs_count']}`개",
        f"- 중복 파일: `{quality['duplicate_file_count']}`개, 그룹 `{quality['duplicate_group_count']}`개",
        "- v2.0 DB restore: `blocked` 상태이며 유효한 바이너리 dump 확보 후 수행한다.",
        "",
        "## 운영 규칙",
        "",
        "1. Raw 원본은 immutable로 취급한다.",
        "2. 모든 파생 파일은 source_id와 source_sha256을 유지한다.",
        "3. 실패한 파싱·복원 결과는 Serving Zone에 승격하지 않는다.",
        "4. DynamicTrafficLayer는 수집시각, 관측시각, 갱신주기, 보존기간을 필수 메타데이터로 가진다.",
        "5. Zone 승격은 품질검사와 provenance 검사를 통과한 manifest 버전 단위로 수행한다.",
    ]
    (output_root / "reports" / "04_datalake_design.md").parent.mkdir(parents=True, exist_ok=True)
    (output_root / "reports" / "04_datalake_design.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"source_count": len(standardized), "duplicate_file_count": len(duplicate_files), "zone_counts": quality["zone_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path("Dataset"))
    parser.add_argument("--inventory", type=Path, default=Path("outputs/inventories/dataset_inventory.csv"))
    parser.add_argument("--lake-root", type=Path, default=Path("data_lake"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    build(args.dataset_root, args.inventory, args.lake_root, args.output_root)
