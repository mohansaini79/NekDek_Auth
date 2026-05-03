"""
Password Reset Routes
POST /api/password/forgot   – Request reset OTP
POST /api/password/verify   – Verify reset OTP (returns short-lived reset token)
POST /api/password/reset    – Set new password (using reset token)
"""

from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash
import jwt

from models.user_model import get_users_collection
from utils.validators import validate_password
from utils.email_utils import generate_otp, send_otp_email

password_bp = Blueprint("password", __name__, url_prefix="/api/password")

RESET_TOKEN_EXPIRY_MINUTES = 15  # short-lived token after OTP verified


# ─── Forgot Password – send OTP ───────────────────────────────────────────────
@password_bp.route("/forgot", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400

    db = current_app.db
    users = get_users_collection(db)
    user = users.find_one({"email": email})

    # ── Security: always return 200 to avoid email enumeration ───────────────
    if not user:
        return jsonify({
            "success": True,
            "message": "If that email exists, an OTP has been sent.",
        }), 200

    otp = generate_otp()
    expiry_minutes = current_app.config["OTP_EXPIRY_MINUTES"]
    users.update_one(
        {"email": email},
        {"$set": {
            "otp": otp,
            "otpExpiry": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
            "otpPurpose": "reset",
            "updatedAt": datetime.now(timezone.utc),
        }},
    )

    send_otp_email(current_app.mail, email, otp, purpose="reset")

    return jsonify({
        "success": True,
        "message": "If that email exists, an OTP has been sent.",
        "email": email,
    }), 200


# ─── Verify Reset OTP ─────────────────────────────────────────────────────────
@password_bp.route("/verify", methods=["POST"])
def verify_reset_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = (data.get("otp") or "").strip()

    if not email or not otp:
        return jsonify({"success": False, "message": "Email and OTP are required."}), 400

    db = current_app.db
    users = get_users_collection(db)
    user = users.find_one({"email": email})

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
    if user.get("otpPurpose") != "reset":
        return jsonify({"success": False, "message": "No pending reset OTP."}), 400

    otp_expiry = user.get("otpExpiry")
    if otp_expiry and otp_expiry.tzinfo is None:
        otp_expiry = otp_expiry.replace(tzinfo=timezone.utc)

    if not otp_expiry or datetime.now(timezone.utc) > otp_expiry:
        return jsonify({"success": False, "message": "OTP has expired. Please request again."}), 410

    if user.get("otp") != otp:
        return jsonify({"success": False, "message": "Invalid OTP."}), 400

    # ── Clear OTP and issue a short-lived reset JWT ──────────────────────────
    users.update_one(
        {"email": email},
        {"$set": {"otp": None, "otpExpiry": None, "otpPurpose": None,
                  "updatedAt": datetime.now(timezone.utc)}},
    )

    cfg = current_app.config
    expiry = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)
    reset_token = jwt.encode(
        {"sub": str(user["_id"]), "email": email, "purpose": "reset", "exp": expiry},
        cfg["JWT_SECRET_KEY"],
        algorithm="HS256",
    )

    return jsonify({
        "success": True,
        "message": "OTP verified. Proceed to reset your password.",
        "resetToken": reset_token,
    }), 200


# ─── Reset Password ───────────────────────────────────────────────────────────
@password_bp.route("/reset", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    reset_token = (data.get("resetToken") or "").strip()
    new_password = data.get("password") or ""

    if not reset_token or not new_password:
        return jsonify({"success": False, "message": "Reset token and new password are required."}), 400

    # ── Validate password strength ───────────────────────────────────────────
    valid, msg = validate_password(new_password)
    if not valid:
        return jsonify({"success": False, "message": msg}), 400

    # ── Decode reset token ───────────────────────────────────────────────────
    cfg = current_app.config
    try:
        payload = jwt.decode(reset_token, cfg["JWT_SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Reset session expired. Please start again."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Invalid reset token."}), 401

    if payload.get("purpose") != "reset":
        return jsonify({"success": False, "message": "Invalid reset token."}), 401

    email = payload.get("email")
    db = current_app.db
    users = get_users_collection(db)

    hashed_pw = generate_password_hash(new_password)
    users.update_one(
        {"email": email},
        {"$set": {"password": hashed_pw, "updatedAt": datetime.now(timezone.utc)}},
    )

    return jsonify({"success": True, "message": "Password reset successfully. You can now log in."}), 200
