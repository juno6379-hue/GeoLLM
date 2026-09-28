/* A shadow result is deliberately separate from executed map/analysis results. */
window.IntentComparison = (() => {
    let generation = 0;
    const terminal = new Set(['COMPLETED', 'FAILED', 'QUEUE_FULL', 'INTERRUPTED']);
    function line(parent, label, value) {
        const p = document.createElement('p');
        p.style.margin = '6px 0';
        p.textContent = `${label}: ${value}`;
        parent.appendChild(p);
    }
    async function watch(id, query) {
        if (!id) return;
        const current = ++generation;
        let panel = document.getElementById('intentComparison');
        if (!panel) {
            panel = document.createElement('section');
            panel.id = 'intentComparison';
            panel.style.cssText = 'margin:12px 0;padding:12px;border:1px solid #64748b;border-radius:8px;font-size:13px;overflow-wrap:anywhere';
            document.getElementById('chatHistory').before(panel);
        }
        const title = document.createElement('strong');
        title.textContent = '규칙 · Qwen · 융합 비교';
        panel.replaceChildren(title);
        line(panel, '질의', query);
        const body = document.createElement('div');
        panel.appendChild(body);
        const link = document.createElement('a');
        link.href = `/api/v1/intent-comparisons/${encodeURIComponent(id)}`;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = '비교 원본·모델 입력·출력 보기';
        panel.appendChild(link);
        for (let attempt = 0; attempt < 600 && current === generation; attempt++) {
            try {
                const response = await fetch(link.href);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const record = await response.json();
                if (current !== generation) return;
                body.replaceChildren();
                line(body, '비교 상태', `${record.status} (${record.model || 'Qwen / Ollama'})`);
                line(body, '실행 판단', `${record.execution?.status || 'PENDING'} · 규칙/실행 검증 사용`);
                line(body, '평가 범위', 'shadow 비교 · 모델 실행 권한 없음 · 점수 보정/정확도 미측정');
                let hasTopTies = false;
                for (const [key, name] of [['rule', '규칙'], ['ollama', 'Qwen'], ['simple_mix', '융합(동일 가중치)']]) {
                    const rank = record.rankings?.[key];
                    if (rank) {
                        const maximum = Math.max(...Object.values(rank.probabilities));
                        const tied = rank.ranking.filter(v => Math.abs(rank.probabilities[v] - maximum) < 1e-9);
                        hasTopTies ||= tied.length > 1;
                        line(body, name, rank.ranking.map(v => `${v} ${rank.probabilities[v].toFixed(3)}`).join(' / ') + (tied.length > 1 ? ` (공동 1위 ${tied.length}개)` : '') + (rank.abstained ? ' (후보 밖: 판단 보류)' : ''));
                    }
                }
                if (record.judgement) {
                    line(body, 'Qwen 해석', record.judgement.reason);
                    line(body, 'Qwen 선택', record.judgement.selected || '후보 밖: 판단 보류');
                    line(body, 'Qwen 추가 확인 판단', record.judgement.needs_clarification ? '필요' : '불필요 — 실제 실행 허용과는 별개');
                    line(body, '원문 슬롯', JSON.stringify({location: record.judgement.location, radius: record.judgement.radius, time: record.judgement.time}));
                    line(body, '순위 비교', hasTopTies ? '상위 동점 있음 — 단순 일치/불일치로 평가하지 않음' : (record.disagreement ? '불일치 — 의미 오류 여부는 별도 검수 필요' : '일치 — 정확도를 의미하지 않음'));
                    line(body, '모델 처리 시간', `${(record.latency_ms / 1000).toFixed(1)}초`);
                }
                if (record.execution?.execution_permission) line(body, '실행 허용 범위', JSON.stringify(record.execution.execution_permission));
                if (record.error) line(body, '비교 실패 사유', record.error);
                // The comparison can finish before the actual task: keep observing execution too.
                if (terminal.has(record.status) && record.execution?.status !== 'PENDING') return;
            } catch (error) {
                body.textContent = `비교 결과 확인 중: ${error.message}`;
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        if (current === generation) line(body, '자동 갱신 종료', '원본 링크에서 최종 상태를 확인하세요.');
    }
    return {watch};
})();
