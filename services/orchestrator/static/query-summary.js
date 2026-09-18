(function () {
    "use strict";

    const names = {
        Wreck: "침선",
        Obstruction: "장애물",
        UnderwaterAwashRock: "수중암·간출암",
        IsolatedDangerBuoy: "고립위험 부표",
        IsolatedDangerBeacon: "고립위험 표지",
        EmergencyWreckMarkingBuoy: "응급 침선표지 부표",
        LateralBuoy: "측방 부표",
        LateralBeacon: "측방 표지",
        CardinalBuoy: "방위표지 부표",
        CardinalBeacon: "방위표지",
        SpecialPurposeGeneralBuoy: "특수목적 부표",
        SpecialPurposeGeneralBeacon: "특수목적 표지",
        LightAllAround: "전방위등",
        LightSectored: "섹터등",
    };
    const featureName = value => names[value] || value || "공간 객체";
    const numberText = value => value.toLocaleString("ko-KR");
    const distanceText = value => Number.isFinite(value) && value >= 0
        ? value >= 1000 ? `${numberText(value / 1000)}km` : `${numberText(value)}m` : "거리 미확인";
    const countValid = value => Number.isInteger(value) && value >= 0;
    const node = id => document.getElementById(id);

    function reset() {
        node("querySummary").hidden = true;
        delete node("querySummary").dataset.resultId;
        for (const id of ["querySummaryQuery", "querySummaryStatus", "querySummaryTitle", "querySummaryBody"]) node(id).textContent = "";
        node("querySummaryFacts").replaceChildren();
        node("querySummary").querySelectorAll(".query-summary-detail").forEach(element => element.remove());
    }

    function show(status, message, query) {
        const previousQuery = node("querySummaryQuery").textContent;
        reset();
        node("querySummary").hidden = false;
        node("querySummaryStatus").textContent = status;
        node("querySummaryQuery").textContent = query ?? previousQuery;
        node("querySummaryTitle").textContent = status;
        const paragraph = String(message || "").split(/\n\s*\n/)[0];
        node("querySummaryBody").textContent = paragraph.length > 320 ? `${paragraph.slice(0, 320)}...` : paragraph;
        if (paragraph.length > 320) {
            const details = document.createElement("details");
            details.className = "query-summary-detail";
            const summary = document.createElement("summary");
            summary.textContent = "상세정보";
            const full = document.createElement("pre");
            full.textContent = paragraph;
            details.append(summary, full);
            node("querySummaryFacts").before(details);
        }
    }

    function fact(label, value) {
        const term = document.createElement("dt");
        const description = document.createElement("dd");
        term.textContent = label;
        description.textContent = value;
        node("querySummaryFacts").append(term, description);
    }

    function percent(value) {
        const n = Number(value);
        return Number.isFinite(n) ? `${(n * 100).toFixed(1)}%` : "-";
    }

    function quality(result) {
        const structured = result?.structured_result || {};
        const orch = result?.orchestrator_v2 || {};
        return result?.quality_metrics || structured.quality_metrics || orch.quality_metrics || {};
    }

    function renderGeneric(result, originalQuery, geojsonData) {
        const structured = result?.structured_result || {};
        const orch = result?.orchestrator_v2 || {};
        const route = orch.route_plan || {};
        const trace = orch.candidate_trace || {};
        const contract = orch.execution_contract || trace.execution_contract || {};
        const status = result?.status || structured.status || "UNKNOWN";
        const query = structured.original_query || originalQuery || node("querySummaryQuery").textContent;
        const summary = result?.answer_text || result?.summary || structured.summary || "";
        const features = Array.isArray(geojsonData?.features)
            ? geojsonData.features.filter(feature => !(feature.properties && (feature.properties.is_buffer || feature.properties.role === "search_buffer")))
            : [];
        const count = structured.returned_count ?? structured.count ?? features.length;
        const q = quality(result);
        const titleName = structured.location_text || route.slots?.location_text || route.slots?.target_term || route.analysis_type || result?.agent_name || "결과";

        show(status === "COMPLETED" ? "분석 완료" : status, summary || "질의 처리 결과를 확인했습니다.", query);
        node("querySummaryTitle").textContent = status === "COMPLETED"
            ? `${titleName} 질의 결과`
            : `${titleName} 처리 상태`;

        if (route.intent) fact("의도", route.intent);
        if (route.analysis_type || structured.analysis_type) fact("분석 유형", route.analysis_type || structured.analysis_type);
        if (structured.location_text) fact("기준 위치", structured.location_text);
        if (structured.geometry || structured.reference_geometry) fact("기준 좌표", structured.geometry || structured.reference_geometry);
        if (Number.isFinite(Number(count))) fact("지도 표시 객체", `${Number(count).toLocaleString("ko-KR")}건`);
        if (q.intent_similarity !== undefined) fact("의도 유사도", percent(q.intent_similarity));
        if (q.kg_similarity !== undefined) fact("KG 유사도", percent(q.kg_similarity));
        if (q.evidence_similarity !== undefined) fact("근거 유사도", percent(q.evidence_similarity));
        if (q.estimated_accuracy !== undefined) fact("추정 정확도", percent(q.estimated_accuracy));
        if (trace.semantic_prior?.place_type_candidates?.length) {
            fact("Semantic Prior", trace.semantic_prior.place_type_candidates
                .slice(0, 3)
                .map(item => `${item.type}:${percent(item.confidence)}`)
                .join(", "));
        }
        if (trace.capability_candidates?.length) {
            fact("Capability top-k", trace.capability_candidates
                .slice(0, 3)
                .map(item => item.candidate_id || item.id || item.label)
                .filter(Boolean)
                .join(", "));
        }
        if (contract.status || contract.readiness || contract.reason) {
            fact("Execution Contract", `${contract.status || contract.readiness || "-"}${contract.reason ? `: ${contract.reason}` : ""}`);
        }
        if (structured.location_resolution?.method) fact("위치 해석", structured.location_resolution.method);
        if (structured.location_resolution?.source_ref || features[0]?.properties?.source_ref) {
            fact("근거", structured.location_resolution?.source_ref || features[0].properties.source_ref);
        }
    }

    function renderRadius(result, originalQuery) {
        const data = result.structured_result || {};
        const query = data.original_query || originalQuery;
        const status = result.status || data.status;
        const needsInput = [status, data.status].some(value => ["NEEDS_CLARIFICATION", "NEEDS_USER_INPUT"].includes(value));
        if (needsInput || !["COMPLETED", "SUCCESS", "SUCCESS_EMPTY"].includes(status)) {
            show(needsInput ? "입력 확인 필요" : status === "FAILED" ? "조회 실패" : "조회 차단", result.summary || result.answer_text || "검색 결과가 확정되지 않았습니다.", query);
            return;
        }
        const total = data.total_count ?? data.count;
        const returned = data.returned_count;
        if (!countValid(total) || !countValid(returned) || returned > total) {
            show("결과 확인 필요", "검색 건수가 확인되지 않아 결과를 요약할 수 없습니다.", query);
            return;
        }
        const location = data.location_text || "지정한 기준점";
        const targets = data.target_features || result.orchestrator_v2?.route_plan?.slots?.target_features || [];
        const target = targets.length === 1 ? featureName(targets[0]) : "주의 대상 객체";
        const range = `${location} 기준 ${distanceText(data.distance_m)} 이내`;
        show(total ? "조회 완료" : "조회 완료 · 해당 객체 없음", "기준점과 각 객체 사이의 거리가 검색 반경 이내인 결과입니다.", query);
        node("querySummary").dataset.resultId = data.result_id || "";
        node("querySummaryTitle").textContent = total
            ? `${range} ${target} ${numberText(total)}건을 찾았습니다.`
            : `${range}에서 조건에 해당하는 객체를 찾지 못했습니다.`;
        const offset = countValid(data.offset) ? data.offset : 0;
        fact("현재 표시", returned
            ? `전체 ${numberText(total)}건 중 ${numberText(offset + 1)}~${numberText(offset + returned)}번째 ${numberText(returned)}건 · 지도·목록·근거 공통`
            : "현재 페이지에 표시할 객체가 없습니다.");
        // Only whole-result type totals may describe the whole search, never page counts.
        const counts = Object.entries(data.total_counts_by_type || {});
        if (counts.length && counts.every(([, count]) => countValid(count)) && counts.reduce((sum, [, count]) => sum + count, 0) === total) {
            fact("전체 구성", counts.map(([name, count]) => `${featureName(name)} ${numberText(count)}건`).join(" · "));
        }
        if (targets.length) fact("검색 대상", targets.map(featureName).join(", "));
        if (data.exclusions?.length) fact("제외 조건", data.exclusions.map(featureName).join(", "));
    }

    window.QuerySummary = { reset, show, renderGeneric, renderRadius, featureName, distanceText };
})();
