from app import db
from app.models import Users
from .auth import passenger_or_admin_required
from flask import Blueprint, request, jsonify, abort


users_bp = Blueprint('users', __name__)

@users_bp.route('/users/<int:id>', methods=["GET"])
@passenger_or_admin_required
def get_user(id: int):
    """ fetch user details """
    user = Users.query.filter_by(id=id).first()

    if not user:
        abort(404)
    return jsonify(user.to_dict())


@users_bp.route('/users/<int:id>', methods=['PUT', 'POST'])
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