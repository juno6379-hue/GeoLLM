import os
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.end_headers()

def run(port, directory):
    os.chdir(directory)
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print(f"Serving 3D Tiles from '{directory}' at http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Server stopped.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Serve 3D Tiles locally with CORS enabled.')
    parser.add_argument('-p', '--port', type=int, default=8000, help='Port to serve on (default: 8000)')
    parser.add_argument('-d', '--dir', type=str, default='.', help='Directory to serve (default: current directory)')
    args = parser.parse_args()
    
    # Use absolute path
    abs_dir = os.path.abspath(args.dir)
    if not os.path.isdir(abs_dir):
        print(f"Error: Directory '{abs_dir}' does not exist.")
        exit(1)
        
    run(args.port, abs_dir)
