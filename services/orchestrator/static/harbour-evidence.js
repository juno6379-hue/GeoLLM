/* Source attributes, not generated descriptions or entrance coordinates. */
window.HarbourEvidence = (() => {
    let activeScope, opened = new Set();
    function render(host, cards, scope) {
        if (!host || !Array.isArray(cards) || !cards.length) return;
        if (scope !== activeScope) {activeScope=scope; opened=new Set();}
        const remember=(element,key)=>{
            element.open=opened.has(key);
            element.addEventListener('toggle',()=>{
                if(scope!==activeScope) return;
                if(element.open) opened.add(key); else opened.delete(key);
            });
        };
        const box = document.createElement('section'); box.className = 'harbour-evidence';
        const add = (parent, tag, value) => {const el=document.createElement(tag); el.textContent=value; parent.appendChild(el); return el;};
        add(box,'h3','소형선항만 원문 안내');
        for (const card of cards) {
            const article=add(box,'details',''); article.className='harbour-source-card'; article.open=false;
            const cardKey=card.source_id || card.name;
            remember(article,cardKey);
            article.style.cssText='border:1px solid #cbd5e1;border-radius:8px;padding:12px;margin:12px 0';
            const heading=add(article,'summary',''); heading.style.cursor='pointer';
            add(heading,'strong',card.name || '항만 안내');
            const metadata=add(heading,'span',[card.address,card.publisher,card.source_year ? `${card.source_year}년 원천` : '원천 연도 미확인'].filter(Boolean).join(' · '));
            metadata.style.cssText='display:block;margin-top:4px;font-size:12px;color:#475569';
            for (const field of card.fields || []) {const details=add(article,'details','');remember(details,`${cardKey}:field:${field.field || field.label}`);add(details,'summary',field.label);const p=add(details,'p',field.text);p.style.whiteSpace='pre-wrap';}
            const damaged=card.unavailable_fields || [];
            if (damaged.length) {
                const details=add(article,'details','');
                add(details,'summary',`원문 손상으로 안내 ${damaged.length}개 항목 표시 보류`);
                add(details,'p',damaged.map(field=>field.label).join(' · '));
                add(details,'p','원문 문자 손상이 확인된 항목입니다. 정상 안내 항목은 각각 펼쳐 볼 수 있습니다.');
            }
            const missingPhotos=[];
            for (const photo of card.photos || []) {
                // Only the controlled source-ID endpoint supplied by the server.
                if (photo.status==='LOCAL_SOURCE_FILE_AVAILABLE' && typeof photo.url==='string' && photo.url.startsWith('/api/v1/harbour-photo?')) {
                    const figure=add(article,'figure',''), img=document.createElement('img');img.src=photo.url;img.alt=photo.caption || '원문 연결 사진';img.loading='lazy';img.style.cssText='max-width:100%;max-height:260px;object-fit:contain';
                    img.addEventListener('error',()=>{img.remove();add(figure,'p','사진 원본을 불러오지 못했습니다.');});figure.appendChild(img);add(figure,'figcaption',`원문 연결 사진: ${photo.caption} · 항만 외 주변 안내 사진일 수 있습니다.`);
                } else missingPhotos.push(photo.reference || '원문 사진 기록');
            }
            if (missingPhotos.length) {
                const details=add(article,'details','');
                add(details,'summary',`원본 사진 ${missingPhotos.length}개 미연결`);
                for (const reference of missingPhotos) add(details,'p',reference);
            }
            const source=add(article,'details','');add(source,'summary','출처 상세');
            remember(source,`${cardKey}:source`);
            add(source,'p',`출처: ${card.source_file || '경로 미기록'} · 원천 객체 ${card.source_id}`);
            if(card.source_sha256) add(source,'small',`원천 SHA-256: ${card.source_sha256}`);
            add(article,'p',(card.limitations || []).join(' '));
        }
        host.appendChild(box);
    }
    return {render};
})();
