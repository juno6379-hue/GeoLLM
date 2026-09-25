"""Read-only harbour catalogue SQL plan and timing."""
import ast
import json
import os
import time
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

tree = ast.parse(Path('services/spatial_analysis_agent/place_resolver.py').read_text(encoding='utf-8'))
statement = next(node.value for node in ast.walk(tree) if isinstance(node, ast.Constant) and isinstance(node.value, str) and 'SELECT min(feature_instance_id)' in node.value)
with psycopg2.connect(os.environ['S101_DB_URL']) as conn:
    conn.set_session(readonly=True)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SET LOCAL statement_timeout = '30000ms'")
        cur.execute('EXPLAIN (FORMAT JSON) ' + statement)
        print(json.dumps(cur.fetchone(),default=str),flush=True)
        start = time.monotonic()
        cur.execute(statement)
        print(json.dumps({'rows':len(cur.fetchall()),'seconds':time.monotonic()-start}),flush=True)
