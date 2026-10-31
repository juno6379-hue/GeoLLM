"""Pure B3-plan serialization into QEC. No lookup, model call or correction.

Only explicit units are normalized. All original fields remain in provenance.
Absent values are None in the typed schema and MISSING in the compiler trace.
Compilation never grants execution authority or selects an analysis/dataset.
"""
import copy
from decimal import Decimal, InvalidOperation
import re
from shared.schemas.agent import QueryExecutionContext, ExecutionSlots
from research.marine_geollm_scie.runners.matched_branches import plan_hash


def explicit_distance(value):
    if isinstance(value,dict):
        number,unit=value.get('value'),value.get('unit')
    elif isinstance(value,str):
        match=re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*(km|m)\s*',value)
        if not match: raise ValueError('DISTANCE_UNIT_OR_VALUE_UNSUPPORTED')
        number,unit=match.groups()
    else:
        raise ValueError('DISTANCE_UNIT_MISSING')
    if unit not in ('m','km') or type(number) is bool:
        raise ValueError('DISTANCE_UNIT_OR_VALUE_UNSUPPORTED')
    try:
        result=Decimal(str(number)) * (1000 if unit=='km' else 1)
    except InvalidOperation as exc:
        raise ValueError('DISTANCE_VALUE_INVALID') from exc
    if not result.is_finite(): raise ValueError('DISTANCE_VALUE_NOT_FINITE')
    # Negative/zero values are intentionally retained for the Validator.
    return float(result)


def compile_task(plan, *, query=None, request_id=None, task_index=None):
    original=copy.deepcopy(plan);digest=plan_hash(original)
    if not isinstance(plan,dict): raise TypeError('Plan must be an object')
    task=plan
    prefix='plan'
    if task_index is not None:
        task=plan['tool_calls'][task_index]
        prefix=f'plan.tool_calls[{task_index}]'
        if not isinstance(task,dict) or not isinstance(task.get('arguments'),dict):
            raise ValueError('Tool call arguments must remain an explicit object')
        values=task['arguments'];prefix_args=prefix+'.arguments'
    else:
        values=task;prefix_args=prefix
    copied={};paths={};errors=[]
    # Deliberately do not inherit omitted child fields from a global plan:
    # that could change a composite subtask's intended scope.
    mapping={'crs':'crs','reference_geometry':'reference_geometry','geometry_ref':'geometry_ref',
             'location_text':'location_text','spatial_relation':'spatial_relation',
             'analysis_type':'analysis_type','operation':'operation'}
    for source,target in mapping.items():
        if source in values:
            copied[target]=copy.deepcopy(values[source]);paths[target]=prefix_args+'.'+source
    if 'relation' in values:
        if copied.get('spatial_relation') is not None and copied['spatial_relation']!=values['relation']:
            errors.append('CONFLICTING_EXPLICIT_RELATIONS')
        else:
            copied['spatial_relation']=copy.deepcopy(values['relation'])
            paths['spatial_relation']=prefix_args+'.relation'
    targets=values.get('target_features',values.get('feature_types'))
    if targets is not None:
        copied['target_features']=copy.deepcopy(targets)
        paths['target_features']=prefix_args+('.target_features' if 'target_features' in values else '.feature_types')
    elif 'feature' in values:
        copied['target_features']=[values['feature']]
        paths['target_features']=prefix_args+'.feature (scalar to singleton list)'
    tool=task.get('tool_id') if task_index is not None else values.get('tool')
    if tool is not None:
        copied['tool']=tool;paths['tool']=prefix+('.tool_id' if task_index is not None else '.tool')
    distances=[]
    for key in ('distance_m','radius_m','distance'):
        if key not in values or values[key] is None: continue
        try:
            value=explicit_distance(values[key]) if key=='distance' else values[key]
            if type(value) not in (int,float): raise ValueError('DISTANCE_VALUE_TYPE_INVALID')
            distances.append((key,value))
        except ValueError as exc:
            errors.append(str(exc))
    if distances:
        if len({v for _,v in distances})!=1:
            errors.append('CONFLICTING_EXPLICIT_DISTANCES')
        else:
            copied['distance_m']=distances[0][1]
            paths['distance_m']=[prefix_args+'.'+k for k,_ in distances]
    filters={k:copy.deepcopy(values[k]) for k in ('source','dataset','dataset_id','dataset_version','filters') if k in values}
    copied['filters']=filters
    required=('crs','reference_geometry','target_features','tool')
    missing=[k for k in required if copied.get(k) is None or copied.get(k)==[]]
    if not any(filters.get(k) is not None for k in ('source','dataset','dataset_id')):
        missing.append('dataset')
    copied['unresolved_slots']=missing
    trace={'compiler_version':'lossless_qec_v1','compiled_from_plan_hash':digest,'original_plan':original,
        'task_index':task_index,'field_sources':paths,'missing_fields':{k:'MISSING' for k in missing},
        'allowed_transformations':['explicit m/km conversion','feature scalar to singleton list','literal field renaming'],
        'semantic_inference_performed':False,'dataset_reselection_performed':False,
        'errors':errors}
    qec=None
    if not errors:
        try:
            slots=ExecutionSlots(**copied)
            # Pydantic coercion is not permitted to silently fix plan types.
            for key,value in copied.items():
                if key!='distance_m' and getattr(slots,key)!=value:
                    raise ValueError('SCHEMA_COERCION_NOT_LOSSLESS:'+key)
            qec=QueryExecutionContext(request_id=request_id,original_query=query,plan_hash=digest,
                slots=slots,route_plan={'analysis_type':copied.get('analysis_type'),
                'original_tool':tool,'execution_ready':False},provenance={'lossless_compilation':trace})
        except (ValueError,TypeError) as exc:
            trace['errors'].append(type(exc).__name__+':SCHEMA_REJECTED_WITHOUT_REPAIR')
    return {'qec':qec,'trace':trace,'compilation_valid':qec is not None}


def compile_plan(plan, **kwargs):
    calls=plan.get('tool_calls') if isinstance(plan,dict) else None
    if calls:
        return [compile_task(plan,task_index=i,**kwargs) for i in range(len(calls))]
    return [compile_task(plan,**kwargs)]


def validate_without_repair(compiled, validator):
    """Detect a validator/adapter that silently changes the experiment input.

    The validator may verify explicit bindings and add reasons, but it cannot
    repair slots or choose a source when the candidate omitted it. No execution
    callback may run after this check raises.
    """
    if not compiled['compilation_valid']:
        raise ValueError('LOSSLESS_COMPILATION_FAILED')
    qec=compiled['qec'].model_copy(deep=True)
    before=qec.slots.model_dump(mode='json')
    checked=validator(qec)
    after=checked.slots.model_dump(mode='json')
    if before!=after:
        raise ValueError('VALIDATOR_CHANGED_SEMANTIC_SLOTS')
    if 'dataset' in compiled['trace']['missing_fields'] and checked.data_bindings:
        raise ValueError('VALIDATOR_SELECTED_MISSING_DATASET')
    explicit=qec.slots.filters
    dataset_id=next((explicit[k] for k in ('dataset_id','dataset','source') if explicit.get(k) is not None),None)
    if dataset_id is not None and any(str(getattr(b,'dataset_id',None))!=str(dataset_id) for b in checked.data_bindings):
        raise ValueError('VALIDATOR_CHANGED_EXPLICIT_DATASET')
    return checked
