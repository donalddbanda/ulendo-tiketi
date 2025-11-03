import jwt
from app import db
from flask import jsonify, request
from flask import Blueprint, current_app
from app.models import User, PasswordResetToken
from ..utils.email_services import send_password_reset_link
from flask_login import login_user, logout_user, current_user, login_required

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return jsonify({"message": "You are already logged in"}), 400
    
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
        return jsonify({"message": "User registered successfully", "redirect": "/login"}), 201
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
    role = data.get('role')
    remember_me = data.get('remember', False)
    redirect = data.get('redirect')

    if not all([email, password]):
        return jsonify({"error": "Provide email and password"}), 400
    
    user = User.query.filter_by(email=email).first()
    
    if user is None or not user.verify_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    login_user(user, remember=remember_me)
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

