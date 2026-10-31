import pytest
from research.marine_geollm_scie.baselines.lossless_qec import compile_plan,validate_without_repair


def test_explicit_units_only_and_missing_fields_remain_missing():
    plan={'feature':'Wreck','distance':'5 km','tool':'radius_search'}
    result=compile_plan(plan)[0];qec=result['qec']
    assert qec.slots.distance_m==5000
    assert qec.slots.target_features==['Wreck']
    assert qec.slots.tool=='radius_search'
    assert qec.slots.crs is None and qec.slots.reference_geometry is None
    assert result['trace']['missing_fields']['dataset']=='MISSING'
    assert qec.data_bindings==[] and qec.tool_bindings==[]
    assert result['trace']['original_plan']==plan


def test_wrong_feature_negative_distance_and_dataset_never_corrected():
    plan={'feature':'WreckTypo','distance':{'value':-5,'unit':'km'},'tool':'wrong_tool','source':'wrong_dataset','crs':'EPSG:999999'}
    qec=compile_plan(plan)[0]['qec']
    assert qec.slots.target_features==['WreckTypo']
    assert qec.slots.distance_m==-5000
    assert qec.slots.crs=='EPSG:999999'
    assert qec.slots.filters['source']=='wrong_dataset'


def test_missing_child_fields_not_filled_from_other_tasks_or_global_plan():
    plan={'crs':'EPSG:4326','target_features':['Wreck'],
        'tool_calls':[{'tool_id':'spatial.query','arguments':{'radius_m':5000}},
                      {'tool_id':'spatial.query','arguments':{'crs':'EPSG:5179','feature_types':['Wrong']}}]}
    tasks=compile_plan(plan)
    assert tasks[0]['qec'].slots.crs is None
    assert tasks[0]['qec'].slots.target_features==[]
    assert tasks[1]['qec'].slots.distance_m is None
    assert tasks[1]['qec'].slots.target_features==['Wrong']


def test_conflicting_values_or_implicit_units_are_rejected_without_repair():
    for plan in ({'distance_m':1000,'distance':'5 km'},{'distance':5},{'distance':'five km'}):
        result=compile_plan(plan)[0]
        assert result['qec'] is None
        assert result['trace']['errors']
        assert result['trace']['original_plan']==plan


def test_validator_cannot_silently_fill_crs_or_fix_feature():
    compiled=compile_plan({'feature':'WreckTypo','distance':'5 km','tool':'radius_search'})[0]
    def repair(qec):
        qec.slots.crs='EPSG:4326'
        qec.slots.target_features=['Wreck']
        return qec
    with pytest.raises(ValueError,match='VALIDATOR_CHANGED_SEMANTIC_SLOTS'):
        validate_without_repair(compiled,repair)
    assert compiled['qec'].slots.crs is None
    assert compiled['qec'].slots.target_features==['WreckTypo']
