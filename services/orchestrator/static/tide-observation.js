(function () {
    'use strict';
    const node = (tag, text) => { const n = document.createElement(tag); if (text != null) n.textContent = text; return n; };
    window.addEventListener('DOMContentLoaded', () => {
        const mapPanel = document.getElementById('map')?.closest('.panel');
        if (!mapPanel) return;
        const panel = node('section'); panel.className = 'panel'; panel.id = 'tideObservation';
        const title = node('div', '국가해양관측망 · 실측·예측 조위'); title.className = 'panel-header';
        const body = node('div'); body.style.cssText = 'padding:16px;overflow:auto;';
        const form = node('form'); form.style.cssText = 'display:flex;gap:10px;flex-wrap:wrap;align-items:end';
        const station = node('input'); station.id = 'tideStation'; station.value = 'DT_0001'; station.required = true; station.pattern = 'DT_[0-9]{4}';
        const date = node('input'); date.id = 'tideDate'; date.type = 'date'; date.required = true;
        const parts = new Intl.DateTimeFormat('en-CA', {timeZone:'Asia/Seoul',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(new Date());
        const part = type => parts.find(p => p.type === type).value;
        date.value = `${part('year')}-${part('month')}-${part('day')}`;
        for (const [input, label] of [[station,'관측소 코드 (인천 DT_0001)'],[date,'조회일']]) {
            const l = node('label',label+' '); l.append(input); form.append(l);
        }
        const button = node('button','조위 조회·저장'); button.type = 'submit'; form.append(button);
        const stored = node('button','저장 이력'); stored.type = 'button'; form.append(stored);
        const status = node('p','조회 버튼을 누르면 공식 API를 호출하고 로컬 DB에 저장합니다. 60분 간격 조회이며 자동 수집은 하지 않습니다.');
        status.setAttribute('role','status');
        const results = node('div'); results.id = 'tideResults';
        const source = node('a','출처: 국립해양조사원 · 공공데이터포털'); source.href = 'https://www.data.go.kr/data/15142507/openapi.do'; source.target = '_blank'; source.rel = 'noopener';
        body.append(form,status,results,source); panel.append(title,body); mapPanel.after(panel);
        async function load(history) {
            if (!form.reportValidity()) return;
            results.replaceChildren(); button.disabled = stored.disabled = true;
            status.textContent = history ? '로컬 저장 이력 조회 중…' : '실측·예측 조위 조회 중…';
            try {
                const params = new URLSearchParams({station:station.value.trim(),date:date.value.replaceAll('-','')});
                const response = await fetch(`/api/v1/observations/tide${history?'/history':''}?${params}`,{signal:AbortSignal.timeout(25000)});
                const data = await response.json();
                if (!response.ok) throw new Error(typeof data.detail?.code === 'string' ? data.detail.code : `HTTP ${response.status}`);
                status.textContent = `${data.returned_count}건 · ${history?'저장된 조회 이력':`DB ${data.storage?.status === 'STORED'?'저장 완료':'저장 실패'}${data.cached?' · 30초 캐시':''}`} · ${data.fetched_at || '조회시각은 표 참조'}`;
                const note = node('p','실측과 예측을 분리 표시합니다. 빈 값은 결측/미제공입니다. 단위·수직기준면은 확인 중이며 수심·UKC 계산에 적용하지 않습니다.');
                const table = node('table'); table.style.cssText='width:100%;border-collapse:collapse;font-size:12px';
                const header = node('tr');
                for (const text of ['관측소','원천 관측시각','실측조위 (원천 값)','예측조위 (원천 값)',...(history?['조회시각']:[])]) header.append(node('th',text));
                table.append(header);
                for (const row of data.rows || []) {
                    const tr = node('tr');
                    for (const v of [row.station_name,row.observed_at,row.observed_level,row.predicted_level,...(history?[row.fetched_at]:[])]) {
                        const td = node('td',v == null?'미제공':String(v)); td.style.cssText='padding:6px;border-bottom:1px solid #e2e8f0'; tr.append(td);
                    }
                    table.append(tr);
                }
                results.append(note,table);
                if (data.has_more) results.append(node('p','현재 페이지 결과입니다. 추가 페이지는 API의 page 파라미터로 조회할 수 있습니다.'));
            } catch (error) { status.textContent = `조회 실패: ${error.name === 'TimeoutError'?'응답 시간 초과':error.message}`; }
            finally { button.disabled = stored.disabled = false; }
        }
        form.addEventListener('submit', event => {event.preventDefault();load(false);});
        stored.addEventListener('click',()=>load(true));
    });
})();
