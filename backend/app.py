"""
Flask Application Factory
Entry point for the NekDek Auth backend.
"""

import re
from flask import Flask, jsonify
from flask_mail import Mail
from flask_cors import CORS
from pymongo import MongoClient

from config.config import Config
from routes.auth_routes import auth_bp
from routes.password_routes import password_bp
from routes.user_routes import user_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── CORS ────────────────────────────────────────────────────────────────
    # Allow: the exact production Vercel URL, ALL Vercel preview URLs
    # (nek-dek-auth-*.vercel.app), and common local dev origins.
    _production_url = app.config["FRONTEND_URL"].rstrip("/")
    _local_origins = [
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
    ]

    def _cors_origin_allowed(origin):
        if not origin:
            return False
        if origin == _production_url:
            return True
        if origin in _local_origins:
            return True
        # Allow any Vercel preview / branch deployment URL
        if re.match(r"https://nek-dek-auth[\w-]*\.vercel\.app$", origin):
            return True
        return False

    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": _cors_origin_allowed
            }
        }
    )

    # ── MongoDB ───────────────────────────────────────────────────────────────
    client = MongoClient(app.config["MONGO_URI"], connect=False)  # lazy connect
    app.db = client[app.config["DB_NAME"]]

    # ── Flask-Mail ────────────────────────────────────────────────────────────
    mail = Mail(app)
    app.mail = mail

    # ── Blueprints ────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(password_bp)
    app.register_blueprint(user_bp)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "message": "NekDek Auth API is running."}), 200

    # ── 404 / 405 handlers ────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "message": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal error: {e}")
        return jsonify({"success": False, "message": "Internal server error."}), 500

    return app


# ── Development entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=True)
