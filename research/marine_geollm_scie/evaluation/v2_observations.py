"""Post-run normalization of emitted output only; never consumes GOLD or source text."""
from copy import deepcopy
from research.marine_geollm_scie.runners.execution_report import normalized_production

TRACE_FIELDS = ('execution_attempted', 'execution_started', 'tool_called', 'sql_executed', 'execution_succeeded')


def normalized_trace(row):
    raw = row.get('execution_observation') or {}
    if not isinstance(raw, dict):
        return {'observation_complete':False, **{key:None for key in TRACE_FIELDS},
                'mapping_errors':['execution_observation must be an object'], 'raw_observation':deepcopy(raw)}
    complete = raw.get('observation_complete') is True
    trace = {'observation_complete': complete, 'scope': raw.get('scope'),
             'limitations': deepcopy(raw.get('limitations', []))}
    for key in TRACE_FIELDS:
        value = raw.get(key)
        trace[key] = value if isinstance(value, bool) and (complete or value is True) else None
    # The legacy observer covers all SQLAlchemy calls, not spatial SQL alone.
    # Retain its observations as legacy evidence, but do not silently certify
    # complete GIS coverage when direct DBAPI/external GIS were unobserved.
    if raw.get('version') == 'research_execution_observer_v1':
        trace['legacy_observation'] = deepcopy(raw)
        trace['observation_complete'] = False
        for key in TRACE_FIELDS:
            trace[key] = None
    return trace


def answer_structure_errors(answer):
    """Reject malformed containers without repairing model-produced fields."""
    errors=[]
    def container(value,kind,path):
        if not isinstance(value,kind):errors.append(path+' has invalid type');return False
        return True
    def optional_string(value,path):
        if value is not None and not isinstance(value,str):errors.append(path+' must be string or null')
    for key in ('status','execution_status','blocker','dataset_snapshot_sha256'):
        optional_string(answer.get(key),key)
    if 'search_executed' in answer and answer['search_executed'] is not None and type(answer['search_executed']) is not bool:
        errors.append('search_executed must be boolean or null')
    for key in ('spatial_tasks','source_coverage','comparison','document_answer','per_task_status'):
        if key in answer and not isinstance(answer[key],dict):errors.append(key+' must be an object')
    tasks=answer.get('spatial_tasks')
    if isinstance(tasks,dict):
        for target,task in tasks.items():
            if not container(task,dict,'spatial_tasks.'+str(target)):continue
            optional_string(task.get('status'),'spatial task status')
            optional_string(task.get('source_snapshot_sha256'),'spatial source hash')
            ids=task.get('object_ids')
            if ids is not None and (not isinstance(ids,list) or any(type(x) not in (str,int) for x in ids)):
                errors.append('object_ids must be scalar ID list or null')
            evidence=task.get('object_evidence',{})
            if container(evidence,dict,'object_evidence'):
                for value in evidence.values():
                    if container(value,dict,'object evidence entry'):
                        optional_string(value.get('source_snapshot_sha256'),'object evidence source hash')
    disclosure=answer.get('source_coverage')
    if isinstance(disclosure,dict):optional_string(disclosure.get('source_snapshot_sha256'),'coverage source hash')
    document=answer.get('document_answer')
    if isinstance(document,dict):
        for key in ('features','attribute_bindings'):
            values=document.get(key,[])
            if not container(values,list,'document_answer.'+key):continue
            for value in values:
                if not container(value,dict,'document '+key+' entry'):continue
                for field in ('code','owner','attribute'):
                    optional_string(value.get(field),'document '+field)
                if 'permitted_primitives' in value and value['permitted_primitives'] is not None:
                    primitives=value['permitted_primitives']
                    if not isinstance(primitives,list) or any(not isinstance(p,str) for p in primitives):
                        errors.append('permitted_primitives must be string list')
        if 'evidence' in document:
            evidence=document['evidence']
            if container(evidence,dict,'document evidence'):
                locators=evidence.get('locators',[])
                if not isinstance(locators,list) or any(not isinstance(x,str) for x in locators):errors.append('document locators must be string list')
                links=evidence.get('claim_source_links',[])
                if not isinstance(links,list) or any(not isinstance(x,dict) for x in links):errors.append('document claim links must be object list')
                elif isinstance(links,list):
                    for link in links:optional_string(link.get('definition_locator'),'claim definition locator')
    comparison=answer.get('comparison')
    if isinstance(comparison,dict) and 'feature_definition_evidence' in comparison and not isinstance(comparison['feature_definition_evidence'],dict):
        errors.append('comparison feature_definition_evidence must be object')
    ids=answer.get('returned_object_ids')
    if ids is not None and (not isinstance(ids,list) or any(type(x) not in (str,int) for x in ids)):
        errors.append('returned_object_ids must be scalar ID list')
    tasks=answer.get('per_task_status')
    if isinstance(tasks,dict) and any(not isinstance(v,str) for v in tasks.values()):errors.append('per_task_status values must be strings')
    return errors


def normalize(row):
    trace = normalized_trace(row)
    emitted = row.get('emitted_answer')
    state=row.get('final_state')
    final=state.get('final_dict') if isinstance(state,dict) else None
    if isinstance(emitted, dict):
        answer = deepcopy(emitted)
        origin = 'emitted_answer'
    elif isinstance(final, dict):
        structured=final.get('structured_result')
        if structured is not None and not isinstance(structured,dict):
            return {'output_available':True,'answer':deepcopy(final),'trace':trace,
                    'mapping_version':'v2_emitted_only','origin':'final_state.final_dict',
                    'schema_errors':['structured_result must be an object']}
        early_errors=answer_structure_errors(structured or {})
        if early_errors:
            return {'output_available':True,'answer':deepcopy(final),'trace':trace,
                    'mapping_version':'v2_emitted_only','origin':'final_state.final_dict','schema_errors':early_errors}
        answer = normalized_production(row) or {}
        structured = final.get('structured_result') or {}
        for key in ('spatial_tasks', 'source_coverage', 'comparison', 'returned_object_ids', 'dataset_snapshot_sha256'):
            if key in structured:
                answer[key] = deepcopy(structured[key])
        answer['status'] = {'NEEDS_CLARIFICATION': 'NEEDS_USER_INPUT'}.get(final.get('status'), final.get('status'))
        answer['blocker'] = {'AOI_REQUIRED': 'MISSING_REFERENCE_GEOMETRY'}.get(final.get('error_code'), final.get('error_code'))
        answer['clarification_request'] = final.get('clarification_questions') or []
        answer['answer_text'] = final.get('answer_text', final.get('summary'))
        origin = 'final_state.final_dict'
    else:
        return {'output_available': False, 'answer': None, 'trace': trace,
                'mapping_version': 'v2_emitted_only', 'origin': None}
    answer.setdefault('status', answer.get('execution_status'))
    answer.setdefault('execution_status', answer.get('status'))
    if trace.get('execution_succeeded') is True:
        answer.setdefault('search_executed', True)
    elif trace.get('observation_complete') and trace.get('execution_attempted') is False:
        answer.setdefault('search_executed', False)
    else:
        answer.setdefault('search_executed', None)
    return {'output_available': True, 'answer': answer, 'trace': trace,
            'mapping_version': 'v2_emitted_only', 'origin': origin,
            'schema_errors':answer_structure_errors(answer),
            'retrieved_text_used_as_answer': False, 'gold_used_for_mapping': False}
