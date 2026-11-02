"""Prepare reserved prospective holdout; never call a model or operational service."""
import argparse, copy, csv, hashlib, json, re, subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from research.marine_geollm_scie.runners.dokdo_spatial_reference import coordinate_pair, vincenty
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'research/marine_geollm_scie/benchmark/holdout_20261102_v1'
DEV=ROOT/'research/marine_geollm_scie/benchmark/gold_v2_immutable_20261101_v1'
FC=ROOT/'outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml'
CSV=ROOT/'Dataset/해양수산부_공동활용체계_해양지명_20221231.csv'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def jsonl(p,xs):p.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in xs),encoding='utf-8')
def compact(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def evaluation_gate(folder,receipt=None):
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'));errors=[]
    for name,h in manifest['files'].items():
        p=folder/name
        if not p.is_file() or sha(p)!=h:errors.append('BENCHMARK_HASH_MISMATCH:'+name)
    source_manifest=json.loads((folder/'source_manifest.json').read_text(encoding='utf-8'))
    for source in source_manifest['sources']:
        p=ROOT/source['path']
        if not p.is_file() or sha(p)!=source['sha256']:errors.append('CURRENT_SOURCE_HASH_MISMATCH:'+source['path'])
    q=rows(folder/'queries.jsonl');dev=rows(DEV/'queries.jsonl')
    if {x['case_id'] for x in q}&{x['case_id'] for x in dev}:errors.append('DEVELOPMENT_ID_OVERLAP')
    norm=lambda s:re.sub(r'\s+','',s).casefold()
    if {norm(x['query']) for x in q}&{norm(x['query']) for x in dev}:errors.append('DEVELOPMENT_QUERY_OVERLAP')
    if {x['equivalence_group'] for x in q}&{x['equivalence_group'] for x in dev}:errors.append('DEVELOPMENT_GROUP_OVERLAP')
    receipt=receipt or {}
    if receipt.get('benchmark_manifest_sha256')!=sha(folder/'manifest.json'):errors.append('FINAL_FREEZE_BENCHMARK_BINDING_REQUIRED')
    if receipt.get('human_holdout_gold_approved') is not True:errors.append('NEW_HOLDOUT_HUMAN_GOLD_APPROVAL_REQUIRED')
    if not receipt.get('reviewer_ids') or not receipt.get('approved_at'):errors.append('HUMAN_REVIEW_PROVENANCE_REQUIRED')
    for key in ('system_source_sha256','model_digest','prompt_sha256','data_snapshot_sha256','evaluation_code_sha256'):
        if not re.fullmatch(r'[a-fA-F0-9]{64}',str(receipt.get(key,''))):errors.append('FINAL_FREEZE_REQUIRED:'+key)
    for key in ('system_source_sha256','prompt_sha256','data_snapshot_sha256','evaluation_code_sha256'):
        path_value=(receipt.get('freeze_artifact_paths') or {}).get(key)
        p=Path(path_value) if isinstance(path_value,str) and path_value else None
        if not p or not p.is_file() or sha(p)!=receipt.get(key):errors.append('VERIFIED_FREEZE_ARTIFACT_REQUIRED:'+key)
    model_path=receipt.get('model_receipt_path')
    model_file=Path(model_path) if isinstance(model_path,str) and model_path else None
    if not model_file or not model_file.is_file() or sha(model_file)!=receipt.get('model_receipt_sha256'):
        errors.append('VERIFIED_MODEL_RECEIPT_REQUIRED')
    else:
        try:
            model=json.loads(model_file.read_text(encoding='utf-8'))
            if model.get('model_digest')!=receipt.get('model_digest') or model.get('verified') is not True:errors.append('MODEL_DIGEST_RECEIPT_MISMATCH')
        except (ValueError,UnicodeError):errors.append('MODEL_RECEIPT_INVALID')
    if receipt.get('no_holdout_used_for_tuning') is not True:errors.append('HOLDOUT_NON_TUNING_ATTESTATION_REQUIRED')
    if receipt.get('system_frozen') is not True:errors.append('FINAL_SYSTEM_FREEZE_REQUIRED')
    if not receipt.get('freeze_at'):errors.append('FREEZE_DATE_REQUIRED')
    return {'evaluation_ready':not errors,'errors':errors,'evaluated':False}

def prepare():
    if OUT.exists():raise FileExistsError('Existing holdout preserved; use a new version')
    devbefore={p.name:sha(p) for p in DEV.iterdir() if p.is_file()}
    root=ET.parse(FC).getroot();ns={'f':root.tag[1:].split('}')[0],'b':'http://www.iho.int/S100Base/5.0'}
    feats={n.findtext('f:code',namespaces=ns):n for n in root.findall('.//f:S100_FC_FeatureType',ns)}
    queries=[];gold=[]
    def add(query,kind,answer,context=None):
        cid=f'HOLDOUT_{len(queries)+1:02}'
        queries.append(dict(case_id=cid,query=query,category=kind,equivalence_group=cid,split='prospective_holdout',context=context or {}))
        gold.append(dict(case_id=cid,expected=answer,human_review_complete=False,preparation='AI_AUTHORED_SOURCE_VERIFIED',model_evaluation_executed=False))
    for code in ['DepthArea','DredgedArea','Coastline','CableSubmarine','Fairway','SeabedArea']:
        n=feats[code];loc=f".//f:S100_FC_FeatureType[f:code='{code}']";assert len(root.findall(loc,ns))==1
        add(f'S-101 2.0.0의 {code} 정의와 허용 geometry를 원문 근거와 함께 설명해 주세요.','DOCUMENT_DEFINITION',
            dict(feature=code,definition=n.findtext('f:definition',namespaces=ns),permitted_primitives=[x.text for x in n.findall('f:permittedPrimitives',ns)],source_sha256=sha(FC),locator=loc,locator_namespaces=ns))
    for code,attr in [('Sounding','qualityOfVerticalMeasurement'),('MooringBuoy','buoyShape'),('Obstruction','waterLevelEffect')]:
        n=feats[code];bs=[b for b in n.findall('f:attributeBinding',ns) if b.find('f:attribute',ns).get('ref')==attr];assert len(bs)==1
        b=bs[0];loc=f".//f:S100_FC_FeatureType[f:code='{code}']/f:attributeBinding"
        verified=[v for v in root.findall(loc,ns) if v.find('f:attribute',ns).get('ref')==attr]
        assert len(verified)==1 and verified[0] is b
        add(f'{code}의 {attr} 속성은 필수인가요? 이 객체에 허용된 코드와 근거를 제시해 주세요.','ATTRIBUTE_BINDING',
            dict(feature=code,attribute=attr,minimum=int(b.findtext('f:multiplicity/b:lower',namespaces=ns)),permitted_values=[x.text for x in b.findall('f:permittedValues/f:value',ns)],binding_xml=ET.tostring(b,encoding='unicode'),source_sha256=sha(FC),locator=loc,locator_namespaces=ns,locator_filter={'child':'f:attribute','attribute':'ref','equals':attr},unique_locator_verified=True))
    with CSV.open(encoding='cp949',newline='') as f:raw=list(csv.DictReader(f))
    points=[]
    for line,r in enumerate(raw,2):
        lat,_=coordinate_pair(r['도분초위도1'],r['도분초위도2'],True);lon,_=coordinate_pair(r['도분초경도1'],r['도분초경도2'],False)
        points.append(dict(id=r['공간정보일련번호'],name=r['지명명'],location_evidence={'column':'해양지위치정보','value':r['해양지위치정보'],'csv_line':line,'source_sha256':sha(CSV)},lat=lat,lon=lon,csv_line=line))
    assert len({p['id'] for p in points})==len(points)
    anchors=[(126.6,37.4),(129.2,37.8),(126.5,33.5),(126.4,34.7),(128.5,34.8),(129.4,36.0)]
    payload=json.dumps(points,ensure_ascii=True);centers=json.dumps([{'idx':i,'lon':x,'lat':y} for i,(x,y) in enumerate(anchors)])
    sql=f"""BEGIN READ ONLY;
SET LOCAL statement_timeout='30000';
WITH p AS (SELECT * FROM json_to_recordset($pts${payload}$pts$::json) AS x(id text,lat float8,lon float8)),
a AS (SELECT * FROM json_to_recordset($anc${centers}$anc$::json) AS x(idx int,lat float8,lon float8)),
d AS (SELECT a.idx,p.id,ST_Distance(ST_SetSRID(ST_MakePoint(p.lon,p.lat),4326)::geography,ST_SetSRID(ST_MakePoint(a.lon,a.lat),4326)::geography,true) distance_m FROM p CROSS JOIN a)
SELECT json_build_object('postgis_version',PostGIS_Full_Version(),'distances',(SELECT json_agg(d ORDER BY idx,id) FROM d));
ROLLBACK;
"""
    response=subprocess.run(['docker','exec','-i','marine-scie-pilot-db','psql','-X','-q','-A','-t','-v','ON_ERROR_STOP=1','-U','postgres','-d','scie_pilot'],input=sql,text=True,capture_output=True,timeout=45,check=True)
    measured=json.loads(response.stdout.strip());dist={(d['idx'],d['id']):d['distance_m'] for d in measured['distances']};assert len(dist)==6*len(points)
    maxerr=0
    for i,(lon,lat) in enumerate(anchors):
        for p in points:maxerr=max(maxerr,abs(dist[i,p['id']]-vincenty(lat,lon,p['lat'],p['lon'])))
    assert maxerr<0.01
    oracle=[]
    for i,(lon,lat) in enumerate(anchors):
        order=sorted(points,key=lambda p:(dist[i,p['id']],int(p['id'])))
        mode=['nearest','radius','annulus','top_k','radius','radius'][i]
        selected=order[:1] if mode=='nearest' else order[:3] if mode=='top_k' else [p for p in order if (5000<dist[i,p['id']]<=25000 if mode=='annulus' else dist[i,p['id']]<=20000)]
        assert selected and not {p['id'] for p in selected}&set(map(str,range(44,55)))
        answer=dict(operator=mode,anchor={'longitude':lon,'latitude':lat,'crs':'EPSG:4326'},distance_mode='WGS84_ELLIPSOIDAL',source_sha256=sha(CSV),source_scope='2022 CSV records only; not complete real-world inventory',object_ids=['mof_marine_names_20221231:'+p['id'] for p in selected],objects=[dict(p,distance_m=dist[i,p['id']]) for p in selected],distance_tolerance_m=0.01,facility_deduplication='SOURCE_RECORD_ID_ONLY',tie_policy='Exact geodesic distance ascending then numeric source ID ascending',k=3 if mode=='top_k' else 1 if mode=='nearest' else None,radius_m=25000 if mode=='annulus' else 20000 if mode=='radius' else None,inner_radius_exclusive_m=5000 if mode=='annulus' else None)
        request={'nearest':'거리 제한 없이 가장 가까운 해양지명 1개','radius':'반경 20km 이내 해양지명 전체','annulus':'5km 초과 25km 이하 거리대의 해양지명 전체','top_k':'거리 제한 없이 가장 가까운 해양지명 3개'}[mode]
        extra=' 각 원본 행의 지명명과 위치 설명 근거도 연결해 주세요.' if i==5 else ''
        add(f'2022 해양지명 CSV만 사용하여 EPSG:4326 경도 {lon}, 위도 {lat}에서 {request}와 거리·원본 ID를 알려 주세요.'+extra,'SPATIAL_SOURCE_BOUND',answer,{'reference_geometry':{'type':'Point','coordinates':[lon,lat]},'crs':'EPSG:4326'})
        oracle.append(dict(case_id=queries[-1]['case_id'],**answer))
    add('두 선택 영역의 해양지명 집합 차이를 비교해 주세요.','MISSING_INPUT',dict(status='NEEDS_USER_INPUT',blocker='MISSING_SECOND_REFERENCE_GEOMETRY',execution_attempted=False,execution_started=False,tool_called=False,sql_executed=False),{'selected_areas':[{'type':'Polygon','coordinates':[[[126.4,37.2],[126.6,37.2],[126.6,37.4],[126.4,37.4],[126.4,37.2]]]}],'crs':'EPSG:4326'})
    add('지도에서 받은 좌표 [126.6, 37.4]를 기준으로 10km 해양지명을 찾아 주세요. 좌표계 정보는 전달받지 못했습니다.','MISSING_INPUT',dict(status='NEEDS_USER_INPUT',blocker='MISSING_CRS',execution_attempted=False,execution_started=False,tool_called=False,sql_executed=False),{'coordinate_pair':[126.6,37.4],'crs':None,'explicit_no_crs_inference':True})
    add('2022 해양지명 CSV만으로 2020년 당시 등록된 해양지명 목록을 확정해 주세요.','TEMPORAL_SOURCE_GAP',dict(status='BLOCKED_DATA',blocker='HISTORICAL_MEMBERSHIP_UNVERIFIED',object_ids=None,count=None,source_sha256=sha(CSV),required_disclosure='2022 판은 2020년의 완전한 등록 상태를 입증하지 않음',execution_attempted=False))
    base=dict(feature='MarinePlaceName',operator='radius',reference_geometry={'type':'Point','coordinates':[126.6,37.4]},crs='EPSG:4326',distance_m=20000,source_sha256=sha(CSV),source_scope='2022_CSV_RECORDS',tool='source_bound_radius_search')
    mutations=[('DISTANCE_UNIT_SCALE','distance_m',20),('CRS_MISMATCH','crs','EPSG:3857'),('SOURCE_HASH_MISMATCH','source_sha256','0'*64),('REFERENCE_AXIS_SWAP','reference_geometry',{'type':'Point','coordinates':[37.4,126.6]}),('TARGET_SUBSTITUTION','feature','Wreck'),('MISSING_SOURCE','source_sha256',None),('MISSING_REFERENCE','reference_geometry',None),('OPERATOR_SUBSTITUTION','operator','nearest'),('RADIUS_EXPANSION','distance_m',40000)]
    faults=[]
    for i,(typ,key,val) in enumerate(mutations):
        changed=copy.deepcopy(base);changed[key]=val
        faults.append(dict(case_id=f'HO_FAULT_{i+1:02}',error_type=typ,expected_invalid=True,request_contract=base,frozen_initial_plan=changed,changed_field=key,expected_action='BLOCK_BEFORE_SPATIAL_EXECUTION',source_evidence=sha(CSV),equivalence_group='HO_FAULT_'+typ))
    for i,plan in enumerate([base,dict(base,distance_m=10000),dict(base,operator='nearest',distance_m=None)]):
        faults.append(dict(case_id=f'HO_CONTROL_{i+1:02}',error_type='VALID_CONTROL',expected_invalid=False,request_contract=plan,frozen_initial_plan=plan,expected_action='ALLOW_IF_SOURCE_SCOPE_APPROVED',source_evidence=sha(CSV),equivalence_group=f'HO_CONTROL_{i+1:02}'))
    recovery=[]
    for i,f in enumerate(faults[:8]):
        missing=f['error_type'] in ['MISSING_SOURCE','MISSING_REFERENCE'];request=copy.deepcopy(base)
        if missing:request[f['changed_field']]=None
        recovery.append(dict(case_id=f'HO_RECOVERY_{i+1:02}',fault_case_id=f['case_id'],request_contract=request,initial_plan=f['frozen_initial_plan'],recoverable=not missing,expected_action='NEEDS_USER_INPUT' if missing else 'RESTORE_EXPLICIT_REQUEST_ONLY',expected_plan=None if missing else base,allowed_mutation_paths=[] if missing else [f['changed_field']],invariants=[k for k in base if k!=f['changed_field']],recovery_success_requires=['actual successful execution','source-bound object set matches independent oracle','all request tuple invariants preserved'] if not missing else ['no execution','request missing information'],oracle_case_id='HOLDOUT_11' if not missing else None))
    # Fault/recovery reference uses the same center as HOLDOUT_10 but a radius query;
    # compute its independent object set explicitly rather than borrow another center.
    recobjects=[p for p in points if dist[0,p['id']]<=20000]
    for x in recovery:
        if x['recoverable']:x['oracle_case_id']=None;x['spatial_gold']={'object_ids':sorted('mof_marine_names_20221231:'+p['id'] for p in recobjects),'source_sha256':sha(CSV),'distance_m':20000}
    assert len(queries)==18 and len(faults)==12 and len(recovery)==8 and recobjects
    dev=rows(DEV/'queries.jsonl');assert not {x['query'] for x in dev}&{x['query'] for x in queries}
    OUT.mkdir(parents=True)
    jsonl(OUT/'queries.jsonl',queries);jsonl(OUT/'gold.jsonl',gold);jsonl(OUT/'rq2_faults.jsonl',faults);jsonl(OUT/'rq4_recovery.jsonl',recovery)
    dump(OUT/'spatial_oracles.json',{'source_rows':len(points),'parsed_rows':len(points),'objects':oracle,'verification':'READ_ONLY_POSTGIS_VS_VINCENTY','max_distance_difference_m':maxerr,'postgis_version':measured['postgis_version']})
    (OUT/'oracle.sql').write_text(sql,encoding='utf-8')
    jsonl(OUT/'all_distances.jsonl',measured['distances'])
    dump(OUT/'source_manifest.json',{'sources':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in (FC,CSV)],'development_manifest_sha256':sha(DEV/'manifest.json'),'development_files_unchanged':all(sha(DEV/p)==h for p,h in devbefore.items()),'source_overlap_with_development':True,'oracle_uses_production_executor':False})
    dump(OUT/'final_freeze_receipt_TEMPLATE.json',dict(benchmark_manifest_sha256=None,system_frozen=False,freeze_at=None,system_source_sha256=None,model_digest=None,prompt_sha256=None,data_snapshot_sha256=None,evaluation_code_sha256=None,human_holdout_gold_approved=False,reviewer_ids=[],approved_at=None,no_holdout_used_for_tuning=False,freeze_artifact_paths={},model_receipt_path=None,model_receipt_sha256=None))
    text="""# 예약 홀드아웃 — 최종 동결 후 평가 계획

개발 18문항과 별도 ID·질의·동등군으로 분리한 신규 18문항, 통제 오류 9+정상3=12사례, 복구 8사례를 준비했다. 모델 호출·실제 평가를 실행하지 않았다. 새 GOLD는 AI 작성·원본 근거 검증 단계이며 기존 개발 GOLD의 인간 승인을 자동 상속하지 않는다.

## 원본 근거 및 공간 검산

FC 2.0.0 실제 Feature 정의/geometry/attribute binding을 직접 추출했다. CSV 전체 행의 DMS를 파싱하고 6개 입력 좌표와의 WGS84 거리를 READ ONLY PostGIS ST_Distance와 별도 Vincenty로 비교했다. 허용 오차 0.01m, 원천 행 ID·거리·SQL·원본 hash를 보존한다. 범위는 2022 CSV 기록으로 한정하며 법적/실세계 완전성이나 운영 APPROVED coverage를 만들지 않는다.

## RQ별 실행

- RQ1: 신규 18문항×8방법. 질의 조건별 과업·근거·인간 의미 정확도를 분리한다.
- RQ2: 12계획×B4/P0/H, 동일 초기 계획/검토 hash. 정상3 사례를 False Block 분모에 포함한다.
- RQ3: 6개 독립 좌표/조건별 공간 Oracle. 실행 성공·객체집합/거리 정답·silent failure를 분리한다.
- RQ4: 복구8사례×B4/H. 명시된 요청만 복원 가능; 원요청에서도 source/reference가 없는 2사례는 질문하고 미실행해야 한다. 실제 비어 있지 않은 source-bound 객체집합과 의미 보존을 동시에 검사한다.
- RQ5: latency/token/tool/SQL·False Ready/False Block. 공유 생성 비용과 단독 비용을 구분한다.

## 실행 전 필수 gate

1. 새 홀드아웃 GOLD를 인간 검수하고 결과·검수자·일시를 별도 기록한다.
2. 개발 수정 후 코드/model/prompt/data/evaluator hash와 동결일을 기록한다. freeze_artifact_paths의 실제 파일 SHA와 검증된 model_receipt_path/digest를 확인하며 임의 64자리 문자열만으로 통과하지 않는다.
3. final_freeze_receipt_TEMPLATE.json을 별도 경로로 복사해 채운다. benchmark manifest hash와 연결한다.
4. `python -m tools.scie_results_ui.prepare_holdout --verify --receipt <path>`가 실패하면 실행 금지. 이 CLI는 검증만 하며 평가 worker를 시작하지 않는다.
5. 동결 receipt를 소비하는 전용 실행 harness와 데이터 주입/채점 계약 통합 검증 후 새 run에서 8방법·fault·recovery를 실행한다. 기존 개발 runner의 18문항 이름만 바꿔 실행하면 안 된다.
6. 평가 후 변경은 새로운 개발 실험으로 분류하며 노출된 홀드아웃을 재사용해 독립 성능으로 주장하지 않는다.

## 독립성 제한

원천 FC/CSV와 일반 오류 유형은 개발셋과 공유한다. 독립성이란 현재 모델 평가·튜닝에 쓰지 않도록 예약한 질의/객체/조건 단위이며 새로운 원천·완전한 도메인 독립·인간 블라인드 설계를 뜻하지 않는다. 과거 전체 질의 corpus에 대한 중복 감사는 미완료다. 작성 에이전트는 내용을 보았으므로 후속 개발자/튜닝 프롬프트에 질의·GOLD를 전달하지 말고 UI에는 수량·상태만 표시한다. 같은 원천 Feature의 정의와 속성 문항은 상관성이 있어 독립 표본으로 단순 합산하지 않는다.
"""
    (OUT/'평가계획_KR.md').write_text(text,encoding='utf-8')
    manifest={'version':'holdout_20261102_v1','status':'CONTENT_FROZEN_EVALUATION_LOCKED','files':{p.name:sha(p) for p in OUT.iterdir() if p.is_file()},'builder_sha256':sha(Path(__file__))}
    dump(OUT/'manifest.json',manifest)
    summary=dict(status='PREPARED_PENDING_FINAL_SYSTEM_FREEZE',main_cases=18,rq2_fault_cases=12,rq2_invalid_cases=9,rq2_valid_controls=3,rq4_recovery_cases=8,rq4_recoverable_cases=6,rq4_missing_input_cases=2,gold_source_verified=True,human_review_complete=False,evaluation_executed=False,system_freeze_complete=False,evaluation_ready=False,split='prospective_holdout',manifest_sha256=sha(OUT/'manifest.json'),spatial_oracle_cases=6,spatial_validation='READ_ONLY_POSTGIS_VS_VINCENTY',limitations=['FC/CSV 원천은 개발셋과 공유하므로 원천 독립 평가가 아닙니다.','신규 홀드아웃 GOLD 인간 승인과 최종 시스템 동결 후 평가합니다.','과거 전체 질의 corpus의 중복 감사는 미완료입니다.','독립 인간 답변 채점은 수행되지 않았습니다.','전용 평가 harness 통합 검증이 필요하며 검증 CLI는 worker를 시작하지 않습니다.'],gate_errors=evaluation_gate(OUT)['errors'])
    dump(OUT/'summary.json',summary)
    print(json.dumps({k:summary[k] for k in ['status','main_cases','rq2_fault_cases','rq4_recovery_cases','evaluation_ready']},ensure_ascii=False))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--verify',action='store_true');parser.add_argument('--receipt',type=Path);args=parser.parse_args()
    if args.verify:
        result=evaluation_gate(OUT,json.loads(args.receipt.read_text(encoding='utf-8')) if args.receipt else None);print(json.dumps(result,ensure_ascii=False));raise SystemExit(0 if result['evaluation_ready'] else 2)
    prepare()
