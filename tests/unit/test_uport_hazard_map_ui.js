/* Exercise the viewport hazard layer's request and explicit failure state. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

async function setup(hazardResponse) {
  const elements = new Map();
  const calls = [];
  const layers = [];
  const element = id => {
    if (!elements.has(id)) elements.set(id, {
      checked: id !== "layer-hazards", textContent: "", handlers: {},
      addEventListener(name, fn) { this.handlers[name] = fn; },
    });
    return elements.get(id);
  };
  const map = {
    layers, setView() { return this; }, on() { return this; },
    whenReady(fn) { fn(); }, getBounds() {
      return { getWest: () => 129.25, getSouth: () => 35.35,
               getEast: () => 129.55, getNorth: () => 35.65 };
    },
    removeLayer(layer) { const index = layers.indexOf(layer); if (index >= 0) layers.splice(index, 1); },
    hasLayer(layer) { return layers.includes(layer); },
  };
  const layer = () => ({
    features: [], addTo() { layers.push(this); return this; }, on() { return this; },
    clearLayers() { this.features = []; }, addData(data) { this.features = data.features; },
    getBounds() { return { isValid: () => false }; },
  });
  const L = { map: () => map, tileLayer: Object.assign(layer, { wms: layer }),
    geoJSON: layer, circleMarker: layer };
  const fetch = async (url, options) => {
    calls.push({ url, options });
    if (url.includes("hazards")) return hazardResponse;
    return { ok: true, json: async () => ({ type: "FeatureCollection", features: [] }) };
  };
  const context = {
    L, fetch, document: { getElementById: element }, window: {
      dispatchEvent() {}, addEventListener() {},
    }, CustomEvent: class {}, AbortController, setTimeout, clearTimeout,
  };
  const source = fs.readFileSync(path.join(__dirname, "../../services/orchestrator/static/uport/map.js"), "utf8");
  vm.runInNewContext(source, context);
  await new Promise(resolve => setTimeout(resolve, 0));
  return { element, calls, layers };
}

test("hazard toggle requests the current bbox and labels source features", async () => {
  const ui = await setup({ ok: true, json: async () => ({ status: "success",
    total_count: 1, returned_count: 1, truncated: false,
    geojson: { type: "FeatureCollection", features: [{ type: "Feature", id: "101",
      geometry: { type: "Point", coordinates: [129.4, 35.5] },
      properties: { feature_name: "Wreck" } }] },
  }) });
  ui.element("layer-hazards").checked = true;
  ui.element("layer-hazards").handlers.change();
  await new Promise(resolve => setTimeout(resolve, 0));
  const request = ui.calls.find(call => call.url.includes("hazards"));
  assert.equal(JSON.parse(request.options.body).bbox, "129.250000,35.350000,129.550000,35.650000");
  assert.match(ui.element("hazard-status").textContent, /위험객체 1건/);
  ui.element("layer-hazards").checked = false;
  ui.element("layer-hazards").handlers.change();
  assert.match(ui.element("hazard-status").textContent, /꺼져/);
});

test("failed hazard request never reports an empty successful layer", async () => {
  const ui = await setup({ ok: false, status: 503 });
  ui.element("layer-hazards").checked = true;
  ui.element("layer-hazards").handlers.change();
  await new Promise(resolve => setTimeout(resolve, 0));
  assert.match(ui.element("hazard-status").textContent, /불러오지 못했습니다/);
});
