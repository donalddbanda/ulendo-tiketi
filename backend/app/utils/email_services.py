from flask import current_app
from ..extensions import mail
from flask_mail import Message

def send_password_reset_code_email(code, email):
    msg = Message(
        subject='Password Reset Code',
        body=f'Here is your password reset code: {code}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[email]
    )
    mail.send(msg)


def send_employee_invitation_email(invite_code: str, email: str, company_name: str = ''):
    """Send an invitation email to a prospective employee. This is a best-effort helper; if mail isn't configured it will raise from flask-mail."""
    subject = f"You're invited to join {company_name or 'a company'} on Ulendo Tiketi"
    body = f"You have been invited to join {company_name or 'a company'} on Ulendo Tiketi. Use this code to accept the invitation: {invite_code}" 
    msg = Message(
        subject=subject,
        body=body,
        sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
        recipients=[email]
    )
    try:
        mail.send(msg)
    except Exception:
        # Fail silently in environments without email configured
        current_app.logger.debug('Failed to send invite email to %s', email)
