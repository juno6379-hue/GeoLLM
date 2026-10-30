import fs from 'node:fs/promises';
import crypto from 'node:crypto';
import path from 'node:path';
import { parseArgs } from 'node:util';
import { AI_BANNER, validateAiRows, cellText, fieldRows } from './annotation_prefill_helpers.mjs';

const { values } = parseArgs({ options: {
  'input-dir': { type: 'string' }, 'output-dir': { type: 'string' },
  'ai-prefill': { type: 'boolean', default: false },
  assignment: { type: 'string' },
  render: { type: 'boolean', default: false }, help: { type: 'boolean', default: false },
} });
if (values.help) {
  console.log('Usage: node export_annotation_workbooks.mjs --input-dir <review export> --output-dir <new output> [--render] [--ai-prefill]');
  console.log('Environment alternatives: SCIE_ANNOTATION_INPUT_DIR, SCIE_ANNOTATION_OUTPUT_DIR');
  process.exit(0);
}
const inputArg = values['input-dir'] || process.env.SCIE_ANNOTATION_INPUT_DIR;
const outputArg = values['output-dir'] || process.env.SCIE_ANNOTATION_OUTPUT_DIR;
if (!inputArg || !outputArg) throw new Error('Explicit input-dir and output-dir are required. Use --help.');
const { Workbook, SpreadsheetFile } = await import('@oai/artifact-tool');

const root=path.resolve(inputArg);
const out=path.resolve(outputArg);
await fs.mkdir(out, { recursive: true });
const text=await fs.readFile(`${root}/reviewer_A/annotations_DRAFT.jsonl`,'utf8');
const rows=text.trim().split('\n').map(JSON.parse);
const aiMode=values['ai-prefill'];
const suffix=aiMode?'AI사전검토':'DRAFT';
const assignments=values.assignment?[values.assignment]:['검수자A','검수자B','합의검토'];
if(assignments.some(a=>!['검수자A','검수자B','합의검토'].includes(a)))throw new Error('Unknown assignment');
const assignmentRows={'검수자A':rows};
const inputTexts={'검수자A':text};
if(aiMode){
 validateAiRows(rows);
 for(const [assignment,file] of [['검수자B','reviewer_B/annotations_DRAFT.jsonl'],['합의검토','adjudication_DRAFT.jsonl']]){
  inputTexts[assignment]=await fs.readFile(path.join(root,file),'utf8');
  assignmentRows[assignment]=inputTexts[assignment].trim().split('\n').map(JSON.parse);
  validateAiRows(assignmentRows[assignment],rows.map(r=>r.case_id));
 }
 for(const r of assignmentRows['검수자B']){
  const original=rows.find(x=>x.case_id===r.case_id);
  if(r.query!==original.query || r.provenance?.benchmark_sha256!==original.provenance?.benchmark_sha256 || r.provenance?.source_packet_sha256!==original.provenance?.source_packet_sha256)
   throw new Error('A/B original query or provenance mismatch');
 }
}
if (!rows.length || rows.some(r => r.annotation_status !== 'DRAFT')) throw new Error('Expected nonempty DRAFT review forms');
for (const assignment of assignments) {
  try {
    await fs.access(path.join(out, `${assignment}_${rows.length}사례_${suffix}.xlsx`));
  } catch (error) { if (error.code === 'ENOENT') continue; throw error; }
  throw new Error('Refusing to overwrite an existing workbook. Choose a new output directory.');
}
const digest=s=>crypto.createHash('sha256').update(s).digest('hex');
const guide=aiMode?[
 ['상태',AI_BANNER],['검토 성격','A/B와 합의는 AI 사전검토 역할입니다. 실제 독립 인간 전문가 2인 검수나 인간 합의를 뜻하지 않습니다.'],
 ['사용자 검토','제시한 근거와 미확정 사유를 확인하고 별도로 승인 여부를 판단하십시오. human_approval=false를 유지합니다.'],
 ['통계 사용','이 자료로 학술적 검수자 간 kappa·정확도·EVQSR을 계산하지 않습니다.'],
 ['입력 근거','제공된 AI 사전검토 JSONL을 표시합니다. 모델 계획 예측이나 답변을 주석으로 복사하지 않습니다.'],
 ['전체 필드','주요 셀은 긴 내용을 요약 표시할 수 있습니다. 입력필드전체 시트에서 같은 사례·필드의 분할 순서를 이어 읽으면 전체 내용입니다.'],
 ['원문 근거','근거 시트는 source_materials 원문을 240자씩 나누고 경로·hash를 보존합니다.'],
 ['미확정','공간 oracle 등 미검증 항목은 미확정으로 유지합니다. null은 오류나 0이 아닙니다.'],
 ['자동 승인 없음','annotation_status=DRAFT, review_kind=AI_PRE_REVIEW, human_approval=false. GOLD 파일과 원래 빈 Excel 양식을 수정하지 않습니다.'],
 ['표본','원문18개 파일럿 사례를 유지하며 독립 holdout이나 승인 GOLD로 간주하지 않습니다.'],
 ['benchmark SHA256',rows[0].provenance?.benchmark_sha256??'미기록'],
 ['source packet SHA256',rows[0].provenance?.source_packet_sha256??'미기록'],
]:[
 ['목적','독립 전문가 검수용 빈 양식. 노란색 칸에만 작성하십시오.'],
 ['검수자 지정','사용자가 지정한 검수자A/B는 각자 받은 파일에 이름 또는 식별자와 검수일을 작성합니다.'],
 ['독립 검수','서로의 검수 결과와 모델 답변을 보기 전에 각자 판단합니다. 파일을 별도로 배포하십시오.'],
 ['DRAFT 유지','작성 완료 후에도 상태는 DRAFT로 유지합니다. Excel 작성은 GOLD 승인이 아닙니다.'],
 ['정답 미리보기 없음','모델 답변, 자동 예상답변, 순위, 정답 제안을 첨부하지 않았습니다.'],
 ['근거 해석','FC 및 실제 KG 관계 원문입니다. 원천에 관계가 있다는 사실만으로 의미 정합성이 보장되지는 않습니다.'],
 ['빈 근거','자료가 검색되지 않았다는 뜻이며 관련 사실이나 표준이 없다는 뜻은 아닙니다.'],
 ['원문 읽기','근거 시트는 원문을 순번별 240자 이하로 나눴습니다. 같은 사례와 자료구분의 순서대로 연결하면 원문이 됩니다.'],
 ['공간 정답','동결된 실제 공간 원본과 독립 SQL·객체 ID 검증 후에만 작성합니다. 모르면 빈칸으로 두십시오.'],
 ['근거 추가','독립 확인한 공식 원천의 문서판·위치·SHA256를 정답근거 칸에 추가하십시오.'],
 ['작성 후 순서','A/B 독립 제출 → 원본 보존 및 해시 계산 → 불일치 대조 → 합의/제3검토 → 담당자 수동 승인'],
 ['자동 승격 없음','이 파일에는 GOLD 자동반영·점수계산·DB연결·매크로가 없습니다. 기존 GOLD 파일은 유지됩니다.'],
 ['holdout 금지','18개 질의는 기존 파일럿에 노출됐습니다. 독립 holdout으로 재사용하지 마십시오.'],
 ['결측과 0 구분','미검수·미측정은 빈칸입니다. 실제 0이나 정상 빈 결과는 독립 근거와 함께 명시합니다.'],
 ['승인 범위','단일 intent 이름보다 필수 작업, 허용 capability 조합, 입출력 계약, 실제 근거를 함께 검토합니다.'],
 ['원본 JSONL SHA256',digest(text)],
 ['benchmark SHA256',rows[0].provenance.benchmark_sha256],
 ['source packet SHA256',rows[0].provenance.source_packet_sha256],
];
function evidenceFor(materialRows){
const evidence=[];
for(const row of materialRows){
 for(const material of row.source_materials){
  const content=Array.from(material.source_text);
  const paths=[...new Set(material.sources.map(s=>s.path))].join('\n');
  const hashes=[...new Set(material.sources.map(s=>s.sha256))].join('\n');
  for(let i=0;i<Math.max(content.length,1);i+=240){
   evidence.push([row.case_id,material.material_type,Math.floor(i/240)+1,
    content.slice(i,i+240).join(''),paths,hashes,material.source_text_sha256]);
  }
 }
}
return evidence;
}
const evidence=evidenceFor(rows);
function writeTable(wb,name,header,data,widths){
 const s=wb.worksheets.add(name);s.showGridLines=false;
 const n=data.length+1,cols=header.length;
 s.getRangeByIndexes(0,0,n,cols).values=[header,...data];
 const all=s.getRangeByIndexes(0,0,n,cols);
 all.format.font={name:'Arial',size:11};all.format.verticalAlignment='top';all.format.wrapText=true;
 all.format.rowHeight=72;
 const h=s.getRangeByIndexes(0,0,1,cols);
 h.format.fill='#263B52';h.format.font={name:'Arial',size:11,bold:true,color:'#FFFFFF'};
 h.format.rowHeight=40;
 for(let c=0;c<cols;c++)s.getRangeByIndexes(0,c,n,1).format.columnWidth=widths[c]??26;
 s.freezePanes.freezeRows(1);s.freezePanes.freezeColumns(1);
 return s;
}
for(const assignment of assignments){
 const wb=Workbook.create();let main;
 const currentRows=aiMode?assignmentRows[assignment]:rows;
 const workbookEvidence=aiMode?evidenceFor(currentRows.map(r=>({...r,source_materials:r.source_materials??rows.find(x=>x.case_id===r.case_id)?.source_materials??[]}))):evidence;
 if(aiMode){
  const notice=writeTable(wb,'AI 사전검토 안내',['항목','내용'],[
   ['중요',AI_BANNER],['역할',assignment+' — AI 역할이며 인간 검수자 신원이 아닙니다.'],
   ['승인','human_approval=false / annotation_status=DRAFT'],
   ['입력 JSONL SHA256',digest(inputTexts[assignment])],
   ['기준', '원문·근거·미확정 사유를 사용자 확인 후 승인 대기. 학술 kappa 계산 없음.']],[30,115]);
  notice.getRange('A2:B2').format.fill='#FFF2CC';notice.getRange('A2:B2').format.font={name:'Arial',size:14,bold:true,color:'#9C0006'};
  const headers=['사례 ID','원문 질의','AI 상태','검토 주체·시각','의도·개념·Feature·속성·관계','QEC 필요 필드','기대 실행 행동','허용 대안','공간 정답 상태','근거·출처','미확정 사유·검토 메모','합의·불일치'];
  main=writeTable(wb,assignment==='합의검토'?'AI 합의안':'AI 검토안',headers,currentRows.map(r=>[
   r.case_id,r.query??rows.find(x=>x.case_id===r.case_id)?.query,AI_BANNER,
   cellText({reviewer:r.annotator_id??r.adjudicator_id??r.reviewer_assignment,reviewed_at:r.reviewed_at??r.adjudicated_at}),
   cellText(r.semantics??r.resolution?.semantics),cellText(r.qec_fields??r.resolution?.qec_fields),
   cellText(r.expected_execution_behavior??r.resolution?.expected_execution_behavior),cellText(r.acceptable_alternatives??r.resolution?.acceptable_alternatives),
   cellText(r.spatial_oracle??r.resolution?.spatial_oracle),cellText(r.required_evidence??r.resolution_sources),
   cellText({uncertainties:r.uncertainties,review_notes:r.review_notes}),cellText({disagreement_fields:r.disagreement_fields,resolution:r.resolution,adjudication_status:r.adjudication_status})
  ]),[23,52,38,36,62,62,48,48,48,68,68,68]);
  main.getRangeByIndexes(1,0,currentRows.length,headers.length).format.rowHeight=250;
  main.getRange(`C2:C${currentRows.length+1}`).format.fill='#FFF2CC';
  const fields=fieldRows(currentRows);
  const detail=writeTable(wb,'입력필드전체',['사례 ID','입력 필드','분할 순번','전체 입력값 (순번대로 연결)'],fields,[23,40,12,110]);
  detail.getRangeByIndexes(1,0,fields.length,4).format.rowHeight=120;
 }else if(assignment==='합의검토'){
  const headers=['사례 ID','원문 질의','상태(유지)','합의 검토자','검토일','A 제출파일 SHA256','B 제출파일 SHA256','불일치 항목','합의 결과','합의 근거·출처','추가 검토사항','수동 승인 기록'];
  main=writeTable(wb,'합의작성',headers,rows.map(r=>[r.case_id,r.query,'DRAFT',null,null,null,null,null,null,null,null,null]),[23,52,16,22,18,30,30,40,48,48,40,40]);
  main.getRange(`D2:L${rows.length+1}`).format.fill='#FFF2CC';main.getRange(`C2:C${rows.length+1}`).dataValidation={rule:{type:'list',values:['DRAFT']}};
 }else{
  const headers=['사례 ID','원문 질의','범주','동등표현 그룹','상태(유지)','검수자 식별자','검수일','의도·개념·Feature','속성·코드·공간관계·단위·CRS','필요 QEC 필드','기대 실행 행동','허용 대안','공간 정답·독립 검증','필수 정답근거·원천','불확실성·검토메모'];
  main=writeTable(wb,'검수작성',headers,rows.map(r=>[r.case_id,r.query,r.category,r.equivalence_group,'DRAFT',null,null,null,null,null,null,null,null,null,null]),[23,52,10,26,16,22,18,42,48,48,40,40,48,48,40]);
  main.getRange(`F2:O${rows.length+1}`).format.fill='#FFF2CC';main.getRange(`E2:E${rows.length+1}`).dataValidation={rule:{type:'list',values:['DRAFT']}};
 }
 const es=writeTable(wb,'근거',['사례 ID','자료 구분','분할 순번','원문 (순번대로 연결)','원천 경로','원천 SHA256','원문 SHA256'],workbookEvidence,[23,27,12,100,48,68,68]);
 es.getRangeByIndexes(1,0,workbookEvidence.length,7).format.rowHeight=100;
 const gs=writeTable(wb,'작성안내',['항목','내용'],guide,[28,110]);gs.getRange(`A2:B${guide.length+1}`).format.rowHeight=48;
 wb.recalculate();
 const inspection=await wb.inspect({kind:'table',range:`${main.name}!A1:G4`,include:'values,formulas',tableMaxRows:4,tableMaxCols:7,maxChars:1200});
 await fs.writeFile(`${out}/${assignment}_inspect.txt`,inspection.ndjson);
 // Small previews only; A/B share the identical layout.
 if(values.render && assignment!=='검수자B'){
  for(const [sheet,range] of [[main.name,'A1:G4'],['근거','A1:D4'],['작성안내','A1:B5']]){
   const blob=await wb.render({sheetName:sheet,range,scale:1,format:'png'});
   await fs.writeFile(`${out}/${assignment}_${sheet}.png`,new Uint8Array(await blob.arrayBuffer()));
  }
 }
 const file=await SpreadsheetFile.exportXlsx(wb);
 await file.save(`${out}/${assignment}_${rows.length}사례_${suffix}.xlsx`);
 console.log(JSON.stringify({assignment,cases:rows.length,evidence_rows:workbookEvidence.length,review_kind:aiMode?'AI_PRE_REVIEW':'EMPTY_HUMAN_REVIEW_FORM'}));
}
await fs.writeFile(`${out}/사용안내_KR.txt`,guide.map(([k,v])=>`${k}: ${v}`).join('\r\n'),'utf8');
if(aiMode){
 const manifest={review_kind:'AI_PRE_REVIEW',human_approval:false,annotation_status:'DRAFT',status:'AI_REVIEW_COMPLETE_HUMAN_APPROVAL_PENDING',cases:rows.length,files:[]};
 for(const assignment of ['검수자A','검수자B','합의검토']){
  const file=`${assignment}_${rows.length}사례_${suffix}.xlsx`;
  manifest.files.push({file,sha256:digest(await fs.readFile(path.join(out,file))),input_jsonl_sha256:digest(inputTexts[assignment])});
 }
 await fs.writeFile(path.join(out,'workbook_manifest.json'),JSON.stringify(manifest,null,2),'utf8');
}
