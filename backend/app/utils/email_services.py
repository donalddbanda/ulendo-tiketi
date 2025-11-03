from flask_mail import Message
from app import mail
from flask import app

def send_password_reset_link(email, reset_url):
    try:
        msg = Message(
            subject="Ulendo Tiketi - Password Reset Request",
            recipients=[email],
            sender=app.config['MAIL_DEFAULT_SENDER'],
            body=f"""
Hello,

You requested a password reset for your Ulendo Tiketi account.

Click the link below to reset your password:
{reset_url}

This link will expire in 15 minutes.

If you didn't request this, please ignore this email.

Best regards,
Ulendo Tiketi Team
            """.strip()
        )

        mail.send(msg)

        # app.logger.info(f"Password reset email sent to {email}")
        return True  # ← SUCCESS

    except Exception as e:
        # app.logger.error(f"Failed to send password reset email to {email}: {str(e)}")
        return False  # ← FAILURE