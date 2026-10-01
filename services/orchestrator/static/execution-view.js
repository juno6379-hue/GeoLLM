/* Current-request observations only. Shadow rankings never authorize execution. */
window.ExecutionView = (() => {
    const ids = ['routing', 'discovery', 'spatial', 'ais', 'knowledge', 'reasoning', 'validation', 'report'];
    const names = {PLACE_LOOKUP:'지명 찾기',SPATIAL_ANALYSIS:'공간 검색·분석',ACCIDENT_ANALYSIS:'사고 조회·분석',STANDARD_RAG:'문서 근거 검색',DATASET_PROVENANCE:'자료 적재 근거',TRAFFIC_ANALYSIS:'통항량 분석'};
    let query = '', result = null, comparison = null, finished = false, observed = {}, coastal = null, coastalModel = null, generation = 0;
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
    function locationAnalysis() {
        if (result?.status !== 'NEEDS_CLARIFICATION' || !/입구|출구|근처|주변|부근|인근/.test(query)) return null;
        const s = result.structured_result || {};
        if (!['EXTERNAL_PLACE_CANDIDATES','LOCATION_UNCONFIRMED','LOCATION_REQUIRED','DISTANCE_REQUIRED','AMBIGUOUS_PLACE'].includes(result.error_code || s.error_code)) return null;
        const location = s.query_interpretation?.location_text || s.location_text || s.extracted_slots?.location_text || '요청한 위치';
        const lines = [`“${location}” 관련 요청의 공간 표현을 다음과 같이 해석했습니다.`];
        if (/입구|출구/.test(query)) lines.push('입구·출구는 항만의 세부 진입·이탈 위치를 가리킵니다. 항만 전체 영역이나 중심점으로 대체하지 않으며, 해당 위치를 뒷받침하는 좌표·지형 근거가 필요합니다.');
        if (/근처|주변|부근|인근/.test(query)) {
            const distance = s.query_interpretation?.distance_m ?? s.distance_m;
            lines.push(`근처·주변은 기준 위치와 검색 범위의 관계입니다. ${distance != null ? `요청에 기록된 반경은 ${distance}m입니다.` : '현재 응답에는 확정된 검색 반경이 없습니다. 반경이나 지도 검색 영역을 정해야 합니다.'}`);
        }
        const candidates = s.location_candidates || [];
        if (candidates.length) {
            const usable = candidates.filter(c => c.geometry && c.crs).length;
            lines.push(`현재 위치 후보 ${candidates.length}개를 찾았습니다. ${usable ? `좌표·좌표계가 있는 후보 ${usable}개의 출처와 세부 위치를 확인할 수 있습니다.` : '후보의 좌표가 미확정이어서 지도에 표시할 기준점을 확정하지 못했습니다.'}`);
        } else lines.push(result.error_code === 'DISTANCE_REQUIRED' ? '기준 위치는 확인했으며 검색 범위 확인이 남아 있습니다.' : '현재 연결된 근거에서 요청 위치의 기준점을 확정하지 못했습니다.');
        if (coastal?.documents?.length) {
            const term = coastal.search_terms?.[0] || '';
            const relative = /입구/.test(query) ? '입구' : /출구/.test(query) ? '출구' : '';
            const pattern = new RegExp((term + relative).replace(/[.*+?^${}()|[\]\\]/g,'\\$&').split('').join('\\s*'));
            const highlights = coastal.documents.filter(d => d.page_no || !coastal.documents.some(other => other.page_no && other.title === d.title));
            for (const doc of highlights.slice(0,2)) {
                const match = pattern.exec(doc.content), start = Math.max(0,(match?.index || 0)-30);
                lines.push(`관련 원문 · ${doc.title} (${doc.page_no ? `PDF ${doc.page_no}쪽` : doc.section})\n…${doc.content.slice(start,start+280)}…`);
            }
            lines.push('위 내용은 원문 발췌이며 판·최신성 확인이 필요합니다. 항만 대표점과 입구 좌표는 구분합니다.');
        }
        lines.push('문서 근거 검색과 요청한 지도 이동·공간 검색은 별도입니다. 위치 확인 대기 중에는 지도 이동·공간 검색을 실행하지 않습니다.');
        return lines.join('\n\n');
    }
    function refreshSummary() {
        const text = locationAnalysis();
        if (!text) return;
        for (const id of ['answerText','querySummaryBody']) { const el = document.getElementById(id); if (el) el.textContent = text; }
        for (const id of ['answerStatus','querySummaryTitle']) { const el = document.getElementById(id); if (el) el.textContent = '공간 표현 해석 · 실행 조건 확인 중'; }
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
        if (coastal) {
            if (coastal.status === 'COMPLETED') paint('knowledge','원문 검색 완료',`${coastal.documents.length}개 발췌. 별도 근거 조회이며 지도 실행 승인이 아닙니다.`);
            if (coastal.embedding_coverage) line('본문·임베딩 적재', `검색 본문 ${coastal.embedding_coverage.total}개 / 임베딩 완료 ${coastal.embedding_coverage.embedded}개 · ${coastal.retrieval_method || ''}`);
            line('항로지·항만 안내 근거 검색', coastal.status === 'COMPLETED' ? `${coastal.documents.length}개 발췌 · ${coastal.knowledge_links?.length || 0}개 출처 연결` : `${coastal.status} · 검색 완료로 보지 않습니다.`);
            for (const doc of coastal.documents || []) {
                const title = `${doc.title} / ${doc.page_no ? `PDF ${doc.page_no}쪽` : doc.section}`;
                const detail = document.createElement('details'), caption = document.createElement('summary'), excerpt = document.createElement('p');
                caption.textContent = title; excerpt.textContent = doc.content; excerpt.style.whiteSpace = 'pre-wrap';
                detail.appendChild(caption); detail.appendChild(excerpt); host.appendChild(detail);
                line('출처', `${doc.metadata?.source_file || doc.source_id} · ${doc.metadata?.version || '판 미확인'}${doc.metadata?.extraction_warning ? ' · ' + doc.metadata.extraction_warning : ''}`);
            }
            if (coastal.documents?.length) {
                for (const port of coastal.harbour_records || []) line('연결된 항만 안내 기록', `${port.name} · ${port.properties?.ADR_KNM || ''} · ${port.properties?.ORIYR || '연도 미확인'}년 원천 · 대표점 ${JSON.stringify(port.geometry?.coordinates)} (입구 좌표 아님)`);
                line('Qwen 설명과 근거 대조', comparison?.judgement ? '위 Qwen 응답은 의도·슬롯 해석입니다. 이 발췌는 실제 원문 검색 결과이며, Qwen이 원문을 읽고 생성한 설명으로 표시하지 않습니다.' : 'Qwen 비교 대기 중에도 원문 근거를 확인할 수 있습니다.');
                line('자료 적용 범위', (coastal.limitations || []).join(' '));
                const button = document.createElement('button'); button.textContent = 'Qwen에 원문 근거를 주고 설명 비교';
                button.disabled = coastalModel?.status === 'RUNNING';
                button.addEventListener('click', () => {
                    const ticket = generation; coastalModel = {status:'RUNNING'}; explain();
                    fetch(`/api/v1/coastal-explanation?query=${encodeURIComponent(query)}`)
                        .then(r => { if (!r.ok) throw new Error('model unavailable'); return r.json(); })
                        .then(data => { if (ticket === generation) { coastalModel=data; explain(); } })
                        .catch(() => { if (ticket === generation) { coastalModel={status:'UNAVAILABLE'}; explain(); } });
                });
                host.appendChild(button);
                if (coastalModel) {
                    line('Qwen 원문 근거 비교', coastalModel.status);
                    for (const quote of coastalModel.quotes || []) line(`${quote.title} / ${quote.page_no ? `PDF ${quote.page_no}쪽` : quote.section}`, quote.quote);
                    line('인용 검증', '원문과 일치하는 인용만 표시합니다. 모델의 선택 적합도와 현재 항해 적용 가능성은 별도 검토 대상입니다.');
                }
            }
        }
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
            line('현재 결과·다음 입력', locationAnalysis() || result.answer_text || result.summary || result.status);
        }
        refreshSummary();
    }
    function begin(text) {
        query = text; result = comparison = coastal = coastalModel = null; finished = false; observed = {};
        const ticket = ++generation;
        if (typeof fetch === 'function') fetch(`/api/v1/coastal-evidence?query=${encodeURIComponent(text)}`)
            .then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
            .then(data => { if (ticket === generation) { coastal = data; explain(); } })
            .catch(() => { if (ticket === generation) { coastal = {status:'UNAVAILABLE',documents:[]}; explain(); } });
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
            if (result.coastal_evidence) coastal = result.coastal_evidence;
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
    return {begin, handle, acceptComparison, end, refreshSummary};
})();
