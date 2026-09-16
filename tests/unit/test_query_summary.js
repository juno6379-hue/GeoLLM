const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const { test } = require("node:test");

class Element {
    constructor(tag) { this.tag = tag; this.textContent = ""; this.dataset = {}; this.children = []; }
    append(...children) { this.children.push(...children); }
    replaceChildren(...children) { this.children = children; }
}

function setup() {
    const elements = new Map();
    const document = {
        getElementById(id) {
            if (!elements.has(id)) elements.set(id, new Element("div"));
            return elements.get(id);
        },
        createElement: tag => new Element(tag),
    };
    const context = { document, window: {} };
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../../services/orchestrator/static/query-summary.js"), "utf8"), context);
    return { summary: context.window.QuerySummary, get: id => document.getElementById(id), facts: () => document.getElementById("querySummaryFacts").children.map(item => item.textContent) };
}

function result(overrides = {}) {
    return { status: "COMPLETED", structured_result: {
        original_query: "부산항 입구 3km 이내 위험객체를 찾아줘", location_text: "부산항 입구", distance_m: 3000,
        total_count: 119, returned_count: 30, offset: 0, result_id: "fixture-result",
        total_counts_by_type: { Obstruction: 103, UnderwaterAwashRock: 14, Wreck: 2 },
        returned_counts_by_type: { Obstruction: 30 },
        target_features: ["Obstruction", "UnderwaterAwashRock", "Wreck"], ...overrides,
    } };
}

test("human summary uses whole-result totals and labels, not page type counts", () => {
    const ui = setup();
    ui.summary.renderRadius(result(), "fallback query");
    assert.equal(ui.get("querySummaryTitle").textContent, "부산항 입구 기준 3km 이내 주의 대상 객체 119건을 찾았습니다.");
    assert.ok(ui.facts().includes("장애물 103건 · 수중암·간출암 14건 · 침선 2건"));
    assert.ok(ui.facts().includes("전체 119건 중 1~30번째 30건 · 지도·목록·근거 공통"));
    assert.equal(ui.get("querySummary").dataset.resultId, "fixture-result");
    assert.equal(ui.get("querySummaryQuery").textContent, result().structured_result.original_query);
});

test("pagination updates the shown range without changing the total", () => {
    const ui = setup();
    ui.summary.renderRadius(result({ offset: 30 }), "query");
    assert.ok(ui.facts().some(value => value.includes("31~60번째 30건")));
    assert.ok(ui.get("querySummaryTitle").textContent.includes("119건"));
    ui.summary.renderRadius(result({ offset: 90, returned_count: 29 }), "query");
    assert.ok(ui.facts().some(value => value.includes("91~119번째 29건")));
});

test("explicit target and exclusion are preserved in ordinary language", () => {
    const ui = setup();
    ui.summary.renderRadius(result({ total_count: 2, returned_count: 2, total_counts_by_type: { Wreck: 2 }, target_features: ["Wreck"], exclusions: ["Obstruction"] }), "query");
    assert.ok(ui.get("querySummaryTitle").textContent.includes("침선 2건"));
    assert.deepEqual(ui.facts().slice(-4), ["검색 대상", "침선", "제외 조건", "장애물"]);
});

test("missing or inconsistent whole-result type totals are not inferred from the page", () => {
    const ui = setup();
    for (const total_counts_by_type of [undefined, { Wreck: 2 }]) {
        ui.summary.renderRadius(result({ total_counts_by_type }), "query");
        assert.ok(!ui.facts().includes("전체 구성"));
    }
});

test("empty success says no matching objects without asserting the area is safe", () => {
    const ui = setup();
    ui.summary.renderRadius(result({ total_count: 0, returned_count: 0, total_counts_by_type: {} }), "query");
    assert.ok(ui.get("querySummaryTitle").textContent.includes("객체를 찾지 못했습니다"));
    assert.ok(!ui.get("querySummaryTitle").textContent.includes("안전"));
});

test("clarification and failure clear old counts and result identity", () => {
    const ui = setup();
    for (const [status, expected] of [["NEEDS_CLARIFICATION", "입력 확인 필요"], ["FAILED", "조회 실패"], ["BLOCKED", "조회 차단"]]) {
        ui.summary.renderRadius(result(), "old query");
        ui.summary.renderRadius({ status, summary: "기준 위치를 확인해 주세요.", structured_result: { total_count: 119 } }, "new query");
        assert.equal(ui.get("querySummaryTitle").textContent, expected);
        assert.equal(ui.get("querySummaryQuery").textContent, "new query");
        assert.equal(ui.get("querySummary").dataset.resultId, undefined);
        assert.equal(ui.facts().length, 0);
    }
});

test("unverified counts never become an empty successful result", () => {
    const ui = setup();
    for (const total_count of [null, undefined, -1, NaN]) {
        ui.summary.renderRadius(result({ total_count }), "query");
        assert.equal(ui.get("querySummaryTitle").textContent, "결과 확인 필요");
        assert.equal(ui.facts().length, 0);
    }
});

test("generic result and loading updates preserve the active query, reset removes it", () => {
    const ui = setup();
    ui.summary.renderRadius(result(), "old query");
    ui.summary.show("분석 중", "새 결과 확인 중", "new query");
    assert.equal(ui.facts().length, 0);
    ui.summary.show("분석 완료", "문서에서 찾은 답변입니다.");
    assert.equal(ui.get("querySummaryQuery").textContent, "new query");
    ui.summary.reset();
    assert.equal(ui.get("querySummary").hidden, true);
    assert.equal(ui.get("querySummaryQuery").textContent, "");
});

test("query and place labels are text, not injected HTML", () => {
    const ui = setup();
    const label = '<img src=x onerror="alert(1)">';
    ui.summary.renderRadius(result({ original_query: label, location_text: label }), "query");
    assert.equal(ui.get("querySummaryQuery").textContent, label);
    assert.equal(ui.get("querySummaryQuery").innerHTML, undefined);
    assert.equal(ui.get("querySummaryTitle").innerHTML, undefined);
});

test("summary precedes query/map panels and loads before dependent renderer", () => {
    const html = fs.readFileSync(path.join(__dirname, "../../services/orchestrator/static/index.html"), "utf8");
    assert.ok(html.indexOf('id="querySummary"') < html.indexOf('<div class="top-row">'));
    assert.ok(html.indexOf('/query-summary.js') < html.indexOf('/radius-results.js'));
    for (const id of ["querySummary", "querySummaryQuery", "querySummaryStatus", "querySummaryTitle", "querySummaryBody", "querySummaryFacts"]) {
        assert.equal(html.split(`id="${id}"`).length - 1, 1);
    }
});
