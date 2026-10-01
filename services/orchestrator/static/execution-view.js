/* Current-request observations only. Shadow rankings never authorize execution. */
window.ExecutionView = (() => {
    const ids = ['routing', 'discovery', 'spatial', 'ais', 'knowledge', 'reasoning', 'validation', 'report'];
    const names = {PLACE_LOOKUP:'지명 찾기',SPATIAL_ANALYSIS:'공간 검색·분석',ACCIDENT_ANALYSIS:'사고 조회·분석',STANDARD_RAG:'문서 근거 검색',DATASET_PROVENANCE:'자료 적재 근거',TRAFFIC_ANALYSIS:'통항량 분석'};
    let query = '', result = null, comparison = null, finished = false, observed = {};
    function paint(id, status, detail) {
        const el = document.getElementById(`step-${id}`);
        if (!el) return;
        el.classList.remove('active', 'done');
        if (status === '진행 중') el.classList.add('active');
        if (['완료','승인','응답 완료'].includes(status)) el.classList.add('done');
        let label = el.querySelector('.execution-state');
        if (!label) {
            label = document.createElement('div'); label.className = 'execution-state';
            label.style.cssText = 'font-size:12px;margin-top:7px;line-height:1.5;color:#334155;white-space:normal';
            el.appendChild(label);
        }
        label.textContent = status;
        el.title = detail || status;
        el.querySelector('.step-circle').textContent = ['완료','승인','응답 완료'].includes(status) ? '✓' : status === '진행 중' ? '↻' : status === '미실행' ? '—' : status === '대기' ? String(ids.indexOf(id) + 1) : '!';
    }
    function rankText(rank) {
        if (!rank?.ranking?.length) return '아직 비교 결과가 없습니다.';
        return rank.ranking.map(key => `${names[key] || key}${Number.isFinite(rank.probabilities?.[key]) ? ` (${rank.probabilities[key].toFixed(3)})` : ''}`).join(' / ') + (rank.abstained ? ' · 판단 보류' : '');
    }
    function explain() {
        const host = document.getElementById('intentAnswer');
        if (!host) return;
        host.replaceChildren(); host.hidden = !query;
        const heading = document.createElement('strong'); heading.textContent = '질의 해석과 실행 판단'; host.appendChild(heading);
        const line = (label, value) => {
            const p = document.createElement('p'); p.style.margin = '8px 0';
            p.textContent = `${label}: ${value}`; host.appendChild(p);
        };
        line('현재 질의', query);
        if (comparison) {
            line('질의 정규화', comparison.execution?.normalized_query || comparison.candidate_trace?.normalized_query || '기록 없음');
            const route = result?.orchestrator_v2?.route_plan?.intent;
            line('규칙 해석', comparison.rankings?.rule ? rankText(comparison.rankings.rule) : route ? `${names[route] || route} · 후보 점수 비교 대기` : rankText(null));
            const judgement = comparison.judgement;
            line('Qwen 해석', judgement ? `선택 의도: ${names[judgement.selected] || judgement.selected || '판단 보류'} / 추가 확인 판단: ${judgement.needs_clarification === true ? '필요' : judgement.needs_clarification === false ? '불필요' : '미기록'} (모델 의견)` : `비교 ${comparison.status || '대기'} · 아직 모델 해석이 없습니다.`);
            if (judgement?.reason) {
                const details = document.createElement('details'), summary = document.createElement('summary'), body = document.createElement('p');
                summary.textContent = 'Qwen 설명 원문'; body.textContent = judgement.reason;
                details.appendChild(summary); details.appendChild(body); host.appendChild(details);
            }
            if (comparison.judgement) {
                const j = comparison.judgement;
                line('Qwen이 추출한 조건', `위치 ${j.location || '미지정'} / 반경 ${j.radius || '미지정'} / 시간 ${j.time || '미지정'}`);
            }
            line('융합 비교', rankText(comparison.rankings?.simple_mix));
            line('비교의 의미', '후보 점수이며 정확도나 실행 승인 값이 아닙니다. Qwen 해석은 검증된 지명·좌표를 대신하지 않습니다.');
        } else line('해석 비교', '규칙·Qwen·융합 비교를 기다리는 중입니다. 실제 처리 상태는 아래에 별도로 표시합니다.');
        if (result) {
            const structured = result.structured_result || {};
            const location = structured.query_interpretation?.location_text || structured.location_text || structured.extracted_slots?.location_text;
            if (location) line('실제 위치 확인 대상', location);
            const modelLocation = comparison?.judgement?.location;
            if (location && modelLocation && String(location).replace(/\s/g,'') !== String(modelLocation).replace(/\s/g,'')) {
                line('위치 해석 차이', `Qwen의 “${modelLocation}”와 실제 요청 대상 “${location}”가 다릅니다. 원문의 세부 위치를 유지하며 모델 표현으로 기준점을 바꾸지 않습니다.`);
            }
            const steps = result.processing_steps || [];
            for (const step of steps.filter(s => ['실행 승인','도구 실행'].includes(s.step))) line(step.step, step.detail);
            if (structured.location_candidates?.length) {
                const selectable = structured.location_candidates.filter(c => c.geometry && c.crs).length;
                line('후보 확인', selectable ? `${structured.location_candidates.length}개 후보 중 좌표·좌표계가 있는 후보 ${selectable}개를 확인할 수 있습니다. 아래 출처·위치를 확인하여 선택하세요. 후보 선택과 권위 지명 등록은 별개입니다.` : `후보 ${structured.location_candidates.length}개는 좌표가 미확정되어 선택할 수 없습니다. 경도·위도를 지정하거나 검증된 위치 근거를 추가해야 합니다.`);
            }
            line('현재 결과·다음 입력', result.answer_text || result.summary || result.status);
        }
    }
    function begin(text) {
        query = text; result = comparison = null; finished = false; observed = {};
        ids.forEach(id => paint(id, '대기', '현재 질의에서 아직 관측된 실행 기록이 없습니다.'));
        paint('routing', '진행 중'); explain();
    }
    function handle(event) {
        if (event.event === 'node_finished') {
            if (/parse_intent|instant_place_lookup|fast_place_lookup/.test(event.node || '')) paint('routing','완료','의도 처리 노드 응답 확인');
            const key = ({data_discovery:'discovery',graph_rag:'knowledge',fast_document_answer:'knowledge',validate_results:'validation',map_report:'report'})[event.node];
            if (key) { observed[key] = `${event.node}: ${event.status || '상태 미기록'}`; paint(key, '처리 기록', observed[key]); }
        }
        if (event.event === 'completed') {
            finished = true; result = event.final_result || {status:event.status,summary:event.error_message};
            // The final receipt overrides transient node messages, including fast paths.
            ids.forEach(id => paint(id,'미실행','이 전문 단계의 실행 완료 기록이 없습니다.'));
            Object.entries(observed).forEach(([id, detail]) => paint(id, '처리 기록', detail));
            paint('routing', '완료','질의 처리 응답을 받았습니다. 해석 정확도를 뜻하지 않습니다.');
            const structured = result.structured_result || {};
            const steps = result.processing_steps || [];
            const approval = steps.find(s => s.step === '실행 승인');
            paint('validation', approval?.status === 'APPROVED' ? '승인' : '미승인', approval?.detail || '실행 승인 기록 없음');
            const candidates = structured.location_candidates || [];
            const run = steps.find(s => s.step === '도구 실행');
            const agent = result.agent_name || '';
            const selected = /Spatial/.test(agent) ? 'spatial' : /AIS|Tracking/.test(agent) ? 'ais' : /RAG|Knowledge/.test(agent) ? 'knowledge' : /Discovery/.test(agent) ? 'discovery' : /Accident|Risk|Reasoning/.test(agent) ? 'reasoning' : null;
            if (selected) paint(selected, candidates.length ? '후보 확인 대기' : run?.status === 'NOT_RUN' ? '미실행' : structured.search_execution?.status === 'COMPLETED' ? '완료' : '기록 확인 필요', run?.detail || result.summary);
            if (candidates.length) paint('discovery','후보 발견',`${candidates.length}개 위치 후보 · 분석 원천 승인과 별개`);
            paint('report','응답 완료','최종 응답 수신. 지도·보고서 도구 실행 성공을 뜻하지 않습니다.');
            explain();
        }
        if (event.event === 'error') {
            finished = true; paint('report','응답 오류',event.message);
        }
    }
    function acceptComparison(record) {
        if (record.query !== query) return;
        comparison = record; explain();
    }
    function end() { if (!finished) handle({event:'error',message:'최종 응답을 받기 전에 연결이 종료됐습니다.'}); }
    return {begin, handle, acceptComparison, end};
})();
