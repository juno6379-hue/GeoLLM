"""Phase 8.7 evidence 후보 검토 템플릿을 생성한다.

기본 decision은 모두 hold이다. 검토자가 명시적으로 approved/rejected/hold를
기입한 항목만 다음 승격 단계에서 사용한다.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "outputs" / "evidence"
REVIEW = ROOT / "outputs" / "review"
DEFAULT_OUTPUT = REVIEW / "evidence_candidate_review_decisions.yaml"
DEFAULT_INPUTS = [
    EVIDENCE / "kg_provenance_candidates.jsonl",
    EVIDENCE / "rag_evidence_candidates.jsonl",
    EVIDENCE / "regulatory_evidence_candidates.jsonl",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def relpath(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/") if path.is_relative_to(ROOT) else str(path)


def compact_candidate(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    return {
        "partition": row.get("partition"),
        "evidence_type": row.get("evidence_type"),
        "summary": row.get("summary"),
        "source_ref": row.get("source_ref"),
        "score": row.get("score"),
        "review_required": row.get("review_required"),
        "dataset_id": data.get("dataset_id"),
        "layer_id": data.get("layer_id"),
        "document_type": data.get("document_type"),
        "title": data.get("title"),
        "source_file": data.get("source_file"),
        "source_id": data.get("source_id"),
        "feature_code": data.get("feature_code"),
        "chunk_id": data.get("chunk_id"),
        "legal_notice_id": data.get("legal_notice_id"),
        "official_dataset_id": data.get("official_dataset_id"),
        "authority_id": data.get("authority_id"),
        "edge_candidates": data.get("edge_candidates") or [],
        "verification_status": data.get("verification_status"),
    }


def build_template(candidates: list[dict[str, Any]], sources: list[Path], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    existing = existing or {}
    previous_decisions = existing.get("decisions") if isinstance(existing.get("decisions"), dict) else {}
    decisions: dict[str, Any] = {}
    for row in sorted(candidates, key=lambda item: (item.get("partition") or "", item.get("evidence_id") or "")):
        evidence_id = row["evidence_id"]
        previous = previous_decisions.get(evidence_id) if isinstance(previous_decisions.get(evidence_id), dict) else {}
        decisions[evidence_id] = {
            "decision": previous.get("decision", "hold"),
            "reviewer": previous.get("reviewer"),
            "reviewed_at": previous.get("reviewed_at"),
            "reason": previous.get("reason", "자동 생성된 evidence 후보입니다. 승인/반려/보류 사유를 검토자가 작성합니다."),
            "review_required_accepted": previous.get("review_required_accepted", False),
            "verification_status_override": previous.get("verification_status_override"),
            "candidate": compact_candidate(row),
        }
    return {
        "version": "0.1",
        "phase": "8.7",
        "status": "review_template_updated" if previous_decisions else "review_template",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources": [relpath(path) for path in sources],
        "policy": {
            "default_decision": "hold",
            "allowed_decisions": ["approved", "rejected", "hold"],
            "approved_requires": ["reviewer", "reviewed_at", "reason"],
            "review_required_candidates_require_acceptance": True,
            "auto_kg_promotion": False,
        },
        "decisions": decisions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 8.7 evidence 후보 검토 템플릿을 생성한다.")
    parser.add_argument("--inputs", nargs="*", type=Path, default=DEFAULT_INPUTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    candidates: list[dict[str, Any]] = []
    for path in args.inputs:
        candidates.extend(load_jsonl(path))
    existing = yaml.safe_load(args.output.read_text(encoding="utf-8")) if args.output.exists() else {}
    doc = build_template(candidates, args.inputs, existing)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(json.dumps({"decisions": len(doc["decisions"]), "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
