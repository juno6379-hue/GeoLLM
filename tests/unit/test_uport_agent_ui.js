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

function setup(reply) {
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
  const body = JSON.parse(ui.calls[0].options.body);
  assert.equal(body.map_selection.feature_id, 7);
  assert.equal(ui.get("agent-feature-list").children.length, 1);
  assert.ok(ui.dispatched.some(event => event.type === "uport:focus-feature"));
  ui.get("agent-feature-list").children[0].click();
  assert.equal(ui.dispatched.filter(event => event.type === "uport:focus-feature").length, 2);
});

test("no selection, blocked result and wrong dataset cannot create a map focus", async () => {
  const ui = setup({ status: "success", narrative: "ok", features: [{ ...feature,
    properties: { dataset_id: "99", dataset_version_id: "3" } }] });
  ui.get("agent-query").value = "보여줘";
  await ui.get("agent-form").handlers.submit({ preventDefault() {} });
  assert.equal(ui.calls.length, 0);
  ui.window.dispatchEvent({ type: "uport:map-selection", detail: selected });
  await ui.get("agent-form").handlers.submit({ preventDefault() {} });
  assert.equal(ui.get("agent-feature-list").children.length, 0);
  assert.ok(!ui.dispatched.some(event => event.type === "uport:focus-feature"));
});
