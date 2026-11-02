import sqlite3

import pytest

from services.orchestrator.task_store import PersistentTaskStore


def test_connection_closed_after_read_and_failed_write(tmp_path):
    store = PersistentTaskStore(str(tmp_path / 'tasks.db'))
    with store._connect() as connection:
        connection.execute('SELECT 1').fetchone()
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        connection.execute('SELECT 1')

    with pytest.raises(RuntimeError):
        with store._connect() as failed:
            failed.execute('CREATE TABLE IF NOT EXISTS rollback_probe (value TEXT)')
            failed.execute("INSERT INTO rollback_probe VALUES ('not committed')")
            raise RuntimeError('failed request')
    with pytest.raises(sqlite3.ProgrammingError, match='closed'):
        failed.execute('SELECT 1')
    with store._connect() as reopened:
        assert reopened.execute('SELECT count(*) FROM rollback_probe').fetchone()[0] == 0


def test_task_updates_survive_reopening_store(tmp_path):
    path = str(tmp_path / 'tasks.db')
    store = PersistentTaskStore(path)
    store.upsert('one', {'query': 'test', 'status': 'RUNNING'})
    store.update('one', status='COMPLETED', final_result={'count': 0})
    restored = PersistentTaskStore(path).get('one')
    assert restored['status'] == 'COMPLETED'
    assert restored['query'] == 'test'
    assert restored['final_result'] == {'count': 0}
