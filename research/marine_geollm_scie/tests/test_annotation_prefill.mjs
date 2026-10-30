import test from 'node:test';
import assert from 'node:assert/strict';
import {validateAiRows,cellText,fieldRows} from '../runners/annotation_prefill_helpers.mjs';

test('AI prefill refuses human approved or GOLD inputs',()=>{
 const row={case_id:'a',annotation_status:'DRAFT',review_kind:'AI_PRE_REVIEW',human_approval:false};
 validateAiRows([row],['a']);
 assert.throws(()=>validateAiRows([{...row,human_approval:true}]));
 assert.throws(()=>validateAiRows([{...row,annotation_status:'GOLD'}]));
 assert.throws(()=>validateAiRows([row],['b']));
});
test('every extra field remains fully reconstructable',()=>{
 const long='한글🙂'.repeat(300);
 const rows=fieldRows([{case_id:'a',extra_reason:long,human_approval:false,source_materials:[]}]);
 assert.equal(rows.filter(r=>r[1]==='extra_reason').map(r=>r[3]).join(''),long);
 assert.equal(rows.find(r=>r[1]==='human_approval')[3],'false');
 assert.match(cellText(long),/전체 원문/);
 assert.match(cellText(null),/미확정/);
});
