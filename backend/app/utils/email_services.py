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


def send_employee_invitation_email(invitation_data):
    """Send employee invitation email"""
    from flask_mail import Message
    from flask import current_app
    from ..extensions import mail
    
    msg = Message(
        subject=f'Invitation to join {invitation_data["company_name"]}',
        recipients=[invitation_data['email']],
        sender=current_app.config['MAIL_DEFAULT_SENDER']
    )
    
    msg.body = f"""
    Hello {invitation_data['full_name']},
    
    You have been invited to join {invitation_data['company_name']} as a {invitation_data['role']}.
    Branch: {invitation_data['branch_name']}
    
    To accept this invitation, please visit:
    {invitation_data['invitation_link']}
    
    Or use this code: {invitation_data['invitation_code']}
    
    This invitation expires on {invitation_data['expires_at']}
    
    Best regards,
    Ulendo Tiketi Team
    """
    
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send invitation email: {e}")
