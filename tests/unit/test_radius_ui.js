const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class Element {
    constructor(tag) {
        this.tag = tag;
        this.children = [];
        this.dataset = {};
        this.textContent = "";
        this.listeners = {};
    }
    append(...nodes) { this.children.push(...nodes); }
    prepend(...nodes) { this.children.unshift(...nodes); }
    replaceChildren(...nodes) { this.children = nodes; }
    setAttribute(name, value) { this[name] = value; }
    addEventListener(name, listener) { this.listeners[name] = listener; }
    createTHead() { const node = new Element("thead"); this.append(node); return node; }
    createTBody() { const node = new Element("tbody"); this.append(node); return node; }
    insertRow() { const node = new Element("tr"); this.append(node); return node; }
    insertCell() { const node = new Element("td"); this.append(node); return node; }
}

const elements = new Map();
const drawnPoints = [];
const drawnSymbols = [];
const popups = [];
const map = { fitBounds() {}, panTo() {} };
const bounds = () => ({ isValid: () => true, extend() {} });
function layerStub(latlng) {
    return {
        listeners: {},
        getLatLng: () => latlng,
        openPopup() {},
        bindPopup(node) { popups.push(node); },
        on(name, listener) { this.listeners[name] = listener; },
    };
}
const namespace = {
    window: {},
    document: {
        createElement: tag => new Element(tag),
        getElementById: id => {
            if (!elements.has(id)) elements.set(id, new Element("div"));
            return elements.get(id);
        },
    },
    L: {
        latLngBounds: bounds,
        divIcon: options => options,
        marker: (latlng, options) => {
            drawnPoints.push(latlng);
            drawnSymbols.push(options.icon.html);
            return layerStub(latlng);
        },
        circleMarker: latlng => {
            drawnPoints.push(latlng);
            return layerStub(latlng);
        },
        geoJSON: (collection, options) => {
            const childLayers = [];
            for (const feature of collection.features) {
                const [lng, lat] = feature.geometry.coordinates;
                const layer = options.pointToLayer(feature, { lat, lng });
                options.onEachFeature(feature, layer);
                childLayers.push(layer);
            }
            return { childLayers, addTo() { return this; }, getBounds: bounds };
        },
    },
};
for (const filename of ["query-summary.js", "radius-results.js"]) {
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../../services/orchestrator/static", filename), "utf8"), namespace);
}
const ui = namespace.window.RadiusResults;
const rows = [11, 12].map(id => ({ feature_instance_id: String(id), dataset_id: "s101", result_id: "r1", evidence_id: `e${id}`, feature_name: "Wreck", distance_m: id, portrayal: { symbol: "WRECKS05", asset: "/static/s101-portrayal/WRECKS05.svg" }, portrayal_symbol: "WRECKS05", portrayal_symbol_asset: "/static/s101-portrayal/WRECKS05.svg" }));
const collection = { type: "FeatureCollection", features: rows.map(row => ({ type: "Feature", geometry: { type: "Point", coordinates: [129.075, 35.075] }, properties: row })) };
const result = {
    status: "COMPLETED", summary: "119 matches, 2 returned",
    structured_result: { analysis_type: "feature_search_by_radius", count: 119, total_count: 119, returned_count: 2, feature_ids: ["11", "12"], features: rows, geojson: collection, result_id: "r1", query_execution_id: "q1", distance_m: 3000 },
    map_layers: [{ role: "matched_features", inline_geojson: collection }],
    evidence_bundle: { spatial_feature_evidence: rows.map(row => ({ evidence_id: row.evidence_id, source_ref: "projection.s101", data: row })) },
};
const options = { map, activeLayers: [], originalQuery: "Original full radius query", submit() {} };
ui.render(result, options);
assert.equal(elements.get("dangerCount").textContent, "119건");
assert.equal(elements.get("returnedCount").textContent, "표시 2건 / 전체 119건");
assert.equal(elements.get("answerStatus").textContent, "조회 완료");
assert.deepEqual(drawnPoints.map(p => [p.lng, p.lat]), [[129.075, 35.075], [129.075, 35.075]]);
assert.equal(drawnSymbols.length, 2);
assert.ok(drawnSymbols.every(html => html.includes("/static/s101-portrayal/WRECKS05.svg")));
const table = elements.get("radiusDetails").children.find(node => node.tag === "table");
assert.deepEqual(table.children.find(node => node.tag === "tbody").children.map(node => node.dataset.featureId), ["11", "12"]);
assert.deepEqual(elements.get("answerEvidence").children.map(node => node.dataset.featureId), ["11", "12"]);
assert.deepEqual(popups.map(node => node.dataset.featureId), ["11", "12"]);
assert.equal(elements.get("querySummary").hidden, false);
assert.ok(elements.get("querySummaryTitle").textContent.includes("119건"));
const firstEvidence = elements.get("answerEvidence").children[0];
assert.equal(firstEvidence.children[0].textContent, "침선 · 기준점에서 11m");
const technical = firstEvidence.children.find(node => node.className === "evidence-technical");
assert.equal(technical.tag, "details");
assert.ok(!technical.open);
assert.ok(technical.children.some(node => node.textContent === "근거 ID: e11"));
assert.ok(!popups[0].children.find(node => node.className === "evidence-technical").open);
options.activeLayers[0].childLayers[1].listeners.click();
assert.ok(table.children.find(node => node.tag === "tbody").children[1].className.includes("radius-selected"));
assert.ok(elements.get("answerEvidence").children[1].className.includes("radius-selected"));

let pageSubmission;
Object.assign(result.structured_result, { result_limit: 2, offset: 2, reference_geometry: "POINT(129.075 35.075)", crs: "EPSG:4326", target_features: ["Wreck"], exclusions: ["Obstruction"], place_id: "dataset-a:place-1", place_version: "version-1", location_resolution: { source_ref: "dataset-a" } });
ui.render(result, { ...options, submit: value => { pageSubmission = value; } });
const pagination = elements.get("radiusDetails").children.find(node => node.tag === "nav");
pagination.children[2].listeners.click();
assert.equal(pageSubmission.fresh, true);
assert.equal(pageSubmission.spatialContext.offset, 4);
assert.equal(pageSubmission.spatialContext.result_limit, 2);
assert.equal(pageSubmission.spatialContext.geometry, "POINT(129.075 35.075)");
assert.deepEqual(Array.from(pageSubmission.spatialContext.target_features), ["Wreck"]);
assert.deepEqual(Array.from(pageSubmission.spatialContext.exclusions), ["Obstruction"]);
assert.equal(pageSubmission.spatialContext.place_id, "dataset-a:place-1");
assert.equal(pageSubmission.spatialContext.place_version, "version-1");
assert.equal(pageSubmission.spatialContext.location_resolution.source_ref, "dataset-a");

result.evidence_bundle.spatial_feature_evidence.pop();
ui.render(result, options);
assert.equal(elements.get("answerStatus").textContent, "결과 확인 필요");
assert.equal(elements.get("querySummaryTitle").textContent, "결과 확인 필요");
assert.equal(elements.get("querySummaryFacts").children.length, 0);

let submission;
ui.render({
    status: "NEEDS_CLARIFICATION", clarification_questions: ["Confirm entrance"],
    structured_result: {
        analysis_type: "feature_search_by_radius", distance_m: 3000, original_query: "Wreck within 3km of user's entrance",
        spatial_context: { target_features: ["Wreck"], exclusions: ["Obstruction"], result_limit: 17, offset: 0, base_location: "Old entrance", geometry: "POINT(1 2)", crs: "EPSG:5179", buffer_distance: 1500, place_id: "old-place", place_version: "old-version", location_resolution: { source_ref: "old-source" } },
        location_candidates: [{ place_id: "p1", place_version: "version-p1", label: "User's entrance", base_location: "Confirmed entrance", geometry: "POINT(129.075 35.075)", crs: "EPSG:4326", status: "test", source_ref: "fixture", source_records: [{ source_ref: "gazetteer.dataset_a", source_revision: "2026-09" }], requires_confirmation: true }],
    },
}, { ...options, submit: value => { submission = value; } });
const candidate = elements.get("radiusDetails").children.find(node => node.className === "location-candidate");
assert.equal(candidate.dataset.placeId, "p1");
assert.equal(candidate.dataset.placeVersion, "version-p1");
assert.ok(candidate.children.find(node => node.tag === "details").children.some(node => String(node.textContent).includes("gazetteer.dataset_a")));
candidate.children.find(node => node.tag === "button").listeners.click();
assert.equal(submission.fresh, true);
assert.equal(submission.query, "Wreck within 3km of user's entrance");
assert.equal(submission.spatialContext.geometry, "POINT(129.075 35.075)");
assert.equal(submission.spatialContext.crs, "EPSG:4326");
assert.equal(submission.spatialContext.buffer_distance, 3000);
assert.equal(submission.spatialContext.base_location, "Confirmed entrance");
assert.deepEqual(Array.from(submission.spatialContext.target_features), ["Wreck"]);
assert.deepEqual(Array.from(submission.spatialContext.exclusions), ["Obstruction"]);
assert.equal(submission.spatialContext.result_limit, 17);
assert.equal(submission.spatialContext.offset, 0);
assert.equal(submission.spatialContext.place_id, "p1");
assert.equal(submission.spatialContext.place_version, "version-p1");
assert.equal("location_resolution" in submission.spatialContext, false);
assert.equal(submission.task_id, undefined);
assert.equal(elements.get("dangerCount").textContent, "-");
assert.equal(elements.get("radiusDetails").dataset.resultId, undefined);

let pointSubmission;
ui.render({
    status: "NEEDS_CLARIFICATION",
    structured_result: {
        analysis_type: "feature_search_by_radius", original_query: "Find hazards near unknown entrance", location_text: "Unknown entrance",
        spatial_context: { target_features: ["Wreck"], exclusions: ["Obstruction"], result_limit: 17, place_id: "old-place", place_version: "old-version", location_resolution: { source_ref: "old-source" } }, location_candidates: [],
    },
}, { ...options, submit: value => { pointSubmission = value; } });
const pointForm = elements.get("radiusDetails").children.find(node => node.tag === "form");
assert.equal(elements.get("radiusDetails").children.filter(node => node.tag === "form").length, 1);
const pointInputs = Object.fromEntries(pointForm.children.find(node => node.className === "radius-point-fields").children.map(label => [label.children[0].name, label.children[0]]));
assert.equal(pointInputs.longitude.value, "");
assert.equal(pointInputs.latitude.value, "");
assert.equal(pointInputs.radius.value, "");
pointForm.listeners.submit({ preventDefault() {} });
assert.equal(pointSubmission, undefined);
for (const invalid of [["181", "35", "3000"], ["129", "91", "3000"], ["129", "35", "0"], ["129", "35", "50001"], ["Infinity", "35", "3000"], ["", "35", "3000"]]) {
    [pointInputs.longitude.value, pointInputs.latitude.value, pointInputs.radius.value] = invalid;
    pointForm.listeners.submit({ preventDefault() {} });
    assert.equal(pointSubmission, undefined);
}
pointInputs.longitude.value = "129.075";
pointInputs.latitude.value = "35.075";
pointInputs.radius.value = "3000";
pointForm.listeners.submit({ preventDefault() {} });
assert.equal(pointSubmission.fresh, true);
assert.equal(pointSubmission.query, "Find hazards near unknown entrance");
assert.equal(pointSubmission.spatialContext.geometry, "POINT(129.075 35.075)");
assert.equal(pointSubmission.spatialContext.crs, "EPSG:4326");
assert.equal(pointSubmission.spatialContext.buffer_distance, 3000);
assert.equal(pointSubmission.spatialContext.result_limit, 17);
assert.deepEqual(Array.from(pointSubmission.spatialContext.target_features), ["Wreck"]);
assert.deepEqual(Array.from(pointSubmission.spatialContext.exclusions), ["Obstruction"]);
assert.equal("place_id" in pointSubmission.spatialContext, false);
assert.equal("place_version" in pointSubmission.spatialContext, false);
assert.equal("location_resolution" in pointSubmission.spatialContext, false);

ui.render({ status: "FAILED", structured_result: { analysis_type: "feature_search_by_radius", blockers: ["Query failed"] } }, options);
assert.equal(elements.get("answerStatus").textContent, "조회 실패");
assert.equal(elements.get("dangerCount").textContent, "-");
assert.equal(elements.get("radiusDetails").children.some(node => node.tag === "table"), false);
assert.equal(elements.get("querySummaryTitle").textContent, "조회 실패");

for (const analysisType of ["place_lookup", "nearest_feature"]) {
    let selectedSubmission;
    let manualSubmission;
    const generic = {
        status: "NEEDS_CLARIFICATION", summary: "Select a reference location",
        structured_result: {
            analysis_type: analysisType, original_query: "Original nearest query",
            spatial_context: { k: 4, target_features: ["Wreck"], exclusions: ["Obstruction"], place_id: "old-place", place_version: "old-version", location_resolution: { source_ref: "old-source" } },
            location_candidates: [{ place_id: "island:7", place_version: "current-version", label: "Island A", geometry: "POINT(129 35)", crs: "EPSG:4326", source_ref: "fixture", requires_confirmation: true }],
        },
    };
    assert.equal(ui.isRadius(generic), true);
    assert.equal(ui.isRadius({ ...generic, status: "COMPLETED" }), analysisType === "place_lookup");
    assert.equal(ui.isRadius({ ...generic, structured_result: { ...generic.structured_result, analysis_type: "unrelated_analysis" } }), false);
    ui.render(generic, { ...options, submit: value => { selectedSubmission = value; } });
    const genericDetails = elements.get("radiusDetails");
    assert.equal(genericDetails.children.some(node => node.className === "radius-surface"), false);
    genericDetails.children.find(node => node.className === "location-candidate").children.find(node => node.tag === "button").listeners.click();
    assert.equal(selectedSubmission.query, "Original nearest query");
    assert.equal(selectedSubmission.fresh, true);
    assert.equal(selectedSubmission.spatialContext.place_id, "island:7");
    assert.equal(selectedSubmission.spatialContext.place_version, "current-version");
    assert.equal(selectedSubmission.spatialContext.k, 4);
    assert.equal("buffer_distance" in selectedSubmission.spatialContext, false);

    generic.structured_result.location_candidates = [];
    ui.render(generic, { ...options, submit: value => { manualSubmission = value; } });
    const genericForm = genericDetails.children.find(node => node.tag === "form");
    const genericInputs = Object.fromEntries(genericForm.children.find(node => node.className === "radius-point-fields").children.map(label => [label.children[0].name, label.children[0]]));
    assert.equal(Object.keys(genericInputs).length, 2);
    assert.equal(genericInputs.radius, undefined);
    genericForm.listeners.submit({ preventDefault() {} });
    assert.equal(manualSubmission, undefined);
    genericInputs.longitude.value = "129";
    genericInputs.latitude.value = "35";
    genericForm.listeners.submit({ preventDefault() {} });
    assert.equal(manualSubmission.spatialContext.geometry, "POINT(129 35)");
    assert.equal(manualSubmission.spatialContext.crs, "EPSG:4326");
    assert.equal(manualSubmission.spatialContext.k, 4);
    assert.equal("buffer_distance" in manualSubmission.spatialContext, false);
    for (const key of ["place_id", "place_version", "location_resolution"]) assert.equal(key in manualSubmission.spatialContext, false);
}

const placeCoordinates = [128.0123456789, 34.987654321];
const placeFeature = {
    type: "Feature", id: "island:7", geometry: { type: "Point", coordinates: placeCoordinates },
    properties: { place_id: "island:7", place_version: "current-version", name: "Source Island", evidence_id: "place:island:7:current-version" },
};
const placeCollection = { type: "FeatureCollection", features: [placeFeature] };
const placeResult = {
    status: "COMPLETED", summary: "Source Island coordinates confirmed", answer_text: "Source Island: exact source coordinates",
    structured_result: {
        analysis_type: "place_lookup", location_text: "Source Island", original_query: "Where is Source Island?",
        place_id: "island:7", place_version: "current-version", count: 1, returned_count: 1, geojson: placeCollection,
        location_resolution: { source_ref: "serving.island_gazetteer_current", source_records: [{ source_id: "7", revision: "2026-09" }] },
    },
    map_layers: [{ inline_geojson: placeCollection }],
};
const pointsBeforePlace = drawnPoints.length;
const symbolsBeforePlace = drawnSymbols.length;
namespace.Math = Object.create(Math);
namespace.Math.random = () => { throw new Error("Place coordinates must not be jittered"); };
ui.render(placeResult, options);
assert.equal(ui.isRadius(placeResult), true);
assert.equal(drawnPoints.length, pointsBeforePlace + 1);
assert.deepEqual([drawnPoints.at(-1).lng, drawnPoints.at(-1).lat], placeCoordinates);
assert.equal(drawnSymbols.length, symbolsBeforePlace);
assert.equal(elements.get("answerStatus").textContent, "위치 확인 완료");
assert.equal(elements.get("querySummaryTitle").textContent, "위치 확인 완료");
assert.equal(elements.get("intentResult").textContent, "지명 조회");
assert.equal(elements.get("dangerCount").textContent, "-");
assert.equal(elements.get("accuracyScore").textContent, "-");
assert.equal(elements.get("similarityScore").textContent, "-");
assert.equal(elements.get("returnedCount").textContent, "확인된 위치 1곳");
assert.equal(elements.get("radiusDetails").dataset.placeId, "island:7");
assert.equal(popups.at(-1).dataset.placeId, "island:7");
const textTree = node => [node.textContent, ...node.children.map(textTree)].join(" ");
const placeEvidence = elements.get("answerEvidence").children[0];
assert.equal(placeEvidence.dataset.placeId, "island:7");
assert.equal(placeEvidence.dataset.evidenceId, "place:island:7:current-version");
assert.ok(textTree(placeEvidence).includes("serving.island_gazetteer_current"));
assert.ok(textTree(placeEvidence).includes("current-version"));
assert.ok(textTree(placeEvidence).includes("2026-09"));
assert.ok(!textTree(popups.at(-1)).includes("Berth"));
assert.ok(!textTree(popups.at(-1)).includes("S-101"));
assert.equal(elements.get("radiusDetails").children.some(node => node.tag === "table" || node.tag === "form"), false);

for (const analysisType of ["place_lookup", "nearest_feature"]) {
    const blocked = { status: "BLOCKED", summary: "Place source is unavailable", structured_result: { analysis_type: analysisType, location_candidates: [] } };
    assert.equal(ui.isRadius(blocked), true);
    const pointsBeforeBlocked = drawnPoints.length;
    ui.render(blocked, options);
    assert.equal(elements.get("answerStatus").textContent, "조회 차단");
    assert.equal(elements.get("querySummaryTitle").textContent, "조회 차단");
    assert.equal(drawnPoints.length, pointsBeforeBlocked);
    assert.equal(elements.get("dangerCount").textContent, "-");
    assert.equal(elements.get("radiusDetails").dataset.placeId, undefined);
    assert.equal(elements.get("radiusDetails").children.some(node => node.tag === "table" || node.tag === "form"), false);
}

const invalidPlace = { ...placeResult, structured_result: { ...placeResult.structured_result, geojson: { type: "FeatureCollection", features: [] } } };
ui.render(invalidPlace, options);
assert.equal(elements.get("answerStatus").textContent, "결과 확인 필요");
assert.equal(elements.get("querySummaryTitle").textContent, "결과 확인 필요");
ui.reset();
assert.equal(elements.get("querySummary").hidden, true);
console.log("Radius UI fixture checks passed: radius identity/counts, candidates, manual validation, pagination, exact place coordinates/provenance, generic clarification and blocked states.");
