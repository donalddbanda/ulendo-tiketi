<<<<<<< HEAD
import jwt
from app import db
from functools import wraps
from flask import jsonify, request
from flask import Blueprint, current_app
from app.models import User, PasswordResetToken
from ..utils.email_services import send_password_reset_link
from flask_login import login_user, logout_user, current_user, login_required

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        logout_user()
    
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    role = data.get('role', 'user')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not all([name, email, password, confirm_password]):
        return jsonify({"error": "Provide name, email, password, and confirm password"}), 400
    
    if password != confirm_password:
        return jsonify({"error": "Password and confirm password mismatch"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    
    new_user = User(name=name, email=email, role=role)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "Account created successfully", "redirect": "/login"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Registration failed", "details": str(e)}), 500


@auth.route('/login', methods=["POST"])
def login():
    if current_user.is_authenticated:
        return jsonify({"message": "You are already logged in"}), 400
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    remember_me = data.get('remember', False)
    redirect = data.get('redirect')

    if not all([email, password]):
        return jsonify({"error": "Provide email and password"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user is None or not user.verify_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    login_user(user, remember=remember_me)
    role = user.role
    return jsonify({"message": "Logged in successfully", "role": role, "redirect": redirect}), 200


@auth.route('/password/reset/request', methods=["POST"])
def request_password_reset():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({
            "message": "If your email is registered, a password reset link has been sent."
        }), 200

    # Delete old tokens for this email
    PasswordResetToken.query.filter_by(email=email).delete()

    # Create new token
    token_obj = PasswordResetToken(email=email)
    token_obj.set_token()

    try:
        db.session.add(token_obj)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"DB Error: {str(e)}")
        return jsonify({"error": "Failed to process request"}), 500

    # Generate frontend reset URL
    frontend_url = current_app.config['FRONTEND_URL']
    reset_url = f"{frontend_url}/reset-password?token={token_obj.token}"

    # Send email
    if not send_password_reset_link(email, reset_url):
        return jsonify({"error": "Failed to send reset email. Please try again later."}), 500

    return jsonify({
        "message": "If your email is registered, a password reset link has been sent."
    }), 200


@auth.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "You have been logged out."}), 200


#---------- Role based access decorators -----------------------

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role.lower() != 'admin':
            return jsonify({"error": "Admin access required"}), 403
=======
import threading
from app import db
from functools import wraps
from app.models import Users, PasswordResetCode
from flask import request, jsonify, abort, Blueprint
from flask_login import current_user, login_required, logout_user
from ..utils.email_services import send_password_reset_code_email


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=["POST"])
def register():
    if current_user.is_authenticated:
        logout_user()
        return jsonify({"message": "you have been logged out"}), 200
    
    data = request.get_json()
    if not data:
        abort(400, description='data not provided')
    
    name = data.get('name')
    email = data.get('email')
    role = data.get('role', 'passenger')
    password = data.get('password')
    phone_number = data.get('phone_number')

    if not all([name, phone_number, password]):
        abort(400, description='name, phone number, and password are required')
    
    user = Users(name=name, email=email, phone_number=phone_number, role=role)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        abort(500, description=str(e))
    
    return jsonify({
        "message": "account registered",
        "user":{ 
            "id": user.id,
            "name": user.name,
            "email": user.name,
            "phone_number": user.phone_number,
            "role": user.role
        }
    })

@auth_bp.route('/login', methods=["POST"])
def login():
    if current_user.is_authenticated:
        abort(400, description='You are already logged in')
    
    data = request.get_json()

    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')

    if not password and email or phone_number:
        abort(400, description='email or phone and password required')
    
    user = Users.query.filter_by(email=email).first() if email else Users.query.filter_by(phone_number=phone_number).first()

    if not user.verify_password(password):
        abort(400, description='Invalid login credentials')
    
    return jsonify({
        "message": "Login successful",
        "user": {
            "id": id,
            "name": user.name,
            "role": user.role
        }
    })
        

@auth_bp.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"})


def create_password_reset_code(email):
    code = PasswordResetCode(email=email)
    code.create_token()

    try:
        db.session.add(code)
        db.session.commit()
    except Exception as e:
        abort(500, description=str(e))
    
    return code.code


@auth_bp.route('/reset-password/request', methods=["POST"])
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


@auth_bp.route('/rest-password', methods=["POST"])
def reset_password():
    data = request.get_json()
    if not data:
        abort(400, description='data not provided')
    
    code = data.get('code')
    new_password = data.get('new_password')
    confirm_new__password = data.get('confirm_new__password')
    
    if not all([code, new_password, confirm_new__password]):
        abort(400, description='code, new password and password confirmation required')
    
    if new_password != confirm_new__password:
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
        if current_user.is_anonnnymous:
            abort(401)
        if current_user.role.lower != 'admin':
            abort(403)
>>>>>>> ef7ae71 (feat: Implement user authentication and password reset functionality)
        return f(*args, **kwargs)
    return decorated_function


<<<<<<< HEAD
def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role.lower() != 'user':
            return jsonify({"error": "User access required"}), 403
=======
def passenger_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonnnymous:
            abort(401)
        if current_user.role.lower != 'passenger':
            abort(403)
>>>>>>> ef7ae71 (feat: Implement user authentication and password reset functionality)
        return f(*args, **kwargs)
    return decorated_function


def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
<<<<<<< HEAD
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role.lower() != 'compnay':
            return jsonify({"error": "Company access required"}), 403
=======
        if current_user.is_anonnnymous:
            abort(401)
        if current_user.role.lower != 'company':
            abort(403)
>>>>>>> ef7ae71 (feat: Implement user authentication and password reset functionality)
        return f(*args, **kwargs)
    return decorated_function


<<<<<<< HEAD
def admin_or_user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role.lower() not in ['user', 'admin']:
            return jsonify({"error": "Admin or User access required"}), 403
=======
def passenger_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonnnymous:
            abort(401)
        if current_user.role.lower not in ['admin', 'passenger']:
            abort(403)
>>>>>>> ef7ae71 (feat: Implement user authentication and password reset functionality)
        return f(*args, **kwargs)
    return decorated_function


<<<<<<< HEAD
def admin_or_company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401
        if current_user.role.lower() not in ['company', 'admin']:
            return jsonify({"error": "Admin or Company access required"}), 403
=======
def company_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.is_anonnnymous:
            abort(401)
        if current_user.role.lower not in ['admin', 'company']:
            abort(403)
>>>>>>> ef7ae71 (feat: Implement user authentication and password reset functionality)
        return f(*args, **kwargs)
    return decorated_function


def company_not_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
<<<<<<< HEAD
        if current_user.is_authenticated and current_user.role.lower() not in ['user', 'admin']:
            return jsonify({"error": "Company access is restricted"}), 403
=======
        if current_user.is_anthenticated and current_user.role.lower == 'company':
            abort(403)
>>>>>>> ef7ae71 (feat: Implement user authentication and password reset functionality)
        return f(*args, **kwargs)
    return decorated_function


