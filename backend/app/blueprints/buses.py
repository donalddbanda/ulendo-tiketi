from app import db
from flask_login import current_user
from app.models import Buses, BusCompanies
from .auth import company_or_admin_required, login_required
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


@buses_bp.route('/company', methods=["GET"])
@company_or_admin_required
def get_company_buses():
    """ Get buses for current user's company """
    company_id = request.args.get('company_id', type=int)
    
    if current_user.role.lower() == 'company':
        company_id = current_user.id
    elif not company_id:
        abort(400, description='Company ID required for admin requests')
    
    buses = Buses.query.filter_by(company_id=company_id).all()
    
    return jsonify({
        'buses': [bus.to_dict() for bus in buses]
    }), 200


@buses_bp.route('/<int:bus_id>', methods=["GET"])
@login_required
def get_bus(bus_id: int):
    """ Get a specific bus """
    bus = Buses.query.filter_by(id=bus_id).first()
    if not bus:
        abort(404, description='Bus not found')
    
    return jsonify(bus.to_dict()), 200


@buses_bp.route('/<int:bus_id>/update', methods=['PUT', 'POST'])
@company_or_admin_required
def update_bus(bus_id: int):
    """ Update bus details """
    bus = Buses.query.filter_by(id=bus_id).first()
    if not bus:
        abort(404, description='Bus not found')
    
    # Check permissions
    if current_user.role.lower() == 'company' and bus.company_id != current_user.id:
        abort(403, description='Not authorized to update this bus')
    
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    if 'seating_capacity' in data:
        bus.seating_capacity = data['seating_capacity']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'message': 'Bus updated successfully',
        'bus': bus.to_dict()
    }), 200


@buses_bp.route('/<int:bus_id>/delete', methods=['DELETE', 'POST'])
@company_or_admin_required
def delete_bus(bus_id: int):
    """ Delete a bus """
    bus = Buses.query.filter_by(id=bus_id).first()
    if not bus:
        abort(404, description='Bus not found')
    
    # Check permissions
    if current_user.role.lower() == 'company' and bus.company_id != current_user.id:
        abort(403, description='Not authorized to delete this bus')
    
    try:
        db.session.delete(bus)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({'message': 'Bus deleted successfully'}), 200
