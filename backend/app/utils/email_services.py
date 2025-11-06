from flask import current_app
from flask_mail import Message

def send_password_reset_code_email(code, email):
    msg = Message(
        subject='Password Reset Code',
        body=f'Here is your password reset code: {code}',
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[email]
    )
    current_app.mail.send(msg)