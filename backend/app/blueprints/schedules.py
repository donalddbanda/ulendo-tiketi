from app import db
from app.models import Schedules
from datetime import datetime, timezone
from .auth import schedule_manager_required
from flask import Blueprint, jsonify, request, abort

schedules_bp = Blueprint('schedules', __name__)

@schedules_bp.route('/create', methods=["POST"])
@schedule_manager_required
def schedule_bus():
    """Create a schedule for a bus."""
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    departure_time = data.get('departure_time')
    arrival_time = data.get('arrival_time')
    price = data.get('price')
    route_id = data.get('route_id')
    available_seats = data.get('available_seats')
    bus_id = data.get('bus_id')

    if not all([departure_time, arrival_time, price, available_seats, bus_id, route_id]):
        abort(400, description='Required data is missing')

    try:
        departure_time = datetime.strptime(departure_time, '%Y,%m,%d,%H,%M,%S').replace(tzinfo=timezone.utc)
        arrival_time = datetime.strptime(arrival_time, '%Y,%m,%d,%H,%M,%S').replace(tzinfo=timezone.utc)
    except ValueError:
        return jsonify({"message": "Date and time must be YYYY,MM,DD,HH,MM,SS"}), 400

    schedule = Schedules(
        departure_time=departure_time,
        arrival_time=arrival_time,
        price=price,
        available_seats=available_seats,
        route_id=route_id,
        bus_id=bus_id
    )

    try:
        db.session.add(schedule)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Schedule created", "schedule": schedule.to_dict()}), 201


@schedules_bp.route('/get', methods=["GET"])
def get_schedules():
    """Get all available schedules."""
    schedules = Schedules.query.all()
    if not schedules:
        return jsonify({"message": "Schedules not available", "schedules": []}), 200

    return jsonify({"schedules": [schedule.to_dict() for schedule in schedules]}), 200


@schedules_bp.route('/<int:schedule_id>', methods=["GET"])
def get_schedule(schedule_id: int):
    """Get a specific schedule by ID."""
    schedule = Schedules.query.filter_by(id=schedule_id).first()
    if not schedule:
        abort(404, description='Schedule not found')
    
    return jsonify(schedule.to_dict()), 200


@schedules_bp.route('/company/schedules', methods=["GET"])
def get_company_schedules():
    """Get all schedules for the company's buses."""
    from app.models import Buses
    from flask_login import current_user
    from app.models import BusCompanies
    
    # Get user's company
    if current_user.role == 'admin':
        # Admin can pass company_id as query param
        company_id = request.args.get('company_id', type=int)
        if not company_id:
            return jsonify({"error": "company_id required for admin"}), 400
    else:
        # Company owner gets their own company schedules
        company = BusCompanies.query.filter_by(owner_id=current_user.id).first()
        if not company:
            return jsonify({"schedules": []}), 200
        company_id = company.id

    # Get all buses for this company
    buses = Buses.query.filter_by(company_id=company_id).all()
    bus_ids = [bus.id for bus in buses]
    
    if not bus_ids:
        return jsonify({"schedules": []}), 200

    # Get all schedules for these buses
    schedules = Schedules.query.filter(Schedules.bus_id.in_(bus_ids)).all()
    
    return jsonify({"schedules": [schedule.to_dict() for schedule in schedules]}), 200


@schedules_bp.route('/<int:schedule_id>/cancel', methods=["POST"])
@schedule_manager_required
def cancel_schedule(schedule_id: int):
    """Cancel a schedule."""
    from app.models import Buses, BusCompanies
    from flask_login import current_user
    
    schedule = Schedules.query.filter_by(id=schedule_id).first()
    if not schedule:
        abort(404, description='Schedule not found')

    # Verify permission: user owns the company that owns the bus
    bus = Buses.query.filter_by(id=schedule.bus_id).first()
    if not bus:
        abort(404, description='Bus not found')

    if current_user.role != 'admin':
        company = BusCompanies.query.filter_by(id=bus.company_id, owner_id=current_user.id).first()
        if not company:
            abort(403, description='Unauthorized')

    try:
        db.session.delete(schedule)
        db.session.commit()
        return jsonify({"message": "Schedule cancelled"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500