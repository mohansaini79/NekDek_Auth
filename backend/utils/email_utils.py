"""
Email Utility
Sends OTP emails via Flask-Mail (SMTP).
"""

import secrets
from flask_mail import Message
from flask import current_app


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure random numeric OTP."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def send_otp_email(mail, to_email: str, otp: str, purpose: str = "verification") -> bool:
    """
    Send an OTP email.

    Args:
        mail:       Flask-Mail instance
        to_email:   Recipient email address
        otp:        The one-time password string
        purpose:    'verification' | 'reset'

    Returns:
        True on success, False on failure.
    """
    subject_map = {
        "verification": "Verify Your Email – NekDek Auth",
        "reset": "Reset Your Password – NekDek Auth",
    }
    action_map = {
        "verification": "activate your account",
        "reset": "reset your password",
    }

    subject = subject_map.get(purpose, "Your OTP – NekDek Auth")
    action = action_map.get(purpose, "proceed")
    expiry = current_app.config.get("OTP_EXPIRY_MINUTES", 5)

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; background:#0f0f1a; margin:0; padding:0; }}
        .wrapper {{ max-width:520px; margin:40px auto; background:#1a1a2e; border-radius:16px;
                    border:1px solid #2d2d4e; overflow:hidden; }}
        .header {{ background:linear-gradient(135deg,#6c63ff,#48cae4); padding:32px; text-align:center; }}
        .header h1 {{ color:#fff; margin:0; font-size:24px; letter-spacing:1px; }}
        .body {{ padding:32px; color:#c8c8d4; }}
        .otp-box {{ background:#0f0f1a; border:2px dashed #6c63ff; border-radius:12px;
                    text-align:center; padding:24px; margin:24px 0; }}
        .otp {{ font-size:48px; font-weight:700; letter-spacing:12px; color:#6c63ff; }}
        .note {{ font-size:13px; color:#888; margin-top:8px; }}
        .footer {{ text-align:center; padding:16px; font-size:12px; color:#555; }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="header"><h1>🔐 NekDek Auth</h1></div>
        <div class="body">
          <p>Hello,</p>
          <p>Use the OTP below to <strong>{action}</strong>. It expires in
             <strong>{expiry} minutes</strong>.</p>
          <div class="otp-box">
            <div class="otp">{otp}</div>
            <div class="note">Do not share this code with anyone.</div>
          </div>
          <p>If you did not request this, please ignore this email.</p>
        </div>
        <div class="footer">© 2026 NekDek Auth. All rights reserved.</div>
      </div>
    </body>
    </html>
    """

    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            html=html_body,
        )
        mail.send(msg)
        return True
    except Exception as exc:
        current_app.logger.error(f"[Email] Failed to send OTP to {to_email}: {exc}")
        return False
