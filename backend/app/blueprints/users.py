from app import db
from app.models import Users
from flask_login import current_user
from .auth import passenger_or_admin_required, passenger_required, admin_required
from flask import Blueprint, request, jsonify, abort


users_bp = Blueprint('users', __name__)

@users_bp.route('/create', methods=['POST'])
@admin_required
def create_user():
    """
    Admin endpoint to create users with any role.
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    name = data.get('full_name') or data.get('name')
    email = data.get('email')
    phone_number = data.get('phone') or data.get('phone_number')
    role = data.get('role', 'passenger')
    password = data.get('password')
    company_id = data.get('company_id')
    branch_id = data.get('branch_id')

    if not all([name, phone_number, password, role]):
        abort(400, description='name, phone number, password, and role are required')
    
    # Validate role
    valid_roles = ['passenger', 'admin', 'company_owner', 'branch_manager', 
                   'accounts_manager', 'bus_manager', 'schedule_manager', 'conductor']
    if role not in valid_roles:
        abort(400, description=f'Invalid role. Must be one of: {", ".join(valid_roles)}')

    # Generate placeholder email if not provided
    if not email:
        email = f"user_{phone_number}@ulendo.local"

    # Check uniqueness
    if Users.query.filter_by(email=email).first():
        abort(400, description='An account with that email already exists')
    if Users.query.filter_by(phone_number=phone_number).first():
        abort(400, description='An account with that phone number already exists')
    
    user = Users(
        name=name, 
        email=email, 
        phone_number=phone_number, 
        role=role,
        company_id=company_id,
        branch_id=branch_id
    )
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        abort(500, description='An unexpected error occurred')
    
    return jsonify({
        "message": "User created successfully",
        "user": user.to_dict()
    }), 201

@users_bp.route('/get/<int:id>', methods=["GET"])
@admin_required
def get_specific_user(id: int):
    """ fetch user details """
    
    user = Users.query.filter_by(id=id).first()

    if not user:
        abort(404)
    return jsonify(user.to_dict())


@users_bp.route('/me', methods=["GET"])
@passenger_required
def get_user():
    """ fetch user details """
    
    user = Users.query.filter_by(id=current_user.id).first()

    if not user:
        abort(404)
    return jsonify(user.to_dict())


@users_bp.route('/list', methods=['GET'])
@admin_required
def list_users():
    """List users for admin with optional filters"""
    role = request.args.get('role', type=str)
    q = request.args.get('q', type=str)

    query = Users.query
    if role:
        query = query.filter(Users.role == role)
    if q:
        like = f"%{q}%"
        query = query.filter((Users.name.ilike(like)) | (Users.email.ilike(like)) | (Users.phone_number.ilike(like)))

    users = query.order_by(Users.created_at.desc()).all()
    return jsonify({
        'count': len(users),
        'users': [u.to_dict() for u in users]
    }), 200


@users_bp.route('/update/<int:id>', methods=['PUT', 'POST'])
@passenger_or_admin_required
def update_user(id: int):
    """ update user info """
    
    user = Users.query.filter_by(id=id).first()
    if not user:
        abort(404)
    
    data = request.get_json()
    if not data:
        abort(400, description='data not provided')

    name = data.get('name', user.name)
    phone_number = data.get('phone_number', user.phone_number)
    email = data.get('email', user.email)
    password = data.get('password')

    # Update user info
    user.name = name
    user.email = email
    user.phone_number = phone_number
    user.password_hash = user.set_password(password) if password else user.password_hash

    try:
        db.session.commit()
    except:
        abort(500)
    
    return jsonify({"user details updated", user.to_dict()})