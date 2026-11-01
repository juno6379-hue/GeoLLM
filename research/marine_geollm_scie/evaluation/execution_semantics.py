"""Method-independent spatial execution telemetry; never infers spatial correctness."""
from copy import deepcopy

VERSION = 'spatial_execution_semantics_v3'
FIELDS = ('execution_attempted', 'execution_started', 'tool_called', 'sql_executed', 'execution_succeeded')


def canonical_trace(raw):
    trace = deepcopy(raw)
    complete = raw.get('observation_complete') is True
    errors = []
    for field in FIELDS:
        value = raw.get(field)
        if value is not None and type(value) is not bool:
            errors.append(field + ': invalid telemetry type')
        trace[field] = value if type(value) is bool and (complete or value is True) else None
    for consequent, antecedents in (
        ('execution_attempted', ('tool_called', 'execution_started', 'sql_executed', 'execution_succeeded')),
        ('execution_started', ('sql_executed', 'execution_succeeded')),
        ('sql_executed', ('execution_started', 'execution_succeeded')),
    ):
        if raw.get(consequent) is False and any(raw.get(k) is True for k in antecedents):
            errors.append(consequent + ': contradicts downstream execution evidence')
    if errors:
        trace.update({k: None for k in FIELDS})
        trace.update(observation_complete=False, telemetry_errors=errors, raw_observation=deepcopy(raw))
    else:
        trace['observation_complete'] = complete
        # A completed controller window with explicit no SQL dispatch is a
        # measured unsuccessful execution, including a pre-SQL tool block.
        known_no_execution = complete and all(type(raw.get(k)) is bool for k in FIELDS[:4]) and raw['sql_executed'] is False
        trace['execution_succeeded'] = (False if known_no_execution else
            raw.get('execution_succeeded') if complete and type(raw.get('execution_succeeded')) is bool else None)
    trace['execution_semantics_version'] = VERSION
    return trace
