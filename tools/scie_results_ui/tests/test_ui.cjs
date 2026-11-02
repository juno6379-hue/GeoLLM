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


test('benchmark composition distinguishes approved GOLD, assisted answers and reserved holdout', () => {
 const ui=browser();
 ui.evaluate('DATA={overview:{selected_run_id:"v6",case_count:18,method_count:8,observed_rows:144,expected_observations:144,fault_rows:27,repeats:1,independent_expert_review_complete:true,review_approval:{approval_date:"2026-11-02"},completion_gate:{observation_comparison_complete:true}},semantic_review:{assisted_review_complete:true,reviewer_A_completed:144,reviewer_B_completed:144,consensus_completed:144},holdout:{main_cases:18,rq2_fault_cases:12,rq4_recovery_cases:8,evaluation_executed:false},benchmark:{cases:[]}}');
 const html=ui.evaluate('benchmarkComposition()');
 assert.match(html,/GOLD 검수 완료/); assert.match(html,/AI 보조 채점 완료/);
 assert.match(html,/평가 미실행/); assert.match(html,/최종 시스템 동결/);
 assert.match(html,/144 \/ 144/); assert.match(html,/27관측/);
 assert.match(html,/운영 Dataset 후속 검증은 별도/);
});


test('zero eligibility is not confused with missing observations',()=>{
 const ui=browser();
 assert.match(ui.evaluate('rate({value:null,denominator:0,measured:0,missing:0})'),/해당 평가 대상 없음/);
 assert.match(ui.evaluate('rate({value:null,denominator:3,measured:0,missing:3})'),/미측정/);
 assert.match(ui.evaluate('rate({value:0,denominator:3,measured:3,missing:0})'),/0%/);
});


test('RQ1 uses the Semantic Grounding table without substituting mechanical accuracy',()=>{
 const ui=browser();
 ui.evaluate('DATA={overview:{selected_run_id:"v6"}}');
 const html=ui.evaluate('rq1GroundingTable({selected_run_id:"v6",rows:[{condition:"OFFICIAL_TERM",n:6,cluster_count:6,b1_semantic_f1:null,b2_semantic_f1:null,ci95:null,strict_match:null,missing_reasons:["측정 계약 없음"]}]})');
 assert.match(html,/Table 9/);assert.match(html,/B1 Text-RAG Semantic F1/);assert.match(html,/B2 Ontology\/KG Semantic F1/);
 assert.match(html,/95% CI/);assert.match(html,/Strict Match/);assert.match(html,/측정 계약 없음/);
 assert.doesNotMatch(html,/0%/);assert.match(html,/미측정/);
});

test('paper metrics separate measured zero, unavailable observations and zero eligibility',()=>{
 const ui=browser();
 const zero=ui.evaluate('paperMetric({value:0,numerator:0,denominator:8,status:"MEASURED",unit:"ratio"})');
 assert.match(zero,/0%/);assert.match(zero,/분모 8/);
 const absent=ui.evaluate('paperMetric({value:null,numerator:null,denominator:8,status:"UNMEASURED",reason:"계측 누락",unit:"ratio"})');
 assert.match(absent,/미측정/);assert.match(absent,/계측 누락/);assert.doesNotMatch(absent,/0%/);
 const ineligible=ui.evaluate('paperMetric({value:null,denominator:0,status:"UNDEFINED",reason:"성공 사례 없음",unit:"ratio"})');
 assert.match(ineligible,/해당 평가 대상 없음/);assert.match(ineligible,/성공 사례 없음/);
 assert.doesNotMatch(ineligible,/0%/);
 const invalid=ui.evaluate('paperMetric({value:0,denominator:0,status:"MEASURED",unit:"ratio"})');
 assert.match(invalid,/산출 불가/);assert.doesNotMatch(invalid,/0%/);
});

test('Table 11 retains all eight methods including B4 and H without making up CI',()=>{
 const ui=browser();
 ui.evaluate('DATA={paper_tables:{run_id:"v6",tables:{table11:{title:"Table 11",columns:[{key:"method",label:"방법"},{key:"esr",label:"ESR"},{key:"cge",label:"CGE"}],rows:["B0","B1","B2","B3","B4","P0","H","P1"].map(method=>({method,esr:{value:null,status:"UNMEASURED",reason:"공통 계약 미측정"},cge:{value:null,status:"UNDEFINED",denominator:0}})),notes:["CGE는 실행 성공과 공간 정답의 격차입니다."]}}}}');
 const html=ui.evaluate('paperTable("table11")');
 for(const method of ['B0','B1','B2','B3','B4','P0','H','P1'])assert.match(html,new RegExp(`<td>${method}(?:<|$)`));
 assert.match(html,/추가 비교 방법/);assert.match(html,/CGE/);
 assert.match(html,/공통 계약 미측정/);assert.doesNotMatch(html,/0%/);assert.doesNotMatch(html,/95% CI/);
});

test('paper table source and metric reasons cannot inject markup',()=>{
 const ui=browser();
 ui.evaluate('DATA={paper_tables:{tables:{table10:{title:"Table 10",columns:[{key:"recall",label:"Recall"}],rows:[{recall:{value:null,status:"UNMEASURED",reason:"<img onerror=x>"}}],source_refs:[{path:"<script>x</script>",sha256:"<b>hash</b>"}]}}}}');
 const html=ui.evaluate('paperTable("table10")');
 assert.doesNotMatch(html,/<img|<script>|<b>hash/);
 assert.match(html,/&lt;img/);assert.match(html,/&lt;script/);
});

test('RQ2 through RQ5 lead with paper tables and keep prior diagnostics collapsed',()=>{
 const ui=browser();
 ui.evaluate('DATA={overview:{selected_run_id:"v6"},rq:{},sources:[],paper_tables:{tables:{}}}');
 for(const [rqNumber,tableNumber] of [[2,10],[3,11],[4,12],[5,14]]){
  const html=ui.evaluate(`rq(${rqNumber})`);
  assert.match(html,new RegExp(`Table ${tableNumber}`));
  assert.match(html,/<details class="panel"><summary>보조 진단/);
  assert.doesNotMatch(html,/<details class="panel" open/);
 }
});

test('Table 13 ablation remains a separate section with no invented full-system substitution',()=>{
 const ui=browser();ui.evaluate('DATA={paper_tables:{tables:{}},overview:{selected_run_id:"v6"}}');
 const html=ui.evaluate('ablationPanel()');
 assert.match(html,/id="ablation"/);assert.match(html,/Table 13/);
 assert.match(html,/전체 시스템 결과를 제거 실험의 대용으로 사용하지/);
 assert.doesNotMatch(html,/0%/);
});

test('RQ1 annotation completion does not fabricate semantic measurement or human approval',()=>{
 const ui=browser();
 ui.evaluate('DATA={overview:{}}');
 const html=ui.evaluate('rq1GroundingTable({gold_atom_annotation:{status:"VALIDATED_AI_ANNOTATION",written_cases:18,expected_cases:18,validated_cases:18,atom_count:120},rows:[]})');
 assert.match(html,/작성 18\/18문항/);
 assert.match(html,/원천 연결 검증 완료/);
 assert.match(html,/새 독립 인간 주석 검수 완료를 뜻하지 않습니다/);
 assert.match(html,/Semantic F1·Strict Match·CI: 미측정/);
});

test('RQ2 distinguishes binary and target code counts without generalizing N1',()=>{
 const ui=browser();const html=ui.evaluate('rq2DiagnosisPanel({methods:[{method:"P0",binary_recall:{value:1,numerator:8,denominator:8},target_code_recall:{value:0,numerator:0,denominator:8},false_block:{value:1,numerator:1,denominator:1}}],rows:[]})');
 assert.match(html,/Binary Recall/);assert.match(html,/Target-fault-code Recall/);
 assert.match(html,/8\/8/);assert.match(html,/0\/8/);assert.match(html,/N=1/);
 assert.match(html,/사후 코드 대응/);assert.match(html,/대상 치환과 대상 추가를 구별하지/);
});

test('RQ3 preserves zero-success undefined SSFR and separates wrong executable development case',()=>{
 const ui=browser();
 const html=ui.evaluate('rq3MeasurementPanel({tables:{table11:{rows:[{method:"P1",esr:{value:0,numerator:0,denominator:5},joint_execution_spatial_success:{value:0,numerator:0,denominator:5},spatial_correctness:{value:null,measured:2,denominator:5,missing:3}}]}},development_spatial:{status:"VERIFIED_DEVELOPMENT_DIAGNOSTIC",spatial_cases:[{case_id:"dev",variant:"wrong",execution_success:true,spatial_correct:false,returned_count:1,gold_count:2,missing_ids:["2"],extra_ids:[]}]}})');
 assert.match(html,/ESR 0\/5/);assert.match(html,/2\/5건 측정, 3건 미측정/);
 assert.match(html,/SSFR 0%를 뜻하지 않습니다/);assert.match(html,/방법별 분모에 합산하지 않습니다/);
 assert.match(html,/dev \/ wrong/);assert.match(html,/>true</);assert.match(html,/>false</);
});
