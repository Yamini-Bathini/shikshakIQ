"""
Vercel serverless function entry point for ShikshakIQ Flask app.

On Vercel the filesystem is read-only (except /tmp), so we:
1. Point the SQLite database to /tmp/shikshakiq.db
2. Point uploads to /tmp/uploads
3. Disable seeding on every cold start (check if DB exists first)
"""
import sys
import os

# Add the backend directory to Python path so all imports work
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# ── Vercel environment overrides ───────────────────────────────────
if os.environ.get('VERCEL', '') == '1':
    # Use /tmp for the SQLite database (only writable location on Vercel)
    os.environ['DATABASE_URL'] = os.environ.get(
        'DATABASE_URL',
        'sqlite:////tmp/shikshakiq.db'
    )
    # Use /tmp for uploads
    os.environ['UPLOAD_FOLDER'] = '/tmp/uploads'

# Import the Flask app factory
from app import create_app

# Create the Flask application
app = create_app()

# Additional health check for Vercel
@app.route('/api/vercel-health')
def vercel_health():
    from flask import jsonify
    return jsonify({
        'status': 'healthy',
        'vercel': True,
        'database': os.environ.get('DATABASE_URL', 'unknown')
    })
