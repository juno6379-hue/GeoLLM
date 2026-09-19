/* Check that reference metadata cannot be displayed as live occupancy. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

async function render(response) {
  const label = { textContent: "" };
  const document = { getElementById: () => label };
  const fetch = async () => response;
  const source = fs.readFileSync(path.join(__dirname, "../../services/orchestrator/static/uport/reference.js"), "utf8");
  vm.runInNewContext(source, { document, fetch });
  // Promise handlers in the UI script complete after two microtask turns.
  await new Promise(resolve => setTimeout(resolve, 0));
  return label.textContent;
}

test("configured reference shows quality flags and no occupancy claim", async () => {
  const text = await render({ ok: true, json: async () => ({
    row_count: 144, warning_counts: { TONNAGE_RANGE_REVERSED: 8, CAPACITY_ZERO: 13 },
    operational_status_available: false,
  }) });
  assert.match(text, /144건/);
  assert.match(text, /실시간 점유 정보 없음/);
  assert.doesNotMatch(text, /가용 선석/);
});

test("missing source remains an explicit empty state", async () => {
  const text = await render({ ok: false, status: 503 });
  assert.match(text, /CSV 미설정/);
});
