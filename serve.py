#!/usr/bin/env python3
"""
Simple HTTP server for Quick Log production build.
Serves dist folder and any JSON file via /file/ path.
"""

import http.server
import socketserver
import os
import sys
import urllib.parse
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
SCRIPT_DIR = Path(__file__).parent.absolute()
DIST_DIR = SCRIPT_DIR / "dist"


class QLHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)
    
    def do_GET(self):
        # Handle /file/* requests - serve any file by absolute path
        # URL format: /file/D:/path/to/file.json or /file//server/share/file.json (UNC)
        if self.path.startswith('/file/'):
            file_path_str = urllib.parse.unquote(self.path[6:])  # Remove '/file/'
            
            # Handle UNC paths: //server/share -> \\server\share
            if file_path_str.startswith('//'):
                file_path_str = file_path_str.replace('/', '\\')
            
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                if file_path.suffix == '.json':
                    self.send_header('Content-Type', 'application/json')
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, f"File not found: {file_path_str}")
                return
        
        # For all other requests, serve from dist directory
        super().do_GET()


if __name__ == "__main__":
    if not DIST_DIR.exists():
        print(f"Error: dist directory not found at {DIST_DIR}")
        print("Please run 'build.cmd' first to build the project.")
        sys.exit(1)
    
    with socketserver.TCPServer(("", PORT), QLHandler) as httpd:
        print(f"Quick Log server running at http://localhost:{PORT}")
        print(f"  Serving: {DIST_DIR}")
        print(f"  Files via: /file/<absolute_path>")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
