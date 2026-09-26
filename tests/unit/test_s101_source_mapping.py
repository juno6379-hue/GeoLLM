import copy
import json
from pathlib import Path
import pytest
from scripts.audit_s101_ontology import audit
from scripts.parse_s101_feature_catalogue import parse
from services.orchestrator.marine_s101_mapping import DATA, registry, resolve_mappings, validate_mappings
from services.orchestrator.marine_mapping_execution import execute, attribute_predicates


def test_full_catalogue_bindings_and_enumerations():
    catalogue=json.loads((DATA/'s101_feature_catalogue_v2_parsed.json').read_text())
    result=audit(catalogue)
    assert result['status']=='PASS'
    feature=next(f for f in catalogue['features'] if f['code']=='ShorelineConstruction')
    assert any(b['ref']=='waterLevelEffect' and '3' in b['permitted_values'] for b in feature['bindings'])
    attr=next(a for a in catalogue['attributes'] if a['code']=='categoryOfShorelineConstruction')
    assert {'label':'Breakwater','value':'1'} in attr['listed_values']


def test_nested_fc_refs_and_complex_attributes(tmp_path):
    source=tmp_path/'fc.xml'
    source.write_text('<FC><S100_FC_ComplexAttribute><code>complex</code><subAttributeBinding><attribute ref="simple"/></subAttributeBinding></S100_FC_ComplexAttribute><S100_FC_SimpleAttribute><code>simple</code><listedValue><label>Choice</label><code>7</code></listedValue></S100_FC_SimpleAttribute><S100_FC_FeatureType><code>Test</code><attributeBinding><multiplicity><lower>0</lower><upper infinite="true"/></multiplicity><attribute ref="complex"/></attributeBinding></S100_FC_FeatureType></FC>')
    parsed=parse(source)
    assert parsed['features'][0]['bindings'][0]['ref']=='complex'
    assert parsed['features'][0]['bindings'][0]['unbounded']
    assert parsed['attributes'][0]['bindings'][0]['ref']=='simple'
    assert parsed['attributes'][1]['listed_values'][0]['value']=='7'


@pytest.mark.parametrize('change',['unknown_attribute','wrong_value','wrong_snapshot'])
def test_invalid_mapping_never_reaches_sql(change):
    document=copy.deepcopy(registry()[0]); catalogue=json.loads((DATA/'s101_feature_catalogue_v2_parsed.json').read_text())
    if change=='unknown_attribute': document['mappings'][0]['filters']['invented']=['1']
    elif change=='wrong_value': document['mappings'][0]['filters']['waterLevelEffect']=['999']
    else: document['fc_sha256']='invalid'
    with pytest.raises(ValueError): validate_mappings(document,catalogue)


def test_mapping_is_a_conjunction_and_missing_fields_are_not_wildcards():
    mapping,=resolve_mappings('수중방파제를 찾아줘')
    assert mapping['filters']=={'categoryOfShorelineConstruction':['1'],'waterLevelEffect':['3']}
    sql,params=attribute_predicates(mapping['filters'])
    assert ' AND ' in sql and 'jsonb_array_elements' in sql
    assert params[-1]==['3']


@pytest.mark.parametrize('term',['물양장','예선','선유장'])
def test_unresolved_terms_do_not_execute(term):
    outcome=execute({'query':term+'을 반경 1km 이내에서 찾아줘','task_id':'fixture'})
    assert outcome['final_dict']['error_code']=='TERM_MAPPING_UNRESOLVED'
    assert outcome['query_execution_context']['execution_status']=='NOT_RUN'


def test_radius_is_not_invented():
    outcome=execute({'query':'잠제를 찾아줘','task_id':'fixture'})
    assert outcome['final_dict']['error_code']=='RADIUS_REQUIRED'


@pytest.mark.parametrize('term',['잠제','수중방파제','물양장','예선','선유장'])
def test_source_search_cannot_complete_as_place_navigation(term):
    from services.orchestrator.fast_path_policy import instant_place_navigation_decision
    decision=instant_place_navigation_decision(term+'를 찾아줘')
    assert not decision['allowed']
    assert decision['reason']=='source_mapping_requires_validation'


@pytest.mark.parametrize('context,code',[
    ({'exclusions':['ShorelineConstruction']},'NEGATION_EXECUTION_NOT_SUPPORTED'),
    ({'target_features':['Wreck']},'COMPOUND_MAPPING_REQUIRED'),
    ({'target_features':['ShorelineConstruction','Wreck']},'COMPOUND_MAPPING_REQUIRED'),
    ({'target_features':[]},'COMPOUND_MAPPING_REQUIRED'),
])
def test_map_constraints_are_checked_before_database_access(monkeypatch,context,code):
    def forbidden(*args,**kwargs):
        pytest.fail('An unsupported constraint reached the database')
    monkeypatch.setattr('services.orchestrator.marine_mapping_execution.psycopg2.connect',forbidden)
    outcome=execute({'query':'반경 1km 이내 잠제를 찾아줘','task_id':'fixture','spatial_context':context})
    assert outcome['final_dict']['error_code']==code
    assert outcome['query_execution_context']['execution_status']=='NOT_RUN'


def test_direct_executor_preserves_negative_query_constraint(monkeypatch):
    def forbidden(*args,**kwargs):
        pytest.fail('An excluded object reached the database')
    monkeypatch.setattr('services.orchestrator.marine_mapping_execution.psycopg2.connect',forbidden)
    outcome=execute({'query':'반경 1km 이내 침선 말고 잠제를 찾아줘','task_id':'fixture'})
    assert outcome['final_dict']['error_code']=='NEGATION_EXECUTION_NOT_SUPPORTED'


def test_dangling_catalogue_reference_detected():
    catalogue=json.loads((DATA/'s101_feature_catalogue_v2_parsed.json').read_text())
    catalogue['features'][0]['bindings'][0]['ref']='nonexistent'
    assert audit(catalogue)['status']=='FAILED'


def test_shadow_surface_enum_retains_original_raw_terms():
    from scripts.run_grounded_intent_shadow import span_schema
    case={'query':'반경 1km 이내 잠제를 찾아줘','candidates':[{'candidate_id':'SPATIAL_ANALYSIS'}],
          'inputs':{'capability_contracts':{'tool.spatial_radius_search':{}},'source_mappings':resolve_mappings('잠제를 찾아줘')}}
    schema=span_schema(case)
    assert '잠제' in schema['properties']['slots']['properties']['target']['enum']
    assert '1km' in schema['properties']['slots']['properties']['radius']['enum']
    assert schema['properties']['query_quote']['enum']==[case['query']]
