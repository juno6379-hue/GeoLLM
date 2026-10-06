"""Read-only MDC connectivity/schema probe; never prints connection credentials."""
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit, unquote, parse_qs

import oracledb
from dotenv import load_dotenv


def connect():
    load_dotenv(Path(__file__).resolve().parents[1] / '.env')
    url = urlsplit(os.environ.get('ORACLE_URL', ''))
    if not url.hostname or not url.username:
        raise ValueError('MDC_NOT_CONFIGURED')
    service = parse_qs(url.query).get('service_name', [None])[0]
    params = dict(host=url.hostname, port=url.port or 1521,
                  tcp_connect_timeout=8, retry_count=0)
    if service:
        params['service_name'] = service
    else:
        params['sid'] = url.path.lstrip('/')
    conn = oracledb.connect(user=unquote(url.username), password=unquote(url.password or ''),
                           params=oracledb.ConnectParams(**params))
    conn.call_timeout = 10000
    return conn


def probe():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            result = {'status': 'CONNECTED', 'version': conn.version, 'tables': {}}
            for name in ('DT', 'T_WRN_TW_BUOY'):
                cur.execute('SELECT column_name,data_type FROM user_tab_columns '
                            'WHERE table_name=:name ORDER BY column_id', name=name)
                columns = cur.fetchall()
                cur.execute(f'SELECT * FROM {name} WHERE ROWNUM <= 2')
                rows = cur.fetchall()
                result['tables'][name] = {'columns': columns,
                    'sample_rows': [dict(zip([d[0] for d in cur.description], r)) for r in rows]}
            conn.rollback()
            return result


if __name__ == '__main__':
    try:
        print(json.dumps(probe(), ensure_ascii=True, default=str))
    except Exception as exc:
        codes = re.findall(r'(?:ORA|DPY|DPI)-\d+', str(exc))
        print(json.dumps({'status': 'UNAVAILABLE', 'error_type': type(exc).__name__,
                          'codes': sorted(set(codes))}))
        raise SystemExit(1)
