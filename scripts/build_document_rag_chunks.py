"""Extract standards, validation and law sources into metadata-complete RAG chunks."""
from __future__ import annotations

import csv
import hashlib
import json
import re
import zipfile
from io import BytesIO
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "Dataset"
OUT = ROOT / "outputs/rag"
HASH_CACHE = {}
WORD_TARGET = 900
WORD_OVERLAP = 120
FIELDS = ("document_id", "document_type", "product_id", "standard_type", "title", "section", "version", "language", "source_file", "page_no", "related_features", "related_concepts", "clearance_level", "source_url")


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


def sha256(path):
    key = str(path)
    if key not in HASH_CACHE:
        HASH_CACHE[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return HASH_CACHE[key]


def rel(path):
    return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")


def product_for(name):
    for product in ("S-101", "S-104", "S-111", "S-124", "S-100", "S-158"):
        if product.replace("-", "") in name.replace("-", "") or product in name:
            return product
    return None


def version_for(name):
    match = re.search(r"(?:Ed[_ ]|_)(\d+\.\d+(?:\.\d+)?)", name)
    if match:
        return match.group(1)
    match = re.search(r"(\d+\.\d+\.\d+)", name)
    return match.group(1) if match else None


def language(text):
    return "ko" if sum(1 for char in text if 0xAC00 <= ord(char) <= 0xD7A3) else "en"


def catalogue_features():
    names = set()
    path = ROOT / "data/s101_catalogue.json"
    if path.exists():
        try:
            names.update(item.get("name", "") for item in json.loads(path.read_text(encoding="utf-8")) if item.get("name"))
        except (OSError, json.JSONDecodeError):
            pass
    names.update({"Wreck", "Obstruction", "RestrictedArea", "TrafficSeparationScheme", "BuoyIsolatedDanger", "BeaconIsolatedDanger"})
    return sorted(names, key=len, reverse=True)


FEATURES = catalogue_features()
CONCEPTS = ("navigation_hazard_object", "navigation_safety", "grounding_risk", "collision_risk", "traffic_density", "water_level", "surface_current", "navigational_warning", "validation", "accident_hotspot", "restricted_navigation_area")


def relations(text):
    lower = text.lower()
    return [feature for feature in FEATURES if feature.lower() in lower][:30], [concept for concept in CONCEPTS if concept.lower() in lower or concept.replace("_", " ") in lower][:20]


def base_metadata(path, document_type, product_id, title, text, page_no=None, section="", infer_relations=True):
    features, concepts = relations(text) if infer_relations else ([], [concept for concept in CONCEPTS if concept.replace("_", " ") in text.lower()])
    return {"document_id": hashlib.sha256(rel(path).encode()).hexdigest()[:24], "document_type": document_type, "product_id": product_id, "standard_type": product_id, "title": title, "section": section, "version": version_for(path.name), "language": language(text), "source_file": rel(path), "page_no": page_no, "related_features": features, "related_concepts": concepts, "clearance_level": "PUBLIC", "source_url": None, "source_sha256": sha256(path), "provenance": {"source_file": rel(path), "source_sha256": sha256(path)}}


def pdf_pages(path):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return [(index + 1, page.extract_text() or "") for index, page in enumerate(reader.pages)]


def docx_text(path):
    with zipfile.ZipFile(path) as archive:
        raw = archive.read("word/document.xml")
    root = ElementTree.fromstring(raw)
    paragraphs = []
    for paragraph in root.iter():
        if paragraph.tag.endswith("}p"):
            text = "".join(node.text or "" for node in paragraph.iter() if node.tag.endswith("}t"))
            if text.strip():
                paragraphs.append(text.strip())
    return "\n".join(paragraphs)


def zip_documents(path):
    texts = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            suffix = Path(name).suffix.lower()
            if suffix not in {".xml", ".txt", ".lua", ".json", ".csv", ".pdf", ".xlsx"}:
                continue
            if suffix == ".pdf":
                from pypdf import PdfReader
                reader = PdfReader(BytesIO(archive.read(name)))
                for page_no, page in enumerate(reader.pages, 1):
                    text = page.extract_text() or ""
                    if text.strip():
                        texts.append((f"{name}#page_{page_no}", text))
                continue
            if suffix == ".xlsx":
                with zipfile.ZipFile(BytesIO(archive.read(name))) as workbook:
                    values = []
                    for member in workbook.namelist():
                        if member.endswith(".xml") and ("sheet" in member or "sharedStrings" in member):
                            try:
                                root = ElementTree.fromstring(workbook.read(member))
                                values.extend(node.text.strip() for node in root.iter() if node.text and node.text.strip())
                            except ElementTree.ParseError:
                                continue
                    if values:
                        texts.append((name, "\n".join(values)))
                continue
            try:
                text, _ = decode_best(archive.read(name))
            except KeyError:
                continue
            if text.strip():
                texts.append((name, text))
    return texts


def word_chunks(text):
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


def make_chunks(path, document_type, product_id, title, sections):
    result = []
    for page_no, text in sections:
        for index, content in enumerate(word_chunks(text)):
            metadata = base_metadata(path, document_type, product_id, title, content, page_no, f"page_{page_no}" if page_no else "")
            metadata["chunk_index"] = len(result)
            result.append({"chunk_id": hashlib.sha256(f"{metadata['document_id']}:{metadata['chunk_index']}".encode()).hexdigest()[:24], "text": content, "metadata": metadata})
    return result


def csv_chunks(path, title):
    text, encoding = decode_best(path.read_bytes())
    rows = list(csv.DictReader(text.splitlines()))
    result = []
    if not rows:
        return result
    columns = list(rows[0].keys())
    header = "columns: " + " | ".join(columns)
    current = []
    current_words = len(header.split())
    start_row = 1
    for row_index, row in enumerate(rows, 1):
        values = " | ".join(str(row.get(column, "")) for column in columns)
        value_words = len(values.split())
        if current and current_words + value_words > WORD_TARGET:
            content = header + "\n" + "\n".join(current)
            metadata = base_metadata(path, "law", None, title, content, None, f"rows_{start_row}-{row_index - 1}", infer_relations=False)
            metadata["encoding"] = encoding
            metadata["source_row_start"] = start_row
            metadata["source_row_end"] = row_index - 1
            metadata["chunk_index"] = len(result)
            result.append({"chunk_id": hashlib.sha256(f"{metadata['document_id']}:{len(result)}".encode()).hexdigest()[:24], "text": content, "metadata": metadata})
            current = []
            current_words = len(header.split())
            start_row = row_index
        current.append(values)
        current_words += value_words
    if current:
        content = header + "\n" + "\n".join(current)
        metadata = base_metadata(path, "law", None, title, content, None, f"rows_{start_row}-{len(rows)}", infer_relations=False)
        metadata["encoding"] = encoding
        metadata["source_row_start"] = start_row
        metadata["source_row_end"] = len(rows)
        metadata["chunk_index"] = len(result)
        result.append({"chunk_id": hashlib.sha256(f"{metadata['document_id']}:{len(result)}".encode()).hexdigest()[:24], "text": content, "metadata": metadata})
    return result


def select_sources():
    sources = {name: [] for name in ("s100_product_spec_chunks.jsonl", "s101_dceg_chunks.jsonl", "s104_chunks.jsonl", "s111_chunks.jsonl", "s124_chunks.jsonl", "s158_validation_chunks.jsonl", "law_chunks.jsonl")}
    for path in sorted(DATASET.iterdir()):
        name = path.name
        product = product_for(name)
        if path.suffix.lower() == ".pdf":
            if "Product_Specification" in name or "Product Specification" in name or (product == "S-100" and "Final" in name):
                target = {"S-100": "s100_product_spec_chunks.jsonl", "S-101": "s101_dceg_chunks.jsonl", "S-104": "s104_chunks.jsonl", "S-111": "s111_chunks.jsonl", "S-124": "s124_chunks.jsonl"}.get(product, "")
            elif "DCEG" in name:
                target = "s101_dceg_chunks.jsonl" if product == "S-101" else "s124_chunks.jsonl"
            else:
                continue
            if target in sources and not re.search(r"\(\d+\)", name):
                sources[target].append((path, "pdf"))
        elif path.suffix.lower() == ".docx" and product in {"S-111", "S-124"}:
            if product == "S-111" and "Clean" in name:
                sources["s111_chunks.jsonl"].append((path, "docx"))
            elif product == "S-124" and "Redline" in name and "(1)" not in name and "(2)" not in name:
                sources["s124_chunks.jsonl"].append((path, "docx"))
        elif path.suffix.lower() == ".zip" and product == "S-158":
            sources["s158_validation_chunks.jsonl"].append((path, "zip"))
        if path.suffix.lower() == ".csv" and any(term in name for term in ("법령", "행정규칙", "선박법령")):
            sources["law_chunks.jsonl"].append((path, "csv"))
    return sources


def main():
    selected = select_sources()
    manifest = {"version": "3.0", "chunk_policy": {"document_target_words": WORD_TARGET, "document_overlap_words": WORD_OVERLAP, "csv_policy": "row_or_semantic_unit"}, "embedding_status": "pending", "files": {}, "sources": []}
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
                rows.extend(csv_chunks(path, title)); continue
            document_type = "dceg" if "DCEG" in path.name else "validation" if product == "S-158" else "product_specification"
            rows.extend(make_chunks(path, document_type, product, title, sections))
            manifest["sources"].append({"source_file": rel(path), "document_type": document_type, "product_id": product, "sha256": sha256(path), "format": kind})
        output = OUT / output_name; output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
        product_counts = {}
        for row in rows:
            key = row["metadata"].get("product_id") or "LAW"
            product_counts[key] = product_counts.get(key, 0) + 1
        manifest["files"][output_name] = {"chunk_count": len(rows), "product_counts": product_counts, "metadata_fields": list(FIELDS), "metadata_complete": all(all(field in row["metadata"] for field in FIELDS) for row in rows)}
        totals += len(rows)
    manifest["chunk_count"] = totals
    (OUT / "rag_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"files": len(selected), "chunks": totals, "sources": len(manifest["sources"]), "missing": [name for name, entries in selected.items() if not entries]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
