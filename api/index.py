"""
Minimal standalone Flask for Vercel - tests Python runtime works.
"""
import sys
import os

from flask import Flask, jsonify

flask_app = Flask(__name__)

@flask_app.route('/')
def root():
    return jsonify({"status": "ok", "message": "Python runtime works"})

@flask_app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@flask_app.route('/debug')
def debug():
    return jsonify({
        "cwd": os.getcwd(),
        "vercel": os.environ.get('VERCEL', 'not set'),
        "vercel_env": os.environ.get('VERCEL_ENV', 'not set'),
        "python": sys.version,
        "path": sys.path[:5]
    })

class _StripPrefixMiddleware:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith('/api/'):
            environ['PATH_INFO'] = path[4:]
        elif path == '/api':
            environ['PATH_INFO'] = '/'
        return self.wsgi_app(environ, start_response)

app = _StripPrefixMiddleware(flask_app)
