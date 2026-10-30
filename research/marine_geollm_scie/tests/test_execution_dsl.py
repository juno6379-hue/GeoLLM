import hashlib
import json
from types import SimpleNamespace
import pytest
from research.marine_geollm_scie.baselines.execution_dsl import Executor, ResearchDatabase, ToolBlocked, DOCUMENT_SQL
from research.marine_geollm_scie.runners.compare_execution import prepare, condition


class Database:
    def __init__(self): self.calls = []
    def query(self, sql, args):
        self.calls.append((sql, args))
        return [{'source_id': 'observed:1'}]


def executor(tmp_path, coverage=None):
    p = tmp_path/'fc.json'
    p.write_text(json.dumps({'features': [{'code': 'Wreck', 'name': 'Wreck', 'definition': 'fixture', 'bindings': []}]}))
    return Executor(Database(), catalogue=p, catalogue_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
        anchors=[{'source_id': 'fixed', 'name': 'Dokdo', 'geometry': {'type': 'Point', 'coordinates': [131.8, 37.2]}}],
        coverage=coverage or {})


def test_no_plan_to_execution_success_promotion(tmp_path):
    result = executor(tmp_path).execute({'action': 'search', 'tool_calls': []})
    assert result['status'] == 'NOT_EXECUTED'
    assert result['execution_success'] is None


def test_spatial_missing_coverage_does_not_erase_document_task(tmp_path):
    tool = executor(tmp_path)
    result = tool.execute({'action': 'search', 'tool_calls': [
        {'tool_id': 'spatial.query', 'arguments': {'relation': 'dwithin', 'source': 's101', 'radius_m': 5000,
            'location_text': 'Dokdo', 'feature_types': ['Wreck']}},
        {'tool_id': 'catalogue.search', 'arguments': {'term': 'Wreck'}}]})
    assert result['status'] == 'TOOLS_PARTIAL'
    assert result['receipts'][0]['reason'] == 'SOURCE_COVERAGE_UNVERIFIED'
    assert result['receipts'][1]['status'] == 'TOOL_RETURNED'
    assert result['execution_success'] is None
    assert not tool.db.calls


def test_actual_query_receipt_requires_verified_scope(tmp_path):
    tool = executor(tmp_path, {'s101': {'scope_verified': True, 'max_radius_m_by_anchor': {'fixed': 5000}}})
    result = tool.call('spatial.query', {'relation': 'dwithin', 'source': 's101', 'radius_m': 5000,
        'location_text': 'Dokdo', 'feature_types': ['Wreck']})
    assert result['rows'][0]['source_id'] == 'observed:1'
    assert len(tool.db.calls) == 1


def test_sql_payload_is_data_and_database_allowlist(monkeypatch):
    commands = []
    def fake(command, **kwargs):
        commands.append(command); return SimpleNamespace(returncode=0, stdout='[]')
    monkeypatch.setattr('subprocess.run', fake)
    ResearchDatabase().query(DOCUMENT_SQL, {'term': "'); DROP TABLE secret; --"})
    sql = commands[0][-1]
    assert 'BEGIN READ ONLY' in sql and 'ROLLBACK' in sql
    assert 'DROP TABLE' not in sql
    assert 'shell' not in commands[0]
    with pytest.raises(ValueError): ResearchDatabase(database='production')


def test_missing_selected_aoi_and_unknown_tools_are_not_executed(tmp_path):
    tool = executor(tmp_path)
    with pytest.raises(ToolBlocked, match='EXPLICIT_AOI'):
        tool.call('spatial.query', {'relation': 'intersects'})
    with pytest.raises(ToolBlocked, match='UNSUPPORTED_TOOL'):
        tool.call('sql.execute', {'sql': 'SELECT 1'})
    assert not tool.db.calls


def test_schedule_all18_and_separate_b4_budget(tmp_path):
    cases = [{'case_id': f'case{i}', 'query': 'What is a Wreck?'} for i in range(18)]
    assert len(prepare(cases)) == 90
    assert len(prepare(cases, 5)) == 450
    called = []
    plan = dict(action='explain', intent='definition', target_features=['Wreck'], attributes=[], spatial_relation='none',
        location_text=None, radius_m=None, crs=None, tool_calls=[{'tool_id': 'catalogue.search', 'arguments': {'term': 'Wreck'}}],
        evidence_refs=[], missing_inputs=[], answer='candidate')
    def model_call(prompt, **kwargs):
        called.append(kwargs)
        return dict(status='completed', raw_response=json.dumps(plan), input_tokens=10, output_tokens=20, latency_ms=1)
    row = condition(cases[0], 'B4', {'evidence_text': '', 'packet_sha256': 'hash'}, executor(tmp_path), model='fixed', seed=42, model_call=model_call)
    assert [x['max_tokens'] for x in called] == [384, 384]
    assert row['tool_execution']['tool_calls_executed'] == 1
    assert row['execution_success'] is None
    assert row['candidate_answer_verified_by_tool_results'] is False
