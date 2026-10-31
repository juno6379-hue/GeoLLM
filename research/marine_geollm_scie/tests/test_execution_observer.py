import asyncio
import pytest
from sqlalchemy import create_engine, text
from research.marine_geollm_scie.runners.execution_observer import ExecutionObserver, q303_checks


def test_no_calls_complete_vs_missing():
    with ExecutionObserver('empty') as observer:
        pass
    result = observer.result()
    assert result['execution_attempted'] is False
    final = {'status': 'NEEDS_CLARIFICATION', 'error_code': 'AOI_REQUIRED', 'clarification_questions': ['Select area.']}
    assert all(q303_checks(final, result).values())
    assert q303_checks(final, {})['execution_attempted_false'] is None


def test_failed_sql_in_thread_is_still_attempted():
    engine = create_engine('sqlite://')
    def execute():
        with engine.connect() as connection:
            connection.execute(text('SELECT * FROM nonexistent_table'))
    with ExecutionObserver('sql') as observer:
        with pytest.raises(Exception):
            asyncio.run(asyncio.to_thread(execute))
    result = observer.result()
    assert result['execution_attempted'] is True
    assert result['execution_started'] is True
    assert result['sql_executed'] is True
    assert q303_checks({}, result)['execution_attempted_false'] is False
    engine.dispose()


def test_interruption_never_fabricates_false():
    with pytest.raises(RuntimeError):
        with ExecutionObserver('failed') as observer:
            raise RuntimeError('interrupted')
    assert observer.result()['execution_attempted'] is None


def test_actual_function_entry_without_sql_is_detected():
    namespace = {'__name__': 'services.spatial_analysis_agent.tool_executor'}
    exec('def execute_spatial_tool(): return None', namespace)
    with ExecutionObserver('tool') as observer:
        namespace['execute_spatial_tool']()
    result = observer.result()
    assert result['tool_called'] is True
    assert result['execution_attempted'] is True
    assert result['execution_started'] is False


def test_common_scoring_does_not_backfill_old_rows():
    from research.marine_geollm_scie.runners.execution_report import normalized_production, check_contract
    row = {'final_state': {'final_dict': {'status': 'NEEDS_CLARIFICATION', 'error_code': 'AOI_REQUIRED'}}}
    check = {'kind': 'observed_execution_value', 'field': 'execution_attempted', 'expected': False}
    assert check_contract(normalized_production(row), check) is None
    with ExecutionObserver('mapping') as observer:
        pass
    row['execution_observation'] = observer.result()
    assert check_contract(normalized_production(row), check) is True
    row['execution_observation']['observation_complete'] = False
    assert check_contract(normalized_production(row), check) is None
