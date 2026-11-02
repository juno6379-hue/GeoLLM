"""Compile explicit AI-reviewed prediction atoms from raw witnesses, never GOLD.

Natural-language adjudication is a named measurement step, not a parser's claim
to understand every new answer. New runs require their own hash-bound reviews.
"""
from __future__ import annotations
import hashlib
import json
import re
from decimal import Decimal

VERSION='rq1_prediction_review.v2'
KINDS={'attribute_binding','comparison_criterion','distance_m','distance_metric','feature',
       'input_requirement','operator','reference','reference_crs','reference_geometry_id',
       'requested_object','source_binding','standard','task_obligation'}
FEATURE_ALIASES={
    'wreck':'Wreck','wrecks':'Wreck','침선':'Wreck',
    'anchorage area':'AnchorageArea','anchoragearea':'AnchorageArea','anchorage':'AnchorageArea',
    '정박지':'AnchorageArea','锚地':'AnchorageArea',
    'restrictedarea':'RestrictedArea','restricted area':'RestrictedArea','제한구역':'RestrictedArea',
    '限制区域':'RestrictedArea','harbour':'Harbour','港口':'Harbour',
    'obstruction':'Obstruction','underwaterawashrock':'UnderwaterAwashRock','foulground':'FoulGround',
    'rock':'Rock','category of wreck':'categoryOfWreck',
    'navigation hazard object':'navigation_hazard_object','regulated area':'regulated_area',
    'protected area':'protected_area','anchor line':'anchor_line','anchor lines':'anchor_line',
}
OBJECT_ALIASES={'lighthouse':'Lighthouse','lighthouses':'Lighthouse','등대':'Lighthouse',
                'marine place names':'MarinePlaceName','해양지명':'MarinePlaceName','부표':'Buoy','buoy':'Buoy'}
REFERENCE_ALIASES={'dokdo':'독도','busan port':'부산항'}
ATTRIBUTE_ALIASES={'색상':'colour','color':'colour','colour':'colour',
                   'default clearance depth':'defaultClearanceDepth',
                   'quality of vertical measurement':'qualityOfVerticalMeasurement'}
TASK_RULES={
    'explain_structure_and_light_distinction':r'구조물|structure',
    'explain_conditional_feature_mapping':r'경우|조건|conditional|depending',
    'explain_anchorage_area_definition':r'정박|anchor',
    'explain_wreck_definition':r'wreck|침선',
    'distinguish_structure_and_light_colour':r'구조물|structure',
    'explain_feature_bound_permitted_values':r'허용|permitted|allowed',
    'distinguish_restriction_and_area_category':r'restriction|제한',
    'explain_restriction_codes':r'restriction|제한',
    'explain_wreck_attribute_bindings':r'attributes|속성',
    'resolve_lighthouse_target_conditions':r'Landmark|Building|LightAllAround|LightSectored',
    'find_nearest':r'closest|nearest|가까운|최근접',
    'resolve_official_port_polygon':r'polygon|항계|경계',
    'search_within_polygon':r'polygon|항계|경계',
    'search_intersections_if_aoi_available':r'if|provided|지정|선택.*필요',
    'search_fixed_gazetteer_5000m':r'frozen|fixed|2022|고정',
    'search_both_targets_5000m':r'5000|5\s*km',
    'search_both_targets_2000m':r'2000|2\s*km|2公里',
    'provide_per_target_evidence':r'evidence|source|근거|출처',
    'compare_target_results':r'compar|비교',
    'search_wrecks_5000m':r'5000|5\s*km',
    'explain_s101_attributes':r'S-?101.*attributes|S-?101.*속성',
    'distinguish_object_values_from_standard_attributes':r'instance|실제.*속성|객체.*값',
    'provide_wreck_definition_text':r'wreck|침선',
    'cite_catalogue_edition_and_locator':r'locator|xpath|페이지|section',
    'compare_fixed_structure_and_floating_aid_models':r'floating|부유',
    'cite_comparison_evidence':r'출처|근거|source|catalogue',
    'provide_anchorage_definition_source':r'source|출처|근거',
}
CRITERION_RULES={
    'per_type_object_count':r'(per.type|각\s*(?:종류|유형)|유형별|종류별).*(count|개수|건수)|count.*(?:per.type|유형별)',
    'per_type_minimum_and_maximum_distance_m':r'(minimum|min|최소).*(maximum|max|최대).*(distance|거리)|거리.*최소.*최대',
    'distinct_FC_feature_definitions':r'(Feature Catalogue|FC|S-?101).*(definition|정의).*(compar|비교|차이)|(?:compar|비교).*(definition|정의)',
    'source_scope_and_reference_disclosure':r'(source|원천).*(scope|범위).*(reference|기준)',
}
METRIC_RULES={
    ('surface','WGS84_ellipsoid'):r'WGS[- ]?84.*(?:ellipsoid|spheroid|타원체)|(?:ellipsoid|타원체).*WGS[- ]?84',
    ('surface','sphere'):r'\bsphere\b|구면',
    ('measurement','point_to_point'):r'point.to.point|점.*점.*거리',
    ('measurement','minimum_geometry_to_geometry'):r'minimum.*geometry.to.geometry|최소.*기하.*기하|기하.*기하.*최소',
    ('measurement','centroid_to_centroid'):r'centroid.to.centroid|중심점.*중심점',
    ('reference','polygon_area'):r'polygon.area|폴리곤.*영역|다각형.*영역',
    ('reference','boundary_line'):r'boundary.line|경계선',
    ('boundary_inclusive',True):r'<=|≤|boundary.inclusive|경계.*포함',
    ('boundary_inclusive',False):r'strictly.less|boundary.exclusive|경계.*제외',
}
POLICY={'version':VERSION,'kinds':sorted(KINDS),'feature_aliases':FEATURE_ALIASES,
    'object_aliases':OBJECT_ALIASES,'reference_aliases':REFERENCE_ALIASES,'attribute_aliases':ATTRIBUTE_ALIASES,
    'task_witness_filters':TASK_RULES,
    'criterion_witness_filters':CRITERION_RULES,
    'metric_witness_filters':[{'field':k[0],'value':k[1],'pattern':v} for k,v in METRIC_RULES.items()],
    'annotation_authority':'AI_MEASUREMENT_REVIEW_NOT_HUMAN_GOLD',
    'task_obligation_interpretation':'EXPLICIT_TASK_RECOGNITION_OR_PLAN_NOT_EXECUTION_SUCCESS_OR_FACTUAL_ANSWER_CORRECTNESS',
    'channels':'UNION_STRUCTURED_AND_ANSWER; preserve disagreement and wrong-field assertions',
    'task_scope':'query for single tasks; explicit shared spatial clause only permits group binding; document task separate',
    'duplicates':'same task/kind/value mirrors merged with all witnesses; repeated instance claims kept in sidecar',
    'failures':'include schema failures and truncated observed text; no JSON repair; no implicit empty predictions',
    'standard':'edition null when not explicit; never borrow catalogue edition',
    'source':'partial binding explicit null fields; path must not be resolved to a missing hash/locator',
    'unknown':'retain literal value, never choose a GOLD-matching alias',
    'review_gate':'full source-key and narrative audit, explicit witnesses, AI reviewer record, per-run raw hash',
    'unreviewed_new_answer':'REVIEW_REQUIRED; not scored and never dropped',
    'optional_gold':'exact optional matches separated; never alter required denominator'}


def canonical_json(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)


def sha(data):return hashlib.sha256(data).hexdigest()


CONTRACT_SHA256=sha(canonical_json(POLICY).encode())


def pointer(data,path):
    if not isinstance(path,str) or not path.startswith('/'):raise ValueError('POINTER_REQUIRED')
    for part in path[1:].split('/'):
        part=part.replace('~1','/').replace('~0','~')
        data=data[int(part)] if isinstance(data,list) else data[part]
    return data


def witness_value(raw,witness):
    if not re.fullmatch(r'/plan(?:/.*)?|/calls/\d+/raw_response|/candidate_answer',str(witness.get('pointer',''))):
        raise ValueError('WITNESS_MUST_BE_MODEL_OUTPUT_NOT_PROMPT_OR_QUERY')
    value=pointer(raw,witness['pointer'])
    if 'span' in witness:
        start,end=witness['span']
        if type(start) is not int or type(end) is not int or not isinstance(value,str) or not 0<=start<end<=len(value):
            raise ValueError('INVALID_SPAN')
        value=value[start:end]
    if canonical_json(value)!=canonical_json(witness['literal']):raise ValueError('WITNESS_CHANGED')
    return value


def normalize_name(kind,value):
    aliases={'feature':FEATURE_ALIASES,'requested_object':OBJECT_ALIASES,
             'reference':REFERENCE_ALIASES,'attribute':ATTRIBUTE_ALIASES}.get(kind,{})
    return aliases.get(str(value).casefold(),value)


def explicit_metres(value):
    if type(value) in (int,float):number=Decimal(str(value))
    else:
        m=re.fullmatch(r'\s*([+-]?\d+(?:\.\d+)?)\s*(km|kilometers?|kilometres?|公里|m|meters?|metres?)\s*',str(value),re.I)
        if not m:raise ValueError('EXPLICIT_DISTANCE_REQUIRED')
        number=Decimal(m[1])*(1000 if m[2].casefold().startswith(('kilo','km','公里')) else 1)
    if not number.is_finite() or number!=number.to_integral_value():raise ValueError('NO_DISTANCE_ROUNDING')
    return int(number)


def check_atom(raw,atom):
    if atom.get('kind') not in KINDS or not isinstance(atom.get('task_id'),str) or not atom['task_id']:
        raise ValueError('ATOM_TYPE_OR_TASK_INVALID')
    if not atom.get('review_note') or not atom.get('witnesses'):raise ValueError('REVIEW_AND_WITNESS_REQUIRED')
    values=[witness_value(raw,w) for w in atom['witnesses']]
    text='\n'.join(str(v) for v in values)
    value=atom.get('value');kind=atom['kind'];rule=atom['rule']
    if rule=='name':
        if kind not in {'feature','requested_object','reference','comparison_criterion','reference_geometry_id'} or not any(canonical_json(normalize_name(kind,v))==canonical_json(value) for v in values):
            raise ValueError('NAME_NOT_WITNESSED')
    elif rule=='metres':
        if kind!='distance_m' or not any(explicit_metres(v)==value for v in values):raise ValueError('DISTANCE_NOT_WITNESSED')
    elif rule=='literal':
        if not any(canonical_json(v)==canonical_json(value) for v in values):raise ValueError('LITERAL_NOT_WITNESSED')
    elif rule=='crs':
        if kind!='reference_crs' or not any(v in ('EPSG:4326','4326',4326) for v in values) or value!='EPSG:4326':raise ValueError('CRS_NOT_WITNESSED')
    elif rule=='spatial_language':
        patterns={'nearest':r'closest|nearest|가장\s*가까', 'intersects':r'intersect|교차',
                  'dwithin':r'within\s+\d+(?:\.\d+)?\s*(?:km|meters?|kilometers?)|반경\s*\d+\s*m|距离.*?\d+公里范围'}
        if kind!='operator' or value not in patterns or not re.search(patterns[value],text,re.I):raise ValueError('RELATION_NOT_WITNESSED')
    elif rule=='standard':
        if kind!='standard' or not isinstance(value,dict) or set(value)!={'standard','edition'}:raise ValueError('STANDARD_SCHEMA')
        if not re.search(re.escape(value['standard']).replace(r'\-',r'[- ]?'),text,re.I):raise ValueError('STANDARD_NOT_WITNESSED')
        if value['edition'] is not None and value['edition'] not in text:raise ValueError('EDITION_NOT_WITNESSED')
    elif rule=='attribute_owner':
        if kind!='attribute_binding' or not isinstance(value,dict) or set(value)!={'owner','attribute'}:raise ValueError('ATTRIBUTE_SCHEMA')
        owner=value['owner'];attribute=value['attribute']
        if owner is not None and not any(normalize_name('feature',v)==owner or normalize_name('requested_object',v)==owner for v in values):raise ValueError('OWNER_NOT_WITNESSED')
        if not any(normalize_name('attribute',v)==attribute for v in values):raise ValueError('ATTRIBUTE_NOT_WITNESSED')
    elif rule=='source_claim':
        if kind!='source_binding' or not isinstance(value,dict):raise ValueError('SOURCE_SCHEMA')
        for key in ('source_sha256','source_path','source_label'):
            if value.get(key) is not None and value[key] not in text:raise ValueError('SOURCE_VALUE_NOT_WITNESSED')
        if any(loc not in text for loc in value.get('locators',[])):raise ValueError('LOCATOR_NOT_WITNESSED')
        if not any(value.get(k) for k in ('source_sha256','source_path','source_label','locators')):raise ValueError('EMPTY_SOURCE_BINDING')
    elif rule=='task_semantics':
        if kind!='task_obligation' or value not in TASK_RULES or not re.search(TASK_RULES[value],text,re.I):raise ValueError('TASK_NOT_WITNESSED')
        # Semantic adequacy beyond this necessary token filter is the explicit
        # AI reviewer decision, retained for independent re-review.
    elif rule=='criterion_semantics':
        if kind!='comparison_criterion' or value not in CRITERION_RULES or not re.search(CRITERION_RULES[value],text,re.I):raise ValueError('CRITERION_NOT_WITNESSED')
    elif rule=='metric_semantics':
        if kind!='distance_metric' or not isinstance(value,dict) or not value:raise ValueError('METRIC_SCHEMA')
        for field,component in value.items():
            pattern=METRIC_RULES.get((field,component))
            if not pattern or not re.search(pattern,text,re.I):raise ValueError('METRIC_COMPONENT_NOT_WITNESSED')
    elif rule=='explicit_requirement':
        if kind!='input_requirement' or value!={'field':'selected_geometry','requirement':'REQUIRED'} or not re.search(r'provide|select.*area|영역.*지정|필요',text,re.I):raise ValueError('REQUIREMENT_NOT_WITNESSED')
    else:raise ValueError('UNKNOWN_EXTRACTION_RULE')
    if atom['task_id']!='query' and not atom.get('task_scope_note'):raise ValueError('COMPOSITE_SCOPE_REQUIRED')


def compile_review(raw_bytes,review):
    if sha(raw_bytes)!=review.get('raw_sha256'):raise ValueError('RAW_HASH_MISMATCH')
    if review.get('contract_sha256')!=CONTRACT_SHA256:raise ValueError('CONTRACT_MISMATCH')
    if review.get('review_authority')!='AI_MEASUREMENT_REVIEW' or review.get('human_review_complete') is not False:
        raise ValueError('AI_REVIEW_AUTHORITY_REQUIRED')
    if review.get('status')!='COMPLETE' or not review.get('reviewer_id') or not review.get('whole_response_review_note'):
        raise ValueError('FULL_RESPONSE_REVIEW_REQUIRED')
    raw=json.loads(raw_bytes)
    if (raw.get('case_id')!=review.get('case_id') or raw.get('method')!=review.get('method')
            or sha(str(raw.get('query','')).encode())!=review.get('query_sha256')):
        raise ValueError('RAW_CASE_METHOD_QUERY_MISMATCH')
    plan=raw.get('plan')
    fields=set(plan) if isinstance(plan,dict) else set()
    field_review=review.get('structured_field_review') or {}
    if set(field_review)!=fields or any(not str(v).strip() for v in field_review.values()):raise ValueError('UNREVIEWED_STRUCTURED_FIELD')
    # Exact complete observed text, including truncated response, is audited.
    pointer_path,text=response_surface(raw)
    receipt=review.get('narrative_review') or {}
    if receipt.get('pointer')!=pointer_path or receipt.get('text_sha256')!=sha(text.encode()) or receipt.get('characters')!=len(text):raise ValueError('UNREVIEWED_NARRATIVE')
    if not isinstance(review.get('claim_sidecar'),list):raise ValueError('OTHER_CLAIM_REVIEW_REQUIRED')
    for claim in review['claim_sidecar']:
        witness_value(raw,claim['witness'])
        if claim.get('disposition') not in {'OUTSIDE_RQ1_FACTUAL_CLAIM','NON_ASSERTED_OR_HYPOTHETICAL','REPEATED_INSTANCE_CLAIM'} or not claim.get('review_note'):
            raise ValueError('CLAIM_DISPOSITION_REQUIRED')
    atoms=review.get('atoms')
    if not isinstance(atoms,list):raise ValueError('EXPLICIT_OBSERVED_ATOMS_REQUIRED')
    ids=set();identities=set()
    for atom in atoms:
        check_atom(raw,atom)
        if not atom.get('prediction_id') or atom['prediction_id'] in ids:raise ValueError('DUPLICATE_PREDICTION_ID')
        ids.add(atom['prediction_id'])
        key=(atom['kind'],atom['task_id'],canonical_json(atom['value']))
        if key in identities and not atom.get('independent_assertion_reason'):raise ValueError('DUPLICATE_REQUIRES_ASSERTION_REASON')
        identities.add(key)
    return {'case_id':review['case_id'],'method':review['method'],'raw_sha256':review['raw_sha256'],
            'query_sha256':review['query_sha256'],'contract_sha256':CONTRACT_SHA256,
            'raw_status':raw.get('status'),'prediction_atoms':atoms,'complete_grounding_extraction':True,
            'annotation_authority':'AI_MEASUREMENT_REVIEW_NOT_INDEPENDENT_HUMAN_REVIEW',
            'human_review_complete':False,'review_sha256':sha(canonical_json(review).encode()),
            'claim_sidecar':review['claim_sidecar']}


def response_surface(raw):
    plan=raw.get('plan')
    if isinstance(plan,dict) and isinstance(plan.get('answer'),str):return '/plan/answer',plan['answer']
    calls=raw.get('calls') or []
    for index,call in reversed(list(enumerate(calls))):
        if isinstance(call,dict) and isinstance(call.get('raw_response'),str):return f'/calls/{index}/raw_response',call['raw_response']
    if isinstance(raw.get('candidate_answer'),str):return '/candidate_answer',raw['candidate_answer']
    return None,''  # Observed no response; still requires explicit AI review.


def prepare_review_template(raw_bytes,*,case_id,method,query):
    """Fresh raw always receives an uncompleted form; previous reviews not reused."""
    raw=json.loads(raw_bytes);plan=raw.get('plan')
    path,text=response_surface(raw)
    return {'case_id':case_id,'method':method,'query_sha256':sha(query.encode()),'raw_sha256':sha(raw_bytes),
            'contract_sha256':CONTRACT_SHA256,'status':'REVIEW_REQUIRED','review_authority':'AI_MEASUREMENT_REVIEW',
            'reviewer_id':None,'human_review_complete':False,'whole_response_review_note':None,
            'structured_field_review':{k:None for k in plan} if isinstance(plan,dict) else {},
            'narrative_review':{'pointer':path,'text_sha256':sha(text.encode()),'characters':len(text)},
            'atoms':None,'claim_sidecar':None}
