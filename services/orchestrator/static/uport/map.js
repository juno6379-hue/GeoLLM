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
        domain: "uport", entityType: "s101_berth", featureId: id,
        datasetId: dataset,
        datasetVersionId: String(feature.properties?.dataset_version_id ?? "unknown")
      };
      window.uportMapContext = context;
      window.dispatchEvent(new CustomEvent("uport:map-selection", { detail: context }));
      selection.textContent = `선택한 S-101 선석 피처 ${id} · 데이터셋 ${dataset} · 점유 상태 정보 없음`;
    })
  }).addTo(map);

  let activeRequest = null;
  let debounceTimer = null;
  let chartReady = false;

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
    const bounds = map.getBounds();
    const bbox = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()]
      .map(value => value.toFixed(6)).join(",");
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

  // Debounce viewport requests and cancel stale responses so rapid pans cannot
  // paint geometry from an earlier map extent over the current extent.
  map.on("moveend", () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(loadBerths, 250);
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
      selection.textContent = "S-101 선석 레이어가 꺼져 있습니다.";
    }
  });
  map.whenReady(loadBerths);
})();
