"""
Authentication Routes
POST /api/auth/signup        – Register new user + send OTP
POST /api/auth/verify-otp    – Verify signup OTP, activate account
POST /api/auth/login         – Login (email + password)
POST /api/auth/resend-otp    – Resend signup OTP
"""

from datetime import datetime, timezone, timedelta

from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from models.user_model import get_users_collection, build_user_doc, serialize_user
from utils.validators import validate_password, validate_email
from utils.jwt_utils import create_access_token
from utils.email_utils import generate_otp, send_otp_email

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# ─── Signup ───────────────────────────────────────────────────────────────────
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    # ── Validate inputs ──────────────────────────────────────────────────────
    if not name:
        return jsonify({"success": False, "message": "Name is required."}), 400
    if not validate_email(email):
        return jsonify({"success": False, "message": "Invalid email address."}), 400

    valid, msg = validate_password(password)
    if not valid:
        return jsonify({"success": False, "message": msg}), 400

    db = current_app.db
    users = get_users_collection(db)

    # ── Check duplicate ──────────────────────────────────────────────────────
    if users.find_one({"email": email}):
        return jsonify({"success": False, "message": "Email is already registered."}), 409

    # ── Create user with OTP ─────────────────────────────────────────────────
    hashed_pw = generate_password_hash(password)
    user_doc = build_user_doc(name, email, hashed_pw)

    otp = generate_otp()
    expiry_minutes = current_app.config["OTP_EXPIRY_MINUTES"]
    user_doc["otp"] = otp
    user_doc["otpExpiry"] = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    user_doc["otpPurpose"] = "signup"

    users.insert_one(user_doc)

    # ── Send OTP email ───────────────────────────────────────────────────────
    sent = send_otp_email(current_app.mail, email, otp, purpose="verification")
    if not sent:
        # Still created; user can resend
        current_app.logger.warning(f"[Signup] OTP email failed for {email}")

    return jsonify({
        "success": True,
        "message": "Account created. Please check your email for the OTP.",
        "email": email,
    }), 201


# ─── Verify OTP ───────────────────────────────────────────────────────────────
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
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
    if user.get("isVerified"):
        return jsonify({"success": False, "message": "Account is already verified."}), 400
    if user.get("otpPurpose") != "signup":
        return jsonify({"success": False, "message": "No pending OTP for signup."}), 400

    # ── Check OTP + expiry ───────────────────────────────────────────────────
    otp_expiry = user.get("otpExpiry")
    if otp_expiry and otp_expiry.tzinfo is None:
        otp_expiry = otp_expiry.replace(tzinfo=timezone.utc)

    if not otp_expiry or datetime.now(timezone.utc) > otp_expiry:
        return jsonify({"success": False, "message": "OTP has expired. Please request a new one."}), 410

    if user.get("otp") != otp:
        return jsonify({"success": False, "message": "Invalid OTP."}), 400

    # ── Activate account ─────────────────────────────────────────────────────
    users.update_one(
        {"email": email},
        {"$set": {"isVerified": True, "otp": None, "otpExpiry": None, "otpPurpose": None,
                  "updatedAt": datetime.now(timezone.utc)}},
    )

    return jsonify({"success": True, "message": "Email verified successfully. You can now log in."}), 200


# ─── Resend OTP ───────────────────────────────────────────────────────────────
@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"success": False, "message": "Email is required."}), 400

    db = current_app.db
    users = get_users_collection(db)
    user = users.find_one({"email": email})

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404
    if user.get("isVerified"):
        return jsonify({"success": False, "message": "Account already verified."}), 400

    otp = generate_otp()
    expiry_minutes = current_app.config["OTP_EXPIRY_MINUTES"]
    users.update_one(
        {"email": email},
        {"$set": {
            "otp": otp,
            "otpExpiry": datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes),
            "otpPurpose": "signup",
            "updatedAt": datetime.now(timezone.utc),
        }},
    )

    sent = send_otp_email(current_app.mail, email, otp, purpose="verification")
    if not sent:
        return jsonify({"success": False, "message": "Failed to send OTP email. Try again."}), 500

    return jsonify({"success": True, "message": "New OTP sent to your email."}), 200


# ─── Login ────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    db = current_app.db
    users = get_users_collection(db)
    user = users.find_one({"email": email})

    if not user or not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    if not user.get("isVerified"):
        return jsonify({
            "success": False,
            "message": "Email not verified. Please verify your email first.",
            "needsVerification": True,
            "email": email,
        }), 403

    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})

    return jsonify({
        "success": True,
        "message": "Login successful.",
        "token": token,
        "user": serialize_user(user),
    }), 200
