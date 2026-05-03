"""
Validation Utility
Password policy enforced with regex and helper functions.
"""

import re

# Strong password: 8+ chars, upper, lower, digit, special (@$!%*?&)
PASSWORD_REGEX = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_password(password: str) -> tuple[bool, str]:
    """
    Check password against the strong policy.

    Returns:
        (True, "") if valid, or (False, error_message) otherwise.
    """
    if not password:
        return False, "Password is required."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[@$!%*?&]", password):
        return False, "Password must contain at least one special character (@$!%*?&)."
    if not PASSWORD_REGEX.match(password):
        return False, "Password does not meet the required policy."
    return True, ""


def validate_email(email: str) -> bool:
    """Return True if email passes basic format validation."""
    return bool(EMAIL_REGEX.match(email or ""))
