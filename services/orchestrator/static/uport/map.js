/* U-Port map integration, Phase 4.
 * The existing GeoLLM Leaflet stack and S-101 WMS are reused. Charted Berth
 * features come from a bounded, read-only GeoLLM API. AIS is deliberately
 * absent until a timestamped live provider is registered. */
(() => {
  "use strict";

  const status = document.getElementById("map-status");
  const selection = document.getElementById("map-selection");
  const chartToggle = document.getElementById("layer-s101");
  const berthToggle = document.getElementById("layer-berths");
  const hazardToggle = document.getElementById("layer-hazards");
  const hazardStatus = document.getElementById("hazard-status");

  // A missing CDN must remain an explicit empty state rather than producing
  // an apparently working map with no chart or geographic context.
  if (typeof L === "undefined") {
    status.textContent = "지도 라이브러리를 불러오지 못했습니다";
    return;
  }

  // Use the same WMS URL, layer name, palette and basic Leaflet stack as the
  // GeoLLM root UI. OSM supplies context beneath the transparent chart layer.
  const map = L.map("port-map").setView([35.50, 129.39], 12);
  const background = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: "© OpenStreetMap contributors"
  }).addTo(map);
  const chart = L.tileLayer.wms("http://localhost:11002/encService", {
    layers: "enc101", format: "image/png", transparent: true,
    version: "1.1.1", displayMode: "base,standard,others", showTeText: true,
    colorPalette: "DAY", simplifiedPoint: false,
    attribution: "© S-101 GreenBlue ENC"
  }).addTo(map);
  const berths = L.geoJSON(null, {
    // The S-101 projection contains both Point and LineString Berth objects.
    // Circle markers distinguish points; lines use the same selected color.
    pointToLayer: (_feature, latlng) => L.circleMarker(latlng, {
      radius: 7, color: "#064da5", weight: 2, fillColor: "#48c5f2", fillOpacity: .9
    }),
    style: { color: "#075fac", weight: 4 },
    onEachFeature: (feature, layer) => layer.on("click", () => {
      // textContent prevents DB values from being interpreted as HTML. This
      // selected ID is the future Map → Agent context key.
      const id = String(feature.id ?? "unknown");
      const dataset = String(feature.properties?.dataset_id ?? "unknown");
      const context = {
        domain: "uport", entity_type: "s101_berth", feature_id: id,
        dataset_id: dataset,
        dataset_version_id: String(feature.properties?.dataset_version_id ?? "unknown")
      };
      window.uportMapContext = context;
      window.dispatchEvent(new CustomEvent("uport:map-selection", { detail: context }));
      selection.textContent = `선택한 S-101 선석 피처 ${id} · 데이터셋 ${dataset} · 점유 상태 정보 없음`;
    })
  }).addTo(map);
  // Agent results live in a separate overlay. Panning reloads the viewport
  // berth collection, but must not silently remove a verified result.
  const resultOverlay = L.geoJSON(null, {
    pointToLayer: (_feature, latlng) => L.circleMarker(latlng, {
      radius: 10, color: "#ec6b19", weight: 3, fillColor: "#ffd468", fillOpacity: 1
    }),
    style: { color: "#ec6b19", weight: 6 }
  }).addTo(map);
  const hazards = L.geoJSON(null, {
    // Keep charted hazards visually separate from the selected berth and
    // verified Agent result. The GeoLLM pipeline supplies the actual objects.
    pointToLayer: (_feature, latlng) => L.circleMarker(latlng, {
      radius: 6, color: "#9c2b27", weight: 2, fillColor: "#f69b42", fillOpacity: .9
    }),
    style: { color: "#c3442d", weight: 3 },
    onEachFeature: (feature, layer) => layer.on("click", () => {
      const type = String(feature.properties?.feature_name || "S-101 위험객체");
      hazardStatus.textContent = `${type} · S-101 피처 ${String(feature.id || "식별자 없음")} · 선박 위험도 판정 아님`;
    })
  });
  const hazardFocus = L.geoJSON(null, {
    pointToLayer: (_feature, latlng) => L.circleMarker(latlng, {
      radius: 11, color: "#8e1c1c", weight: 3, fillColor: "#ffd468", fillOpacity: 1
    }),
    style: { color: "#8e1c1c", weight: 6 }
  }).addTo(map);

  let activeRequest = null;
  let debounceTimer = null;
  let chartReady = false;
  let hazardRequest = null;

  // The Agent reads the current extent at submit time. It never reuses a
  // stale bbox saved before the user panned or zoomed the Leaflet map.
  window.uportGetMapBbox = () => {
    const bounds = map.getBounds();
    return [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()]
      .map(value => value.toFixed(6)).join(",");
  };

  function showHazards(result) {
    if (result.status !== "success" || result.geojson?.type !== "FeatureCollection" ||
        !Array.isArray(result.geojson.features) ||
        !Array.isArray(result.evidence_bundle?.spatial_feature_evidence) ||
        result.evidence_bundle.spatial_feature_evidence.length !== result.geojson.features.length ||
        !result.source_layer || result.geojson.features.length !== result.returned_count) {
      throw new Error("Invalid S-101 hazard response");
    }
    hazards.clearLayers();
    hazards.addData(result.geojson);
    hazardToggle.checked = true;
    if (!map.hasLayer(hazards)) hazards.addTo(map);
    hazardStatus.textContent = `현재 범위 위험객체 ${result.total_count}건 중 ${result.returned_count}건 표시 · S-101 근거 제공${result.truncated ? " · 범위를 좁혀 더 보기" : ""}`;
  }

  // Agent → Map and result table → Map reuse the same verified GeoJSON. A
  // charted hazard never becomes a selected berth or a live vessel position.
  window.addEventListener("uport:hazard-query-result", event => {
    try { showHazards(event.detail); }
    catch (_error) { hazardStatus.textContent = "위험객체 결과 형식을 확인할 수 없습니다."; }
  });
  window.addEventListener("uport:focus-hazard", event => {
    const feature = event.detail?.feature;
    if (!feature || feature.type !== "Feature" || !feature.geometry || !feature.id) return;
    try {
      hazardFocus.clearLayers();
      hazardFocus.addData(feature);
      const bounds = hazardFocus.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.25), { maxZoom: 16 });
      hazardStatus.textContent = `${String(feature.properties?.feature_name || "S-101 위험객체")} · 피처 ${String(feature.id)} 강조`;
    } catch (_error) {
      hazardStatus.textContent = "위험객체 위치를 지도에 표시할 수 없습니다.";
    }
  });

  function focusVerifiedFeature(feature) {
    // The execution API returns source-attributed S-101 GeoJSON. Require the
    // same identity fields the map selection sends, and ignore malformed
    // events instead of treating an arbitrary UI string as map geometry.
    if (!feature || feature.type !== "Feature" || !feature.geometry ||
        !feature.id || !feature.properties?.dataset_id ||
        !feature.properties?.dataset_version_id) return;
    try {
      resultOverlay.clearLayers();
      resultOverlay.addData(feature);
      const bounds = resultOverlay.getBounds();
      if (bounds.isValid()) map.fitBounds(bounds.pad(0.25), { maxZoom: 16 });
      const context = {
        domain: "uport", entity_type: "s101_berth", feature_id: String(feature.id),
        dataset_id: String(feature.properties.dataset_id),
        dataset_version_id: String(feature.properties.dataset_version_id)
      };
      window.uportMapContext = context;
      window.dispatchEvent(new CustomEvent("uport:map-selection", { detail: context }));
      selection.textContent = `검증된 S-101 선석 피처 ${context.feature_id} 강조 · 데이터셋 ${context.dataset_id}`;
    } catch (_error) {
      selection.textContent = "결과 피처의 지도 형식을 확인할 수 없습니다.";
    }
  }

  // Agent → Map, Table → Map, Alert → Map share one verified feature event.
  // An alert with no source feature simply cannot create a map marker.
  window.addEventListener("uport:focus-feature", event => focusVerifiedFeature(event.detail?.feature));

  chart.on("tileload", () => {
    chartReady = true;
    status.textContent = "S-101 해도 연결됨";
  });
  chart.on("tileerror", () => {
    if (!chartReady) status.textContent = "S-101 해도 서버 연결 실패";
  });

  async function loadBerths() {
    if (!berthToggle.checked) return;
    if (activeRequest) activeRequest.abort();
    activeRequest = new AbortController();
    const bbox = window.uportGetMapBbox();
    try {
      const response = await fetch(`/api/v1/uport/map/berths?bbox=${encodeURIComponent(bbox)}`, {
        signal: activeRequest.signal
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      if (result.type !== "FeatureCollection" || !Array.isArray(result.features)) {
        throw new Error("Invalid GeoJSON response");
      }
      berths.clearLayers();
      berths.addData(result);
      const suffix = result.truncated ? " · 범위를 좁혀 더 보기" : "";
      selection.textContent = `현재 지도 범위: S-101 선석 피처 ${result.features.length}개${suffix}. 점유 상태는 제공되지 않습니다.`;
    } catch (error) {
      if (error.name === "AbortError") return;
      berths.clearLayers();
      selection.textContent = `S-101 선석 피처를 불러오지 못했습니다 (${error.message}).`;
    }
  }

  async function loadHazards() {
    if (!hazardToggle.checked) return;
    if (hazardRequest) hazardRequest.abort();
    hazardRequest = new AbortController();
    const thisRequest = hazardRequest;
    const bbox = window.uportGetMapBbox();
    hazardStatus.textContent = "현재 지도 범위의 S-101 위험객체 검색 중…";
    try {
      const response = await fetch("/api/v1/uport/s101/hazards/viewport", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ bbox }), signal: thisRequest.signal
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const result = await response.json();
      showHazards(result);
    } catch (error) {
      if (error.name === "AbortError") return;
      hazards.clearLayers();
      hazardStatus.textContent = `S-101 위험객체를 불러오지 못했습니다 (${error.message}).`;
    } finally {
      if (hazardRequest === thisRequest) hazardRequest = null;
    }
  }

  // Debounce viewport requests and cancel stale responses so rapid pans cannot
  // paint geometry from an earlier map extent over the current extent.
  map.on("moveend", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => { loadBerths(); loadHazards(); }, 250);
  });
  chartToggle.addEventListener("change", () => {
    if (chartToggle.checked) chart.addTo(map);
    else map.removeLayer(chart);
  });
  berthToggle.addEventListener("change", () => {
    if (berthToggle.checked) { berths.addTo(map); loadBerths(); }
    else {
      if (activeRequest) activeRequest.abort();
      map.removeLayer(berths);
      window.uportMapContext = null;
      window.dispatchEvent(new CustomEvent("uport:map-selection", { detail: null }));
      selection.textContent = "S-101 선석 레이어가 꺼져 있습니다.";
    }
  });
  hazardToggle.addEventListener("change", () => {
    if (hazardToggle.checked) loadHazards();
    else {
      if (hazardRequest) hazardRequest.abort();
      hazardRequest = null;
      map.removeLayer(hazards);
      hazards.clearLayers();
      hazardStatus.textContent = "항행 위험객체 레이어는 꺼져 있습니다.";
    }
  });
  map.whenReady(loadBerths);
})();
