#!/usr/bin/env python
"""Build the GeoLLM preset query list and matching benchmark cases."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = ROOT / "services" / "orchestrator" / "static" / "index.html"
CASES_JSONL = ROOT / "tests" / "benchmark" / "geollm_ui_preset_cases_v1.jsonl"

FORBIDDEN_TEXT = [
    "Object of type date is not JSON serializable",
    "Agent 'ClarificationAgent' has no entry_point",
    "task_id\n  Input should be a valid string",
    "user_id\n  Input should be a valid string",
    "organization_id\n  Input should be a valid string",
    "1 validation error for TaskPlan",
    "context\n  Input should be a valid string",
    "timed out",
]

PRESET_QUERIES: list[dict[str, Any]] = [
    {"query": "해운대구로 이동", "category": "place_fast_path", "expected_status": ["COMPLETED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 6000, "expected_nodes": ["instant_place_lookup"], "forbidden_nodes": ["parse_intent"]},
    {"query": "독도를 찾아줘", "category": "place_lookup", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 12000},
    {"query": "부산항 입구로 이동", "category": "place_fast_path", "expected_status": ["COMPLETED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 8000},
    {"query": "인천항으로 이동", "category": "place_fast_path", "expected_status": ["COMPLETED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 8000},
    {"query": "울릉도 주변 지명을 찾아줘", "category": "gazetteer", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 20000},
    {"query": "독도 부근 지명을 찾아줘", "category": "gazetteer", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 20000},
    {"query": "독도 부근 해저지명을 찾아줘", "category": "marine_gazetteer", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 20000},
    {"query": "독도구근해저지명", "category": "normalizer_typo", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 20000, "forbidden_text": ["location_text\": \"\""]},
    {"query": "해양지명 gazetteer와 도서지명 gazetteer가 어떤 근거로 적재되었는지 설명해줘", "category": "evidence_dataset", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "위험객체", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 20000},
    {"query": "부산항 입구 3km 이내 위험객체를 찾아줘", "category": "s101_hazard_radius", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항입구3km위험객체", "category": "normalizer_spacing", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 입구 위험객체", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "부산항 입구 1km 이내 침선을 찾아줘", "category": "s101_wreck", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 입구 5km 이내 암초와 간출암을 표시해줘", "category": "s101_rocks", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 입구 3km 이내 부표와 위험표지를 같이 보여줘", "category": "navigation_aid_hazard", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "울산항 3km 이내 장애물을 찾아줘", "category": "s101_hazard_radius", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "목포항 주변 항로표지를 보여줘", "category": "navigation_aid", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "항로표지정보_20250623.csv 파싱/표준화/공간 적재 근거를 보여줘", "category": "evidence_dataset", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Dataset 폴더의 해양수산부 항로표지 CSV는 embedding 대상인지 확인해줘", "category": "embedding_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "정박지는 S-101에서 어떤 Feature야?", "category": "s101_definition", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 입구 주변 정박지와 항로표지를 같이 조회해줘", "category": "multi_layer_spatial", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "정박지/일반항로/통항분리 레이어가 적재되어 있는지 확인해줘", "category": "spatial_layer_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "진입제한구역과 속도제한구역 레이어가 적재되어 있는지 확인해줘", "category": "spatial_layer_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "인천항 주변 통항분리구역을 표시해줘", "category": "traffic_separation", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 주변 일반항로를 보여줘", "category": "fairway", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "여수항 주변 정박지를 보여줘", "category": "anchorage", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "최근 1년간 AIS/V-PASS 통항량을 분석해줘", "category": "dynamic_traffic", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "AIS와 V-PASS 데이터는 어느 기간까지 적재되어 있어?", "category": "dynamic_traffic_metadata", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "최근 1년 통항량이 가장 높은 격자와 월을 알려줘", "category": "dynamic_traffic_grid", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "부산항 최근 12개월 AIS 통항량을 구역별로 요약해줘", "category": "dynamic_traffic_area", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "인천항 최근 12개월 V-PASS 통항량을 월별로 보여줘", "category": "dynamic_traffic_monthly", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "통항량 지도 셀을 클릭했을 때 보여줄 AIS/V-PASS 세부정보를 설명해줘", "category": "ui_explainability", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "독도 부근 사고 이력", "category": "accident_spatial", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000, "forbidden_text": ["location_text\": \"\""]},
    {"query": "독도 사고 이력", "category": "accident_place", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "독도 주변 10km 이내 사고와 위험객체를 같이 비교해줘", "category": "multi_tool_spatial", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 45000},
    {"query": "창원 정비불량 사건을 찾아줘", "category": "accident_event", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "해양경찰청 해상조난사고 데이터는 임베딩되었나?", "category": "embedding_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산 앞바다 충돌 사고 이력을 찾아줘", "category": "accident_type", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "포항 기관손상 사고 사례를 찾아줘", "category": "accident_cause", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "최근 사고 이력", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "사고 찾아줘", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "S-101 2.0 Obstruction 정의와 DCEG 근거를 알려줘", "category": "s101_definition", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Wreck 정의와 S-101 근거를 알려줘", "category": "s101_definition", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Obstruction 렌더링 규칙 설명해줘", "category": "portrayal", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "S-101 portrayal symbol과 장애물 아이콘 매칭 근거를 보여줘", "category": "portrayal", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "지도에서 빨간 폴리곤이 무엇인지 설명 가능한 정보로 보여줘", "category": "ui_explainability", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "위험객체 지도 클릭 시 feature 정보와 근거를 같이 보여줘", "category": "ui_explainability", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "제부도 바닷길 예측 정보를 알려줘", "category": "sea_parting", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "제부도바닷길예측정보", "category": "normalizer_spacing", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "무창포 바다갈라짐 시간을 알려줘", "category": "sea_parting", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "진도 모도 바다갈라짐 예측을 보여줘", "category": "sea_parting", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "바다갈라짐 알려줘", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "바다갈라짐 예측정보 데이터는 공간 적재되었나?", "category": "spatial_layer_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "인천항 주변 선박안전교통관제구역을 표시해줘", "category": "vts_area", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "인천항VTS표시", "category": "normalizer_spacing", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 주변 선박안전교통관제구역을 찾아줘", "category": "vts_area", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "선박안전교통관제구역 보여줘", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "부산항 주변 투기장을 찾아줘", "category": "dumping_ground", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 산업폐기물투기구역 찾아줘", "category": "dumping_ground", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "산업폐기물투기구역찾아줘", "category": "normalizer_spacing", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED", "COMPLETED"], "max_elapsed_ms": 30000},
    {"query": "투기장 보여줘", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "독도 주변 보호수역을 찾아줘", "category": "protected_area", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "해운대구 주변 천연보호구역을 찾아줘", "category": "external_gap_fill", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "독도 부근 천연보호구역을 찾아줘", "category": "external_gap_fill", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "전자해도에 없으면 국가유산 보호구역 근거도 찾아줘", "category": "external_gap_fill", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "OSM에서 해운대구 지명과 주소 후보를 보완해줘", "category": "external_gap_fill", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000},
    {"query": "보호수역 찾아줘", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "포항 주변 와류 위험구역을 보여줘", "category": "eddy_hazard", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "울산 주변 와류 발생 위험을 찾아줘", "category": "eddy_hazard", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "와류 위험구역 보여줘", "category": "clarification", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "신항만예정지역을 지도에 표시해줘", "category": "planned_port", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산 신항만예정지역을 찾아줘", "category": "planned_port", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Dataset 폴더 안의 공간 적재 완료 현황을 요약해줘", "category": "dataset_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Dataset 폴더 안의 embedding 완료 현황을 요약해줘", "category": "embedding_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "해양수산부 바다갈라짐 ZIP은 어떤 방식으로 좌표를 보완했어?", "category": "dataset_provenance", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "공간 적재되지 않은 Dataset 항목이 남아 있는지 알려줘", "category": "dataset_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "법령/사고/표준 문서 embedding 산출물이 live knowledge.document_chunks에 병합되었는지 확인해줘", "category": "embedding_audit", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "capability_embeddings 테이블과 pgvector top-k가 동작하는지 확인해줘", "category": "capability_retrieval", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "질의를 multi-label route로 분류한 근거를 보여줘", "category": "router_explainability", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Resolver Registry에서 사용 가능한 해양 resolver 목록을 보여줘", "category": "registry", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Ontology/KG validator가 후보를 제거한 이유를 설명해줘", "category": "kg_validation", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "ExecutionValidator가 이 질의를 실행 가능한지 판단한 근거를 보여줘", "category": "execution_validator", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "위치 없이 부근 사고를 찾아줘", "category": "validator_negative", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000, "forbidden_text": ["execution_ready\": true"]},
    {"query": "부근 해저지명 찾아줘", "category": "validator_negative", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000, "forbidden_text": ["execution_ready\": true"]},
    {"query": "3km 이내 위험객체를 찾아줘", "category": "validator_negative", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000, "forbidden_text": ["execution_ready\": true"]},
    {"query": "해운대구 근처 사고와 보호구역을 같이 찾아줘", "category": "multi_intent", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 40000},
    {"query": "독도 주변 해저지명과 사고 이력을 같이 보여줘", "category": "multi_intent", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 40000},
    {"query": "부산항 주변 항로표지와 위험객체를 같이 보여줘", "category": "multi_intent", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 40000},
    {"query": "인천항 주변 VTS와 통항량을 같이 분석해줘", "category": "multi_intent", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 40000},
    {"query": "독도부근사고이력", "category": "normalizer_spacing", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 35000, "forbidden_text": ["location_text\": \"\""]},
    {"query": "해운대구로이동", "category": "normalizer_spacing", "expected_status": ["COMPLETED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 10000},
    {"query": "부산항입구위험객체", "category": "normalizer_spacing_clarify", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED", "COMPLETED"], "max_elapsed_ms": 30000},
    {"query": "Dokdo nearby marine gazetteer", "category": "mixed_language", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "Haeundae-gu move map", "category": "mixed_language", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "부산항 obstruction 3km", "category": "mixed_language", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "내일 인천 앞바다 파고 예보를 알려줘", "category": "unsupported_weather_or_external", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "9월 인천 대조기 일정을 알려줘", "category": "unsupported_tide_or_external", "expected_status": ["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION"], "max_elapsed_ms": 30000},
    {"query": "없는항구 주변 위험객체를 찾아줘", "category": "resolver_negative", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
    {"query": "asdfasdf 위험객체", "category": "resolver_negative", "expected_status": ["NEEDS_CLARIFICATION", "BLOCKED"], "max_elapsed_ms": 25000},
]


def build_case(row: dict[str, Any], index: int) -> dict[str, Any]:
    case: dict[str, Any] = {
        "case_id": f"GEOLLM_UI_{index:03d}_{row['category'].upper()}",
        "query": row["query"],
        "category": row["category"],
        "expected_status": row["expected_status"],
        "forbidden_text": FORBIDDEN_TEXT + row.get("forbidden_text", []),
        "max_elapsed_ms": row["max_elapsed_ms"],
    }
    if row.get("expected_nodes"):
        case["expected_nodes"] = row["expected_nodes"]
    if row.get("forbidden_nodes"):
        case["forbidden_nodes"] = row["forbidden_nodes"]
    if row.get("expected_text"):
        case["expected_text"] = row["expected_text"]
    return case


def update_cases() -> None:
    if len(PRESET_QUERIES) != 100:
        raise RuntimeError(f"Expected exactly 100 preset queries, got {len(PRESET_QUERIES)}")
    lines = [json.dumps(build_case(row, idx), ensure_ascii=False) for idx, row in enumerate(PRESET_QUERIES, start=1)]
    CASES_JSONL.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_index() -> None:
    text = INDEX_HTML.read_text(encoding="utf-8")
    prompts = [row["query"] for row in PRESET_QUERIES]
    static_buttons = "\n".join(
        f'                        <div class="preset-btn" onclick="document.getElementById(\'query\').value=this.innerText">{html.escape(prompt)}</div>'
        for prompt in prompts
    )
    text = re.sub(
        r'(<div class="preset-prompts" id="chatHistory">\n)(.*?)(\n\s*</div>\n\s*<div class="chat-input-area">)',
        lambda match: match.group(1) + static_buttons + match.group(3),
        text,
        count=1,
        flags=re.DOTALL,
    )

    prompts_js = json.dumps(prompts, ensure_ascii=False, indent=16)
    replacement = (
        "function setupPresetPrompts() {\n"
        f"            const prompts = {prompts_js};\n"
        "            const container = document.getElementById(\"chatHistory\");\n"
        "            if (!container) return;\n"
        "            container.innerHTML = \"\";\n"
        "            prompts.forEach(prompt => {\n"
        "                const button = document.createElement(\"div\");\n"
        "                button.className = \"preset-btn\";\n"
        "                button.textContent = prompt;\n"
        "                button.onclick = () => { document.getElementById(\"query\").value = prompt; };\n"
        "                container.appendChild(button);\n"
        "            });\n"
        "        }\n\n"
        "        "
    )
    text = re.sub(
        r"function setupPresetPrompts\(\) \{.*?\n\s*window\.addEventListener",
        replacement + "window.addEventListener",
        text,
        count=1,
        flags=re.DOTALL,
    )
    INDEX_HTML.write_text(text, encoding="utf-8")


def main() -> int:
    update_cases()
    update_index()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
