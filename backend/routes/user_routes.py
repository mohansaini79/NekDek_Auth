"""
User / Dashboard Routes  (JWT-protected)
GET  /api/user/me          – Return current user profile
PUT  /api/user/profile     – Update name
DELETE /api/user/account   – Delete account
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, current_app
from bson import ObjectId
from werkzeug.security import check_password_hash

from models.user_model import get_users_collection, serialize_user
from utils.jwt_utils import jwt_required

user_bp = Blueprint("user", __name__, url_prefix="/api/user")


# ─── Get current user ─────────────────────────────────────────────────────────
@user_bp.route("/me", methods=["GET"])
@jwt_required
def get_me(current_user_id=None, current_user_email=None):
    db = current_app.db
    users = get_users_collection(db)
    user = users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    return jsonify({"success": True, "user": serialize_user(user)}), 200


# ─── Update profile ───────────────────────────────────────────────────────────
@user_bp.route("/profile", methods=["PUT"])
@jwt_required
def update_profile(current_user_id=None, current_user_email=None):
    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()

    if not new_name:
        return jsonify({"success": False, "message": "Name cannot be empty."}), 400

    db = current_app.db
    users = get_users_collection(db)
    users.update_one(
        {"_id": ObjectId(current_user_id)},
        {"$set": {"name": new_name, "updatedAt": datetime.now(timezone.utc)}},
    )

    user = users.find_one({"_id": ObjectId(current_user_id)})
    return jsonify({"success": True, "message": "Profile updated.", "user": serialize_user(user)}), 200


# ─── Delete account ───────────────────────────────────────────────────────────
@user_bp.route("/account", methods=["DELETE"])
@jwt_required
def delete_account(current_user_id=None, current_user_email=None):
    data = request.get_json(silent=True) or {}
    password = data.get("password") or ""

    db = current_app.db
    users = get_users_collection(db)
    user = users.find_one({"_id": ObjectId(current_user_id)})

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    if not check_password_hash(user["password"], password):
        return jsonify({"success": False, "message": "Incorrect password."}), 401

    users.delete_one({"_id": ObjectId(current_user_id)})
    return jsonify({"success": True, "message": "Account deleted."}), 200
