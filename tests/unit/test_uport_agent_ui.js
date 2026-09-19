/* Verify Map → Agent → Map and Table → Map without a browser or live DB. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

class Element {
  constructor() { this.textContent = ""; this.value = ""; this.children = []; this.handlers = {}; this.disabled = false; }
  addEventListener(name, handler) { this.handlers[name] = handler; }
  replaceChildren(...children) { this.children = children; }
  appendChild(child) { this.children.push(child); }
  click() { this.handlers.click(); }
}

function setup(reply, routeMode = "s101_berth") {
  const elements = new Map();
  const events = {};
  const dispatched = [];
  const calls = [];
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, new Element());
      return elements.get(id);
    },
    createElement: () => new Element(),
  };
  const window = {
    addEventListener: (name, handler) => { events[name] = handler; },
    dispatchEvent: event => { dispatched.push(event); events[event.type]?.(event); },
  };
  class CustomEvent { constructor(type, options) { this.type = type; this.detail = options.detail; } }
  const fetch = async (url, options) => {
    calls.push({ url, options });
    if (url.endsWith("/query/route")) {
      return { ok: true, json: async () => ({ mode: routeMode }) };
    }
    return { ok: true, json: async () => reply };
  };
  const source = fs.readFileSync(path.join(__dirname, "../../services/orchestrator/static/uport/agent.js"), "utf8");
  vm.runInNewContext(source, { document, window, CustomEvent, fetch, AbortController });
  return { get: id => document.getElementById(id), window, dispatched, calls };
}

const selected = { entity_type: "s101_berth", feature_id: "7", dataset_id: "2", dataset_version_id: "3" };
const feature = {
  type: "Feature", id: "7", geometry: { type: "Point", coordinates: [129.4, 35.5] },
  properties: { dataset_id: "2", dataset_version_id: "3" },
};

test("map selection enters execution request and verified result focuses map", async () => {
  const ui = setup({ status: "success", narrative: "검증된 선석", features: [feature], evidence: [{}] });
  ui.window.dispatchEvent({ type: "uport:map-selection", detail: selected });
  ui.get("agent-query").value = "이 선석 보여줘";
  await ui.get("agent-form").handlers.submit({ preventDefault() {} });
  const body = JSON.parse(ui.calls[1].options.body);
  assert.equal(body.map_selection.feature_id, 7);
  assert.equal(ui.get("agent-feature-list").children.length, 1);
  assert.ok(ui.dispatched.some(event => event.type === "uport:focus-feature"));
  ui.get("agent-feature-list").children[0].click();
  assert.equal(ui.dispatched.filter(event => event.type === "uport:focus-feature").length, 2);
});

test("no selection, blocked result and wrong dataset cannot create a map focus", async () => {
  const ui = setup({ status: "success", narrative: "ok", features: [{ ...feature,
    properties: { dataset_id: "99", dataset_version_id: "3" } }] });
  ui.get("agent-query").value = "선석을 보여줘";
  await ui.get("agent-form").handlers.submit({ preventDefault() {} });
  assert.equal(ui.calls.length, 1);
  ui.window.dispatchEvent({ type: "uport:map-selection", detail: selected });
  await ui.get("agent-form").handlers.submit({ preventDefault() {} });
  assert.equal(ui.get("agent-feature-list").children.length, 0);
  assert.ok(!ui.dispatched.some(event => event.type === "uport:focus-feature"));
});

test("natural-language viewport hazards use the current map bounds and source evidence", async () => {
  const hazard = { type: "Feature", id: "101",
    geometry: { type: "Point", coordinates: [129.4, 35.5] },
    properties: { feature_name: "Wreck", dataset_id: "12", dataset_version_id: "34" } };
  const ui = setup({ status: "success", narrative: "위험객체 1건",
    returned_count: 1, geojson: { type: "FeatureCollection", features: [hazard] },
    source_layer: { physical_table: "projection.s101_feature_valid" },
    evidence_bundle: { spatial_feature_evidence: [{ evidence_id: "source-101" }] },
  }, "s101_hazard_viewport");
  ui.window.uportGetMapBbox = () => "129.25,35.35,129.55,35.65";
  ui.get("agent-query").value = "지도 범위 위험객체를 보여줘";
  await ui.get("agent-form").handlers.submit({ preventDefault() {} });
  assert.equal(ui.calls[1].url, "/api/v1/uport/s101/hazards/query");
  assert.equal(JSON.parse(ui.calls[1].options.body).bbox, "129.25,35.35,129.55,35.65");
  assert.equal(ui.get("agent-feature-list").children.length, 1);
  assert.ok(ui.dispatched.some(event => event.type === "uport:hazard-query-result"));
  ui.get("agent-feature-list").children[0].click();
  assert.ok(ui.dispatched.some(event => event.type === "uport:focus-hazard"));
});

test("hazard result without matching feature evidence cannot reach the map", async () => {
  const ui = setup({ status: "success", returned_count: 1,
    geojson: { type: "FeatureCollection", features: [{ type: "Feature", id: "101",
      geometry: { type: "Point", coordinates: [129.4, 35.5] }, properties: {} }] },
    evidence_bundle: { spatial_feature_evidence: [] },
  }, "s101_hazard_viewport");
  ui.window.uportGetMapBbox = () => "129.25,35.35,129.55,35.65";
  ui.get("agent-query").value = "지도 범위 위험객체를 보여줘";
  await ui.get("agent-form").handlers.submit({ preventDefault() {} });
  assert.equal(ui.get("agent-feature-list").children.length, 0);
  assert.ok(!ui.dispatched.some(event => event.type === "uport:hazard-query-result"));
});
