"""Loopback-only research viewer. Start: python -m tools.scie_results_ui.server."""
from __future__ import annotations
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from urllib.parse import parse_qs, urlsplit
from .adapter import BASE, ResultsAdapter

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / 'static'
_CACHE = {}
_LOCK = threading.Lock()


def get_snapshot(root):
    """Bound repeated page/artifact reads; no experiments or background polling."""
    key = str(root)
    with _LOCK:
        cached = _CACHE.get(key)
        if cached and time.monotonic() - cached[0] < 15:
            return cached[1], cached[2]
        adapter = ResultsAdapter(root)
        dashboard = adapter.dashboard()
        _CACHE[key] = (time.monotonic(), adapter, dashboard)
        return adapter, dashboard


class Handler(BaseHTTPRequestHandler):
    root = ROOT

    def respond(self, data: bytes, content_type: str, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path in ('/', BASE, BASE + '/'):
            path = STATIC / 'index.html'
            if path.is_file():
                return self.respond(path.read_bytes(), 'text/html; charset=utf-8')
        if url.path.startswith(BASE + '/static/'):
            name = url.path[len(BASE + '/static/'):]
            path = (STATIC / name).resolve()
            if path.is_relative_to(STATIC.resolve()) and path.is_file() and path.suffix in ('.js', '.css'):
                return self.respond(path.read_bytes(), 'text/javascript; charset=utf-8' if path.suffix == '.js' else 'text/css; charset=utf-8')
        if url.path in (BASE + '/api/dashboard', BASE + '/artifact'):
            adapter, dashboard = get_snapshot(self.root)
            if url.path.endswith('/api/dashboard'):
                return self.respond(json.dumps(dashboard, ensure_ascii=False, allow_nan=False).encode('utf-8'), 'application/json; charset=utf-8')
            key = parse_qs(url.query).get('path', [''])[0]
            path = adapter.allowed.get(key)
            if path and path.is_file():
                # Plain text only: untrusted markdown/JSON must not become executable HTML.
                return self.respond(path.read_bytes(), 'text/plain; charset=utf-8')
        self.respond(b'Not found', 'text/plain', 404)

    def do_POST(self):
        self.respond(b'Read-only research viewer', 'text/plain', 405)

    do_PUT = do_POST
    do_PATCH = do_POST
    do_DELETE = do_POST


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8001)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Research-only results: http://localhost:{args.port}{BASE}', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
