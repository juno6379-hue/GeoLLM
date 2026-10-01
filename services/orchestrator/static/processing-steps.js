window.ProcessingSteps = (() => {
    function reset() { document.getElementById('processingSteps')?.remove(); }
    function render(result) {
        reset();
        const steps = result?.processing_steps;
        if (!Array.isArray(steps)) return;
        const host = document.createElement('section');
        host.id = 'processingSteps';
        host.style.cssText = 'margin:12px 0;padding:16px;background:white;border:1px solid #cbd5e1;border-radius:8px;overflow-wrap:anywhere';
        const title = document.createElement('h3');
        title.textContent = '이번 질의의 단계별 처리 결과';
        host.appendChild(title);
        const list = document.createElement('ol');
        for (const step of steps) {
            const item = document.createElement('li');
            item.style.marginBottom = '12px';
            const label = document.createElement('strong');
            label.textContent = `${step.step} · ${{RECORDED:"기록 확인",UNRECORDED:"기록 없음",APPROVED:"승인",NOT_APPROVED:"미승인",NOT_RUN:"미실행",COMPLETED:"완료",PARTIAL:"일부 완료",BLOCKED:"차단",NEEDS_CLARIFICATION:"입력 확인 필요",FAILED:"실패"}[step.status] || step.status}`;
            const detail = document.createElement('div');
            detail.textContent = step.detail;
            item.append(label, detail);
            list.appendChild(item);
        }
        host.appendChild(list);
        document.getElementById('answerEvidence').parentElement.after(host);
    }
    return {reset, render};
})();
