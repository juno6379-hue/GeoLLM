const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');

test('Dataset task completion never becomes whole Dataset semantic approval', () => {
  const ui = browser();
  ui.evaluate('DATA={dataset_audit:{stages:[{stage:"source",status:"COMPLETED",counts:{chunks_scanned:12},limitations:["의미 미검증"]}]}}');
  const html = ui.evaluate('datasetAuditPanel()');
  assert.match(html, /해당 검사 작업 완료/);
  assert.match(html, /전체 의미 검증은 아직 완료되지/);
  assert.match(html, /임베딩 생성 완료/);
  assert.match(html, /홀드아웃은 사용하지/);
});

test('operational verification remains separate and unknown counts are not zero', () => {
  const ui = browser();
  ui.evaluate('DATA={operational:{status:"DEVELOPMENT_VERIFIED",passed_cases:8,total_cases:8,corpus_row_count:1146,observations:[{case:"s101_busan_unverified",status:"BLOCKED",count:null}],limitations:["Dataset 전체 지명·위치·좌표 전수 검증: 미완료"]},sources:[]}');
  const html = ui.evaluate('operationalPanel()');
  assert.match(html, /기존 v6 ESR·FalseBlock/);
  assert.match(html, /정상 가능 요청/);
  assert.match(html, /미확정 · 0건 아님/);
  assert.match(html, /coverage UNKNOWN/);
  assert.match(html, /전수 검증: 미완료/);
});

// Load the real renderer in an isolated browser shell. No HTTP or operational APIs.
function browser(fetchImpl = async () => ({ ok: false, status: 503 })) {
  const nodes = new Map();
  function node(selector) {
    if (!nodes.has(selector)) nodes.set(selector, {
      innerHTML: '', textContent: '', disabled: false, value: '',
      addEventListener() {}, showModal() {}, close() {},
    });
    return nodes.get(selector);
  }
  const context = vm.createContext({
    console, Intl, Date,
    document: { querySelector: node, querySelectorAll: () => [], addEventListener() {} },
    fetch: fetchImpl,
    IntersectionObserver: class { observe() {} },
  });
  vm.runInContext(source, context);
  return { context, node, evaluate: code => vm.runInContext(code, context) };
}

test('missing rate remains unmeasured and retains its measured denominator', () => {
  const html = browser().evaluate('rate({value:null,denominator:5,measured:2,missing:3})');
  assert.match(html, /미측정/);
  assert.match(html, /2\/5/);
  assert.doesNotMatch(html, /0%/);
});

test('an actually measured zero remains zero rather than unavailable', () => {
  const html = browser().evaluate('rate({value:0,denominator:8,measured:8,missing:0})');
  assert.match(html, /0%/);
  assert.match(html, /분모 8/);
  assert.doesNotMatch(html, /미측정/);
});

test('conditional correctness is unavailable for missing or zero-denominator source', () => {
  const ui = browser();
  assert.equal(ui.evaluate('conditionalCorrectness({silent_spatial_failure_given_success:{value:null,denominator:3}})'), null);
  assert.equal(ui.evaluate('conditionalCorrectness({silent_spatial_failure_given_success:{value:0,denominator:0}})'), null);
});

test('conditional correctness preserves the original success denominator and missing count', () => {
  const metric = browser().evaluate('conditionalCorrectness({silent_spatial_failure_given_success:{value:0,denominator:3,measured:3,missing:0}})');
  assert.equal(metric.value, 1);
  assert.equal(metric.denominator, 3);
  assert.equal(metric.measured, 3);
  assert.equal(metric.missing, 0);
});

test('artifact content cannot inject an HTML element or event attribute', () => {
  const escaped = browser().evaluate('esc("<img src=x onerror=alert(1)> & \\"quoted\\"")');
  assert.doesNotMatch(escaped, /<img/);
  assert.match(escaped, /&lt;img/);
  assert.match(escaped, /&amp;/);
  assert.match(escaped, /&quot;/);
});

test('a stopped run is explicitly shown as stopped, never observation complete', () => {
  const html = browser().evaluate('badge("STOPPED_REQUIRES_REVIEW")');
  assert.match(html, /중단/);
  assert.doesNotMatch(html, /관측 완료/);
});

test('failed data loading discloses failure without inventing zero measurements', async () => {
  const ui = browser();
  await new Promise(resolve => setImmediate(resolve));
  assert.match(ui.node('#notice').textContent, /HTTP 503/);
  assert.match(ui.node('#notice').textContent, /0으로 대체하지 않습니다/);
  assert.match(ui.node('#overview-cards').innerHTML, /자료 없음/);
  assert.doesNotMatch(ui.node('#overview-cards').innerHTML, /0%/);
});

test('initial load and refresh only GET the isolated research endpoint', async () => {
  const calls = [];
  const ui = browser(async (url, options) => {
    calls.push({ url, options });
    return { ok: false, status: 503 };
  });
  await new Promise(resolve => setImmediate(resolve));
  await ui.evaluate('load()');
  assert.equal(calls.length, 2);
  for (const { url, options } of calls) {
    assert.equal(url, '/research/scie-results/api/dashboard');
    assert.equal(options.method, 'GET');
    assert.equal(options.cache, 'no-store');
  }
});

test('prepared holdout is shown as awaiting final freeze rather than completed evaluation', () => {
  const ui=browser();
  ui.evaluate('DATA={holdout:{status:"PREPARED_PENDING_FINAL_SYSTEM_FREEZE",main_cases:18,rq2_fault_cases:12,rq4_recovery_cases:8,evaluation_executed:false,system_freeze_complete:false},sources:[]}');
  const html=ui.evaluate('holdoutPanel()');
  assert.match(html,/준비 완료 · 최종 동결 대기/);
  assert.match(html,/평가 미실행/);
  assert.match(html,/RQ2/);
  assert.match(html,/RQ4/);
  assert.match(html,/질문·정답·오류 계획을 공개하지/);
});

test('human scoring missing labels remains unmeasured even if GOLD was approved', () => {
  const ui=browser();
  ui.evaluate('DATA={semantic_review:{status:"AWAITING_HUMAN_ANSWER_LABELS",total_answers:144,reviewer_A_completed:0,reviewer_B_completed:0,paired_completed:0,consensus_completed:0,gold_review_complete:true,human_answer_scoring_complete:false,semantic_human_accuracy:1},sources:[]}');
  const html=ui.evaluate('humanReviewPanel()');
  assert.match(html,/0 \/ 144/);
  assert.match(html,/미측정/);
  assert.doesNotMatch(html,/100%/);
});
