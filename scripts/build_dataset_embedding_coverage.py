"""Classify Dataset sources and build supplemental RAG chunks for embeddable gaps."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import struct
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
RAG = ROOT / "outputs" / "rag"
REPORTS = ROOT / "outputs" / "reports"
OUT = RAG / "dataset_supplemental_chunks.jsonl"

WORD_TARGET = 900
WORD_OVERLAP = 120
MAX_SUPPLEMENTAL_PDF_PAGES = int(os.getenv("MAX_SUPPLEMENTAL_PDF_PAGES", "80"))
MAX_SUPPLEMENTAL_PDF_BYTES = int(os.getenv("MAX_SUPPLEMENTAL_PDF_BYTES", str(10 * 1024 * 1024)))
FULL_HASH_MAX_BYTES = int(os.getenv("DATASET_COVERAGE_FULL_HASH_MAX_BYTES", str(5 * 1024 * 1024)))
HASH_CACHE: dict[str, str] = {}

SPATIAL_TERMS = (
    "정박지", "일반항로", "통항분리", "진입제한", "속도제한", "도서지명", "해양지명",
    "양식장", "보호수역", "바다목장", "간출암", "어초", "투기", "해양경찰서관할구역",
    "주의경계해역", "조업특정해역", "직선영해기선", "광구", "공동영업구역", "갯골",
    "신항만예정지역", "선박안전교통관제구역", "낚시", "분구", "항로표지",
)
TRAFFIC_TERMS = ("AIS", "V-PASS", "통항로", "항로분석", "동적정보", "정적정보", "선박통계")
SKIP_NAMES = {"100000_prompts.jsonl", "generate_geollm_prompts_from_s_101.py"}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def sha256(path: Path) -> str:
    key = str(path)
    if key in HASH_CACHE:
        return HASH_CACHE[key]
    digest = hashlib.sha256()
    size = path.stat().st_size
    with path.open("rb") as handle:
        if size <= FULL_HASH_MAX_BYTES:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
            HASH_CACHE[key] = digest.hexdigest()
        else:
            digest.update(handle.read(1024 * 1024))
            handle.seek(max(0, size - 1024 * 1024))
            digest.update(handle.read(1024 * 1024))
            HASH_CACHE[key] = "partial:" + digest.hexdigest()
    return HASH_CACHE[key]


def stable_id(prefix: str, value: str) -> str:
    return prefix + ":" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def decode_best(raw: bytes) -> tuple[str, str]:
    candidates: list[tuple[int, str, str]] = []
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        score = sum(1 for char in text if 0xAC00 <= ord(char) <= 0xD7A3) - text.count("\ufffd") * 10000
        candidates.append((score, encoding, text))
    if not candidates:
        return raw.decode("utf-8", errors="replace"), "utf-8-replace"
    _, encoding, text = max(candidates, key=lambda item: item[0])
    return text, encoding


def language(text: str) -> str:
    return "ko" if any(0xAC00 <= ord(char) <= 0xD7A3 for char in text) else "en"


def product_for(name: str) -> str | None:
    normalized = name.replace("-", "")
    for product in ("S-101", "S-104", "S-111", "S-124", "S-100", "S-158", "S-57"):
        if product.replace("-", "") in normalized or product in name:
            return product
    if "SOLAS" in name.upper():
        return "SOLAS"
    return None


def version_for(name: str) -> str | None:
    match = re.search(r"(?:Ed[_ ]|_)(\d+\.\d+(?:\.\d+)?)", name)
    if match:
        return match.group(1)
    match = re.search(r"(\d+\.\d+\.\d+)", name)
    return match.group(1) if match else None


def existing_embedding_sources() -> set[str]:
    return set()


def is_known_embedded(path: Path) -> bool:
    source = rel(path)
    name = path.name
    if not source.startswith("Dataset/"):
        return False
    if path.parent == DATASET and path.suffix.lower() in {".pdf", ".docx", ".zip"}:
        if any(product in name for product in ("S-100", "S-101", "S-104", "S-111", "S-124", "S-158")) and "signature" not in name.lower():
            return True
    if path.parent == DATASET and path.suffix.lower() == ".csv":
        if any(term in name for term in ("법령", "행정규칙", "선박법령", "사고정보", "해상조난사고")):
            return True
    if "Dataset/rag_sources/xml/101_Feature_Catalogue_2.0.0.xml" == source:
        return True
    return False


def word_chunks(text: str) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + WORD_TARGET, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - WORD_OVERLAP)
    return chunks


def metadata(path: Path, document_type: str, title: str, content: str, section: str = "", page_no: int | None = None) -> dict:
    source = rel(path)
    source_id = stable_id(document_type, source)
    product = product_for(path.name)
    return {
        "document_id": hashlib.sha256(source.encode("utf-8")).hexdigest()[:24],
        "document_type": document_type,
        "product_id": product,
        "standard_type": product,
        "title": title,
        "section": section,
        "version": version_for(path.name),
        "language": language(content),
        "source_file": source,
        "source_path": source,
        "page_no": page_no,
        "related_features": [],
        "related_concepts": concepts_for(path.name, content),
        "clearance_level": "PUBLIC",
        "source_url": None,
        "source_id": source_id,
        "source_sha256": sha256(path),
        "extraction_status": "dataset_embedding_coverage",
        "extraction_limit": f"max_pdf_pages={MAX_SUPPLEMENTAL_PDF_PAGES}",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {"source_file": source, "source_sha256": sha256(path)},
    }


def concepts_for(name: str, text: str) -> list[str]:
    value = f"{name}\n{text}".lower()
    concepts: list[str] = []
    checks = {
        "maritime_law": ("법령", "행정규칙", "solas", "regulation"),
        "accident_hotspot": ("사고", "조난", "casualty", "collision"),
        "traffic_density": ("ais", "v-pass", "통항", "traffic"),
        "marine_gazetteer": ("해양지명", "도서지명", "gazetteer"),
        "navigation_safety": ("항로", "항만", "안전", "navigation"),
        "spatial_layer_metadata": ("shapefile", "polygon", "point", "polyline"),
    }
    for concept, needles in checks.items():
        if any(needle in value for needle in needles):
            concepts.append(concept)
    return concepts


def make_text_chunks(path: Path, document_type: str, title: str, sections: list[tuple[str, str, int | None]]) -> list[dict]:
    rows: list[dict] = []
    for section, text, page_no in sections:
        for chunk in word_chunks(text):
            item_metadata = metadata(path, document_type, title, chunk, section, page_no)
            item_metadata["chunk_index"] = len(rows)
            chunk_id = hashlib.sha256(f"{item_metadata['source_id']}:{len(rows)}".encode("utf-8")).hexdigest()[:24]
            rows.append({"chunk_id": chunk_id, "text": chunk, "metadata": item_metadata})
    return rows


def pdf_sections(path: Path) -> list[tuple[str, str, int | None]]:
    from pypdf import PdfReader

    sections: list[tuple[str, str, int | None]] = []
    reader = PdfReader(str(path))
    for index, page in enumerate(reader.pages[:MAX_SUPPLEMENTAL_PDF_PAGES], 1):
        text = page.extract_text() or ""
        if text.strip():
            sections.append((f"page_{index}", text, index))
    if len(reader.pages) > MAX_SUPPLEMENTAL_PDF_PAGES:
        sections.append((
            "extraction_limit",
            f"PDF source has {len(reader.pages)} pages. Supplemental embedding was limited to the first {MAX_SUPPLEMENTAL_PDF_PAGES} pages; use the source file for complete legal citation.",
            None,
        ))
    return sections


def file_profile(path: Path, policy: str) -> str:
    return json.dumps({
        "source_file": rel(path),
        "file_name": path.name,
        "size_bytes": path.stat().st_size,
        "product_id": product_for(path.name),
        "version": version_for(path.name),
        "embedding_policy": policy,
    }, ensure_ascii=False, indent=2)


def docx_sections(path: Path) -> list[tuple[str, str, int | None]]:
    from scripts.docx_source_text import docx_source_text
    text=docx_source_text(path.read_bytes())
    return [("document", text, None)] if text else []


def xlsx_text(raw: bytes) -> str:
    from scripts.xlsx_source_text import xlsx_source_text
    return xlsx_source_text(raw)


def csv_profile(path: Path) -> tuple[str, str]:
    with path.open("rb") as handle:
        raw = handle.read(256 * 1024)
    text, encoding = decode_best(raw)
    reader = csv.DictReader(text.splitlines())
    rows = []
    for index, row in enumerate(reader):
        if index >= 40:
            break
        rows.append(row)
    columns = reader.fieldnames or []
    body = {
        "source_file": rel(path),
        "encoding": encoding,
        "columns": columns,
        "sample_rows": rows,
        "embedding_policy": "profile_and_sample_only_for_structured_dataset",
    }
    return json.dumps(body, ensure_ascii=False, indent=2), encoding


def shapefile_archive_profile(path: Path) -> dict:
    result = {"source_file": rel(path), "archive_members": [], "embedding_policy": "metadata_only_geometry_rows_stay_in_spatial_db"}
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            for name in names:
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
                result["archive_members"].append({
                    "member": name,
                    "geometry_type": {1: "Point", 3: "Polyline", 5: "Polygon", 8: "MultiPoint"}.get(shape_type, f"ShapeType_{shape_type}"),
                    "record_count": record_count,
                    "bbox": bbox,
                })
    except zipfile.BadZipFile:
        result["error"] = "bad_zip_file"
    return result


def classify(path: Path, embedded_sources: set[str]) -> tuple[str, str]:
    source = rel(path)
    name = path.name
    lower_suffix = path.suffix.lower()
    if name in SKIP_NAMES:
        return "excluded", "generated prompt corpus or helper script"
    if "S-101_FC_1.1.0" in name:
        return "excluded", "older S-101 feature catalogue; current runtime baseline is S-101 2.0.0"
    if source in embedded_sources or is_known_embedded(path):
        return "embedded", "source is present in current embedding outputs"
    if any(part.startswith(".") for part in path.relative_to(DATASET).parts):
        return "excluded", "hidden/system path"
    if lower_suffix in {".shp", ".shx", ".dbf", ".prj", ".qpj", ".sbn", ".sbx", ".cpg"}:
        return "spatial_component", "component file is represented by its archive or spatial table"
    if lower_suffix == ".dump":
        return "database_restore", "database dump is not embedded directly"
    if lower_suffix == ".zip":
        if "signature" in name.lower():
            return "excluded", "signature archive"
        if any(term in name for term in TRAFFIC_TERMS):
            return "analytics_metadata", "traffic source stays analytical; embed metadata only"
        if any(term in name for term in SPATIAL_TERMS) or "지명" in str(path):
            return "spatial_metadata", "spatial geometry stays in PostGIS; embed layer metadata only"
        if "SOLAS" in str(path).upper() or "Validation" in name or "Catalogue" in name:
            return "embeddable_archive", "document archive"
        return "spatial_metadata", "archive treated as dataset metadata"
    if lower_suffix == ".txt" and any(term in name for term in TRAFFIC_TERMS):
        return "analytics_metadata", "traffic source stays analytical; embed metadata/sample only"
    if lower_suffix in {".pdf", ".docx", ".md", ".txt"}:
        return "embeddable_document", "text document"
    if lower_suffix in {".csv", ".xlsx", ".xls"}:
        if any(term in name for term in TRAFFIC_TERMS):
            return "analytics_metadata", "raw traffic rows are queried analytically; embed metadata/sample only"
        if any(term in name for term in SPATIAL_TERMS):
            return "spatial_metadata", "structured/spatial source metadata"
        return "embeddable_structured", "structured reference data profile"
    if lower_suffix == ".xml":
        return "embeddable_document", "XML catalogue/reference document"
    return "excluded", "unsupported format"


def build_rows_for(path: Path, status: str) -> list[dict]:
    title = path.stem
    suffix = path.suffix.lower()
    try:
        if status == "embeddable_document" and suffix == ".pdf":
            text = file_profile(path, "metadata_only_pdf; core standards already have dedicated full-text chunks")
            return make_text_chunks(path, "dataset_profile", title, [("large_pdf_profile", text, None)])
        if status == "embeddable_document" and suffix == ".docx":
            return make_text_chunks(path, "supplemental_document", title, docx_sections(path))
        if status == "embeddable_document" and suffix in {".md", ".txt", ".xml"}:
            text, _ = decode_best(path.read_bytes())
            return make_text_chunks(path, "supplemental_document", title, [("document", text, None)])
        if status in {"embeddable_structured", "analytics_metadata", "spatial_metadata"} and suffix in {".csv", ".xlsx", ".xls", ".txt"}:
            if suffix in {".xlsx", ".xls"}:
                text = f"Binary Excel workbook metadata. source_file={rel(path)} size_bytes={path.stat().st_size}"
            elif suffix == ".txt":
                sample, encoding = decode_best(path.read_bytes()[:256 * 1024])
                text = json.dumps({
                    "source_file": rel(path),
                    "encoding": encoding,
                    "size_bytes": path.stat().st_size,
                    "sample": sample[:8000],
                    "embedding_policy": "profile_and_sample_only_for_traffic_text",
                }, ensure_ascii=False, indent=2)
            else:
                text, _ = csv_profile(path)
            return make_text_chunks(path, "dataset_profile", title, [("profile", text, None)])
        if status in {"spatial_metadata", "analytics_metadata"} and suffix == ".zip":
            text = file_profile(path, "metadata_only_archive; raw geometry or traffic stays in PostGIS/analytics stores")
            return make_text_chunks(path, "dataset_profile", title, [("archive_profile", text, None)])
        if status == "embeddable_archive" and suffix == ".zip":
            text = file_profile(path, "metadata_only_document_archive; expand explicitly when a query needs member-level text")
            return make_text_chunks(path, "dataset_profile", title, [("archive_profile", text, None)])
    except Exception as exc:
        error_text = json.dumps({"source_file": rel(path), "error": str(exc), "embedding_policy": "parse_error_metadata_only"}, ensure_ascii=False)
        return make_text_chunks(path, "dataset_profile", title, [("parse_error", error_text, None)])
    return []


def main() -> None:
    embedded_sources = existing_embedding_sources()
    files = sorted(path for path in DATASET.rglob("*") if path.is_file())
    inventory: list[dict] = []
    rows: list[dict] = []
    for path in files:
        status, reason = classify(path, embedded_sources)
        chunk_start = len(rows)
        if status in {"embeddable_document", "embeddable_structured", "embeddable_archive", "spatial_metadata", "analytics_metadata"}:
            rows.extend(build_rows_for(path, status))
        inventory.append({
            "source_file": rel(path),
            "status": status,
            "reason": reason,
            "size_bytes": path.stat().st_size,
            "supplemental_chunks": len(rows) - chunk_start,
        })

    RAG.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    inventory_path = REPORTS / "dataset_embedding_coverage.json"
    REPORTS.mkdir(parents=True, exist_ok=True)
    inventory_path.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_root": rel(DATASET),
        "supplemental_chunk_file": rel(OUT),
        "supplemental_chunk_count": len(rows),
        "inventory": inventory,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    chunk_counts: dict[str, int] = {}
    for item in inventory:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
        chunk_counts[item["status"]] = chunk_counts.get(item["status"], 0) + item["supplemental_chunks"]
    lines = [
        "# Dataset Embedding Coverage",
        "",
        f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- dataset_files: `{len(inventory)}`",
        f"- already_embedded_files: `{counts.get('embedded', 0)}`",
        f"- supplemental_chunk_file: `{rel(OUT)}`",
        f"- supplemental_chunks_to_embed: `{len(rows)}`",
        "",
        "## Classification Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: files `{counts[key]}`, chunks `{chunk_counts.get(key, 0)}`")
    lines += [
        "",
        "## Policy",
        "",
        "- 문서/PDF/MD/TXT/XML은 본문 chunk로 임베딩한다.",
        "- 공간 ZIP/CSV는 좌표 원자료를 임베딩하지 않고 레이어 메타데이터만 임베딩한다.",
        "- AIS/V-PASS 원자료는 raw row 임베딩 대상이 아니며 분석 테이블/타일에서 조회하고, Dataset 출처 메타데이터만 임베딩한다.",
        "- 이미 `outputs/rag/*embeddings*.jsonl`에 존재하는 source는 중복 chunk 생성을 피한다.",
    ]
    (REPORTS / "dataset_embedding_coverage.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(inventory), "supplemental_chunks": len(rows), "counts": counts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
