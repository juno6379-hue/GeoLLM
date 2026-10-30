"""Source-checked third AI synthesis; never human approval or GOLD promotion."""
import copy
from datetime import datetime, timezone
import hashlib
import json
import argparse
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'research/marine_geollm_scie/benchmark/review_exports/20261030_ai_prefill'
FC=ROOT/'data/s101_feature_catalogue_v2_parsed.json'
XML=ROOT/'outputs/staging/s101_feature_catalogue_2_0_0/S-101/CATALOGUES/101_Feature_Catalogue_2.0.0.xml'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines() if s.strip()]

# Written synthesis decisions, based on both independent AI proposals and FC source inspection.
DECISIONS={
'PILOT_Q1_01':('등대 구조물과 광원을 구분하여 FC2.0.0 정의·원천을 설명한다. Landmark 및 LightAllAround/LightSectored를 후보로 제시하고, Building은 정의와 실제 객체 분류가 부합하는 건조물일 때만 조건부 설명에 포함한다. function=33 또는 Tower만으로 모든 등대를 식별하지 않는다.', ['등대의 구조물·등화·시설 전체 중 어떤 의미를 업무상 기준으로 삼을지 승인해 주세요.']),
'PILOT_Q1_02':('정박 구역 개념은 AnchorageArea로 설명한다. AnchorBerth는 지정된 정박 구역의 별도 FC 정의를 비교 설명할 수 있으나 두 개념을 무조건 동의어로 대체하지 않는다.', ['AnchorBerth의 보충 설명을 허용 대안으로 인정할지 확인해 주세요.']),
'PILOT_Q1_03':('Wreck의 FC 정의와 point/surface 허용 기하를 설명한다. 좌초 또는 침몰하여 사용할 수 없게 된 선박 잔해라는 범위를 유지하고 일반 장애물 전체로 확장하지 않는다.', []),
'PILOT_Q2_01':('구조물 색과 등화색의 소유 Feature를 구분한다. Landmark.colour는 1~13, LightAllAround.colour는 1,3,4,5,6,9,10,11이 허용된다. LightSectored는 sectorCharacteristics/lightSector의 하위 colour 경로를 설명한다. 공통 colour 코드목록 전체를 모든 소유 객체의 허용값으로 복사하지 않는다.', ['구조물 표면색과 등화색 중 질문의 초점을 확인하거나 두 가지를 조건부로 병기하는 방식을 승인해 주세요.']),
'PILOT_Q2_02':('RestrictedArea의 restriction은 행위 제한이고 categoryOfRestrictedArea는 영역 종류이다. FC 소유 바인딩별 허용 코드를 각각 설명한다. registry 명칭과 FC2.0.0 명칭의 차이를 숨기거나 허용값을 바꾸지 않는다.', ['FC2.0.0 RestrictedArea와 기존 registry 별칭의 대응은 별도 운영 검토가 필요합니다.']),
'PILOT_Q2_03':('Wreck의 attributeBinding만 속성 목록으로 설명하며 필수/선택·다중도·허용값을 함께 보존한다. informationBinding/featureBinding을 단순 속성으로 섞지 않고 실제 개별 객체 값을 추정하지 않는다.', []),
'PILOT_Q3_01':('독도 기준 위치를 원천에서 먼저 해소하고 등대 범주·중복 정책을 정한 뒤 최근접 1개를 거리·원천과 함께 제시한다. 반경이 원문에 없으므로 임의 반경을 정답조건으로 강제하지 않는다. 검색 범위 제한이 필요하면 정책을 공개하고 사용자 확인을 받는다.', ['등대 범주, 구조물·등화 중복 제거, 동거리 처리 및 데이터의 검색범위를 승인해 주세요.']),
'PILOT_Q3_02':('부산항의 검증된 영역 polygon 안에 있는 AnchorageArea를 검색한다. 영역을 항만 중심점의 임의 반경으로 대체하지 않는다. within과 경계 포함/교차 처리의 업무 계약을 먼저 명시한다.', ['부산항의 공식 영역 원천 및 경계 접촉 객체 포함 정책을 확인해 주세요.']),
'PILOT_Q3_03':('현재 비어 있는 spatial_context에는 selected area가 없으므로 AOI를 요청한다. AOI가 확보되고 validator가 승인한 뒤 Wreck의 point/surface 교차 검색을 수행한다. 정의 설명을 실제 공간검색 완료로 표시하지 않는다.', ['선택 영역 geometry를 제공하거나 지도에서 영역을 지정해 주세요.']),
'PILOT_Q4_01':('독도 원천 기준점과 지명 원천을 해소하고 5km를 5000m로 정규화하여 해양지명 목록·원천을 검색한다. SeaAreaNamedWaterArea는 FC 참고 개념일 뿐 전체 해양지명의 단일 검색 필터로 강제하지 않는다.', ['지명 원천 범위, 독도 기준점 및 동명이명·중복 정책을 승인해 주세요.']),
'PILOT_Q4_02':('5000m는 5km와 동일하다. Q4 세 표현은 동일 snapshot·기준점·지명 범주·거리 정책 아래 같은 공간조건으로 평가한다. 해양지명을 위험객체로 바꾸거나 SeaAreaNamedWaterArea 하나로 한정하지 않는다.', ['Q4 세 표현의 동일 공간조건 및 지명 원천 범위를 확인해 주세요.']),
'PILOT_Q4_03':('marine place names를 해양지명 검색 대상으로 유지하고 Dokdo를 기준 위치로 해소한다. 5km는 5000m로 정규화한다. 언어 변화 때문에 지명 범주나 공간 조건을 바꾸지 않는다.', ['Q4 세 표현의 업무상 동등성과 지명 범위를 확인해 주세요.']),
'PILOT_Q5_01':('독도 5000m 내 등대와 Wreck 검색을 별도 하위 작업으로 유지한다. 등대 범주·원천을 해소하고 반환 객체별 근거를 연결한다. 한 분기의 미지원/미해결을 다른 분기의 완료로 숨기지 않는다.', ['등대 범주, 시설 중복 제거 및 실제 geometry 거리판정 정책을 확인해 주세요.']),
'PILOT_Q5_02':('부산항 기준점에서 2000m 이내 AnchorageArea와 RestrictedArea를 각각 검색하고 비교한다. 영역 객체의 최소 geometry 거리와 중심점 거리 중 사용할 정책을 명시하며 조용히 바꾸지 않는다.', ['부산항 기준점 원천, 영역 객체 거리 기준과 비교 항목을 승인해 주세요.']),
'PILOT_Q5_03':('독도 5000m 내 실제 Wreck를 검색하고 반환 객체의 실제 속성값을 FC의 속성 정의·단위·허용값과 연결하여 설명한다. FC 허용 속성 목록만 제시하고 개별 객체 검색·설명이 끝났다고 하지 않는다.', ['거리 CRS·경계 포함 및 실제 데이터 미보유 속성의 표시 정책을 확인해 주세요.']),
'PILOT_Q6_01':('Wreck 정의의 정확한 FC2.0.0 영문 원문과 XML/파생 레코드 위치·hash를 제시한다. 한국어 해설을 원문 인용과 구분하며 KG 요약을 원문으로 대체하지 않는다.', []),
'PILOT_Q6_02':('고정된 등대 구조물과 등화 equipment, 부유식 표지의 구조·기능을 구분해 FC 근거를 설명한다. 부표에도 등화가 있을 수 있으므로 발광 여부만으로 구별하지 않는다. 열거한 부표 Feature는 예시이며 전체 유형이라고 주장하지 않는다.', ['구조물·등화·부표의 비교 범위와 부표 예시 목록을 허용 답안으로 승인해 주세요.']),
'PILOT_Q6_03':('AnchorageArea 정의를 FC2.0.0 feature 레코드와 원 XML의 실제 위치·hash로 추적한다. KG의 mapsToProduct 관계만으로 정의의 근거가 충분하다고 하지 않는다.', []),
}

def synthesize(revise_existing=False):
    output=BASE/'adjudication_DRAFT.jsonl'
    if output.exists():
        if not revise_existing: raise FileExistsError('Preserve existing synthesis; use explicit review before replacing')
        archive=BASE/('adjudication_DRAFT.before_'+sha(output)[:12]+'.jsonl')
        if not archive.exists(): shutil.copy2(output,archive)
    ap=BASE/'reviewer_A/annotations_DRAFT.jsonl'; bp=BASE/'reviewer_B/annotations_DRAFT.jsonl'
    aa=read(ap); bb={r['case_id']:r for r in read(bp)}
    fc=json.loads(FC.read_text(encoding='utf-8')); features={f['code']:f for f in fc['features']}
    attrs={a['code']:a for a in fc['attributes']}
    source={'path':FC.relative_to(ROOT).as_posix(),'sha256':sha(FC),'version':'2.0.0'}
    xml={'path':XML.relative_to(ROOT).as_posix(),'sha256':sha(XML)}
    assert xml['sha256']=='2743d0689d8a2130f9b809554591d794f01cd9953f222f065ac891b590bd3cfc'
    assert len(aa)==len(bb)==18
    now=datetime.now(timezone.utc).isoformat(); result=[]
    for a in aa:
        b=bb[a['case_id']]; case=a['case_id']; category=a['category']
        assert a['query']==b['query'] and a['provenance']['benchmark_sha256']==b['provenance']['benchmark_sha256']
        assert all(r.get('human_approval') is False and r.get('review_kind')=='AI_PRE_REVIEW' and r['annotation_status']=='DRAFT' for r in (a,b))
        explanation,questions=DECISIONS[case]
        af=a['semantics'].get('canonical_concept_candidates',[]); bf=b['semantics'].get('feature_candidates',[])
        targets=list(dict.fromkeys(af+bf)); conditional=[]; differences=[]
        if 'Building' in targets:
            conditional.append('Building은 원천 객체의 정의·기능이 부합할 때만 조건부 후보이다. 모든 Building을 등대로 분류하지 않는다.')
            differences.append({'field':'feature_scope','A':af,'B':bf,'resolution':'Building 보충 설명을 조건부 대안으로 보존하며 단일 등대 정답 Feature로 확정하지 않는다.','kind':'CONDITIONAL_SCOPE_NOT_LABEL_ERROR'})
        if any(name in targets for name in ('Landmark','LightAllAround','LightSectored')):
            conditional.append('열거 Feature는 해석 후보이지 전부 필수인 정답집합이 아니다. LightAllAround에는 부표 등의 등화도 포함될 수 있으므로 물리적 등대 동일성 및 지지구조 연결을 원천에서 확인하기 전 등대 정답 객체로 확정하지 않는다. point 형상만으로 등대를 식별하지 않는다.')
        if case=='PILOT_Q1_02':
            differences.append({'field':'supplementary_concept','A':af,'B':bf,'resolution':'AnchorageArea를 주 개념으로, AnchorBerth를 구분 설명 가능한 보충 개념으로 둔다.','kind':'EXPLANATORY_SCOPE'})
        if category=='Q4':
            differences.append({'field':'gazetteer_vs_FC_candidate','A':af,'B':bf,'resolution':'A의 SeaAreaNamedWaterArea는 참고 개념으로 보존하고 B의 제한 없는 지명 원천 검색을 실행 대상으로 채택한다. 실제 지명 원천 가용성은 미확정이다.','kind':'TARGET_SCOPE_REQUIRES_HUMAN_APPROVAL'})
            target_kind='marine_place_names'; executable_targets=[]
        else: target_kind='S101_feature_concept'; executable_targets=targets
        relation=b['semantics'].get('relation'); distance=b['semantics'].get('normalized_distance_m')
        spatial=category in ('Q3','Q4','Q5')
        if spatial:
            differences.append({'field':'execution_preconditions','A':a['expected_execution_behavior'],'B':b['expected_execution_behavior'],'resolution':'원천 위치 해소를 먼저 시도하고 실제 geometry/tool/data 검증 후 실행한다. 미해결일 때만 구체적인 추가 입력을 요청하며 미실행을 0건으로 표시하지 않는다.','kind':'CONDITIONAL_POLICY_NOT_DISAGREEMENT_RATE'})
        definitions=[]
        for name in targets:
            if name in features:
                f=features[name]
                definitions.append({'feature':name,'definition_original':f['definition'],'permitted_primitives':f['permitted_primitives'],
                    'attribute_bindings':[v for v in f['bindings'] if v['kind']=='attributeBinding'] if category=='Q2' or case=='PILOT_Q5_03' else [],
                    'source':{**source,'locator':'features/'+name}})
        necessary=['검증된 원천 위치/선택영역 geometry','실제 data/tool bindings','ExecutionValidator 승인'] if spatial else ['FC 원문·소유 바인딩·판·locator 확인']
        if relation=='nearest': necessary+=['nearest_k=1, 검색범위·동거리·중복 정책']; distance=None
        if relation=='within': necessary+=['공식 영역 polygon 및 경계 포함 계약']; distance=None
        if relation=='intersects': necessary+=['선택 AOI 제공']; distance=None
        oracle={'status':'NOT_EXECUTED_PENDING_REFERENCE_CHECK' if spatial else 'NOT_APPLICABLE',
            'expected_object_ids':None,'expected_geometry':None,'expected_distance':None,'expected_count':None,
            'reason_ko':'실제 dataset 조회·독립 SQL·geometry 검증을 수행하지 않았으므로 수치나 객체 정답을 만들지 않는다.' if spatial else '표준 개념·속성·원문 질의이며 GIS 객체집합 정답을 요구하지 않는다.'}
        uncertainties=list(dict.fromkeys(a['uncertainties']+b['uncertainties']))
        resolution={'status':'AI_SYNTHESIS_COMPLETE_HUMAN_APPROVAL_PENDING','summary_ko':explanation,
            'semantics':{'interpretation_ko':explanation,'target_kind':target_kind,'target_features':executable_targets,
                'target_features_role':'CANDIDATES_NOT_REQUIRED_SET','direct_use_as_gold_or_set_metric':False,
                'reference_concepts':targets,'conditional_alternatives':conditional,'spatial_relation':relation,'distance_m':distance,'gold_intent_label':None},
            'qec_fields':{'contract_reference':'shared/schemas/agent.py#QueryExecutionContext','target_features_candidates':executable_targets,
                'distance_m':distance,'spatial_relation':relation,'reference_geometry':None,'crs':None,'data_bindings':None,'tool_bindings':None,
                'nearest_k':1 if relation=='nearest' else None,'required_before_execution':necessary,'execution_authority':'ExecutionValidator only; AI synthesis grants no execution readiness'},
            'expected_execution_behavior':explanation+' 실제 실행결과와 근거가 없으면 완료 또는 0건으로 표시하지 않는다.' if spatial else explanation+' 불필요한 위치 이동·반경 입력을 요구하지 않는다.',
            'acceptable_alternatives':{'A':a['acceptable_alternatives'],'B':b['acceptable_alternatives'],'synthesis_condition':conditional},
            'spatial_oracle':oracle,'user_confirmation_questions':questions,
            'uncertainties':uncertainties,'source_checked_feature_records':definitions}
        result.append({'case_id':case,'query':a['query'],'category':category,'equivalence_group':a['equivalence_group'],
            'annotation_status':'DRAFT','review_kind':'AI_PRE_REVIEW','human_approval':False,'adjudicator_id':'AI_SYNTHESIS','adjudicated_at':now,
            'adjudication_status':'AI_SYNTHESIS_COMPLETE_HUMAN_APPROVAL_PENDING','reviewer_A_annotation_hash':sha(ap),'reviewer_B_annotation_hash':sha(bp),
            'disagreement_fields':differences,'resolution':resolution,
            'resolution_sources':{'fc_parsed':source,'fc_xml':xml,'source_check':'FC definitions and owner binding values cross-checked against local frozen sources; not full human adjudication',
                'feature_records':definitions,'reviewer_A_file':str(ap.relative_to(ROOT)),'reviewer_B_file':str(bp.relative_to(ROOT))},
            'uncertainties':uncertainties,'review_notes':{'review_complete':True,'approval_pending':True,'user_confirmation_questions':questions,
                'reviewer_A_view':a['semantics'],'reviewer_B_view':b['semantics'],
                'statistics':'No kappa, semantic disagreement rate, accuracy or GOLD promotion. Different JSON shapes are not scored as disagreements.'},
            'source_materials':copy.deepcopy(a['source_materials']),'provenance':copy.deepcopy(a['provenance'])})
    output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result),encoding='utf-8')
    manifest={'review_kind':'AI_PRE_REVIEW','human_approval':False,'status':'AI_REVIEW_COMPLETE_HUMAN_APPROVAL_PENDING','cases':18,
        'source_hashes':{'reviewer_A':sha(ap),'reviewer_B':sha(bp),'adjudication':sha(output)},'fc':source,'xml':xml,
        'gold_written':False,'model_predictions_used':False,'kappa':None,'synthesis_script_sha256':sha(Path(__file__))}
    (BASE/'ai_synthesis_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'cases':18,'status':manifest['status'],'adjudication_sha256':sha(output)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--revise-existing',action='store_true')
    synthesize(parser.parse_args().revise_existing)
