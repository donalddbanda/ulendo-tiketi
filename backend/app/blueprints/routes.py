from app import db
from app.models import Route
from flask import request, jsonify, Blueprint
from .auth import admin_required, company_not_required


routes = Blueprint('route', __name__)

@routes.route('/routes', methods=["POST"])
@admin_required
def create_route():
    """ Create a route """

    data = request.get_json()

    if not data:
        return jsonify({"error": "Data not provided"}), 400

    origin = data.get('origin')
    destination = data.get('destination')
    distance = data.get('distance')

    if not all([origin, destination]):
        return jsonify({"error": "Origin and destination must be provided"}), 400

    route = Route(origin=origin, destination=destination, distance=distance)

    try: 
        db.session.add(route)
        db.session.commit()

    except Exception as e:
        return jsonify({"error": "Failed to create route", "details": str(e)}), 500

    return jsonify({
        "message": "Route added successfully",
        "route": {
            "id": route.id,
            "origin": route.origin,
            "destination": route.destination,
            "distance": route.distance
        }
    })