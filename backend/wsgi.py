"""
WSGI entry point for Gunicorn / Render deployment.
Usage: gunicorn wsgi:application
"""

from app import create_app

application = create_app()
