/* A shadow result is deliberately separate from executed map/analysis results. */
window.IntentComparison = (() => {
    const terminal = new Set(['COMPLETED', 'FAILED', 'QUEUE_FULL', 'INTERRUPTED']);
    let generation = 0;
    function begin() {
        generation += 1;
        document.getElementById('intentComparisonEvidence')?.replaceChildren();
        return generation;
    }
    function line(parent, label, value) {
        const p = document.createElement('p');
        p.style.margin = '6px 0';
        p.textContent = `${label}: ${value}`;
        parent.appendChild(p);
    }
    function unavailableComparison(record) {
        if (record.status === 'QUEUE_FULL') return '비교 대기열이 가득 차 결과를 얻지 못했습니다.';
        if (record.status === 'INTERRUPTED') return '비교가 중단되어 결과를 얻지 못했습니다.';
        if (record.status === 'FAILED') {
            return /timeout|timed out/i.test(record.error || '')
                ? 'Qwen 비교 시간이 초과되어 결과를 얻지 못했습니다.'
                : '비교 처리에 실패하여 결과를 얻지 못했습니다.';
        }
        return record.status === 'COMPLETED' ? '비교 기록에 결과가 없습니다.' : '비교 결과를 기다리고 있습니다.';
    }
    async function watch(id, query, requestGeneration = generation) {
        if (!id || requestGeneration !== generation) return;
        if (document.getElementById(`intentComparison-${id}`)) return;
        let host = document.getElementById('intentComparisonEvidence');
        if (!host) {
            host = document.createElement('section');
            host.id = 'intentComparisonEvidence';
            host.setAttribute('aria-label', '질의별 의도 해석 비교 근거');
            document.getElementById('answerEvidence').parentElement.after(host);
        }
        const panel = document.createElement('details');
        panel.id = `intentComparison-${id}`;
        panel.style.cssText = 'margin:10px 0;padding:10px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;overflow-wrap:anywhere';
        host.prepend(panel);
        const title = document.createElement('summary');
        title.style.cursor = 'pointer';
        title.textContent = `규칙 · Qwen · 융합 비교 근거 — ${query}`;
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
        const review = document.createElement('button');
        review.type = 'button';
        review.textContent = 'Evidence 검토 메뉴';
        review.style.marginLeft = '10px';
        review.addEventListener('click', () => window.EvidenceWorkspace?.show('evidence'));
        panel.appendChild(review);
        for (let attempt = 0; attempt < 600; attempt++) {
            if (requestGeneration !== generation) return;
            try {
                const response = await fetch(link.href);
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const record = await response.json();
                if (requestGeneration !== generation) return;
                if (record.query !== query || (record.comparison_id && record.comparison_id !== id)) {
                    throw new Error('현재 질의와 비교 기록이 일치하지 않습니다.');
                }
                window.ExecutionView?.acceptComparison(record);
                title.textContent = `규칙 · Qwen · 융합 비교 근거 — ${query} · ${record.status}`;
                body.replaceChildren();
                line(body, '비교 상태', `${record.status} (${record.model || 'Qwen / Ollama'})`);
                line(body, '질의 정규화', record.execution?.normalized_query || record.candidate_trace?.normalized_query || '미기록');
                line(body, '실행 판단', `${record.execution?.status || 'PENDING'} · 규칙/실행 검증 사용`);
                line(body, '평가 범위', 'shadow 비교 · 모델 실행 권한 없음 · 점수 보정/정확도 미측정');
                let hasTopTies = false;
                for (const [key, name] of [['rule', '규칙'], ['ollama', 'Qwen'], ['simple_mix', '융합(동일 가중치)']]) {
                    const rank = record.rankings?.[key];
                    if (rank && Array.isArray(rank.ranking) && rank.ranking.length) {
                        const scores = rank.probabilities || {};
                        const measured = rank.ranking.filter(v => typeof scores[v] === 'number' && Number.isFinite(scores[v]));
                        const maximum = Math.max(...measured.map(v => scores[v]));
                        const tied = measured.filter(v => Math.abs(scores[v] - maximum) < 1e-9);
                        hasTopTies ||= tied.length > 1;
                        line(body, name, rank.ranking.map(v => `${v} ${measured.includes(v) ? scores[v].toFixed(3) : '점수 미기록'}`).join(' / ') + (tied.length > 1 ? ` (공동 1위 ${tied.length}개)` : '') + (rank.abstained ? ' (후보 밖: 판단 보류)' : ''));
                    } else {
                        line(body, name, key === 'rule' ? '순위 미기록' : unavailableComparison(record));
                    }
                }
                if (record.judgement) {
                    line(body, 'Qwen 해석', record.judgement.reason);
                    line(body, 'Qwen 선택', record.judgement.selected || '후보 밖: 판단 보류');
                    line(body, 'Qwen 추가 확인 판단', record.judgement.needs_clarification === true ? '필요' : record.judgement.needs_clarification === false ? '불필요 — 실제 실행 허용과는 별개' : '미기록');
                    line(body, '원문 슬롯', JSON.stringify({location: record.judgement.location, radius: record.judgement.radius, time: record.judgement.time}));
                    line(body, '순위 비교', hasTopTies ? '상위 동점 있음 — 단순 일치/불일치로 평가하지 않음' : record.disagreement === true ? '불일치 — 의미 오류 여부는 별도 검수 필요' : record.disagreement === false ? '일치 — 정확도를 의미하지 않음' : '미평가');
                    line(body, '모델 처리 시간', typeof record.latency_ms === 'number' && Number.isFinite(record.latency_ms) ? `${(record.latency_ms / 1000).toFixed(1)}초` : '미기록');
                }
                if (['FAILED', 'QUEUE_FULL', 'INTERRUPTED'].includes(record.status)) {
                    line(body, '비교와 실행 구분', 'Qwen·융합 비교의 실패는 공간 검색 실패나 허용을 뜻하지 않습니다. 실제 실행 상태와 차단·추가 입력 사유를 확인하세요.');
                    if (record.execution?.error_code) line(body, '실제 실행 사유', record.execution.error_code);
                    if (record.execution?.summary) line(body, '실제 실행 안내', record.execution.summary);
                }
                if (record.execution?.execution_permission) line(body, '실행 허용 범위', JSON.stringify(record.execution.execution_permission));
                if (record.error) line(body, '비교 실패 사유', record.error);
                // The comparison can finish before the actual task: keep observing execution too.
                if (terminal.has(record.status) && record.execution?.status !== 'PENDING') return;
            } catch (error) {
                if (requestGeneration !== generation) return;
                body.textContent = `비교 결과 확인 중: ${error.message}`;
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        line(body, '자동 갱신 종료', '원본 링크에서 최종 상태를 확인하세요.');
    }
    return {begin, watch};
})();
