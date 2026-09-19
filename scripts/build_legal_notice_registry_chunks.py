"""Build RAG chunks from the authoritative legal notice registry."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs" / "rag"
REPORTS = ROOT / "outputs" / "reports"
DEFAULT_REGISTRY = DATA / "legal_notice_registry.yaml"
DEFAULT_OUTPUT = OUT / "legal_notice_registry_chunks.jsonl"


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_registry(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    values = value if isinstance(value, list) else [value]
    return [str(item) for item in values if str(item or "").strip()]


def build_chunks(registry: dict[str, Any], registry_path: Path) -> list[dict[str, Any]]:
    registries = registry.get("registries") or {}
    notices = registries.get("legal_notices") or {}
    laws = registries.get("laws") or {}
    authorities = registries.get("authorities") or {}
    families = registries.get("notice_families") or {}
    source_text = registry_path.read_text(encoding="utf-8")
    source_sha = sha256_text(source_text)
    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []

    for notice_id, notice in sorted(notices.items()):
        if not isinstance(notice, dict):
            continue
        family_id = notice.get("notice_family")
        family = families.get(family_id or "", {}) if isinstance(families, dict) else {}
        authority = authorities.get(notice.get("authority_id") or "", {}) if isinstance(authorities, dict) else {}
        basis_law_titles = [
            (laws.get(law_id) or {}).get("title_ko") or law_id
            for law_id in as_list(notice.get("basis_laws"))
            if isinstance(laws, dict)
        ]
        ports = as_list(notice.get("ports"))
        keywords = as_list(notice.get("scope_keywords"))
        layers = as_list(notice.get("governs_layers"))
        title = str(notice.get("title_ko") or notice_id)
        notice_no = str(notice.get("notice_no") or "")
        summary = str(notice.get("summary_ko") or "")
        text = "\n".join(
            part
            for part in [
                f"문서명: {title}",
                f"고시번호: {notice_no}" if notice_no else "",
                f"문서유형: {notice.get('notice_type') or '고시'}",
                f"notice_family: {family_id or ''}",
                f"family_label: {family.get('label_ko') or ''}",
                f"항만: {', '.join(ports)}" if ports else "항만: 전체 또는 비항만 특정",
                f"발행기관: {authority.get('name_ko') or notice.get('authority_id') or ''}",
                f"시행일: {notice.get('effective_date') or notice.get('notice_date') or ''}",
                f"근거 법령: {', '.join(str(item) for item in basis_law_titles)}" if basis_law_titles else "",
                f"관련 레이어: {', '.join(layers)}" if layers else "",
                f"공간 적재 상태: {notice.get('spatial_binding_status') or 'unknown'}",
                f"핵심 키워드: {', '.join(keywords)}" if keywords else "",
                f"요약: {summary}" if summary else "",
                f"원문 URL: {notice.get('source_url') or ''}",
            ]
            if part
        )
        chunk_id = hashlib.sha256(f"legal_notice_registry:{notice_id}".encode("utf-8")).hexdigest()[:24]
        metadata = {
            "document_id": f"legal_notice:{notice_id}",
            "document_type": "legal_notice",
            "title": title,
            "section": "legal_notice_registry",
            "version": notice_no or None,
            "language": "ko",
            "source_file": str(registry_path.relative_to(ROOT)).replace("\\", "/"),
            "source_url": notice.get("source_url"),
            "source_id": f"legal_notice:{notice_id}",
            "source_sha256": source_sha,
            "notice_id": notice_id,
            "notice_family": family_id,
            "notice_family_label": family.get("label_ko"),
            "ports": ports,
            "authority_id": notice.get("authority_id"),
            "authority_name": authority.get("name_ko"),
            "basis_laws": as_list(notice.get("basis_laws")),
            "basis_law_titles": basis_law_titles,
            "governs_layers": layers,
            "spatial_binding_status": notice.get("spatial_binding_status"),
            "clearance_level": "PUBLIC",
            "extraction_status": "legal_notice_registry_profile",
            "generated_at": generated_at,
        }
        rows.append({"chunk_id": chunk_id, "text": text, "metadata": metadata})
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    registry_path = args.registry if args.registry.is_absolute() else ROOT / args.registry
    output_path = args.output if args.output.is_absolute() else ROOT / args.output
    registry = read_registry(registry_path)
    rows = build_chunks(registry, registry_path)
    write_jsonl(output_path, rows)

    REPORTS.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "OK",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(registry_path.relative_to(ROOT)).replace("\\", "/"),
        "output": str(output_path.relative_to(ROOT)).replace("\\", "/"),
        "chunk_count": len(rows),
        "notice_families": sorted(set(row["metadata"].get("notice_family") for row in rows if row["metadata"].get("notice_family"))),
    }
    (REPORTS / "legal_notice_registry_chunks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (REPORTS / "legal_notice_registry_chunks.md").write_text(
        "\n".join(
            [
                "# Legal Notice Registry Chunk Report",
                "",
                f"- generated_at: `{report['generated_at']}`",
                f"- registry: `{report['registry']}`",
                f"- output: `{report['output']}`",
                f"- chunk_count: `{report['chunk_count']}`",
                f"- notice_families: `{', '.join(report['notice_families'])}`",
                "",
                "Embedding policy: legal notice registry chunks carry `notice_family`, `ports`, `authority`, `basis_laws`, and `spatial_binding_status` metadata so vector recall can still be verified by Registry/KG precision gates.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
