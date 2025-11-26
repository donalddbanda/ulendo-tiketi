import threading
from app import db
from functools import wraps
from app.models import Users, PasswordResetCode
from flask import request, jsonify, abort, Blueprint
from flask_login import current_user, login_required, logout_user, login_user
from ..utils.email_services import send_password_reset_code_email
from sqlalchemy.exc import IntegrityError


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=["POST"])
def register():
    if current_user.is_authenticated:
        logout_user()
        return jsonify({"message": "you have been logged out"}), 200
    
    data = request.get_json()
    if not data:
        abort(400, description='data not provided')
    
    name = data.get('full_name') or data.get('name')
    email = data.get('email')  # optional
    # Public registration only allowed for passengers. Admins create other roles.
    role = 'passenger'
    password = data.get('password')
    phone_number = data.get('phone') or data.get('phone_number')

    if not all([name, phone_number, password]):
        abort(400, description='name, phone number, and password are required')

    # Generate placeholder email if not provided
    if not email:
        email = f"user_{phone_number}@ulendo.local"

    # Check uniqueness of email/phone early to give friendly errors
    if Users.query.filter_by(email=email).first():
        abort(400, description='An account with that email already exists')
    if Users.query.filter_by(phone_number=phone_number).first():
        abort(400, description='An account with that phone number already exists')
    
    user = Users(name=name, email=email, phone_number=phone_number, role=role)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # Likely a unique constraint violation; rollback and return 400
        db.session.rollback()
        # Log for server-side debugging
        print('IntegrityError on user registration:', e)
        abort(400, description='Account already exists or invalid data')
    except Exception as e:
        db.session.rollback()
        print('Error on user registration:', e)
        abort(500, description='An unexpected error occurred')
    
    return jsonify({
        "message": "account registered",
        "user":{ 
            "id": user.id,
            "full_name": user.name,
            "email": user.email,
            "phone": user.phone_number,
            "role": user.role
        }
    })

@auth_bp.route('/login', methods=["POST"])
def login():
    if current_user.is_authenticated:
        abort(400, description='You are already logged in')
    
    data = request.get_json()

    # Accept either email or phone as login identifier
    login_identifier = data.get('email') or data.get('phone') or data.get('phone_number')
    password = data.get('password')

    if not password or not login_identifier:
        abort(400, description='Email or phone number and password are required')
    
    # Try to find user by email first, then by phone
    user = Users.query.filter_by(email=login_identifier).first()
    if not user:
        user = Users.query.filter_by(phone_number=login_identifier).first()

    if not user:
        abort(400, description='Account not found')

    if not user.verify_password(password):
        abort(400, description='Invalid login credentials')
    
    login_user(user)
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "full_name": user.name,
            "email": user.email,
            "phone": user.phone_number,
            "role": user.role
        }
    })
        

@auth_bp.route('/logout', methods=["POST"])
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"})


@auth_bp.route('/whoami', methods=["GET"])
def whoami():
    """Return information about the currently authenticated user."""
    if current_user.is_anonymous:
        return jsonify({'user': None}), 200

    user = Users.query.get(current_user.get_id())
    if not user:
        return jsonify({'user': None}), 200

    return jsonify({'user': {
        'id': user.id,
        'full_name': user.name,
        'email': user.email,
        'phone': user.phone_number,
        'role': user.role
    }}), 200


def create_password_reset_code(email):
    code = PasswordResetCode(email=email)
    code.create_code()

    try:
        db.session.add(code)
        db.session.commit()
    except Exception as e:
        abort(500, description=str(e))
    
    return code.code


@auth_bp.route('/request/password-reset/', methods=["POST"])
def request_password_reset():
    data = request.get_json()
    if not data:
        abort(400, description='data not provided')
    
    email = data.get('email')
    if not email:
        abort(400, description='email required')

    if not Users.query.filter_by(email=email).first():
        abort(400, description='account not found')

    code = create_password_reset_code(email=email)
    
    # Create a thread to send emails in the background
    thread = threading.Thread(
        target=send_password_reset_code_email,
        args=(code, email)
    )
    thread.start()

    return jsonify({"message": "Password reset code sent. Check your spam if you haven't recieved it."}), 200


@auth_bp.route('/reset-password', methods=["POST"])
def reset_password():
    data = request.get_json()
    if not data:
        abort(400, description='data not provided')
    
    code = data.get('code')
    new_password = data.get('new_password')
    # Accept both spellings to be forgiving: confirm_new__password (legacy) and confirm_new_password
    confirm_new_password = data.get('confirm_new_password')
    
    if not all([code, new_password, confirm_new_password]):
        abort(400, description='code, new password and password confirmation required')
    
    if new_password != confirm_new_password:
        abort(400, description='passwords do not match')

    query_code = PasswordResetCode.query.filter_by(code=code).first()
    if not query_code or  not query_code.is_code_valid():
        abort(400, description='invalid code')
    
    user = Users.query.filter_by(email=query_code.email).first()
    if not user:
        abort(400, description='account not found')
    
    user.set_password(new_password)
    try:
        db.session.commit()
    except:
        abort(500)
    
    return jsonify({"message": "password reset successful"}), 200


# ROLE BASED ACCESS
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def passenger_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() != 'passenger':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def company_owner_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() != 'company_owner':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def passenger_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() not in ['admin', 'passenger']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def company_owner_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() not in ['admin', 'company_owner']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def company_owner_not_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_authenticated and current_user.role.lower().strip() == 'company_owner':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def accounts_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() not in ["account_manager", "company_owner"]:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def conductor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() != "conductor":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def branch_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() not in ['company_owner', 'branch_manager']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def schedule_or_bus_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() not in ['bus_manager', 'schedule_manager']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def schedule_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if current_user.role.lower().strip() != 'schedule_manager':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
