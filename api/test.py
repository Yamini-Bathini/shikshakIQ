"""Minimal Vercel Python function for testing."""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    """Simple handler to verify Python runtime works on Vercel."""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = {
            'status': 'ok',
            'message': 'Vercel Python runtime is working!'
        }
        self.wfile.write(json.dumps(response).encode())
        return
