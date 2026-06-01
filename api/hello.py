"""Minimal Flask test - no heavy imports."""
from flask import Flask, jsonify

# Minimal Flask app - no heavy dependencies
hello_app = Flask(__name__)

@hello_app.route('/')
def hello():
    return jsonify({
        'status': 'ok',
        'message': 'Vercel Python runtime is working!'
    })

# WSGI entry point for Vercel
app = hello_app
