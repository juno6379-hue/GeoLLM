const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function setup(){
 class E{constructor(){this.children=[];this.style={};this.classList={add(){},remove(){}};this.circle={};} appendChild(e){this.children.push(e);} replaceChildren(){this.children=[];} querySelector(s){return s==='.step-circle'?this.circle:this.children.find(e=>e.className==='execution-state');}}
 const dom=Object.fromEntries(['routing','discovery','spatial','ais','knowledge','reasoning','validation','report'].map(x=>['step-'+x,new E()]));dom.intentAnswer=new E();
 const context={window:{},document:{getElementById:id=>dom[id],createElement:()=>new E()}};
 vm.runInNewContext(fs.readFileSync('services/orchestrator/static/execution-view.js','utf8'),context);
 return {ui:context.window.ExecutionView,dom,state:id=>dom['step-'+id].querySelector('.execution-state').textContent,text:()=>{const visit=e=>[e.textContent||'',...e.children.map(visit)].join('\n');return visit(dom.intentAnswer);}};
}
test('fast place clarification persists observed states and never completes unrun agents',()=>{
 const x=setup();x.ui.begin('해운대');x.ui.handle({event:'node_finished',node:'instant_place_lookup',status:'NEEDS_CLARIFICATION'});
 x.ui.handle({event:'completed',final_result:{status:'NEEDS_CLARIFICATION',agent_name:'Spatial Analysis Agent',summary:'후보를 선택해 주세요',structured_result:{location_candidates:[{id:1}]},processing_steps:[{step:'실행 승인',status:'NOT_APPROVED',detail:'NEEDS_USER_INPUT'},{step:'도구 실행',status:'NOT_RUN',detail:'미실행'}]}});
 assert.equal(x.state('routing'),'완료');assert.equal(x.state('spatial'),'후보 확인 대기');assert.equal(x.state('validation'),'미승인');assert.equal(x.state('ais'),'미실행');x.ui.end();assert.equal(x.state('report'),'응답 완료');
 x.ui.acceptComparison({query:'해운대',status:'COMPLETED',judgement:{reason:'행정 지명 후보',location:'해운대'},rankings:{simple_mix:{ranking:['PLACE_LOOKUP'],probabilities:{PLACE_LOOKUP:1}}}});
 assert.match(x.text(),/행정 지명 후보/);assert.match(x.text(),/융합 비교: 지명 찾기/);assert.equal(x.state('validation'),'미승인');
 x.ui.begin('독도');x.ui.acceptComparison({query:'해운대',judgement:{reason:'이전 해석'}});assert.doesNotMatch(x.text(),/이전 해석|행정 지명 후보/);
});
test('positive execution and broken stream remain distinct',()=>{
 const x=setup();x.ui.begin('검색');x.ui.handle({event:'completed',final_result:{status:'COMPLETED',agent_name:'Spatial Analysis Agent',structured_result:{search_execution:{status:'COMPLETED'}},processing_steps:[{step:'실행 승인',status:'APPROVED'},{step:'도구 실행',status:'RECORDED'}]}});assert.equal(x.state('spatial'),'완료');assert.equal(x.state('validation'),'승인');assert.equal(x.state('knowledge'),'미실행');
 x.ui.begin('다음');x.ui.end();assert.equal(x.state('report'),'응답 오류');
});
test('all SSE events reach view before radius early return and no terminal reset remains',()=>{
 const html=fs.readFileSync('services/orchestrator/static/index.html','utf8');
 assert.ok(html.indexOf('ExecutionView.handle(data)')<html.indexOf('RadiusResults.isRadius(data.final_result)'));
 assert.ok(!html.includes('setStep('));
 for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g))new vm.Script(match[1]);
});

test('entrance and nearby explain spatial relations without inventing execution or a default radius',()=>{
 const x=setup();x.ui.begin('부산항 입구 근처 지명을 찾아줘');x.ui.handle({event:'completed',final_result:{status:'NEEDS_CLARIFICATION',error_code:'EXTERNAL_PLACE_CANDIDATES',structured_result:{location_text:'부산항 입구',location_candidates:[{id:'x'}]}}});
 assert.match(x.text(),/항만 전체 영역이나 중심점으로 대체하지/);assert.match(x.text(),/확정된 검색 반경이 없습니다/);assert.match(x.text(),/후보의 좌표가 미확정/);assert.match(x.text(),/실행 결과는 아닙니다/);
 x.ui.begin('부산항 근처 3000m 지명');x.ui.handle({event:'completed',final_result:{status:'NEEDS_CLARIFICATION',error_code:'LOCATION_UNCONFIRMED',structured_result:{location_text:'부산항',distance_m:3000}}});assert.match(x.text(),/반경은 3000m/);assert.doesNotMatch(x.text(),/확정된 검색 반경이 없습니다/);
});
