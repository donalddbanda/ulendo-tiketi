from app import db
from flask_login import current_user
from app.models import Buses, BusCompanies
from .auth import company_or_admin_required
from flask import jsonify, Blueprint, abort, request


buses_bp = Blueprint('buses', __name__)

@buses_bp.route('/add', methods=["POST"])
@company_or_admin_required
def add_bus():
    """ Add bus (admin or company) """

    if current_user.role.lower().strip() == 'company' and not current_user.can_add_bus():
        return jsonify({"message": "company not registered to add bus"}), 403
    
    data = request.get_json()
    if not data:
        abort(400, description='data not provided')

    bus_number = data.get('bus_number')
    seating_capacity = data.get('seating_capacity')
    company_id = data.get('company_id', None)

    if not all([bus_number, seating_capacity]):
        abort(400, description='bus number and seating capacity is required')

    if current_user.role.lower().strip() == 'admin' and not company_id:
        abort(400, description='company_id is required for admin users')
    
    company = BusCompanies.query.filter_by(id=company_id).first()

    if company_id and not company:
        abort(400, description='company with provided company_id does not exist')
    
    if company.status != 'registered':
        return jsonify({"message": "unregistered companies cannot add buses"}), 403

    if current_user.role.lower() != 'admin' and company_id != current_user.id:
        abort(403)
    
    if current_user.role.lower().strip() == 'company':
        company = BusCompanies.query.filter_by(id=current_user.id).first()
        if company.status != 'registered':
            return jsonify({"message": "unregistered companies cannot add buses"}), 403
    
    if Buses.query.filter_by(bus_number=bus_number).first():
        abort(400, description='Bus with this number already exists.')
    
    if current_user.role.lower().strip() == 'admin' and company_id == None:
        abort(400, description='admins must provide company_id')
    
    bus = Buses(bus_number=bus_number, seating_capacity=seating_capacity)
    bus.company_id = current_user.id if current_user.role.lower().strip() == 'company' else company_id

    try:
        db.session.add(bus)
        db.session.commit()
    except:
        abort(500)
    
    return jsonify({"message": "bus successfuly added", "bus": bus.to_dict()}), 201


@buses_bp.route('/get-buses', methods=["GET"])
def get_buses():
    """ Get all buses from registered companies """
    
    buses = Buses.query.all()
    if buses == []:
        return jsonify({"message": "no buses found", "buses": []})

    return jsonify({"buses": [bus.to_dict() for bus in buses]})
