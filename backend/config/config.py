"""
Application Configuration
Loads all environment variables and provides defaults for development.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# ── Load env file from backend root ──────────────────────────────────────────
# Supports both "NekDek_Auth.env" (project convention) and standard ".env"
_base_dir = os.path.dirname(os.path.abspath(__file__))          # config/
_backend_dir = os.path.dirname(_base_dir)                        # backend/
_env_file = os.path.join(_backend_dir, "NekDek_Auth.env")
if not os.path.exists(_env_file):
    _env_file = os.path.join(_backend_dir, ".env")               # fallback
load_dotenv(dotenv_path=_env_file, override=True)


class Config:
    # ── Flask ────────────────────────────────────────────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # ── MongoDB ──────────────────────────────────────────────────────────────
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/nekdek_auth")
    DB_NAME = os.getenv("DB_NAME", "nekdek_auth")

    # ── JWT ──────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-super-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_EXPIRY_HOURS", "24"))
    )

    # ── Email / SMTP ─────────────────────────────────────────────────────────
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)

    # ── OTP ──────────────────────────────────────────────────────────────────
    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "5"))

    # ── CORS ─────────────────────────────────────────────────────────────────
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5500")
