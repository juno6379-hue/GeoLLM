export const AI_BANNER='AI 사전검토 · 사용자 승인 대기 · GOLD 아님';
export function validateAiRows(rows, expectedIds=null){
 if(!rows.length || rows.some(r=>r.annotation_status!=='DRAFT'||r.review_kind!=='AI_PRE_REVIEW'||r.human_approval!==false))
  throw new Error('AI prefill requires DRAFT, AI_PRE_REVIEW and human_approval=false on every row');
 const ids=rows.map(r=>r.case_id);
 if(new Set(ids).size!==ids.length)throw new Error('Duplicate case IDs');
 if(expectedIds && (ids.length!==expectedIds.length||expectedIds.some(id=>!ids.includes(id))))throw new Error('Reviewer/adjudication case sets differ');
}
export function cellText(value,max=320){
 if(value===undefined||value===null)return '미확정 / 입력 없음';
 const text=typeof value==='string'?value:JSON.stringify(value,null,2);
 return text.length>max?text.slice(0,max)+'\n[요약 표시: 전체 원문은 입력필드전체 시트]':text;
}
export function fieldRows(rows){
 const output=[];
 for(const row of rows){
  for(const [key,original] of Object.entries(row)){
   // Evidence text is reproduced in the evidence sheet; retain every source locator and metadata here.
   const value=key==='source_materials'&&Array.isArray(original)
    ?original.map(({source_text,...metadata})=>({...metadata,source_text_location:'근거 시트의 동일 사례/자료구분 분할순번으로 전체 원문 연결'})):original;
   const text=typeof value==='string'?value:JSON.stringify(value,null,2);
   const chars=Array.from(text??'null');
   for(let at=0;at<Math.max(chars.length,1);at+=240)
    output.push([row.case_id,key,Math.floor(at/240)+1,chars.slice(at,at+240).join('')]);
  }
 }
 return output;
}
