"""
User Model
Provides schema-like helpers and CRUD operations for the 'users' collection.
All passwords are stored hashed; plain-text never touches the DB.
"""

from datetime import datetime, timezone
from bson import ObjectId


# ─── Schema reference ────────────────────────────────────────────────────────
# {
#   _id:          ObjectId
#   name:         str
#   email:        str  (unique, lowercase)
#   password:     str  (bcrypt hash)
#   isVerified:   bool
#   otp:          str | None
#   otpExpiry:    datetime | None
#   otpPurpose:   "signup" | "reset" | None
#   createdAt:    datetime
#   updatedAt:    datetime
# }


def get_users_collection(db):
    """Return the users collection and ensure indexes exist."""
    col = db["users"]
    col.create_index("email", unique=True)
    return col


def build_user_doc(name: str, email: str, hashed_password: str) -> dict:
    """Create a new user document ready for insertion."""
    now = datetime.now(timezone.utc)
    return {
        "name": name,
        "email": email.lower().strip(),
        "password": hashed_password,
        "isVerified": False,
        "otp": None,
        "otpExpiry": None,
        "otpPurpose": None,
        "createdAt": now,
        "updatedAt": now,
    }


def serialize_user(user: dict) -> dict:
    """Convert a MongoDB document to a JSON-safe dict (strip sensitive data)."""
    if not user:
        return {}
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "isVerified": user.get("isVerified", False),
        "createdAt": user.get("createdAt", datetime.now(timezone.utc)).isoformat(),
    }
