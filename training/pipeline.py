from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

import yaml
from pydantic import ValidationError

from training.models import TrainingCase

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_FILES = {
    "agent_registry": ROOT / "data/agent_registry.json",
    "capability_registry": ROOT / "data/capability_registry.yaml",
    "tool_registry": ROOT / "data/tool_registry.yaml",
    "data_registry": ROOT / "data/data_registry.yaml",
    "spatial_layer_registry": ROOT / "data/spatial_layer_registry.yaml",
    "query_template_registry": ROOT / "data/query_template_registry.yaml",
    "derived_concept_registry": ROOT / "data/derived_concept_registry_v2.yaml",
    "ontology_registry": ROOT / "data/upper_ontology_registry.yaml",
}


def load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8-sig")
    return json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)


def registry_snapshot() -> dict[str, str]:
    versions: dict[str, str] = {}
    digest = hashlib.sha256()
    for name, path in REGISTRY_FILES.items():
        raw = path.read_bytes()
        digest.update(name.encode())
        digest.update(raw)
        data = load(path)
        versions[name] = str(data.get("version", "unversioned")) if isinstance(data, dict) else "unversioned"
    versions["snapshot_hash"] = f"sha256:{digest.hexdigest()}"
    return versions


def registry_ids() -> dict[str, set[str]]:
    agent_doc = load(REGISTRY_FILES["agent_registry"])
    agent_rows = agent_doc.get("agents", []) if isinstance(agent_doc, dict) else agent_doc
    agents = {row["agent_name"] for row in agent_rows if isinstance(row, dict) and row.get("agent_name")}
    docs = {name: load(path) for name, path in REGISTRY_FILES.items() if name != "agent_registry"}
    return {
        "agents": agents,
        "capabilities": {row["capability_id"] for row in docs["capability_registry"].get("capabilities", []) if row.get("capability_id")},
        "tools": set(docs["tool_registry"].get("tools", {})),
        "datasets": set(docs["data_registry"].get("datasets", {})),
        "layers": set(docs["spatial_layer_registry"].get("layers", {})),
        "templates": set(docs["query_template_registry"].get("templates", {})),
        "concepts": set(docs["derived_concept_registry"].get("derived_concepts", {})),
    }


def canonical_query(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).casefold()
    return re.sub(r"[\W_]+", "", value)


def validate_registry_refs(case: TrainingCase, ids: dict[str, set[str]]) -> list[str]:
    errors: list[str] = []
    checks = [
        ("agent", [case.expected_routing.primary_agent, *case.expected_routing.secondary_agents], ids["agents"]),
        ("capability", case.expected_routing.required_capabilities, ids["capabilities"]),
        ("tool", case.expected_routing.tools, ids["tools"]),
        ("dataset", case.expected_data_bindings.datasets, ids["datasets"]),
        ("layer", case.expected_data_bindings.layers, ids["layers"]),
        ("concept", case.expected_semantics.derived_concepts, ids["concepts"]),
    ]
    if case.expected_routing.query_template:
        checks.append(("query_template", [case.expected_routing.query_template], ids["templates"]))
    for kind, values, allowed in checks:
        for value in values:
            if value and value not in allowed:
                errors.append(f"unknown {kind}: {value}")
    return errors


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def validate_rows(rows: list[dict[str, Any]], holdout_paths: list[Path] | None = None) -> tuple[list[TrainingCase], list[str]]:
    ids = registry_ids()
    seen_ids: set[str] = set()
    seen_queries: set[str] = set()
    holdouts: set[str] = set()
    for path in holdout_paths or []:
        for row in read_jsonl(path):
            query = row.get("query") or row.get("input", {}).get("user_query")
            if query:
                holdouts.add(canonical_query(query))
    parsed: list[TrainingCase] = []
    errors: list[str] = []
    for index, row in enumerate(rows, 1):
        label = row.get("case_id", f"line {index}")
        try:
            case = TrainingCase.model_validate(row)
        except ValidationError as exc:
            errors.append(f"{label}: schema: {exc}")
            continue
        if case.case_id in seen_ids:
            errors.append(f"{label}: duplicate case_id")
        seen_ids.add(case.case_id)
        query_key = canonical_query(case.input.user_query)
        if query_key in seen_queries:
            errors.append(f"{label}: duplicate normalized query")
        seen_queries.add(query_key)
        if case.split in {"train", "seed"} and query_key in holdouts:
            errors.append(f"{label}: exact holdout contamination")
        errors.extend(f"{label}: {item}" for item in validate_registry_refs(case, ids))
        parsed.append(case)
    return parsed, errors


def make_candidate(seed: dict[str, Any], suffix: str, query: str, kind: str) -> dict[str, Any]:
    row = copy.deepcopy(seed)
    family = re.sub(r"^MGEO-SEED-", "", seed["case_id"])
    row["case_id"] = f"MGEO-DRY-{family}-{suffix}"
    row["origin"] = "synthetic_from_seed"
    row["split"] = "train"
    row["review_status"] = "CANDIDATE"
    row["input"]["user_query"] = query
    row["lineage"].update(parent_seed_id=seed["case_id"], generation_kind=kind, generator="deterministic_prompt_dry_run")
    row["quality"] = {"human_verified": False, "reviewer": None, "review_notes": [], "validation_checks": []}
    return row


def dry_run(seed: dict[str, Any]) -> list[dict[str, Any]]:
    slots = seed["expected_slots"]
    location = slots["location_text"]["value"]
    distance_m = slots["distance_m"]["value"]
    distance_km = f"{distance_m / 1000:g}"
    target = slots["target_term"]["value"]
    rows = [
        make_candidate(seed, "PARA-001", f"{location} 반경 {distance_km}km의 {target}를 검색해줘", "semantic_paraphrase"),
        make_candidate(seed, "PARA-002", f"{location}에서 {distance_m}m 안에 있는 {target}를 보여줘", "semantic_paraphrase"),
        make_candidate(seed, "SLOT-001", f"안전항해 검토 범위를 2km로 설정하고 {location}의 {target} S-101 객체 목록을 요청", "slot_variation"),
        make_candidate(seed, "NEG-001", f"{location} {distance_km}km 이내 {target}의 법적 근거만 설명해줘", "hard_negative"),
        make_candidate(seed, "AMB-001", f"{target}를 찾아줘", "ambiguity_missing_slot"),
        make_candidate(seed, "FOLLOW-001", f"{location} 검색 반경을 {distance_m + 1000}m로 조정해줘", "conversational_followup"),
    ]
    rows[2]["expected_slots"]["location_text"]["value"] = location
    rows[2]["expected_slots"]["distance_m"]["value"] = 2000
    rows[2]["expected_semantics"]["normalized_query"] = f"{location} 2km 이내 {target} 검색"

    negative = rows[3]
    negative["expected_semantics"].update(intent="knowledge_search", execution_requested=False, dynamic_data_required=False, spatial_relation=None)
    negative["expected_routing"].update(fast_path="DOCUMENT_PATH", required_capabilities=["tool.graph_scoped_rag"], primary_agent="Standard RAG Agent", tools=["rag.graph_scoped_retrieve"], query_template="graph_scoped_rag", resolver_chain=[])
    negative["expected_data_bindings"] = {"datasets": [], "layers": [], "required_versions": {}}
    negative["expected_execution"].update(execution_ready=True, orchestration_status=["COMPLETED", "BLOCKED"], execution_outcomes=["SUCCESS_WITH_RESULTS", "SUCCESS_EMPTY"])
    negative["expected_evidence"] = {"required_bundle_fields": ["rag_evidence", "kg_provenance"], "execution_trace_required": False, "citation_required": True}
    negative["negative_constraints"] = {"forbidden_agents": ["Spatial Analysis Agent"], "forbidden_capabilities": ["tool.spatial_radius_search"], "forbidden_tools": ["postgis.dwithin"]}
    negative["quality"]["review_notes"] = ["Hard negative: legal-evidence wording must not trigger spatial execution tools."]

    for row in rows[4:6]:
        row["expected_execution"].update(execution_ready=False, orchestration_status=["NEEDS_CLARIFICATION"], execution_outcomes=["NOT_EXECUTED"], blockers=["MISSING_LOCATION"])
        row["expected_routing"]["tools"] = []
        row["ambiguity"] = {"is_ambiguous": True, "candidate_interpretations": ["이전 대화의 위치 사용", "사용자에게 위치 확인"], "clarification_question": "어느 지역을 기준으로 검색할까요?"}
        row["expected_answer"] = {"mode": "clarification", "reference_answer": "어느 지역을 기준으로 검색할까요?", "required_points": ["위치 확인"], "forbidden_claims": ["임의 위치 추정"]}
    rows[4]["expected_semantics"].update(execution_requested=False, dynamic_data_required=False)
    rows[5]["input"]["conversation_context"] = [{"role": "user", "content": seed["input"]["user_query"]}, {"role": "assistant", "content": "검색 조건을 확인했습니다."}]
    rows[5]["expected_slots"]["location_text"].update(value="부산항 입구", source="conversation_context")
    rows[5]["expected_slots"]["distance_m"].update(value=distance_m + 1000, source="user_explicit")
    rows[5]["expected_execution"].update(execution_ready=True, orchestration_status=["COMPLETED", "BLOCKED"], execution_outcomes=["SUCCESS_WITH_RESULTS", "SUCCESS_EMPTY"], blockers=[])
    rows[5]["expected_routing"]["tools"] = seed["expected_routing"]["tools"]
    rows[5]["ambiguity"] = {"is_ambiguous": False, "candidate_interpretations": [], "clarification_question": None}
    rows[5]["expected_answer"] = {"mode": "behavioral", "reference_answer": None, "required_points": ["변경된 검색 반경", "실행 상태", "근거 요약"], "forbidden_claims": ["실행되지 않은 동적 결과 수"]}
    return rows


def derive_views(cases: list[TrainingCase], out_dir: Path) -> None:
    component: list[dict[str, Any]] = []
    end_to_end: list[dict[str, Any]] = []
    response: list[dict[str, Any]] = []
    for case in cases:
        data = case.model_dump(mode="json")
        component.append({"case_id": case.case_id, "input": {"gold_semantics": data["expected_semantics"], "gold_slots": data["expected_slots"]}, "target": data["expected_routing"]})
        end_to_end.append({"case_id": case.case_id, "input": data["input"], "target": {"semantics": data["expected_semantics"], "slots": data["expected_slots"], "routing": data["expected_routing"], "execution": data["expected_execution"]}})
        response.append({"case_id": case.case_id, "input": {"query": case.input.user_query, "resolved_context": {"semantics": data["expected_semantics"], "slots": data["expected_slots"]}, "route_plan": data["execution_fixture"]["route_plan"], "execution_result": data["execution_fixture"]["execution_result"], "evidence_bundle": data["execution_fixture"]["evidence_bundle"], "answer_policy": data["expected_answer"]}, "target": data["expected_answer"]})
    write_jsonl(out_dir / "component_teacher_forcing.jsonl", component)
    write_jsonl(out_dir / "end_to_end.jsonl", end_to_end)
    write_jsonl(out_dir / "response_generator.jsonl", response)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["schema", "dry-run", "validate", "views"])
    parser.add_argument("--input", type=Path, default=ROOT / "training/seeds/canonical_seeds.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "training/generated")
    args = parser.parse_args()
    if args.command == "schema":
        target = ROOT / "training/schemas/training_case.schema.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(TrainingCase.model_json_schema(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(target)
        return 0
    rows = read_jsonl(args.input)
    if args.command == "dry-run":
        rows = dry_run(rows[0])
        write_jsonl(args.output / "dry_run_candidates.jsonl", rows)
    holdouts = [ROOT / "tests/benchmark/benchmark_cases_v1.jsonl", ROOT / "tests/benchmark/geollm_ui_preset_cases_v1.jsonl"]
    cases, errors = validate_rows(rows, holdouts)
    if errors:
        print("\n".join(errors))
        return 1
    if args.command in {"dry-run", "views"}:
        derive_views(cases, args.output / "views")
    print(f"validated={len(cases)} errors=0 snapshot={registry_snapshot()['snapshot_hash']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
