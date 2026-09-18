"""Materialize Data Discovery Agent capability and deferred-edge reports."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from services.data_discovery_agent.agent import build_discovery_snapshot, DEFERRED_RELATIONS, PROJECT_ROOT

def main():
    result = build_discovery_snapshot()
    graph = PROJECT_ROOT / "outputs/graph"
    reports = PROJECT_ROOT / "outputs/reports"
    graph.mkdir(parents=True, exist_ok=True); reports.mkdir(parents=True, exist_ok=True)
    (graph / "deferred_edges_status.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in result["blocked_relations"]), encoding="utf-8")
    (graph / "candidate_edges_from_discovery.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in result["candidate_data"]), encoding="utf-8")
    (graph / "verified_edges_from_discovery.jsonl").touch(exist_ok=True)
    (reports / "08_data_discovery_agent_integration.md").write_text(f'''# Data Discovery Agent 통합 보고서

## 현재 판정

- discovery_status: `{result['discovery_status']}`
- execution_level: `{result['execution_level']}`
- can_execute_spatial_query: `{result['can_execute_spatial_query']}`
- can_verify_spatial_edges: `{result['can_verify_spatial_edges']}`

Data Discovery Agent는 Data Lake Inventory, v2 Dictionary/Registry, RAG manifest, KG bootstrap 산출물을 조회한다. S101 v2 DB 연결이 없으면 공간 도구를 호출하지 않고 catalogue availability와 실행 불가 사유만 반환한다.

## 사용 가능 데이터

{chr(10).join('- '+x for x in result['available_data'])}

## 누락 데이터

{chr(10).join('- '+x for x in result['missing_data'])}

## 다음 조치

{chr(10).join('- '+x for x in result['required_next_actions'])}

## Provenance

`outputs/inventories/dataset_inventory.csv`, `outputs/rag/rag_manifest.json`, `outputs/graph/kg_nodes_v2.jsonl`, S101 DB probe 설정을 사용했다.
''', encoding="utf-8")
    (reports / "08_1_deferred_relation_resolution_report.md").write_text(f'''# Deferred Relation Resolution 보고서

대상 관계: {', '.join(DEFERRED_RELATIONS)}

{chr(10).join(f"- `{x['relation']}`: **{x['status']}**. {x['reason']}" for x in result['blocked_relations'])}

현재 `verified_edges_from_discovery.jsonl`은 비어 있다. LLM 추측으로 관계를 VERIFIED 처리하지 않으며, geometry·문서 본문·사고 위치 근거가 확보될 때만 후속 검증 작업에서 갱신한다.
''', encoding="utf-8")
    print(f"discovery_reports_generated level={result['execution_level']}")

if __name__ == "__main__": main()
