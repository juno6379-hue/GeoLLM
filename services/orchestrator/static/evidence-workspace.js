/* Review evidence without changing model authority or manufacturing human gold. */
window.EvidenceWorkspace = (() => {
    let dashboard, workspace, records, status;
    function element(tag, text, parent) {
        const node = document.createElement(tag);
        if (text !== undefined) node.textContent = text;
        if (parent) parent.append(node);
        return node;
    }
    function fact(parent, name, value) {
        element('dt', name, parent);
        element('dd', value == null ? '미기록' : typeof value === 'object' ? JSON.stringify(value) : String(value), parent);
    }
    function render(record) {
        const panel = element('details', undefined, records);
        panel.className = 'comparison-review';
        panel.dataset.comparisonId = record.comparison_id;
        element('summary', `${record.query || '질의 미기록'} · ${record.status}`, panel);
        const facts = element('dl', undefined, panel);
        const execution = record.execution || {};
        const qec = execution.query_execution_context || {};
        const trace = record.candidate_trace || {};
        fact(facts, '요청 / 비교 ID', `${record.task_id} / ${record.comparison_id}`);
        fact(facts, '사용자 질의', record.query);
        fact(facts, '질의 정규화', execution.normalized_query || trace.normalized_query || qec.normalized_query);
        fact(facts, '지도·대화 문맥', record.context);
        fact(facts, '실행 슬롯', qec.slots);
        for (const [key, label] of [['rule', '규칙'], ['ollama', 'Qwen'], ['simple_mix', '융합 (동일 가중치)']]) {
            const rank = record.rankings?.[key];
            fact(facts, label, rank?.ranking?.map(id => `${id}: ${Number(rank.probabilities?.[id]).toFixed(3)}`).join(' / ') || '대기 또는 미기록');
        }
        fact(facts, 'Qwen 해석 근거', record.judgement?.reason);
        fact(facts, '후보 간 불일치', record.disagreement == null ? '미평가' : record.disagreement ? '있음 — 오분류 확정 아님' : '없음 — 정확도 보증 아님');
        fact(facts, '실행 결과', execution.status);
        fact(facts, '실행 검증', qec.provenance?.execution_validation || qec.readiness);
        fact(facts, '차단 사유', qec.blockers || execution.error_code);
        fact(facts, '실행 요약', execution.summary);
        fact(facts, '모델 / 프롬프트 / registry 버전', {model: record.model, prompt: record.prompt_version, registry: record.registry_version});
        fact(facts, 'Human gold', record.human_gold || '미승인 — Evidence 승인과 별도로 검수 필요');
        if (record.error) fact(facts, '비교 실패', record.error);
        const link = element('a', '모델 입력·출력 및 후보 원본', panel);
        link.href = `/api/v1/intent-comparisons/${encodeURIComponent(record.comparison_id)}`;
        link.target = '_blank';
        link.rel = 'noopener';
    }
    async function refresh() {
        status.textContent = '저장된 비교 이력을 불러오는 중…';
        try {
            const response = await fetch('/api/v1/intent-comparisons?limit=30');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            records.replaceChildren();
            data.items.forEach(render);
            status.textContent = `최근 ${data.items.length}건 · 의도 오류와 기능 미지원은 실행 계약·근거를 확인한 뒤 판정합니다.`;
        } catch (error) {
            status.textContent = `이력을 불러오지 못했습니다: ${error.message}`;
        }
    }
    function init() {
        const content = document.querySelector('.content-area');
        const approval = document.getElementById('evidenceApprovalPanel');
        if (!content || !approval) return;
        const style = element('style', `
            [hidden] { display:none !important; }
            .workspace-menu { background:none; border:0; border-left:3px solid transparent; text-align:left; font:inherit; }
            #evidenceWorkspace { min-width:0; }
            #dashboardWorkspace { display:flex; flex-direction:column; gap:10px; min-width:0; }
            #evidenceWorkspace h1 { font-size:20px; margin:0 0 12px; }
            #evidenceWorkspace .review-panel { margin:16px 0; }
            .comparison-review { background:white; border:1px solid #cbd5e1; border-radius:8px; padding:12px; margin:10px 0; overflow-wrap:anywhere; }
            .comparison-review summary { cursor:pointer; font-weight:600; }
            .comparison-review dl { display:grid; grid-template-columns:minmax(100px,180px) 1fr; gap:8px; font-size:13px; }
            .comparison-review dt { color:#475569; }
            .comparison-review dd { margin:0; white-space:pre-wrap; }
            .workspace-mobile { display:none; }
            @media(max-width:1180px) { .workspace-mobile { display:flex; gap:8px; margin-bottom:12px; } }
        `, document.head);
        dashboard = element('div');
        dashboard.id = 'dashboardWorkspace';
        while (content.firstChild) dashboard.append(content.firstChild);
        content.append(dashboard);
        workspace = element('section', undefined, content);
        workspace.id = 'evidenceWorkspace';
        workspace.hidden = true;
        workspace.setAttribute('aria-label', 'Evidence 검토 및 승인');
        element('h1', 'Evidence 검토·승인', workspace);
        element('p', '근거 후보의 출처와 내용을 검토하고 승인합니다. 아래 질의 비교는 검토 보조 자료이며, Evidence 승인 자체가 실행 허용이나 학습용 정답 승인을 뜻하지 않습니다.', workspace);
        workspace.append(approval);
        element('h2', '질의 해석·실행 비교 이력', workspace);
        const button = element('button', '비교 이력 새로고침', workspace);
        button.type = 'button';
        button.addEventListener('click', refresh);
        status = element('p', '저장된 최근 30건을 표시합니다.', workspace);
        status.setAttribute('role', 'status');
        records = element('div', undefined, workspace);
        const mobile = element('nav');
        mobile.className = 'workspace-mobile';
        mobile.setAttribute('aria-label', '주요 메뉴');
        for (const [view, label] of [['dashboard', '통합 대시보드'], ['evidence', 'Evidence 검토·승인']]) {
            const button = element('button', label, mobile);
            button.type = 'button';
            button.addEventListener('click', () => show(view));
        }
        content.prepend(mobile);
    }
    function show(view) {
        if (!workspace) return;
        const reviewing = view === 'evidence';
        dashboard.hidden = reviewing;
        workspace.hidden = !reviewing;
        for (const [id, active] of [['dashboardMenu', !reviewing], ['evidenceMenu', reviewing]]) {
            const button = document.getElementById(id);
            button.classList.toggle('active', active);
            if (active) button.setAttribute('aria-current', 'page');
            else button.removeAttribute('aria-current');
        }
        if (reviewing) refresh();
        else window.dispatchEvent(new Event('resize'));
    }
    document.addEventListener('DOMContentLoaded', init);
    return {show, refresh};
})();
