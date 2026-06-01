"""
Vercel serverless function entry point for ShikshakIQ Flask app.

Vercel looks for an `app` object in this file.
All API routes (/api/*) are routed here by vercel.json.
"""
import sys
import os

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# On Vercel, the filesystem is read-only except /tmp
# Point SQLite database and uploads to /tmp/
if os.environ.get('VERCEL', '') == '1' or os.environ.get('VERCEL_ENV', '') != '':
    os.environ.setdefault('DATABASE_URL', 'sqlite:////tmp/shikshakiq.db')
    os.environ.setdefault('UPLOAD_FOLDER', '/tmp/uploads')
    # Create /tmp/dist so Flask's static_folder='../dist' doesn't fail
    os.makedirs('/tmp/dist', exist_ok=True)
    # Override the static folder AND the public directory so the app starts
    # even though dist won't be at the expected path (Vercel CDN serves static files)

# Import and create the Flask application
from app import create_app

# Vercel requires the Flask app instance to be named 'app'
flask_app = create_app()

# On Vercel, the static folder ../dist doesn't exist at the expected path.
# Update it to a safe fallback since Vercel CDN serves static files anyway.
if os.environ.get('VERCEL', '') == '1' or os.environ.get('VERCEL_ENV', '') != '':
    flask_app.static_folder = '/tmp/dist'

# =====================================================================
# WSGI middleware to strip /api prefix from request paths
#
# Vercel routes /api/(.*) to this function, but Flask blueprints define
# routes WITHOUT the /api prefix (e.g. /auth/login, not /api/auth/login).
# This middleware strips /api from the path before Flask processes it.
# =====================================================================
class _StripPrefixMiddleware:
    """Strips /api prefix from request path before it reaches Flask."""
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        if path.startswith('/api/'):
            environ['PATH_INFO'] = path[4:]  # strip '/api'
        elif path == '/api':
            environ['PATH_INFO'] = '/'
        # Preserve the original path in a separate header for any logging
        return self.wsgi_app(environ, start_response)

# Wrap the Flask app with the prefix-stripping middleware
app = _StripPrefixMiddleware(flask_app)
