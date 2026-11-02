import sys
from types import SimpleNamespace
import pytest
from research.marine_geollm_scie.runners.reliability_telemetry import ReliabilityObserver
from research.marine_geollm_scie.runners.eight_method_runner import p1_costs
from research.marine_geollm_scie.runners.graph_source_scope import install
from research.marine_geollm_scie.runners.freeze_comparison_sources import verify_parent_for_new_code


def test_async_resumptions_not_double_counted():
    observer=ReliabilityObserver('case')
    # Hashable frame stand-in, same identity on coroutine resumption.
    class Frame:
        f_globals={'__name__':'services.orchestrator.graph'}
        f_code=SimpleNamespace(co_name='execute_agent_node')
    frame=Frame()
    observer.profile(frame,'call',None);observer.profile(frame,'call',None)
    observer.complete=True
    row=observer.telemetry({'status':'WAITING_FOR_REVIEW','retry_count':0})
    assert row['tool_calls']==1 and row['human_escalation'] is True and row['retries']==0


def test_partial_observation_not_measured_zero():
    row=ReliabilityObserver('case').telemetry({})
    assert row['tool_calls'] is None and row['sql_calls'] is None and row['human_escalation'] is None


def test_hitl_and_unknown_final_status_are_distinct():
    observer=ReliabilityObserver('case');observer.complete=True
    assert observer.telemetry({'status':'NEEDS_HITL'})['human_escalation'] is True
    assert observer.telemetry({'status':'NEW_UNINSTRUMENTED_STATE'})['human_escalation'] is None
    assert observer.telemetry({})['human_escalation'] is None


def test_p1_telemetry_and_openai_usage_preserved():
    row=p1_costs({'reliability_telemetry':{'complete':True,'tool_calls':3,'sql_calls':6,'retries':0,
        'human_escalation':False,'tool_call_scope':'fixed'},'_imported_model_calls':[
        {'path':'/v1/chat/completions','response':{'usage':{'prompt_tokens':10,'completion_tokens':8}}}]})
    assert (row['tool_calls'],row['sql_calls'],row['input_tokens'],row['output_tokens'])==(3,6,10,8)


def test_source_scope_never_installs_in_operational_process(monkeypatch):
    monkeypatch.delenv('SCIE_MODEL_GRAPH',raising=False)
    with pytest.raises(RuntimeError,match='Research worker'):install({},'.')


def test_new_code_freeze_never_accepts_data_change(tmp_path):
    import hashlib
    def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
    data=tmp_path/'rows.csv';data.write_text('frozen')
    code=tmp_path/'current.py';code.write_text('old')
    parent={'relations':[{'csv_path':'rows.csv','sha256':sha(data)}],
            'files':[{'path':'current.py','sha256':sha(code)}]}
    code.write_text('new')
    assert len(verify_parent_for_new_code(parent,tmp_path,[code],root=tmp_path))==1
    data.write_text('changed')
    with pytest.raises(ValueError,match='data changed'):verify_parent_for_new_code(parent,tmp_path,[code],root=tmp_path)
