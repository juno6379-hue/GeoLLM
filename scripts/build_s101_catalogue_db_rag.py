"""Build and upsert S-101 Feature Catalogue + S100_dev DB text RAG chunks.

This script intentionally embeds semantic descriptions, not every S-101
feature instance. Geometry-heavy feature rows remain in PostGIS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "data/s101_feature_catalogue_v2_parsed.json"
DEFAULT_DATASET_ROOT = Path(os.getenv("DATASET_ROOT", str(ROOT / "Dataset")))
DEFAULT_CHUNKS = ROOT / "outputs/rag/s101_catalogue_db_chunks.jsonl"
DEFAULT_EMBEDDINGS = ROOT / "outputs/rag/s101_catalogue_db_embeddings.jsonl"
DEFAULT_REPORT = ROOT / "outputs/reports/17_s101_catalogue_db_embedding_report.md"

SOURCE_IDS = {
    "feature_catalogue": "s101_feature_catalogue_v2_xml",
    "attribute_catalogue": "s101_attribute_catalogue_v2_xml",
    "product_specification": "s101_product_specification_2_0_pdf",
    "dceg": "s101_dceg_2_0_pdf",
    "portrayal_catalogue": "s101_portrayal_catalogue_2_0",
    "validation_checks": "s158_101_validation_checks_1_1",
    "db_feature_profile": "gbhd_s101_20_db_feature_profile",
    "db_text_values": "gbhd_s101_20_db_text_values",
    "valid_geometry_profile": "gbhd_s101_20_valid_geometry_profile",
    "accident_relation_profile": "gbhd_s101_20_accident_relation_profile",
}

S101_PRODUCT_SPECIFICATION = os.getenv("S101_PRODUCT_SPECIFICATION", "INT.IHO.S-101.2.0")
S101_CATALOGUE_VERSION = os.getenv("S101_CATALOGUE_VERSION", "2.0.0")


def stable_id(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:24]}"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clean_text(value: Any) -> str:
    return " ".join(str(value or "").replace("\x00", " ").split())


def decode_best(raw: bytes) -> str:
    candidates = []
    for encoding in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
        try:
            value = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        score = sum(1 for char in value if "\uac00" <= char <= "\ud7a3") - value.count("\ufffd") * 10000
        candidates.append((score, value))
    if candidates:
        return max(candidates, key=lambda item: item[0])[1]
    return raw.decode("utf-8", errors="replace")


def xlsx_text(raw: bytes) -> str:
    values: list[str] = []
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


def pdf_pages_from_bytes(raw: bytes) -> list[tuple[int, str]]:
    try:
        from pypdf import PdfReader
    except ModuleNotFoundError:
        print("pdf_extraction_unavailable=pypdf")
        return []

    reader = PdfReader(BytesIO(raw))
    return [(index + 1, page.extract_text() or "") for index, page in enumerate(reader.pages)]


def pdf_pages(path: Path) -> list[tuple[int, str]]:
    return pdf_pages_from_bytes(path.read_bytes())


def iter_zip_text_members(path: Path, max_depth: int = 2) -> list[tuple[str, str]]:
    def walk(raw_zip: bytes, prefix: str, depth: int) -> list[tuple[str, str]]:
        texts: list[tuple[str, str]] = []
        with zipfile.ZipFile(BytesIO(raw_zip)) as archive:
            for name in archive.namelist():
                suffix = Path(name).suffix.lower()
                member_name = f"{prefix}{name}"
                raw = archive.read(name)
                if suffix == ".zip" and depth < max_depth:
                    texts.extend(walk(raw, member_name + "::", depth + 1))
                elif suffix == ".pdf":
                    for page_no, text in pdf_pages_from_bytes(raw):
                        if text.strip():
                            texts.append((f"{member_name}#page_{page_no}", text))
                elif suffix == ".xlsx":
                    text = xlsx_text(raw)
                    if text.strip():
                        texts.append((member_name, text))
                elif suffix in {".xml", ".txt", ".lua", ".json", ".csv", ".xsl", ".xslt"}:
                    text = decode_best(raw)
                    if text.strip():
                        texts.append((member_name, text))
        return texts

    return walk(path.read_bytes(), "", 0)


def word_chunks(text: str, target_words: int = 900, overlap_words: int = 120) -> list[str]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + target_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap_words)
    return chunks


def keywords_from_text(text: str, extra: list[str] | None = None) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}|[가-힣]{2,}", text)
    seen: set[str] = set()
    result: list[str] = []
    for word in (extra or []) + words:
        key = word.lower()
        if key not in seen:
            result.append(word)
            seen.add(key)
        if len(result) >= 24:
            break
    return result


def chunk_row(
    *,
    chunk_id: str,
    content: str,
    metadata: dict[str, Any],
    related_features: list[str] | None = None,
    related_concepts: list[str] | None = None,
) -> dict[str, Any]:
    content = clean_text(content)
    if not content:
        raise ValueError("empty chunk content")
    source_id = metadata["source_id"]
    metadata = {
        "document_id": metadata.get("document_id", source_id),
        "document_type": metadata["document_type"],
        "product_id": "S-101",
        "standard_type": "S-101",
        "title": metadata["title"],
        "section": metadata["section"],
        "version": metadata.get("version", "2.0.0"),
        "product_specification": metadata.get("product_specification", S101_PRODUCT_SPECIFICATION),
        "language": metadata.get("language", "en"),
        "source_file": metadata["source_file"],
        "page_no": None,
        "related_features": related_features or [],
        "related_concepts": related_concepts or [],
        "clearance_level": "PUBLIC",
        "source_url": None,
        "source_id": source_id,
        "source_sha256": metadata["source_sha256"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **{k: v for k, v in metadata.items() if k not in {"document_type", "title", "section", "source_file", "source_id", "source_sha256"}},
    }
    return {
        "chunk_id": chunk_id,
        "text": content,
        "content": content,
        "metadata": metadata,
        "document_id": metadata["document_id"],
        "document_type": metadata["document_type"],
        "product_id": "S-101",
        "standard_type": "S-101",
        "title": metadata["title"],
        "section": metadata["section"],
        "version": metadata["version"],
        "language": metadata["language"],
        "keywords": keywords_from_text(content, [metadata["document_type"], metadata["section"]]),
        "related_features": metadata["related_features"],
        "related_concepts": metadata["related_concepts"],
        "clearance_level": "PUBLIC",
        "source_file": metadata["source_file"],
        "source_url": None,
        "page_no": None,
        "source_id": source_id,
        "source_sha256": metadata["source_sha256"],
    }


def load_catalogue_chunks(path: Path) -> list[dict[str, Any]]:
    parsed = json.loads(path.read_text(encoding="utf-8"))
    meta = parsed.get("metadata", {})
    source_file = meta.get("source", str(path))
    source_sha = meta.get("sha256") or sha256_file(path)
    version = meta.get("versionNumber") or "2.0.0"
    rows: list[dict[str, Any]] = []

    for feature in parsed.get("features", []):
        code = clean_text(feature.get("code"))
        name = clean_text(feature.get("name"))
        definition = clean_text(feature.get("definition"))
        aliases = [clean_text(x) for x in feature.get("aliases", []) if clean_text(x)]
        primitives = [clean_text(x) for x in feature.get("permitted_primitives", []) if clean_text(x)]
        bindings = feature.get("bindings", [])
        binding_text = ", ".join(sorted({clean_text(b.get("ref")) for b in bindings if clean_text(b.get("ref"))})[:40])
        content = (
            f"S-101 Feature Catalogue feature definition. Feature code: {code}. "
            f"Feature name: {name}. Definition: {definition}. "
            f"Aliases: {', '.join(aliases) if aliases else 'none'}. "
            f"Permitted primitives: {', '.join(primitives) if primitives else 'not specified'}. "
            f"Attribute/information bindings: {binding_text if binding_text else 'not parsed from XML'}."
        )
        rows.append(chunk_row(
            chunk_id=stable_id("s101_feature", f"{code}|{name}|{definition}"),
            content=content,
            metadata={
                "document_type": "feature_catalogue",
                "title": "S-101 Feature Catalogue 2.0.0",
                "section": f"feature:{code or name}",
                "version": version,
                "source_file": source_file,
                "source_id": SOURCE_IDS["feature_catalogue"],
                "source_sha256": source_sha,
                "feature_code": code,
                "feature_name": name,
                "aliases": aliases,
                "permitted_primitives": primitives,
            },
            related_features=[name or code],
            related_concepts=["feature_definition"],
        ))

    for attr in parsed.get("attributes", []):
        code = clean_text(attr.get("code"))
        name = clean_text(attr.get("name"))
        definition = clean_text(attr.get("definition"))
        aliases = [clean_text(x) for x in attr.get("alias", []) if clean_text(x)]
        listed_values = [
            f"{clean_text(v.get('value'))}={clean_text(v.get('label'))}"
            for v in attr.get("listed_values", [])
            if clean_text(v.get("value")) or clean_text(v.get("label"))
        ]
        content = (
            f"S-101 Feature Catalogue attribute description. Attribute code: {code}. "
            f"Attribute name: {name}. Definition: {definition}. "
            f"Value type: {clean_text(attr.get('value_type')) or 'not specified'}. "
            f"Unit of measure: {clean_text(attr.get('uom')) or 'not specified'}. "
            f"Aliases: {', '.join(aliases) if aliases else 'none'}. "
            f"Listed values: {', '.join(listed_values[:80]) if listed_values else 'none'}."
        )
        rows.append(chunk_row(
            chunk_id=stable_id("s101_attribute", f"{code}|{name}|{definition}"),
            content=content,
            metadata={
                "document_type": "attribute_catalogue",
                "title": "S-101 Feature Catalogue 2.0.0",
                "section": f"attribute:{code or name}",
                "version": version,
                "source_file": source_file,
                "source_id": SOURCE_IDS["attribute_catalogue"],
                "source_sha256": source_sha,
                "attribute_code": code,
                "attribute_name": name,
                "value_type": clean_text(attr.get("value_type")),
                "aliases": aliases,
            },
            related_concepts=["attribute_description"],
        ))

    return rows


def find_dataset_file(dataset_root: Path, pattern: str) -> Path | None:
    if not dataset_root.exists():
        return None
    matches = sorted(
        (path for path in dataset_root.iterdir() if path.is_file() and re.search(pattern, path.name, re.IGNORECASE)),
        key=lambda path: ("(" in path.stem, path.name),
    )
    return matches[0] if matches else None


def load_pdf_document_chunks(
    path: Path,
    *,
    document_type: str,
    title: str,
    source_id: str,
    related_concepts: list[str],
) -> list[dict[str, Any]]:
    source_sha = sha256_file(path)
    rows: list[dict[str, Any]] = []
    for page_no, text in pdf_pages(path):
        page_text = clean_text(text)
        if not page_text:
            continue
        for chunk_index, content in enumerate(word_chunks(page_text)):
            section = f"page:{page_no}:chunk:{chunk_index}"
            rows.append(chunk_row(
                chunk_id=stable_id(document_type, f"{path.name}|{section}|{content[:120]}"),
                content=content,
                metadata={
                    "document_type": document_type,
                    "title": title,
                    "section": section,
                    "version": S101_CATALOGUE_VERSION,
                    "source_file": str(path),
                    "source_id": source_id,
                    "source_sha256": source_sha,
                    "page_no": page_no,
                },
                related_concepts=related_concepts,
            ))
    return rows


def load_zip_document_chunks(
    path: Path,
    *,
    document_type: str,
    title: str,
    source_id: str,
    related_concepts: list[str],
) -> list[dict[str, Any]]:
    source_sha = sha256_file(path)
    rows: list[dict[str, Any]] = []
    for member, text in iter_zip_text_members(path):
        member_text = clean_text(text)
        if not member_text:
            continue
        for chunk_index, content in enumerate(word_chunks(member_text)):
            section = f"member:{member}:chunk:{chunk_index}"
            rows.append(chunk_row(
                chunk_id=stable_id(document_type, f"{path.name}|{section}|{content[:120]}"),
                content=f"Archive member: {member}. {content}",
                metadata={
                    "document_type": document_type,
                    "title": title,
                    "section": section[:480],
                    "version": S101_CATALOGUE_VERSION,
                    "source_file": str(path),
                    "source_member": member,
                    "source_id": source_id,
                    "source_sha256": source_sha,
                },
                related_concepts=related_concepts,
            ))
    return rows


def load_existing_s101_pdf_chunks(path: Path = ROOT / "outputs/rag/s101_dceg_chunks.jsonl") -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        source = json.loads(line)
        metadata = dict(source.get("metadata") or {})
        if metadata.get("product_id") != "S-101":
            continue
        content = source.get("content") or source.get("text") or ""
        title = clean_text(metadata.get("title") or "S-101 PDF Source")
        document_type = "dceg" if "DCEG" in title.upper() else "product_specification"
        source_id = SOURCE_IDS["dceg"] if document_type == "dceg" else SOURCE_IDS["product_specification"]
        section = clean_text(metadata.get("section") or f"chunk:{len(rows)}")
        rows.append(chunk_row(
            chunk_id=source.get("chunk_id") or stable_id(f"s101_existing_{document_type}", f"{metadata.get('source_file')}|{section}|{content[:160]}"),
            content=content,
            metadata={
                "document_type": document_type,
                "title": title,
                "section": section,
                "version": metadata.get("version") or S101_CATALOGUE_VERSION,
                "product_specification": S101_PRODUCT_SPECIFICATION,
                "source_file": metadata.get("source_file") or str(path),
                "source_id": source_id,
                "source_sha256": metadata.get("source_sha256") or sha256_file(path),
                "page_no": metadata.get("page_no"),
                "legacy_chunk_id": source.get("chunk_id"),
            },
            related_features=metadata.get("related_features") or [],
            related_concepts=(metadata.get("related_concepts") or []) + [document_type, "s101_core"],
        ))
    return rows


def load_dataset_s101_core_chunks(dataset_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    sources = [
        (
            find_dataset_file(dataset_root, r"^S-101_ENC_Product_Specification_Ed_2\.0\.0\.pdf$"),
            "product_specification",
            "S-101 ENC Product Specification 2.0.0",
            SOURCE_IDS["product_specification"],
            ["product_specification", "s101_core"],
        ),
        (
            find_dataset_file(dataset_root, r"^S-101_Annex_A_DCEG_Ed_2\.0\.0\.pdf$"),
            "dceg",
            "S-101 Annex A DCEG 2.0.0",
            SOURCE_IDS["dceg"],
            ["dceg", "feature_encoding", "s101_core"],
        ),
    ]
    for path, document_type, title, source_id, related_concepts in sources:
        if path:
            before = len(rows)
            rows.extend(load_pdf_document_chunks(
                path,
                document_type=document_type,
                title=title,
                source_id=source_id,
                related_concepts=related_concepts,
            ))
            if len(rows) == before:
                print(f"pdf_chunks_missing source={path.name}; using existing JSONL fallback if available")

    zip_sources = [
        (
            find_dataset_file(dataset_root, r"^101_Portrayal_Catalogue_2\.0\.0\.zip\.signature\.zip$"),
            "portrayal_catalogue",
            "S-101 Portrayal Catalogue 2.0.0",
            SOURCE_IDS["portrayal_catalogue"],
            ["portrayal", "drawing_rules", "s101_core"],
        ),
        (
            find_dataset_file(dataset_root, r"^S-158-101_Validation_Checks_Ed_1\.1\.0\.zip$"),
            "validation",
            "S-158-101 Validation Checks 1.1.0",
            SOURCE_IDS["validation_checks"],
            ["validation", "s101_core"],
        ),
    ]
    for path, document_type, title, source_id, related_concepts in zip_sources:
        if path:
            rows.extend(load_zip_document_chunks(
                path,
                document_type=document_type,
                title=title,
                source_id=source_id,
                related_concepts=related_concepts,
            ))
    if not any(row["document_type"] in {"product_specification", "dceg"} for row in rows):
        rows.extend(load_existing_s101_pdf_chunks())
    return rows


def connect(database_url: str):
    import psycopg2

    return psycopg2.connect(database_url)


def fetch_db_chunks(database_url: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    db_sha_seed: list[str] = []
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT to_regclass('projection.s101_feature_current')")
            has_projection = cur.fetchone()[0] is not None
            if has_projection:
                cur.execute("""
                    SELECT feature_type_code,
                           COUNT(*) AS feature_count,
                           COUNT(geometry) AS geometry_count,
                           COALESCE(string_agg(DISTINCT GeometryType(geometry), ', '), '') AS geometry_types
                    FROM projection.s101_feature_current
                    WHERE product_specification = %s
                    GROUP BY feature_type_code
                    ORDER BY feature_type_code
                """, (S101_PRODUCT_SPECIFICATION,))
            else:
                cur.execute("""
                    SELECT f.featurecode AS feature_type_code,
                           COUNT(*) AS feature_count,
                           COUNT(f.geom) AS geometry_count,
                           COALESCE(string_agg(DISTINCT GeometryType(f.geom), ', '), '') AS geometry_types
                    FROM public.s101_feature AS f
                    JOIN public.s101_legacy_meta_binding AS b
                      ON b.legacy_meta_seq = f.meta_seq
                    JOIN public.s101_dataset AS d
                      ON d.dataset_id = b.dataset_id
                    WHERE d.product_specification = %s
                    GROUP BY f.featurecode
                    ORDER BY f.featurecode
                """, (S101_PRODUCT_SPECIFICATION,))
            feature_profiles = cur.fetchall()

            cur.execute("SELECT to_regclass('canonical.feature_record'), to_regclass('canonical.feature_attribute_value')")
            has_canonical_record, has_canonical_attr = cur.fetchone()
            if has_canonical_record and has_canonical_attr:
                cur.execute("""
                    SELECT fr.nftc,
                           fav.natc,
                           COUNT(*) AS value_count,
                           array_agg(DISTINCT left(fav.value_text, 160)) FILTER (
                               WHERE fav.value_text IS NOT NULL
                                 AND fav.value_text !~ '^[0-9. ()+-]+$'
                           ) AS text_samples
                    FROM canonical.feature_record fr
                    JOIN canonical.feature_attribute_value fav
                      ON fav.feature_record_id = fr.feature_record_id
                    GROUP BY fr.nftc, fav.natc
                    ORDER BY fr.nftc, fav.natc
                """)
            else:
                cur.execute("""
                    SELECT f.featurecode AS nftc,
                           fav.attrname AS natc,
                           COUNT(*) AS value_count,
                           array_agg(DISTINCT left(fav.attrvalue, 160)) FILTER (
                               WHERE fav.attrvalue IS NOT NULL
                                 AND fav.attrvalue !~ '^[0-9. ()+-]+$'
                           ) AS text_samples
                    FROM public.s101_feature AS f
                    JOIN public.s101_legacy_meta_binding AS b
                      ON b.legacy_meta_seq = f.meta_seq
                    JOIN public.s101_dataset AS d
                      ON d.dataset_id = b.dataset_id
                    JOIN public.s101_feature_attr_value AS fav
                      ON fav.feature_seq = f.seq
                    WHERE d.product_specification = %s
                    GROUP BY f.featurecode, fav.attrname
                    ORDER BY f.featurecode, fav.attrname
                """, (S101_PRODUCT_SPECIFICATION,))
            attr_profiles = cur.fetchall()

            if has_canonical_attr:
                cur.execute("""
                    SELECT fav.natc,
                           COUNT(*) AS value_count,
                           array_agg(DISTINCT left(fav.value_text, 180)) FILTER (
                               WHERE fav.value_text IS NOT NULL
                                 AND fav.value_text !~ '^[0-9. ()+-]+$'
                           ) AS text_samples
                    FROM canonical.feature_attribute_value fav
                    GROUP BY fav.natc
                    ORDER BY fav.natc
                """)
            else:
                cur.execute("""
                    SELECT fav.attrname AS natc,
                           COUNT(*) AS value_count,
                           array_agg(DISTINCT left(fav.attrvalue, 180)) FILTER (
                               WHERE fav.attrvalue IS NOT NULL
                                 AND fav.attrvalue !~ '^[0-9. ()+-]+$'
                           ) AS text_samples
                    FROM public.s101_feature AS f
                    JOIN public.s101_legacy_meta_binding AS b
                      ON b.legacy_meta_seq = f.meta_seq
                    JOIN public.s101_dataset AS d
                      ON d.dataset_id = b.dataset_id
                    JOIN public.s101_feature_attr_value AS fav
                      ON fav.feature_seq = f.seq
                    WHERE d.product_specification = %s
                    GROUP BY fav.attrname
                    ORDER BY fav.attrname
                """, (S101_PRODUCT_SPECIFICATION,))
            text_value_profiles = cur.fetchall()

            valid_geometry_profile = None
            cur.execute("SELECT to_regclass('projection.s101_feature_valid')")
            if cur.fetchone()[0] is not None:
                cur.execute("""
                    SELECT COUNT(*) AS feature_count,
                           COUNT(*) FILTER (WHERE geometry IS NOT NULL) AS geometry_count,
                           COUNT(*) FILTER (WHERE geometry IS NOT NULL) AS valid_geometry_count,
                           0::bigint AS invalid_geometry_count,
                           COUNT(*) FILTER (WHERE was_geometry_repaired) AS repaired_geometry_count,
                           COALESCE(string_agg(DISTINCT GeometryType(geometry), ', '), '') AS geometry_types
                    FROM projection.s101_feature_valid
                    WHERE product_specification = %s
                """, (S101_PRODUCT_SPECIFICATION,))
                valid_geometry_profile = cur.fetchone()

            accident_relation_profile = None
            accident_relation_types = []
            cur.execute("SELECT to_regclass('serving.accident_s101_relation_current')")
            if cur.fetchone()[0] is not None:
                cur.execute("""
                    SELECT COUNT(*) AS relation_count,
                           COUNT(DISTINCT event_id) AS accident_count,
                           MIN(distance_meters) AS min_distance_meters,
                           ROUND(AVG(distance_meters), 3) AS avg_distance_meters,
                           MAX(distance_meters) AS max_distance_meters
                    FROM serving.accident_s101_relation_current
                    WHERE product_specification = %s
                """, (S101_PRODUCT_SPECIFICATION,))
                accident_relation_profile = cur.fetchone()
                cur.execute("""
                    SELECT relation_type,
                           COUNT(*) AS relation_count,
                           COUNT(DISTINCT event_id) AS accident_count
                    FROM serving.accident_s101_relation_current
                    WHERE product_specification = %s
                    GROUP BY relation_type
                    ORDER BY relation_type
                """, (S101_PRODUCT_SPECIFICATION,))
                accident_relation_types = cur.fetchall()

    attrs_by_nftc: dict[int, list[str]] = {}
    for nftc, natc, value_count, samples in attr_profiles:
        sample_values = [clean_text(x) for x in (samples or []) if clean_text(x)]
        text = f"NATC {natc}: {value_count} values"
        if sample_values:
            text += f"; text samples: {', '.join(sample_values[:12])}"
        attrs_by_nftc.setdefault(nftc, []).append(text)

    profile_count = 0
    for feature_type_code, feature_count, geometry_count, geometry_types in feature_profiles:
        attr_text = ". ".join(attrs_by_nftc.get(feature_type_code, [])[:80])
        content = (
            f"GBHD S-101 2.0 database feature profile. DB feature_type_code/NFTC: {feature_type_code}. "
            f"Feature instance count: {feature_count}. Geometry count: {geometry_count}. "
            f"Geometry types: {geometry_types or 'none'}. "
            f"Observed DB attribute profile: {attr_text if attr_text else 'no attribute values observed'}."
        )
        db_sha_seed.append(content)
        rows.append(chunk_row(
            chunk_id=stable_id("s101_db_feature", content),
            content=content,
            metadata={
                "document_type": "s101_db_feature_profile",
                "title": "GBHD S-101 2.0 DB Feature Profile",
                "section": f"feature_type_code:{feature_type_code}",
                "version": S101_CATALOGUE_VERSION,
                "product_specification": S101_PRODUCT_SPECIFICATION,
                "source_file": "gbhd_s101/projection.s101_feature_current + public.s101_feature_attr_value",
                "source_id": SOURCE_IDS["db_feature_profile"],
                "source_sha256": "pending",
                "feature_type_code": feature_type_code,
                "feature_count": feature_count,
                "geometry_count": geometry_count,
                "geometry_types": geometry_types,
            },
            related_concepts=["gbhd_s101_20_db_profile"],
        ))
        profile_count += 1

    for natc, value_count, samples in text_value_profiles:
        sample_values = [clean_text(x) for x in (samples or []) if clean_text(x)]
        if not sample_values:
            continue
        content = (
            f"GBHD S-101 2.0 database textual attribute values. NATC: {natc}. "
            f"Observed value count: {value_count}. Distinct text samples: {', '.join(sample_values[:120])}."
        )
        db_sha_seed.append(content)
        rows.append(chunk_row(
            chunk_id=stable_id("s101_db_attr_text", content),
            content=content,
            metadata={
                "document_type": "s101_db_text_values",
                "title": "GBHD S-101 2.0 DB Text Attribute Values",
                "section": f"natc:{natc}",
                "version": S101_CATALOGUE_VERSION,
                "product_specification": S101_PRODUCT_SPECIFICATION,
                "source_file": "gbhd_s101/public.s101_feature_attr_value",
                "source_id": SOURCE_IDS["db_text_values"],
                "source_sha256": "pending",
                "natc": natc,
                "value_count": value_count,
            },
            related_concepts=["gbhd_s101_20_db_text_values"],
        ))

    db_sha = hashlib.sha256("\n".join(db_sha_seed).encode("utf-8")).hexdigest()
    for row in rows:
        row["source_sha256"] = db_sha
        row["metadata"]["source_sha256"] = db_sha
    if valid_geometry_profile:
        feature_count, geometry_count, valid_count, invalid_count, repaired_count, geometry_types = valid_geometry_profile
        content = (
            "GBHD S-101 2.0 valid geometry serving profile. "
            f"Feature count: {feature_count}. Geometry count: {geometry_count}. "
            f"Valid geometry count: {valid_count}. Invalid geometry count: {invalid_count}. "
            f"Repaired geometry count: {repaired_count}. Geometry types: {geometry_types or 'none'}. "
            "This layer is the preferred S-101 spatial serving layer for validated geometry operations."
        )
        rows.append(chunk_row(
            chunk_id=stable_id("s101_valid_geometry_profile", content),
            content=content,
            metadata={
                "document_type": "s101_valid_geometry_profile",
                "title": "GBHD S-101 2.0 Valid Geometry Profile",
                "section": "projection.s101_feature_valid",
                "version": S101_CATALOGUE_VERSION,
                "product_specification": S101_PRODUCT_SPECIFICATION,
                "source_file": "gbhd_s101/projection.s101_feature_valid",
                "source_id": SOURCE_IDS["valid_geometry_profile"],
                "source_sha256": db_sha,
                "feature_count": feature_count,
                "geometry_count": geometry_count,
                "valid_geometry_count": valid_count,
                "invalid_geometry_count": invalid_count,
                "repaired_geometry_count": repaired_count,
            },
            related_concepts=["valid_geometry", "spatial_reliability"],
        ))
    if accident_relation_profile:
        relation_count, accident_count, min_distance, avg_distance, max_distance = accident_relation_profile
        relation_type_text = "; ".join(
            f"{relation_type}: {rel_count} relations across {acc_count} accidents"
            for relation_type, rel_count, acc_count in accident_relation_types
        )
        content = (
            "GBHD S-101 2.0 accident relation serving profile. "
            f"Relation count: {relation_count}. Accident count with relation: {accident_count}. "
            f"Distance meters min/avg/max: {min_distance}/{avg_distance}/{max_distance}. "
            f"Relation type distribution: {relation_type_text or 'none'}. "
            "Relations are generated from standardized accident points and the S-101 valid geometry layer."
        )
        rows.append(chunk_row(
            chunk_id=stable_id("s101_accident_relation_profile", content),
            content=content,
            metadata={
                "document_type": "s101_accident_relation_profile",
                "title": "GBHD S-101 2.0 Accident Relation Profile",
                "section": "serving.accident_s101_relation_current",
                "version": S101_CATALOGUE_VERSION,
                "product_specification": S101_PRODUCT_SPECIFICATION,
                "source_file": "gbhd_s101/serving.accident_s101_relation_current",
                "source_id": SOURCE_IDS["accident_relation_profile"],
                "source_sha256": db_sha,
                "relation_count": relation_count,
                "accident_count": accident_count,
            },
            related_concepts=["accident_hotspot", "s101_relation", "spatial_reliability"],
        ))
    print(f"db_profiles={profile_count} db_text_value_chunks={len(rows) - profile_count}")
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def load_existing_embeddings(output: Path) -> dict[str, dict[str, Any]]:
    existing: dict[str, dict[str, Any]] = {}
    for source_path in (ROOT / "outputs/rag/embeddings_v2.jsonl", output):
        if not source_path.exists():
            continue
        for line in source_path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("chunk_id") and row.get("embedding"):
                existing[row["chunk_id"]] = row
    return existing


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def embed_rows(rows: list[dict[str, Any]], output: Path, resume: bool = True) -> list[dict[str, Any]]:
    model = os.getenv("EMBEDDING_MODEL", "bge-m3")
    endpoint = os.getenv(
        "OLLAMA_EMBEDDING_URL",
        os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434").rstrip("/") + "/api/embed",
    )
    timeout = int(os.getenv("EMBEDDING_TIMEOUT_SEC", "600"))
    batch_size = int(os.getenv("EMBEDDING_BATCH_SIZE", "4"))
    existing = load_existing_embeddings(output) if resume else {}
    if output.exists() and not resume:
        output.unlink()
    embedded: list[dict[str, Any]] = []
    for row in rows:
        existing_row = existing.get(row["chunk_id"])
        if not existing_row:
            continue
        item = dict(row)
        item["embedding"] = existing_row["embedding"]
        item["model"] = existing_row.get("model", model)
        item["dimension"] = len(existing_row["embedding"])
        embedded.append(item)
    pending = [row for row in rows if row["chunk_id"] not in existing]
    print(f"embedding_resume existing={len(embedded)} pending={len(pending)} total={len(rows)}")
    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        body = json.dumps({"model": model, "input": [row["content"] for row in batch]}).encode("utf-8")
        req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            vectors = json.load(response)["embeddings"]
        batch_embedded: list[dict[str, Any]] = []
        for row, vector in zip(batch, vectors):
            item = dict(row)
            item["embedding"] = vector
            item["model"] = model
            item["dimension"] = len(vector)
            batch_embedded.append(item)
        append_jsonl(output, batch_embedded)
        embedded.extend(batch_embedded)
        print(f"embedded={len(embedded)}/{len(rows)}")
    return embedded


def ensure_table(cur, dimension: int) -> None:
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cur.execute("CREATE SCHEMA IF NOT EXISTS knowledge")
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS knowledge.document_chunks (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            product_id TEXT,
            standard_type TEXT,
            title TEXT,
            section TEXT,
            version TEXT,
            language TEXT DEFAULT 'ko',
            content TEXT NOT NULL,
            keywords TEXT[],
            related_features TEXT[],
            related_concepts TEXT[],
            clearance_level TEXT DEFAULT 'PUBLIC',
            source_file TEXT,
            source_url TEXT,
            page_no INTEGER,
            metadata JSONB NOT NULL,
            embedding vector({dimension}),
            created_at TIMESTAMP DEFAULT NOW(),
            source_id TEXT,
            source_sha256 TEXT
        )
    """)
    cur.execute(f"ALTER TABLE knowledge.document_chunks ADD COLUMN IF NOT EXISTS embedding vector({dimension})")


def db_values(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["chunk_id"],
        row["document_id"],
        row["document_type"],
        row["product_id"],
        row["standard_type"],
        row["title"],
        row["section"],
        row["version"],
        row["language"],
        row["content"],
        row["keywords"],
        row["related_features"],
        row["related_concepts"],
        row["clearance_level"],
        row["source_file"],
        row["source_url"],
        row["page_no"],
        json.dumps(row["metadata"], ensure_ascii=False),
        "[" + ",".join(str(float(x)) for x in row["embedding"]) + "]",
        row["source_id"],
        row["source_sha256"],
    )


def upsert_rows(database_url: str, rows: list[dict[str, Any]], replace_source: bool) -> dict[str, Any]:
    if not rows:
        raise RuntimeError("no embedded rows to upsert")
    dimensions = {len(row["embedding"]) for row in rows}
    if len(dimensions) != 1:
        raise RuntimeError(f"embedding dimension mismatch: {sorted(dimensions)}")
    source_ids = sorted({row["source_id"] for row in rows})
    with connect(database_url) as conn:
        with conn.cursor() as cur:
            ensure_table(cur, next(iter(dimensions)))
            if replace_source:
                cur.execute("DELETE FROM knowledge.document_chunks WHERE source_id = ANY(%s)", (source_ids,))
            from psycopg2.extras import execute_batch

            execute_batch(cur, """
                INSERT INTO knowledge.document_chunks
                    (chunk_id, document_id, document_type, product_id, standard_type, title, section, version,
                     language, content, keywords, related_features, related_concepts, clearance_level, source_file,
                     source_url, page_no, metadata, embedding, source_id, source_sha256)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector,%s,%s)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    document_type=EXCLUDED.document_type,
                    title=EXCLUDED.title,
                    section=EXCLUDED.section,
                    content=EXCLUDED.content,
                    keywords=EXCLUDED.keywords,
                    related_features=EXCLUDED.related_features,
                    related_concepts=EXCLUDED.related_concepts,
                    metadata=EXCLUDED.metadata,
                    embedding=EXCLUDED.embedding,
                    source_id=EXCLUDED.source_id,
                    source_sha256=EXCLUDED.source_sha256
            """, [db_values(row) for row in rows], page_size=100)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_metadata ON knowledge.document_chunks USING GIN (metadata)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_v2_embedding ON knowledge.document_chunks USING hnsw (embedding vector_cosine_ops)")
            cur.execute("SELECT COUNT(*), COUNT(*) FILTER (WHERE embedding IS NULL) FROM knowledge.document_chunks")
            total_count, null_embeddings = cur.fetchone()
            cur.execute(
                "SELECT document_type, COUNT(*) FROM knowledge.document_chunks WHERE source_id = ANY(%s) GROUP BY document_type ORDER BY document_type",
                (source_ids,),
            )
            inserted_by_type = dict(cur.fetchall())
    return {
        "total_document_chunks": total_count,
        "null_embeddings": null_embeddings,
        "source_ids": source_ids,
        "inserted_by_type": inserted_by_type,
        "inserted_count": sum(inserted_by_type.values()),
    }


def write_report(path: Path, chunks: list[dict[str, Any]], embedded: list[dict[str, Any]], db_result: dict[str, Any] | None) -> None:
    counts: dict[str, int] = {}
    for row in chunks:
        counts[row["document_type"]] = counts.get(row["document_type"], 0) + 1
    lines = [
        "# S-101 2.0 Catalogue and GBHD DB RAG Build Report",
        "",
        f"- generated_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"- dataset_root: `{DEFAULT_DATASET_ROOT}`",
        f"- product_specification: `{S101_PRODUCT_SPECIFICATION}`",
        f"- catalogue_version: `{S101_CATALOGUE_VERSION}`",
        f"- chunk_count: `{len(chunks)}`",
        f"- embedded_count: `{len(embedded)}`",
        f"- output_chunks: `{DEFAULT_CHUNKS.relative_to(ROOT)}`",
        f"- output_embeddings: `{DEFAULT_EMBEDDINGS.relative_to(ROOT)}`" if embedded else "- output_embeddings: `not generated`",
        "",
        "## Chunk Counts",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in sorted(counts.items()))
    if db_result:
        lines += [
            "",
            "## DB Upsert",
            "",
            f"- inserted_or_replaced_count: `{db_result['inserted_count']}`",
            f"- total_document_chunks: `{db_result['total_document_chunks']}`",
            f"- null_embeddings: `{db_result['null_embeddings']}`",
            f"- source_ids: `{', '.join(db_result['source_ids'])}`",
            f"- inserted_by_type: `{json.dumps(db_result['inserted_by_type'], ensure_ascii=False)}`",
        ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--chunks-output", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--embeddings-output", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--database-url", default=os.getenv("S101_DB_URL") or os.getenv("POSTGIS_URL"))
    parser.add_argument("--embed", action="store_true")
    parser.add_argument("--upsert", action="store_true")
    parser.add_argument("--replace-source", action="store_true")
    args = parser.parse_args()

    chunks = load_catalogue_chunks(args.catalogue)
    chunks.extend(load_dataset_s101_core_chunks(args.dataset_root))
    if args.database_url:
        chunks.extend(fetch_db_chunks(args.database_url))
    else:
        print("database_url_missing=true; only XML catalogue chunks will be generated")
    chunks = sorted({row["chunk_id"]: row for row in chunks}.values(), key=lambda row: row["chunk_id"])
    write_jsonl(args.chunks_output, chunks)

    embedded: list[dict[str, Any]] = []
    db_result = None
    if args.embed:
        embedded = embed_rows(chunks, args.embeddings_output)
    if args.upsert:
        if not embedded:
            if not args.embeddings_output.exists():
                raise RuntimeError("--upsert requires --embed or an existing embeddings output")
            embedded = [json.loads(line) for line in args.embeddings_output.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not args.database_url:
            raise RuntimeError("--upsert requires --database-url, S101_DB_URL, or POSTGIS_URL")
        db_result = upsert_rows(args.database_url, embedded, args.replace_source)

    write_report(args.report_output, chunks, embedded, db_result)
    print(json.dumps({"chunks": len(chunks), "embedded": len(embedded), "db_result": db_result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
