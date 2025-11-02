from flask import Blueprint
from app import db
from app.models import User
from flask import jsonify, request
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

    if not all([name, email, password]):
        return jsonify({"error": "Provide email and password"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400
    
    new_user = User(name=name, email=email, role=role)
    new_user.set_password(password)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User registered successfully", "redirect": "/login"}), 201
    except Exception as e:
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


@auth.route('/logout', methods=["POST"])
def logout():
    logout_user()

