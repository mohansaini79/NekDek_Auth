"""
JWT Utility
Creates and validates JSON Web Tokens using PyJWT.
"""

import jwt
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, current_app


def create_access_token(payload: dict) -> str:
    """
    Create a signed JWT.

    Args:
        payload: Dict of claims to embed (do NOT include 'exp' – added here).

    Returns:
        Signed JWT string.
    """
    cfg = current_app.config
    expiry = datetime.now(timezone.utc) + cfg["JWT_ACCESS_TOKEN_EXPIRES"]
    payload = {**payload, "exp": expiry, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, cfg["JWT_SECRET_KEY"], algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Returns:
        Decoded payload dict.

    Raises:
        jwt.ExpiredSignatureError | jwt.InvalidTokenError
    """
    cfg = current_app.config
    return jwt.decode(token, cfg["JWT_SECRET_KEY"], algorithms=["HS256"])


def jwt_required(f):
    """
    Route decorator that enforces a valid Bearer JWT in the Authorization header.
    Injects 'current_user_id' and 'current_user_email' into kwargs.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"success": False, "message": "Authorization header missing or malformed"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "message": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "message": "Invalid token."}), 401

        kwargs["current_user_id"] = payload.get("sub")
        kwargs["current_user_email"] = payload.get("email")
        return f(*args, **kwargs)

    return decorated
