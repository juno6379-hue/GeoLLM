from unittest.mock import MagicMock, patch

from scripts import check_mdc_connection as mdc


def test_service_and_escaped_password(monkeypatch):
    monkeypatch.setenv('ORACLE_URL', 'oracle+oracledb://reader:a%23%24@localhost:31000/?service_name=orcl')
    with patch.object(mdc, 'load_dotenv'), patch.object(mdc.oracledb, 'connect') as connect:
        mdc.connect()
        assert connect.call_args.kwargs['password'] == 'a#$'
        params = connect.call_args.kwargs['params']
        assert params.service_name == 'orcl'
        assert params.port == 31000
        assert connect.return_value.call_timeout == 10000


def test_sid_connection(monkeypatch):
    monkeypatch.setenv('ORACLE_URL', 'oracle+oracledb://reader:secret@localhost:31000/orcl')
    with patch.object(mdc, 'load_dotenv'), patch.object(mdc.oracledb, 'connect') as connect:
        mdc.connect()
        assert connect.call_args.kwargs['params'].sid == 'orcl'


def test_probe_uses_read_only_transaction_and_fixed_tables():
    conn = MagicMock()
    conn.version = 'test'
    cur = conn.cursor.return_value.__enter__.return_value
    cur.description = [('STATION_ID',)]
    cur.fetchall.side_effect = [[('STATION_ID', 'VARCHAR2')], [('test',)], [], []]
    with patch.object(mdc, 'connect') as connect:
        connect.return_value.__enter__.return_value = conn
        result = mdc.probe()
    calls = [call.args[0] for call in cur.execute.call_args_list]
    assert calls[0] == 'SET TRANSACTION READ ONLY'
    assert 'SELECT * FROM DT WHERE ROWNUM <= 2' in calls
    assert 'SELECT * FROM T_WRN_TW_BUOY WHERE ROWNUM <= 2' in calls
    assert result['status'] == 'CONNECTED'
    conn.rollback.assert_called_once()
