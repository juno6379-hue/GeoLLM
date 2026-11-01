import copy
import json
from research.marine_geollm_scie.baselines.tool_contract import TOOL_PLAN_SCHEMA
from research.marine_geollm_scie.runners.eight_method_runner import parse_candidate, make_prompt


def plan():
    return dict(action='search',intent='spatial_search',target_features=['Wreck'],attributes=[],
                spatial_relation='dwithin',location_text=None,radius_m=1000,crs='EPSG:4326',
                tool_calls=[{'tool_id':'spatial.query','arguments':dict(source='s101',feature_types=['Wreck'],
                    crs='EPSG:4326',reference_geometry='POINT(129 35)',relation='dwithin',radius_m=1000,
                    analysis_type='feature_search_by_radius')}],evidence_refs=[],missing_inputs=[],answer='')


def test_schema_rejects_copied_source_alternatives_without_repair():
    value=plan(); value['tool_calls'][0]['arguments']['source']=['s101','marine_places','navigation_aids']
    original=copy.deepcopy(value)
    decoded,valid,errors=parse_candidate(json.dumps(value),schema=TOOL_PLAN_SCHEMA)
    assert not valid and errors and decoded==original and value==original


def test_valid_typed_call_retains_all_values():
    value=plan();decoded,valid,errors=parse_candidate(json.dumps(value),schema=TOOL_PLAN_SCHEMA)
    assert valid and not errors and decoded==value


def test_schema_is_syntax_not_authority_or_slot_completion():
    value=plan(); args=value['tool_calls'][0]['arguments'];args.pop('reference_geometry');args['crs']=None
    decoded,valid,_=parse_candidate(json.dumps(value),schema=TOOL_PLAN_SCHEMA)
    assert valid and decoded['tool_calls'][0]['arguments']==args


def test_only_tool_condition_gets_typed_interface():
    case={'query':'Find requested objects','spatial_context':{}};packet={'evidence_text':''};profile={}
    direct=make_prompt(case,packet,profile,tools=False);agent=make_prompt(case,packet,profile,tools=True)
    assert '"oneOf"' not in direct and '"oneOf"' in agent
    assert 'exact FC code]' not in agent and 'source: s101|marine_places' not in agent
    assert 'No domain tools available' in direct
