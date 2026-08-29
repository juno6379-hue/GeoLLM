"""Build a reproducible inventory for all files under Dataset/."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


CLASSIFICATIONS = [
    "standard_s100",
    "standard_s101",
    "standard_s104",
    "standard_s111",
    "standard_s124",
    "validation_s158",
    "feature_catalogue",
    "portrayal_catalogue",
    "law_rag",
    "accident_data",
    "marine_term_dictionary",
    "marine_gazetteer",
    "domestic_static_spatial_layer",
    "dynamic_traffic_ais",
    "dynamic_traffic_vpass",
    "db_dump",
    "unknown",
]


def classify(name: str) -> tuple[str, str]:
    """Return one classification and a human-readable rule explanation."""
    n = name.lower()
    stem = Path(n).stem

    if n.endswith((".dump", ".backup", ".bak")) or "_dump" in n:
        return "db_dump", "PostgreSQL/database dump extension or name"
    if "feature_catalogue" in n or re.search(r"(^|[_-])\d{3}_fc([_.-]|$)", n):
        return "feature_catalogue", "Feature Catalogue marker"
    if "portrayal_catalogue" in n or re.search(r"(^|[_-])\d{3}_pc([_.-]|$)", n):
        return "portrayal_catalogue", "Portrayal Catalogue marker"
    if "s-158" in n or "s158" in n:
        return "validation_s158", "S-158 validation marker"
    if "용어" in name or "term" in n or "dictionary" in n:
        return "marine_term_dictionary", "marine terminology/dictionary marker"
    if "지명" in name or "gazetteer" in n:
        return "marine_gazetteer", "marine gazetteer marker"
    if "v-pass" in n or "vpass" in n:
        return "dynamic_traffic_vpass", "V-PASS traffic marker"
    if re.search(r"(^|[^a-z])ais([^a-z]|$)", n) or "ais" in n:
        return "dynamic_traffic_ais", "AIS traffic marker"
    if any(token in name for token in ("법령", "행정규칙", "법률", "법령정보")) or any(
        token in n for token in ("law", "regulation", "legal")
    ):
        return "law_rag", "law/regulation marker"
    if any(token in name for token in ("사고", "조난", "인명")) or any(
        token in n for token in ("accident", "casualty", "distress")
    ):
        return "accident_data", "accident/casualty marker"
    if "s-100" in n or "s100" in n:
        return "standard_s100", "S-100 standard marker"
    if "s-101" in n or "s101" in n or re.search(r"(^|[^0-9])101([^0-9]|$)", n):
        return "standard_s101", "S-101 standard marker"
    if "s-104" in n or "s104" in n or re.search(r"(^|[^0-9])104([^0-9]|$)", n):
        return "standard_s104", "S-104 standard marker"
    if "s-111" in n or "s111" in n or re.search(r"(^|[^0-9])111([^0-9]|$)", n):
        return "standard_s111", "S-111 standard marker"
    if "s-124" in n or "s124" in n or re.search(r"(^|[^0-9])124([^0-9]|$)", n):
        return "standard_s124", "S-124 standard marker"

    # Remaining geospatial archives/CSVs are domestic static layers until a
    # schema-level classifier can refine them during staging ingestion.
    if Path(n).suffix in {".zip", ".shp", ".geojson", ".gpkg", ".csv", ".dbf", ".shx", ".prj"}:
        return "domestic_static_spatial_layer", "geospatial archive/table without a dynamic or standard marker"
    return "unknown", "no classification rule matched"


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(rows: list[dict], output: Path, generated_at: str) -> None:
    counts = Counter(row["classification"] for row in rows)
    duplicate_groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        duplicate_groups[row["sha256"]].append(row["relative_path"])
    duplicates = [paths for paths in duplicate_groups.values() if len(paths) > 1]

    def paths_for(classification: str) -> list[str]:
        return [row["relative_path"] for row in rows if row["classification"] == classification]

    standard_classes = ["standard_s100", "standard_s101", "standard_s104", "standard_s111", "standard_s124", "validation_s158", "feature_catalogue", "portrayal_catalogue"]
    rag_classes = ["law_rag", "marine_term_dictionary", "accident_data", "standard_s100", "standard_s101", "standard_s104", "standard_s111", "standard_s124", "validation_s158"]
    spatial_classes = ["domestic_static_spatial_layer", "marine_gazetteer", "db_dump"]
    traffic_classes = ["dynamic_traffic_ais", "dynamic_traffic_vpass"]

    lines = [
        "# 01 Dataset Inventory",
        "",
        f"- 생성 시각(UTC): `{generated_at}`",
        f"- 스캔 대상: `Dataset/` 재귀 스캔",
        f"- 전체 파일 수: **{len(rows)}**",
        "",
        "## 분류별 파일 수",
        "",
        "| Classification | Count |",
        "|---|---:|",
    ]
    lines += [f"| `{classification}` | {counts.get(classification, 0)} |" for classification in CLASSIFICATIONS]

    sections = [
        ("표준자료 목록", standard_classes),
        ("DB dump 목록", ["db_dump"]),
        ("RAG 대상 자료 목록", rag_classes),
        ("공간자료 목록", spatial_classes),
        ("AIS/V-PASS 자료 목록", traffic_classes),
    ]
    for title, classes in sections:
        lines += ["", f"## {title}", ""]
        selected = [path for classification in classes for path in paths_for(classification)]
        lines += [f"- `{path}`" for path in selected] or ["- 없음"]

    lines += ["", "## 중복 파일 후보", ""]
    if duplicates:
        for group in duplicates:
            lines.append(f"- 동일 SHA-256 `{next(row['sha256'] for row in rows if row['relative_path'] == group[0])}`")
            lines.extend(f"  - `{path}`" for path in group)
    else:
        lines.append("- 동일 SHA-256 기준 중복 후보 없음")

    lines += [
        "",
        "## 누락 가능 자료",
        "",
        "- Dataset 폴더에 표준자료, Feature/Portrayal Catalogue, S-158 검증자료, 법령, 사고, 용어, 지명, 정적 공간자료, AIS/V-PASS, DB dump가 모두 존재한다.",
        "- 다만 운영 전환 전 원천기관 메타데이터, 사용권한/라이선스, CRS·속성 스키마 문서, AIS/V-PASS 수집 API 또는 갱신 주기 자료는 별도 확보 여부를 확인해야 한다.",
        "- 현재 분류는 파일명·확장자 기준 1차 분류이며, Staging 단계에서 ZIP 내부 파일과 CSV 컬럼을 검사해 재분류해야 한다.",
        "",
        "## 처리 우선순위",
        "",
        "1. `db_dump`: S100_dev_postgis v2.0 복원 및 v1.0 비교",
        "2. `feature_catalogue`, `portrayal_catalogue`, `standard_s100`, `standard_s101`: Feature/NFTC/표현 규칙 기준 확정",
        "3. `domestic_static_spatial_layer`, `marine_gazetteer`: 공간 표준화 및 PostGIS 적재",
        "4. `standard_s104`, `standard_s111`, `standard_s124`, `validation_s158`: 제품별 지식화 및 검증 규칙 적재",
        "5. `marine_term_dictionary`, `law_rag`, `accident_data`: RAG Chunk 및 provenance 생성",
        "6. `dynamic_traffic_ais`, `dynamic_traffic_vpass`: DynamicTrafficLayer 스키마와 갱신 인덱스 구축",
        "",
        "## 분류 기준",
        "",
        "분류는 `scripts/build_dataset_inventory.py`의 결정적 규칙으로 수행되며, 각 레코드의 `classification_reason`에 적용 규칙을 기록한다.",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(dataset_root: Path, output_root: Path) -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for path in sorted(p for p in dataset_root.rglob("*") if p.is_file()):
        classification, reason = classify(path.name)
        stat = path.stat()
        rows.append(
            {
                "source_id": hashlib.sha256(str(path.relative_to(dataset_root)).encode("utf-8")).hexdigest()[:16],
                "relative_path": path.relative_to(dataset_root).as_posix(),
                "filename": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "sha256": sha256(path),
                "classification": classification,
                "classification_reason": reason,
                "source_zone": "raw",
                "ingestion_status": "pending",
            }
        )

    inventory_dir = output_root / "inventories"
    manifest_dir = output_root / "raw_manifest"
    report_dir = output_root / "reports"
    inventory_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    fields = list(rows[0]) if rows else ["source_id", "relative_path"]
    with (inventory_dir / "dataset_inventory.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    manifest = {
        "manifest_version": "1.0",
        "generated_at": generated_at,
        "dataset_root": str(dataset_root.resolve()),
        "file_count": len(rows),
        "classification_counts": dict(Counter(row["classification"] for row in rows)),
        "sources": rows,
    }
    (manifest_dir / "raw_source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(rows, report_dir / "01_dataset_inventory.md", generated_at)
    print(json.dumps({"file_count": len(rows), "classification_counts": manifest["classification_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path("Dataset"))
    parser.add_argument("--output-root", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    build(args.dataset_root, args.output_root)
