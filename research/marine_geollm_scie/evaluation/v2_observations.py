"""Post-run normalization of emitted output only; never consumes GOLD or source text."""
from copy import deepcopy
from research.marine_geollm_scie.runners.execution_report import normalized_production

TRACE_FIELDS = ('execution_attempted', 'execution_started', 'tool_called', 'sql_executed', 'execution_succeeded')


def normalized_trace(row):
    raw = row.get('execution_observation') or {}
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


def normalize(row):
    trace = normalized_trace(row)
    emitted = row.get('emitted_answer')
    if isinstance(emitted, dict):
        answer = deepcopy(emitted)
        origin = 'emitted_answer'
    elif isinstance((row.get('final_state') or {}).get('final_dict'), dict):
        final = row['final_state']['final_dict']
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
            'retrieved_text_used_as_answer': False, 'gold_used_for_mapping': False}
