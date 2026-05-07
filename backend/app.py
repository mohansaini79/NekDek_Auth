"""
Flask Application Factory
Entry point for the NekDek Auth backend.
"""

import re
from flask import Flask, jsonify, request, make_response
from flask_mail import Mail
from pymongo import MongoClient

from config.config import Config
from routes.auth_routes import auth_bp
from routes.password_routes import password_bp
from routes.user_routes import user_bp


# ── Allowed origins (module-level) ────────────────────────────────────────────
_LOCAL_ORIGINS = {
    "http://localhost:5500", "http://127.0.0.1:5500",
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:5000", "http://127.0.0.1:5000",
}
# Matches production + any Vercel preview/branch URL:
#   https://nek-dek-auth.vercel.app
#   https://nek-dek-auth-git-main-xyz.vercel.app  etc.
_VERCEL_PATTERN = re.compile(r"^https://nek-dek-auth[\w-]*\.vercel\.app$")


def _is_origin_allowed(origin: str, production_url: str) -> bool:
    if not origin:
        return False
    if origin == production_url:
        return True
    if origin in _LOCAL_ORIGINS:
        return True
    if _VERCEL_PATTERN.match(origin):
        return True
    return False


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    _production_url = app.config["FRONTEND_URL"].rstrip("/")

    # ── CORS – manual handlers ────────────────────────────────────────────────
    # We use a manual approach instead of flask-cors because the callable-origin
    # API can silently fail to set headers on OPTIONS preflight requests when
    # running under gunicorn on Render.  This is explicit and always reliable.

    @app.before_request
    def handle_preflight():
        """Respond immediately to OPTIONS preflight so CORS headers are set."""
        if request.method == "OPTIONS":
            origin = request.headers.get("Origin", "")
            resp = make_response("", 200)
            if _is_origin_allowed(origin, _production_url):
                resp.headers["Access-Control-Allow-Origin"] = origin
                resp.headers["Access-Control-Allow-Credentials"] = "true"
                resp.headers["Access-Control-Allow-Methods"] = (
                    "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                )
                resp.headers["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-Requested-With"
                )
                resp.headers["Access-Control-Max-Age"] = "600"
                resp.headers["Vary"] = "Origin"
            return resp

    @app.after_request
    def apply_cors(response):
        """Add CORS headers to every non-OPTIONS response."""
        origin = request.headers.get("Origin", "")
        if _is_origin_allowed(origin, _production_url):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"
        return response

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
