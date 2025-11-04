from app import db
from app.models import Bus
from flask_login import current_user
from flask import Blueprint, request, jsonify
from .auth import admin_or_user_required, admin_or_company_required


bus = Blueprint("bus", __name__)


@bus.route('/bus', methods=["POST"])
@admin_or_company_required
def add_bus():
    data = request.get_json()

    bus_number = data.get('bus_number')
    company_id = data.get("company_id")
    seating_capacity = data.get("seating_capacity")

    if not all([bus_number, seating_capacity]):
        return jsonify({"error": "Bus number and seating capacity is required"}), 400

    if current_user.role.lower() == 'admin' and not company_id:
        return jsonify({"error": "Company ID is required"}), 400
    
    bus = Bus(
        bus_company_id = current_user.id if current_user.role.lower == 'company' else company_id,
        bus_number = bus_number,
        seating_capacity = seating_capacity
    )

    try:
        db.session.add(bus)
        db.session.commit()
    except Exception as e:
        return jsonify({"error": "Failed to add bus", "details": str(e)}), 500
    
    return jsonify({
        "message": "Bus successfuly addded",
        "bus": {
            "id": id,
            "bus_number": bus_number,
            "bus_company_id": company_id,
            "seating_capacity": seating_capacity
        }
    })