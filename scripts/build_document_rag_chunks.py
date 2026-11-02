"""Extract document bodies into metadata-complete RAG chunks."""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from io import BytesIO, StringIO
from pathlib import Path
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path(os.getenv("DATASET_ROOT", str(ROOT / "Dataset")))
OUT = ROOT / "outputs/rag"
HASH_CACHE: dict[str, str] = {}
WORD_TARGET = 900
WORD_OVERLAP = 120
FIELDS = (
    "document_id",
    "document_type",
    "product_id",
    "standard_type",
    "title",
    "section",
    "version",
    "language",
    "source_file",
    "page_no",
    "related_features",
    "related_concepts",
    "clearance_level",
    "source_url",
)


def decode_best(raw: bytes) -> tuple[str, str]:
    candidates = []
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            value = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        korean_count = sum(1 for char in value if 0xAC00 <= ord(char) <= 0xD7A3)
        score = korean_count - value.count("\ufffd") * 10000
        candidates.append((score, encoding, value))
    if not candidates:
        return raw.decode("utf-8", errors="replace"), "utf-8-replace"
    _, encoding, value = max(candidates, key=lambda item: item[0])
    return value, encoding


def sha256(path: Path) -> str:
    key = str(path)
    if key not in HASH_CACHE:
        HASH_CACHE[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return HASH_CACHE[key]


def stable_id(prefix: str, value: str) -> str:
    return prefix + ":" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def product_for(name: str) -> str | None:
    normalized = name.replace("-", "")
    for product in ("S-101", "S-104", "S-111", "S-124", "S-100", "S-158"):
        if product.replace("-", "") in normalized or product in name:
            return product
    return None


def version_for(name: str) -> str | None:
    match = re.search(r"(?:Ed[_ ]|_)(\d+\.\d+(?:\.\d+)?)", name)
    if match:
        return match.group(1)
    match = re.search(r"(\d+\.\d+\.\d+)", name)
    return match.group(1) if match else None


def has_korean(text: str) -> bool:
    return any(0xAC00 <= ord(char) <= 0xD7A3 for char in text)


def language(text: str) -> str:
    return "ko" if has_korean(text) else "en"


def looks_like_law_csv(path: Path) -> bool:
    try:
        text, _ = decode_best(path.read_bytes()[:256 * 1024])
    except OSError:
        return False
    lines = text.splitlines()
    header = lines[0] if lines else ""
    name = html.unescape(path.name)
    legal_terms = (
        "\ubc95\ub839",
        "\ud589\uc815\uaddc\uce59",
        "\uad00\ub828 \ubc95",
        "\uc120\ubc15\ubc95",
        "\ud56d\ub9cc",
    )
    accident_terms = ("\uc0ac\uace0", "\uc870\ub09c")
    if any(term in name for term in accident_terms):
        return False
    return any(term in name or term in header for term in legal_terms)


def catalogue_features() -> list[str]:
    names = set()
    path = ROOT / "data/s101_catalogue.json"
    if path.exists():
        try:
            names.update(
                item.get("name", "")
                for item in json.loads(path.read_text(encoding="utf-8"))
                if item.get("name")
            )
        except (OSError, json.JSONDecodeError):
            pass
    names.update(
        {
            "Wreck",
            "Obstruction",
            "RestrictedArea",
            "TrafficSeparationScheme",
            "BuoyIsolatedDanger",
            "BeaconIsolatedDanger",
        }
    )
    return sorted(names, key=len, reverse=True)


FEATURES = catalogue_features()
CONCEPTS = (
    "navigation_hazard_object",
    "navigation_safety",
    "grounding_risk",
    "collision_risk",
    "traffic_density",
    "water_level",
    "surface_current",
    "navigational_warning",
    "validation",
    "accident_hotspot",
    "restricted_navigation_area",
)


def relations(text: str) -> tuple[list[str], list[str]]:
    lower = text.lower()
    features = [feature for feature in FEATURES if feature.lower() in lower][:30]
    concepts = [
        concept
        for concept in CONCEPTS
        if concept.lower() in lower or concept.replace("_", " ") in lower
    ][:20]
    return features, concepts


def base_metadata(
    path: Path,
    document_type: str,
    product_id: str | None,
    title: str,
    text: str,
    page_no: int | None = None,
    section: str = "",
    infer_relations: bool = True,
    source_member: str | None = None,
) -> dict:
    features, concepts = relations(text) if infer_relations else ([], [])
    source = rel(path)
    source_id = stable_id(document_type, f"{source}|{source_member or ''}")
    return {
        "document_id": hashlib.sha256(source.encode()).hexdigest()[:24],
        "document_type": document_type,
        "product_id": product_id,
        "standard_type": product_id,
        "title": title,
        "section": section,
        "version": version_for(path.name),
        "language": language(text),
        "source_file": source,
        "source_member": source_member,
        "page_no": page_no,
        "related_features": features,
        "related_concepts": concepts,
        "clearance_level": "PUBLIC",
        "source_url": None,
        "source_id": source_id,
        "source_sha256": sha256(path),
        "extraction_status": "parsed_body",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {"source_file": source, "source_sha256": sha256(path)},
    }


def pdf_pages(path: Path) -> list[tuple[int, str]]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return [(index + 1, page.extract_text() or "") for index, page in enumerate(reader.pages)]


def docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        raw = archive.read("word/document.xml")
    root = ElementTree.fromstring(raw)
    paragraphs = []
    for paragraph in root.iter():
        if paragraph.tag.endswith("}p"):
            text = "".join(
                node.text or "" for node in paragraph.iter() if node.tag.endswith("}t")
            )
            if text.strip():
                paragraphs.append(text.strip())
    return "\n".join(paragraphs)


def xlsx_text(raw: bytes) -> str:
    values = []
    with zipfile.ZipFile(BytesIO(raw)) as workbook:
        for member in workbook.namelist():
            if not member.endswith(".xml"):
                continue
            if "sheet" not in member and "sharedStrings" not in member:
                continue
            try:
                root = ElementTree.fromstring(workbook.read(member))
            except ElementTree.ParseError:
                continue
            values.extend(node.text.strip() for node in root.iter() if node.text and node.text.strip())
    return "\n".join(values)


def zip_documents(path: Path) -> list[tuple[str, str]]:
    texts = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            suffix = Path(name).suffix.lower()
            if suffix not in {".xml", ".txt", ".lua", ".json", ".csv", ".pdf", ".xlsx"}:
                continue
            raw = archive.read(name)
            if suffix == ".pdf":
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(raw))
                for page_no, page in enumerate(reader.pages, 1):
                    text = page.extract_text() or ""
                    if text.strip():
                        texts.append((f"{name}#page_{page_no}", text))
                continue
            if suffix == ".xlsx":
                text = xlsx_text(raw)
            else:
                text, _ = decode_best(raw)
            if text.strip():
                texts.append((name, text))
    return texts


def word_chunks(text: str) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + WORD_TARGET, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - WORD_OVERLAP
    return chunks


def make_chunks(
    path: Path,
    document_type: str,
    product_id: str | None,
    title: str,
    sections: list[tuple[int | None, str]],
) -> list[dict]:
    result = []
    for page_no, text in sections:
        section_name = f"page_{page_no}" if page_no else ""
        for content in word_chunks(text):
            metadata = base_metadata(path, document_type, product_id, title, content, page_no, section_name)
            metadata["chunk_index"] = len(result)
            chunk_id = hashlib.sha256(f"{metadata['source_id']}:{len(result)}".encode()).hexdigest()[:24]
            result.append({"chunk_id": chunk_id, "text": content, "metadata": metadata})
    return result


def csv_chunks(path: Path, title: str) -> list[dict]:
    text, encoding = decode_best(path.read_bytes())
    parsed = list(csv.reader(StringIO(text)))
    result = []
    if not parsed:
        return result
    columns = parsed[0]
    rows = [row for row in parsed[1:] if row]
    if not rows:
        return result
    duplicate_columns = [i for i, name in enumerate(columns) if columns.count(name) > 1]
    # DictReader loses cells when headings repeat (including empty headings).
    # Positional rows also retain extra cells and quoted multiline field text.
    revised = bool(duplicate_columns or any(len(row) != len(columns) or any('\n' in value or '\r' in value for value in row) for row in rows))
    def identify(metadata, content, index):
        identity = f"{metadata['source_id']}:{index}"
        if revised:
            metadata.update(extraction_method='csv_positional_v2',
                            source_column_names=list(columns),
                            duplicate_header_column_indexes=duplicate_columns,
                            source_column_index_base=0,
                            source_locators=['csv-header:0', f"csv-rows:{metadata['source_row_start']}-{metadata['source_row_end']}"],
                            extraction_revision='csv_positional_v2',
                            requires_new_embedding=True)
            identity += ':csv_positional_v2:' + hashlib.sha256(content.encode()).hexdigest()
        return hashlib.sha256(identity.encode()).hexdigest()[:24]
    header = "columns: " + " | ".join(columns)
    current = []
    current_words = len(header.split())
    start_row = 1
    for row_index, row in enumerate(rows, 1):
        values = " | ".join(row)
        value_words = len(values.split())
        if current and current_words + value_words > WORD_TARGET:
            content = header + "\n" + "\n".join(current)
            metadata = base_metadata(
                path,
                "law",
                None,
                title,
                content,
                None,
                f"rows_{start_row}-{row_index - 1}",
                infer_relations=False,
            )
            metadata["encoding"] = encoding
            metadata["source_row_start"] = start_row
            metadata["source_row_end"] = row_index - 1
            metadata["chunk_index"] = len(result)
            chunk_id = identify(metadata, content, len(result))
            result.append({"chunk_id": chunk_id, "text": content, "metadata": metadata})
            current = []
            current_words = len(header.split())
            start_row = row_index
        current.append(values)
        current_words += value_words
    if current:
        content = header + "\n" + "\n".join(current)
        metadata = base_metadata(
            path,
            "law",
            None,
            title,
            content,
            None,
            f"rows_{start_row}-{len(rows)}",
            infer_relations=False,
        )
        metadata["encoding"] = encoding
        metadata["source_row_start"] = start_row
        metadata["source_row_end"] = len(rows)
        metadata["chunk_index"] = len(result)
        chunk_id = identify(metadata, content, len(result))
        result.append({"chunk_id": chunk_id, "text": content, "metadata": metadata})
    return result


def select_sources() -> dict[str, list[tuple[Path, str]]]:
    names = (
        "s100_product_spec_chunks.jsonl",
        "s101_dceg_chunks.jsonl",
        "s104_chunks.jsonl",
        "s111_chunks.jsonl",
        "s124_chunks.jsonl",
        "s158_validation_chunks.jsonl",
        "law_chunks.jsonl",
    )
    sources: dict[str, list[tuple[Path, str]]] = {name: [] for name in names}
    for path in sorted(DATASET.iterdir()):
        name = path.name
        product = product_for(name)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            if "Product_Specification" in name or "Product Specification" in name:
                target = {
                    "S-101": "s101_dceg_chunks.jsonl",
                    "S-104": "s104_chunks.jsonl",
                    "S-111": "s111_chunks.jsonl",
                    "S-124": "s124_chunks.jsonl",
                }.get(product, "")
            elif product == "S-104":
                target = "s104_chunks.jsonl"
            elif product == "S-100" and "Final" in name:
                target = "s100_product_spec_chunks.jsonl"
            elif "DCEG" in name:
                target = "s101_dceg_chunks.jsonl" if product == "S-101" else "s124_chunks.jsonl"
            else:
                continue
            if target in sources and not re.search(r"\(\d+\)", name):
                sources[target].append((path, "pdf"))
        elif suffix == ".docx" and product in {"S-111", "S-124"}:
            if product == "S-111" and "Clean" in name:
                sources["s111_chunks.jsonl"].append((path, "docx"))
            elif product == "S-124" and "Redline" in name and "(1)" not in name and "(2)" not in name:
                sources["s124_chunks.jsonl"].append((path, "docx"))
        elif suffix == ".zip" and product == "S-158" and not re.search(r"\(\d+\)", name):
            sources["s158_validation_chunks.jsonl"].append((path, "zip"))
        elif suffix == ".csv" and looks_like_law_csv(path):
            sources["law_chunks.jsonl"].append((path, "csv"))
    return sources


def main() -> None:
    selected = select_sources()
    manifest = {
        "version": "3.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chunk_policy": {
            "document_target_words": WORD_TARGET,
            "document_overlap_words": WORD_OVERLAP,
            "csv_policy": "row_or_semantic_unit",
        },
        "embedding_status": "pending",
        "files": {},
        "sources": [],
    }
    totals = 0
    for output_name, entries in selected.items():
        rows = []
        for path, kind in entries:
            product = product_for(path.name)
            title = path.stem
            if kind == "pdf":
                sections = pdf_pages(path)
            elif kind == "docx":
                sections = [(None, docx_text(path))]
            elif kind == "zip":
                sections = [(None, f"Archive member: {member}\n{text}") for member, text in zip_documents(path)]
            else:
                rows.extend(csv_chunks(path, title))
                manifest["sources"].append(
                    {
                        "source_file": rel(path),
                        "document_type": "law",
                        "product_id": None,
                        "sha256": sha256(path),
                        "format": kind,
                    }
                )
                continue
            document_type = (
                "dceg"
                if "DCEG" in path.name
                else "validation"
                if product == "S-158"
                else "product_specification"
            )
            rows.extend(make_chunks(path, document_type, product, title, sections))
            manifest["sources"].append(
                {
                    "source_file": rel(path),
                    "document_type": document_type,
                    "product_id": product,
                    "sha256": sha256(path),
                    "format": kind,
                }
            )
        output = OUT / output_name
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        product_counts: dict[str, int] = {}
        for row in rows:
            key = row["metadata"].get("product_id") or "LAW"
            product_counts[key] = product_counts.get(key, 0) + 1
        manifest["files"][output_name] = {
            "chunk_count": len(rows),
            "product_counts": product_counts,
            "metadata_fields": list(FIELDS),
            "metadata_complete": all(
                all(field in row["metadata"] for field in FIELDS) for row in rows
            ),
            "extraction_status": "parsed_body",
        }
        totals += len(rows)
    manifest["chunk_count"] = totals
    (OUT / "rag_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "files": len(selected),
                "chunks": totals,
                "sources": len(manifest["sources"]),
                "missing": [name for name, entries in selected.items() if not entries],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
