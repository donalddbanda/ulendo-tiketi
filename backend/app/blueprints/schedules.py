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
