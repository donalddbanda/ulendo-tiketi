from app import db
from app.models import Schedule, Bus, Route
from flask import jsonify, request, Blueprint
from flask_login import login_required
from .auth import admin_or_company_required, company_not_required


schedules = Blueprint("schedule", __name__)

@schedules.route('/schedules', metjods=["POST"])
@admin_or_company_required
def create_schedule():
    """ Create schedule for a bus """

    data = request.get_json()

    if not data:
        return jsonify({"error": "data not provided"}), 400

    bus_id = data.get("bus_id")
    route_id = data.get("route_id")
    departure_time = data.get("departure_time")
    arrival_time = data.get("arrival_time")
    price = data.get('price')


    if not all([bus_id, price, departure_time, arrival_time, route_id]):
        return jsonify({"error": "Provide route id, price, bus id, departure time, and arrival time"}), 400
    
    schedule = Schedule(
        bus_id = bus_id,
        price = price,
        route_id = route_id,
        departure_time = departure_time,
        arrival_time = arrival_time
    )

    try:
        db.session.add(schedule)
        db.session.commit()

    except Exception as e:
        return jsonify({"error": "Failed to schedule bus", "details": str(e)}), 500
    
    return jsonify({
        "message": "Schedule successfully created",
        "schedule": {
            "id": schedule.id,
            "bus_id": schedule.bus_id,
            "departure_time": schedule.departure_time,
            "arrival_time": schedule.arrival_time,
            "price": schedule.price
        }
    }), 201


@schedules.route('/schedules', methods=["GET"])
@company_not_required
def get_schedule():
    """ List all schedules """

    try:
        schedules = Schedule.query.all()
    except Exception as e:
        return jsonify({"error": "Failed to fetch schedules", "details": str(e)}), 500

    if schedules == []: return jsonify({"message": "No available schedules"}), 200

    return jsonify({
        "schedlues": [
            {
                "id": schedule.id,
                "bus_number": Bus.query.filter_by(id=schedule.bus_id).first().bus_number, 
                "route": f"{Route.query.filter_by(id=schedule.route_id).first().origin} -- {Route.query.filter_by(id=schedule.route_id).first().destination}",
                "departure_time": schedule.departure_time,
                "arrival_time": schedule.arrival_time,
                "price": schedule.price
            } for schedule in schedules
        ]
    })


