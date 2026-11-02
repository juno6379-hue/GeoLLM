"""Source-only derivation of the 18 development-query grounding annotations.
Never reads model predictions, run results, production state, or holdout inputs.
"""
from pathlib import Path
import hashlib
import json
from collections import Counter

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
BASE = 'research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1'
CONTRACT = BASE + '/answer_contracts.jsonl'
QUERIES = BASE + '/queries.jsonl'
CONDITIONS = 'outputs/scie_rq_v2_audit_20261030/condition_metadata.jsonl'
APPROVAL = 'research/marine_geollm_scie/review/20261102_approved_gold_rescore_v1/approval.json'

def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def readrows(p): return [json.loads(l) for l in (ROOT/p).read_text(encoding='utf-8-sig').splitlines() if l.strip()]
def ptr(obj, path):
    for key in path.strip('/').split('/'):
        key=key.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj

def main():
    cs, qs, cond = readrows(CONTRACT), readrows(QUERIES), readrows(CONDITIONS)
    assert len(cs)==len(qs)==len(cond)==18
    qmap={q['case_id']:q for q in qs}; cmap={c['case_id']:(i+1,c) for i,c in enumerate(cond)}
    approval=json.loads((ROOT/APPROVAL).read_text(encoding='utf-8'))
    assert approval['gold_manifest_sha256']==sha(BASE+'/manifest.json')
    rows=[]
    for line,c in enumerate(cs,1):
        cid=c['case_id']; q=qmap[cid]; condline,meta=cmap[cid]
        queryhash=hashlib.sha256(c['query'].encode()).hexdigest()
        assert q['query']==c['query'] and queryhash==meta['query_sha256']
        atoms=[]
        def ref(path, source=CONTRACT, source_line=line):
            r=dict(path=source,sha256=sha(source),json_pointer=path)
            if source.endswith('.jsonl'): r['jsonl_line']=source_line
            return r
        def add(kind,value,paths,note='',derivation='DIRECT_CONTRACT_VALUE',source=CONTRACT,source_line=line):
            refs=[ref(p,source,source_line) for p in paths]
            atoms.append(dict(atom_id=f'{cid}:a{len(atoms)+1:03}',kind=kind,task_id='query',accepted_values=[value],derivation=derivation,source_refs=refs,note_ko=note))
        def direct(kind,path,note=''): add(kind,ptr(c,path),[path],note)
        # Intent/obligation atoms preserve approved decomposition, but runtime
        # checks, fallback policies and result reporting are not semantic atoms.
        exclude={'resolve_reference','resolve_approved_anchor','verify_coverage','verify_both_target_coverages','report_objects_or_unresolved_reason','report_source_bound_objects','separate_partial_document_answer','disclose_subset_limitations','require_selected_aoi','request_aoi_when_missing'}
        for i,t in enumerate(c['required_task_obligations']):
            if t not in exclude: direct('task_obligation',f'/required_task_obligations/{i}','기존 GOLD의 의미 과업 식별자. 실제 실행 완료 점수가 아니다.')
        doc=c.get('document_scope') or {}
        for i,feature in enumerate(doc.get('selected_feature_codes',[])):
            direct('feature',f'/document_scope/selected_feature_codes/{i}','카탈로그 설명 대상. 구조물·등화 대안은 한 실재 시설에 모두 존재한다는 뜻이 아니다.')
        for i,b in enumerate((doc.get('attribute_scope') or {}).get('bindings',[])):
            add('attribute_binding',{'owner':b['owner'],'attribute':b['attribute']},[f'/document_scope/attribute_scope/bindings/{i}/owner',f'/document_scope/attribute_scope/bindings/{i}/attribute'],'소유 객체/복합속성→속성의 연결. 허용 코드 값·원문 정의 정답은 별도 답안계약에서 평가한다.','CONTRACT_PROJECTION')
        if doc:
            add('standard', {'standard':'S-101','edition':doc['evidence_requirements']['edition']}, ['/document_scope/evidence_requirements/edition','/document_scope/evidence_requirements/source_path'], '표준과 판본을 함께 식별한다.', 'CONTRACT_PROJECTION')
            if c['category']=='Q6':
                evidence=doc['evidence_requirements']
                add('source_binding',{'source_sha256':evidence['source_sha256'],'locators':evidence['locators']},['/document_scope/evidence_requirements/source_sha256','/document_scope/evidence_requirements/locators'],'FC 원천 identity와 주장 대상 locator. 실제 인용지지 여부는 별도 평가.','CONTRACT_PROJECTION')
        qec=c['required_qec_fields']
        if 'slots.location_text' in qec: direct('reference','/required_qec_fields/slots.location_text','GOLD에서 정규화한 장소명; 실제 geometry 검색 성공과 다르다.')
        if 'slots.distance_m' in qec: add('distance_m',int(qec['slots.distance_m']),['/required_qec_fields/slots.distance_m'],'정수 미터로 고정. 예측 추출도 5000.0/5000 및 명시 km를 동일 의미의 정수 미터로 정규화한다.','CONTRACT_PROJECTION')
        short=cid.replace('PILOT_','')
        if short in ['Q3_01','Q5_01']:
            add('requested_object','Lighthouse',['/expected_spatial_behavior/per_target/Lighthouse'],'질의의 시설 개념이며 S-101의 단일 Lighthouse Feature를 뜻하지 않는다.','AI_CANONICALIZATION_PROPOSAL')
        if short in ['Q3_02','Q5_02']:
            add('operator','covers' if short=='Q3_02' else 'dwithin',['/spatial_predicate'],'동결 SQL을 정규 연산명으로 표현. covers는 경계 포함, dwithin은 별도 거리측정 원자를 따른다.','CONTRACT_PROJECTION')
            if short=='Q5_02': add('distance_metric',{'surface':'WGS84_ellipsoid','measurement':'minimum_geometry_to_geometry','reference':'polygon_area','boundary_inclusive':True},['/spatial_predicate','/distance_mode'],'polygon 경계선만의 거리가 아니라 영역과 대상 최소거리이며 내부/겹침은 0이다.','CONTRACT_PROJECTION')
            direct('reference_geometry_id','/reference_geometry/id','동결 부산항 polygon ID. 실행 결과 객체 ID가 아니다.')
            add('reference_crs','EPSG:'+str(c['reference_geometry']['srid']),['/reference_geometry/srid'],'EPSG 접두어 표준 표현. 원본 정수 SRID와 동일하다.','CONTRACT_PROJECTION')
        if short=='Q3_02':
            add('feature','AnchorageArea',['/spatial_gold/AnchorageArea'],'공간 GOLD의 대상 종류 키에서 파생. 객체 목록은 원자에 넣지 않는다.','CONTRACT_PROJECTION')
        if short=='Q3_01':
            idx=c['required_task_obligations'].index('find_nearest')
            add('operator','nearest',[f'/required_task_obligations/{idx}'],'최대 검색반경을 새로 만들지 않는다.','AI_CANONICALIZATION_PROPOSAL')
        if short=='Q3_03':
            direct('feature','/semantic_gold/feature');direct('operator','/semantic_gold/operator')
            add('input_requirement',{'field':'selected_geometry','requirement':c['qec_gold']['selected_geometry']},['/qec_gold/selected_geometry'],'필수 입력 대상을 명시. 현재 없음은 policy 참조로 구분한다.','CONTRACT_PROJECTION')
        if c['category']=='Q4':
            add('requested_object','MarinePlaceName',['/required_task_obligations/1'],'S-101 Feature가 아닌 고정 해양지명 corpus의 지명 레코드.','AI_CANONICALIZATION_PROPOSAL')
            add('operator','dwithin',['/spatial_reference/distance_policy'],'원문 inclusive <=5000m를 정규 연산으로 주석화.','AI_CANONICALIZATION_PROPOSAL')
            direct('reference_geometry_id','/spatial_reference/reference_geometry_source/place_id')
            direct('reference_crs','/spatial_reference/reference_crs')
            add('distance_metric',{'surface':'WGS84_ellipsoid','measurement':'point_to_point','boundary_inclusive':True},['/spatial_reference/distance_policy','/spatial_reference/reference_geometry_source/coordinate_role'],'고정 동도 기준점과 원천 지명 좌표 사이의 포함 경계 지오데식 거리.','CONTRACT_PROJECTION')
        if short in ['Q5_01','Q5_03']:
            idx=next(i for i,t in enumerate(c['required_task_obligations']) if t in ['search_both_targets_5000m','search_wrecks_5000m'])
            add('operator','dwithin',[f'/required_task_obligations/{idx}','/required_qec_fields/slots.distance_m'],'반경 질의의 의미 연산. 범위 밖 판정 때문에 이 의미를 제거하지 않는다.','AI_CANONICALIZATION_PROPOSAL')
        if short=='Q5_02':
            for i,_ in enumerate(c['comparison_gold']['criteria']): direct('comparison_criterion',f'/comparison_gold/criteria/{i}','기존 GOLD에 고정된 비교 축; 실제 비교 결과값을 원자에 넣지 않는다.')
        optional_atoms=[]
        if short in ['Q5_01','Q5_02','Q5_03']:
            import copy
            transformed=[]
            common={'reference','distance_m','operator','reference_geometry_id','reference_crs','distance_metric'}
            targets={'Q5_01':['spatial:lighthouse','spatial:wreck'],'Q5_02':['spatial:AnchorageArea','spatial:RestrictedArea'],'Q5_03':['spatial:wreck']}[short]
            for a in atoms:
                value=a['accepted_values'][0]
                if a['kind'] in common:
                    for task in targets:
                        b=copy.deepcopy(a);b['task_id']=task;transformed.append(b)
                    continue
                if short=='Q5_01':
                    if a['kind']=='standard' or (a['kind']=='feature' and value!='Wreck'):
                        a['task_id']='document:lighthouse';optional_atoms.append(a);continue
                    if a['kind']=='feature':a['task_id']='spatial:wreck'
                    elif a['kind']=='requested_object' or value=='resolve_lighthouse_target_conditions':a['task_id']='spatial:lighthouse'
                    elif value=='provide_per_target_evidence':
                        for task in targets:
                            b=copy.deepcopy(a);b['task_id']=task;transformed.append(b)
                        continue
                    elif value=='search_both_targets_5000m':
                        # Operator/distance atoms attached to each target already
                        # represent the two searches; retain shared conjunction.
                        a['task_id']='query'
                elif short=='Q5_02':
                    if a['kind']=='feature':a['task_id']='spatial:'+value
                    elif a['kind'] in ['comparison_criterion','standard'] or value=='compare_target_results':a['task_id']='comparison'
                else:
                    if a['kind'] in ['attribute_binding','standard'] or value in ['explain_s101_attributes','distinguish_object_values_from_standard_attributes']:
                        a['task_id']='document:Wreck'
                    elif a['kind']=='feature':
                        a['task_id']='spatial:wreck'
                        b=copy.deepcopy(a);b['task_id']='document:Wreck';transformed.append(b)
                    else:a['task_id']='spatial:wreck'
                transformed.append(a)
            atoms=transformed
        for index,a in enumerate(atoms,1):a['atom_id']=f'{cid}:a{index:03}'
        for index,a in enumerate(optional_atoms,1):a['atom_id']=f'{cid}:optional{index:03}'
        task_mapping={task:{'scope':{'query':'whole query/conjunction','spatial:lighthouse':'requested lighthouse facility search, not singleton FC Lighthouse','spatial:wreck':'requested Wreck spatial search','spatial:AnchorageArea':'requested AnchorageArea spatial search','spatial:RestrictedArea':'requested RestrictedArea spatial search','comparison':'compare the two returned target types','document:Wreck':'explicit requested Wreck attribute explanation','document:lighthouse':'optional source-bound lighthouse definition fallback'}[task]} for task in sorted({a['task_id'] for a in atoms+optional_atoms})}
        assert atoms
        for a in atoms+optional_atoms:
            if a['derivation']=='DIRECT_CONTRACT_VALUE': assert a['accepted_values'][0]==ptr(c,a['source_refs'][0]['json_pointer'])
        policy={k:c[k] for k in ['expected_spatial_behavior','expected_behavior','blocker','execution_gold','evaluation_stratum','spatial_condition','scope_notes','optional_document_task'] if k in c}
        rows.append(dict(case_id=cid,query=c['query'],query_sha256=queryhash,equivalence_group=c['equivalence_group'],terminology_condition=meta['terminology_condition'],complexity=meta['complexity'],condition_annotation_status=meta['annotation_status'],condition_source=ref('',CONDITIONS,condline),task_mapping=task_mapping,annotation_status='AI_SOURCE_LINKED_ANNOTATION_COMPLETE_PENDING_REVIEW',human_approval=False,post_hoc=True,holdout_eligible=False,source_contract=ref('',CONTRACT,line),parent_gold_approval=ref('',APPROVAL),atoms=atoms,optional_atoms=optional_atoms,policy_context_not_rq1_atoms=policy,scope_notes=c['scope_notes'],new_canonicalization_review_required=any(a['derivation']=='AI_CANONICALIZATION_PROPOSAL' for a in atoms)))
    (OUT/'gold_atoms.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')
    counts=Counter(a['kind'] for r in rows for a in r['atoms'])
    schema=dict(version='rq1_grounding_annotation.v1',task_ids=sorted({a['task_id'] for r in rows for a in r['atoms']+r['optional_atoms']}),task_id_policy='Single-task queries use query. Q5 target searches use spatial:lighthouse, spatial:wreck, spatial:AnchorageArea, spatial:RestrictedArea; comparison uses comparison; explicit Wreck attribute explanation uses document:Wreck. Optional lighthouse fallback uses document:lighthouse. Public task_mapping per row defines role independent of model-specific subtask names.',kinds=sorted(counts),derivations=['DIRECT_CONTRACT_VALUE','CONTRACT_PROJECTION','AI_CANONICALIZATION_PROPOSAL'],scorer='research/marine_geollm_scie/evaluation/grounding_atoms_v1.py',prediction_policy='Prediction annotation must be independent of GOLD contents. Canonical task vocabulary and extraction rules must be fixed before scoring. Do not fill missing prediction atoms from GOLD.',accepted_values_policy='Canonical JSON values; distance_m is integer metres. Prediction extraction must apply the fixed lossless canonicalization rules before exact scoring; the scorer itself performs no inference. No unvalidated feature aliases.',not_in_rq1=['object result IDs','distance result values','actual SQL execution','coverage approval','real-world completeness','literal definition-text equality','full answer semantic correctness'],human_review_status='New atom representation and canonicalization are AI annotations, not a newly attested human review; existing approval covers parent GOLD only.')
    schema['canonicalization']={'operator':{'covers':['covers','ST_Covers(reference,target)'],'dwithin':['dwithin','ST_DWithin(target::geography,reference::geography,2000,true)'],'nearest':['nearest','find_nearest'],'intersects':['intersects','ST_Intersects']},'distance_m':{'json_type':'integer','rules':['finite exact whole metres: 5000 and 5000.0 become integer 5000','explicit km multiplied by 1000; only exact integral metre result admitted','no missing-distance default; no rounding']},'reference_crs':{'canonical':'EPSG:4326','explicit_literals':['EPSG:4326',4326,'4326'],'rules':['only explicit same CRS identifier conversion; never infer missing CRS or transform geometry']},'limits':['direction/reference arguments of spatial relations are preserved','Q5_02 distance_metric distinguishes polygon-area minimum geodesic distance from boundary-line distance','no model output used to choose canonical forms']}
    (OUT/'schema.json').write_text(json.dumps(schema,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    text=['# RQ1 개발 18문항 GOLD grounding atom 주석','', '**작성: 18/18 완료. 실제 RQ1 Semantic F1·Strict Match·CI: 미측정.** 기존 승인 GOLD에서 파생한 AI 원자 주석이다. 새 원자 표현·정규화에 대한 인간 검수 완료를 생성하지 않는다. 포인터·해시의 기계 검증은 의미의 독립 검수가 아니다. 모델 답변·홀드아웃은 읽지 않았다.','', '## 평가 경계','', '- 원자 값은 covers/dwithin/nearest/intersects, 정수 미터, EPSG:4326로 정규화한다. 명시 5000.0과 5000은 동일 의미다. schema.json의 무손실 변환만 예측 추출에 허용하며 누락 슬롯을 추론하지 않는다.','- 의미 과업, 대상 Feature, 속성 소유 연결, 연산, 기준 위치·거리·입력 문맥을 평가한다. 원문 정의의 문자열 일치를 의미 정확도로 쓰지 않는다.','- 단일 과업은 `query`, Q5는 대상별 `spatial:*`와 `comparison`/`document:Wreck`로 분리한다. 거리·기준·연산은 각 공간 하위과업에 귀속한다. 공개 task_mapping은 모델 자체 subtask 이름과 무관하다.','- 실행 여부·결과 객체집합·안전중단·공간 정답성은 기존 GOLD 별도 계약이다. 범위 밖 독도 요청도 질문 의미 원자는 유지한다.','- `Lighthouse`는 requested_object이며 S-101 단일 Feature를 신설하지 않는다. 구조물/등화의 조건부 설명은 기존 GOLD를 따른다.','- 조건 라벨은 기존 사후 metadata를 그대로 연결했다. UNSEEN_SYNONYM을 새로 만들지 않았다. Q4 영문 일반표현의 용어축 미분류도 유지한다.','', f'총 원자 **{sum(counts.values())}개**. 종류별: '+', '.join(f'{k}={v}' for k,v in sorted(counts.items())), '', '## 사례별 근거와 원자','']
    for r in rows:
        text += [f"### {r['case_id']} — {r['query']}",'',f"조건: {', '.join(r['terminology_condition']) or '용어축 미분류'} / 동등군: `{r['equivalence_group']}` / 원자 {len(r['atoms'])}개",'',f"근거: `{CONTRACT}` line {r['source_contract']['jsonl_line']} · SHA256 `{r['source_contract']['sha256']}`",'', '| 원자 | 종류 | 정답 허용값 | 파생 | 원본 JSON pointer |','|---|---|---|---|---|']
        for a in r['atoms']:
            val=json.dumps(a['accepted_values'][0],ensure_ascii=False).replace('|','\\|')
            text.append(f"| {a['atom_id'].split(':')[-1]} ({a['task_id']}) | {a['kind']} | `{val}` | {a['derivation']} | "+'<br>'.join('`'+x['json_pointer']+'`' for x in a['source_refs'])+' |')
        if r['optional_atoms']: text += ['', '선택적 보충 원자(주 RQ1 분모 제외): '+', '.join(a['kind']+':'+json.dumps(a['accepted_values'][0],ensure_ascii=False) for a in r['optional_atoms'])]
        text += ['', '해석 범위: '+'; '.join(r['scope_notes'] or ['기존 GOLD 범위 유지.']), '']
    text += ['## 다음 평가 연결','', '1. 새 원자 표현과 예측 추출 규칙을 독립 검토한다.','2. B1/B2의 실제 원본 답변에서 같은 schema의 예측 원자를 별도 주석화하고 원문 span/hash를 고정한다. GOLD에서 누락값을 채우지 않는다.','3. 조건별 F1·Strict Match와 동등군 paired CI를 계산한다. 18개는 개발셋이고 사후 조건 라벨이므로 탐색적 결과로 표시한다.','4. 운영 코드 변경 후의 방법 비교는 새 동결 전체 실행으로 수행한다. 기존 v6 재주석은 기존 원본 분석일 뿐 새 시스템 성능이 아니다.','']
    (OUT/'annotation_KR.md').write_text('\n'.join(text),encoding='utf-8')
    sources=[CONTRACT,QUERIES,CONDITIONS,APPROVAL,BASE+'/manifest.json']
    manifest=dict(version='rq1_grounding_annotation.v1',task_ids=sorted({a['task_id'] for r in rows for a in r['atoms']+r['optional_atoms']}),status='ANNOTATED_18_PENDING_REVIEW_AND_PREDICTION_EXTRACTION',case_count=18,atom_count=sum(counts.values()),optional_atom_count=sum(len(r['optional_atoms']) for r in rows),kind_counts=dict(counts),metric_status='NOT_MEASURED',human_approval=False,parent_gold_approval_status=approval['status'],new_annotation_is_independent_human_review=False,model_outputs_read=False,holdout_read=False,sources=[dict(path=p,sha256=sha(p)) for p in sources],files={name:hashlib.sha256((OUT/name).read_bytes()).hexdigest() for name in ['gold_atoms.jsonl','schema.json','annotation_KR.md','build.py']})
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':18,'atoms':sum(counts.values()),'kinds':dict(counts)},ensure_ascii=False))
if __name__=='__main__':main()
