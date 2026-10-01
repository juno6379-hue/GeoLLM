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
