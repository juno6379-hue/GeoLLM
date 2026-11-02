const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
test('same-request refresh preserves expansion; a new query resets it',()=>{
 const make=tag=>({tag,children:[],style:{},events:{},textContent:'',appendChild(v){this.children.push(v);},addEventListener(k,fn){this.events[k]=fn;}});
 const ctx={window:{},document:{createElement:make}};
 vm.runInNewContext(fs.readFileSync('services/orchestrator/static/harbour-evidence.js','utf8'),ctx);
 const cards=[{name:'북항',source_id:'s',fields:[{label:'소개',field:'INTRODU',text:'원문 일부'}]}];
 const host=make('host');ctx.window.HarbourEvidence.render(host,cards,1);
 const card=host.children[0].children.find(e=>e.className==='harbour-source-card');
 card.open=true;card.events.toggle();
 const field=card.children.find(e=>e.tag==='details');field.open=true;field.events.toggle();
 const same=make('host');ctx.window.HarbourEvidence.render(same,cards,1);
 const restored=same.children[0].children.find(e=>e.className==='harbour-source-card');
 assert(restored.open);assert(restored.children.find(e=>e.tag==='details').open);
 const next=make('host');ctx.window.HarbourEvidence.render(next,cards,2);
 assert.equal(next.children[0].children.find(e=>e.className==='harbour-source-card').open,false);
});
test('source card escapes text, does not invent missing photos, uses only controlled URLs',()=>{
 const elements=[];
 const make=tag=>{const el={tag,children:[],style:{},textContent:'',appendChild(v){this.children.push(v);},addEventListener(){}};elements.push(el);return el;};
 const ctx={window:{},document:{createElement:make}};
 vm.runInNewContext(fs.readFileSync('services/orchestrator/static/harbour-evidence.js','utf8'),ctx);
 const host=make('host');
 ctx.window.HarbourEvidence.render(host,[{name:'<script>unsafe</script>',source_id:'s',source_file:'Dataset/a.shp',source_sha256:'a',fields:[{label:'소개',text:'원문'}],unavailable_fields:[{label:'시설'}],photos:[{reference:'missing.jpg',status:'SOURCE_ASSET_UNAVAILABLE'},{status:'LOCAL_SOURCE_FILE_AVAILABLE',url:'https://evil/x.jpg'},{status:'LOCAL_SOURCE_FILE_AVAILABLE',url:'/api/v1/harbour-photo?source_id=s&index=1',caption:'원문1'}]}]);
 assert.equal(elements.filter(e=>e.tag==='img').length,1);
 assert(elements.some(e=>e.textContent==='원본 사진 2개 미연결'));
 assert(elements.some(e=>e.textContent==='missing.jpg'));
 assert(elements.some(e=>e.textContent==='<script>unsafe</script>'));
 assert(elements.some(e=>e.textContent.includes('원천 객체 s')));
 assert.equal(host.children.length,1);
 const card=elements.find(e=>e.className==='harbour-source-card');
 assert.equal(card.tag,'details');assert.equal(card.open,false);
 assert.equal(card.children[0].tag,'summary');
 assert(card.children[0].children.some(e=>e.tag==='strong' && e.textContent==='<script>unsafe</script>'));
 assert(elements.some(e=>e.tag==='summary' && e.textContent==='원문 손상으로 안내 1개 항목 표시 보류'));
 const source=card.children.find(e=>e.tag==='details' && e.children[0]?.textContent==='출처 상세');
 assert(source.children.some(e=>e.textContent.includes('원천 SHA-256: a')));
});

test('four harbour cards stay collapsed with identifying metadata and readable sections',()=>{
 const make=tag=>({tag,children:[],style:{},textContent:'',appendChild(v){this.children.push(v);},addEventListener(){}});
 const ctx={window:{},document:{createElement:make}};
 vm.runInNewContext(fs.readFileSync('services/orchestrator/static/harbour-evidence.js','utf8'),ctx);
 const host=make('host');
 ctx.window.HarbourEvidence.render(host,['북항','연안항','남항','내항'].map(name=>({name:`인천항(${name})`,address:'인천',publisher:'원천기관',source_year:2022,source_id:name,fields:[{label:'항해 안내',text:'원문 안내'}],unavailable_fields:[{label:'소개'},{label:'시설'}],photos:Array.from({length:5},(_,i)=>({reference:`${i}.jpg`,status:'SOURCE_ASSET_UNAVAILABLE'}))})));
 const cards=host.children[0].children.filter(e=>e.className==='harbour-source-card');
 assert.equal(cards.length,4);
 for(const card of cards){
  assert.equal(card.open,false);
  assert(card.children[0].children.some(e=>e.textContent==='인천 · 원천기관 · 2022년 원천'));
  const sections=card.children.filter(e=>e.tag==='details');
  assert(sections.some(e=>e.children[0].textContent==='항해 안내' && e.children[1].textContent==='원문 안내'));
  assert(sections.some(e=>e.children[0].textContent==='원본 사진 5개 미연결' && e.children.length===6));
  assert(sections.some(e=>e.children[0].textContent==='원문 손상으로 안내 2개 항목 표시 보류'));
 }
});
