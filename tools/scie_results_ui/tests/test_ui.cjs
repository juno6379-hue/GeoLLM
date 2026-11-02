const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');

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
