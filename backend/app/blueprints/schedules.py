from app import db
from app.models import Schedules
from .auth import company_or_admin_required
from flask import Blueprint, jsonify, request, request, abort


schedules_bp = Blueprint('schedules', __name__)

@schedules_bp.route('/schedule', methods=["POST"])
@company_or_admin_required
def schedule_bus():
    """ Create a schedule for a bus """

    data = request.get_json()
    if not data:
        abort(400, description='data not provided')
    
    departure_time = data.get('departure_time')
    arrival_time = data.get('arrival_time')
    price = data.get('price')
    route_id = data.get('route_id')
    available_seats = data.get('available_seats')
    bus_id = data.get('bus_id')

    if not all([departure_time, arrival_time, price, available_seats, bus_id, route_id]):
        abort(400, description='required data is missing')
    
    schedule = Schedules(
        departure_time=departure_time, arrival_time=arrival_time, price=price,
        available_seats=available_seats, route_id=route_id, bus_id=bus_id
    )
    try:
        db.session.add(schedule)
        db.session.commit()
    except:
        abort(500)

    return jsonify({"message": "Schedule created", "schedule": schedule.to_dict()}), 201


@schedules_bp.route('/schedules', methods=["GET"])
def get_schedules():
    """ Get all available schedules """

    schedules = Schedules.query.all()
    if schedules == []:
        return jsonify({"message": "schedules not available", "schedules": []})

    return jsonify({"schedules": [schedule.to_dict() for schedule in schedules]}), 200

