const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('new request clears previous evidence and ignores late results and started events', async () => {
    class Element {
        constructor() { this.children = []; this.style = {}; }
        appendChild(node) { this.children.push(node); }
        prepend(node) { this.children.unshift(node); }
        replaceChildren(...nodes) { this.children = nodes; }
        setAttribute() {}
        addEventListener() {}
    }
    const host = new Element();
    const pending = [];
    const context = {window: {}, document: {
        getElementById: id => id === 'intentComparisonEvidence' ? host : null,
        createElement: () => new Element(),
    }, fetch: () => new Promise(resolve => pending.push(resolve)), setTimeout};
    vm.runInNewContext(fs.readFileSync('services/orchestrator/static/intent-comparison.js', 'utf8'), context);
    const ui = context.window.IntentComparison;
    const old = ui.begin();
    const oldWork = ui.watch('old', '울릉도', old);
    assert.equal(host.children.length, 1);
    const current = ui.begin();
    assert.equal(host.children.length, 0);
    await ui.watch('late-start', '울릉도', old);
    assert.equal(host.children.length, 0);
    const work = ui.watch('new', '해운대 해수욕장', current);
    pending[0]({ok:true,json:async()=>({query:'울릉도',status:'COMPLETED',execution:{status:'COMPLETED'}})});
    await oldWork;
    assert.equal(host.children.length, 1);
    pending[1]({ok:true,json:async()=>({comparison_id:'new',query:'해운대 해수욕장',status:'COMPLETED',execution:{status:'NEEDS_CLARIFICATION'}})});
    await work;
    assert.ok(host.children[0].children[0].textContent.includes('해운대 해수욕장'));
    assert.ok(!host.children[0].children[0].textContent.includes('울릉도'));
    const html = fs.readFileSync('services/orchestrator/static/index.html', 'utf8');
    assert.ok(html.includes('const comparisonGeneration = IntentComparison.begin();'));
    assert.ok(html.includes('IntentComparison.watch(data.comparison_id, query, comparisonGeneration)'));
});

async function renderRecord(record) {
    class Element {
        constructor() { this.children = []; this.style = {}; this.textContent = ''; }
        appendChild(node) { this.children.push(node); }
        prepend(node) { this.children.unshift(node); }
        replaceChildren(...nodes) { this.children = nodes; }
        setAttribute() {}
        addEventListener() {}
    }
    const host = new Element();
    const context = {window: {}, document: {
        getElementById: id => id === 'intentComparisonEvidence' ? host : null,
        createElement: () => new Element(),
    }, fetch: async () => ({ok:true,json:async()=>record}),
    setTimeout: () => { throw new Error('Terminal records must not loop on render errors'); }};
    vm.runInNewContext(fs.readFileSync('services/orchestrator/static/intent-comparison.js', 'utf8'), context);
    const ui = context.window.IntentComparison;
    await ui.watch(record.comparison_id, record.query, ui.begin());
    const text = node => [node.textContent, ...node.children.map(text)].join('\n');
    return text(host);
}

test('stored timeout case separates unavailable Qwen and fusion from execution clarification', async () => {
    const text = await renderRecord({comparison_id:'timeout', query:'부산항입구위험객체', status:'FAILED',
        error:'TimeoutError: timed out', rankings:{rule:{ranking:['PLACE_LOOKUP'],probabilities:{PLACE_LOOKUP:0.476}}},
        execution:{status:'NEEDS_CLARIFICATION',error_code:'DISTANCE_REQUIRED',summary:'검색 반경을 지정해 주세요.'}});
    assert.match(text, /Qwen: Qwen 비교 시간이 초과/);
    assert.match(text, /융합\(동일 가중치\): Qwen 비교 시간이 초과/);
    assert.match(text, /실제 실행 사유: DISTANCE_REQUIRED/);
    assert.match(text, /실행 판단: NEEDS_CLARIFICATION/);
    assert.match(text, /PLACE_LOOKUP 0\.476/);
});

test('missing score and boolean observations remain unknown without breaking the result panel', async () => {
    const text = await renderRecord({comparison_id:'missing',query:'검증 질의',status:'COMPLETED',
        rankings:{rule:{ranking:['A','B'],probabilities:{A:null}}}, judgement:{reason:'recorded'},
        disagreement:null,latency_ms:null,execution:{status:'PARTIAL'}});
    assert.match(text,/A 점수 미기록/);
    assert.match(text,/B 점수 미기록/);
    assert.match(text,/Qwen 추가 확인 판단: 미기록/);
    assert.match(text,/순위 비교: 미평가/);
    assert.match(text,/모델 처리 시간: 미기록/);
    assert.doesNotMatch(text,/NaN|0\.000|비교 결과 확인 중/);
});

test('queue full is distinct from model timeout and retains blocked execution', async () => {
    const text = await renderRecord({comparison_id:'queue',query:'위험객체',status:'QUEUE_FULL',
        error:'shadow queue capacity exceeded',execution:{status:'BLOCKED',error_code:'DATA_COVERAGE_UNVERIFIED'}});
    assert.match(text,/비교 대기열이 가득/);
    assert.match(text,/실제 실행 사유: DATA_COVERAGE_UNVERIFIED/);
    assert.doesNotMatch(text,/시간이 초과/);
});
