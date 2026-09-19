/* Phase 9 connects the selected S-101 map entity to GeoLLM's execution API.
 * Only a successful, source-attributed Tool response creates a focus action.
 * Unavailable datasets and blocked plans remain visible as explicit messages. */
(() => {
  "use strict";

  const form = document.getElementById("agent-form");
  const query = document.getElementById("agent-query");
  const submit = document.getElementById("agent-submit");
  const contextLabel = document.getElementById("agent-context");
  const resultLabel = document.getElementById("agent-result");
  const featureList = document.getElementById("agent-feature-list");
  let selection = null;
  let activeRequest = null;

  window.addEventListener("uport:map-selection", event => {
    // Map identifiers are converted to numbers only at the API boundary;
    // unknown values stay out of the execution request entirely.
    const nextSelection = event.detail?.entity_type === "s101_berth" ? event.detail : null;
    if (JSON.stringify(nextSelection) !== JSON.stringify(selection)) {
      if (activeRequest) {
        activeRequest.abort();
        activeRequest = null;
        submit.disabled = false;
      }
      renderFeatures([]);
      resultLabel.textContent = nextSelection
        ? "선택한 선석이 변경됐습니다. 질문을 다시 보내 주세요."
        : "지도에서 선석을 선택하면 질의할 수 있습니다.";
    }
    selection = nextSelection;
    contextLabel.textContent = selection
      ? `선택한 S-101 선석 ${selection.feature_id} · 데이터셋 ${selection.dataset_id} · 버전 ${selection.dataset_version_id}`
      : "선택한 지도 객체 없음";
  });

  function renderFeatures(features, kind = "berth") {
    featureList.replaceChildren();
    for (const feature of features) {
      if (feature.type !== "Feature" || !feature.id || !feature.geometry) continue;
      if (kind === "berth" &&
          (!feature.properties?.dataset_id || !feature.properties?.dataset_version_id)) continue;
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = kind === "hazard"
        ? `${String(feature.properties?.feature_name || "S-101 위험객체")} ${feature.id} · 지도에서 보기`
        : `S-101 선석 ${feature.id} · 지도에서 보기`;
      button.addEventListener("click", () => {
        const eventName = kind === "hazard" ? "uport:focus-hazard" : "uport:focus-feature";
        window.dispatchEvent(new CustomEvent(eventName, { detail: { feature } }));
      });
      featureList.appendChild(button);
    }
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();
    const prompt = query.value.trim();
    if (!prompt) return;
    if (activeRequest) activeRequest.abort();
    activeRequest = new AbortController();
    const thisRequest = activeRequest;
    submit.disabled = true;
    resultLabel.textContent = "Capability 선택과 S-101 데이터 검증 중…";
    renderFeatures([]);
    try {
      // The backend Registry chooses the implemented capability. Browser
      // keywords never bypass the shared Agent execution validation path.
      const routeResponse = await fetch("/api/v1/uport/query/route", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: prompt, map_selection: selection }),
        signal: thisRequest.signal
      });
      if (!routeResponse.ok) throw new Error(`Capability HTTP ${routeResponse.status}`);
      const route = await routeResponse.json();
      if (route.mode === "s101_hazard_viewport") {
        const bbox = window.uportGetMapBbox?.();
        if (!bbox) {
          resultLabel.textContent = "지도 범위를 확인할 수 없습니다.";
          return;
        }
        const response = await fetch("/api/v1/uport/s101/hazards/query", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: prompt, bbox }), signal: thisRequest.signal
        });
        if (!response.ok) {
          const failure = await response.json();
          resultLabel.textContent = `${failure.detail?.code || "DATASET_NOT_AVAILABLE"}: ${failure.detail?.message || "위험객체 조회에 실패했습니다."}`;
          return;
        }
        const result = await response.json();
        const features = result.geojson?.features;
        const evidence = result.evidence_bundle?.spatial_feature_evidence;
        if (result.status !== "success" || !Array.isArray(features) ||
            !Array.isArray(evidence) || evidence.length !== features.length ||
            features.length !== result.returned_count) {
          throw new Error("Invalid hazard evidence or GeoJSON response");
        }
        resultLabel.textContent = `${result.narrative} · 피처 근거 ${evidence.length}건`;
        renderFeatures(features, "hazard");
        window.dispatchEvent(new CustomEvent("uport:hazard-query-result", { detail: result }));
        return;
      }
      if (route.mode !== "s101_berth") {
        resultLabel.textContent = "현재 실행 가능한 U-Port 전문 기능이 없습니다. 필요한 데이터·모델 연결 상태를 확인해 주세요.";
        return;
      }
      if (!selection) {
        resultLabel.textContent = "먼저 지도에서 S-101 선석 피처를 선택해 주세요.";
        return;
      }
      const ids = [selection.feature_id, selection.dataset_id, selection.dataset_version_id]
        .map(value => Number(value));
      if (ids.some(value => !Number.isSafeInteger(value) || value <= 0)) {
        resultLabel.textContent = "선택한 피처의 ID가 유효하지 않습니다. 다시 선택해 주세요.";
        return;
      }
      const response = await fetch("/api/v1/uport/query/execute", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: prompt,
          map_selection: {
            entity_type: "s101_berth", feature_id: ids[0],
            dataset_id: ids[1], dataset_version_id: ids[2]
          }
        }), signal: thisRequest.signal
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      if (result.status !== "success") {
        resultLabel.textContent = `${result.error_code || "VALIDATION_FAILED"}: ${result.warnings?.join(" · ") || "실행 조건을 확인해 주세요."}`;
        return;
      }
      const features = Array.isArray(result.features) ? result.features : [];
      const verified = features.filter(feature => feature.type === "Feature" && feature.geometry &&
        String(feature.id) === String(ids[0]) &&
        String(feature.properties?.dataset_id) === String(ids[1]) &&
        String(feature.properties?.dataset_version_id) === String(ids[2]));
      // Narrative is already generated from Tool facts by the backend. The
      // source evidence count is shown separately from the map feature count.
      resultLabel.textContent = `${result.narrative || "조회가 완료됐습니다."} · 근거 ${result.evidence?.length || 0}건`;
      renderFeatures(verified);
      if (verified[0]) {
        window.dispatchEvent(new CustomEvent("uport:focus-feature", { detail: { feature: verified[0] } }));
      }
    } catch (error) {
      if (error.name !== "AbortError") resultLabel.textContent = `질의를 완료하지 못했습니다 (${error.message}).`;
    } finally {
      if (activeRequest === thisRequest) {
        activeRequest = null;
        submit.disabled = false;
      }
    }
  });
})();
