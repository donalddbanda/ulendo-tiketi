from app import db
from app.models import Routes
from .auth import admin_required
from flask import Blueprint, jsonify, request, abort


routes_bp = Blueprint('routes', methods=["POST"])
@admin_required
def create_route():
    """ Create route """

    data = request.get_json()
    if not data:
        abort(400, description='data not provided')
    
    origin = data.get('origin')
    distance = data.get('distance')
    destination = data.get('destination')

    if not all([origin, destination]):
        abort(400, destination='provide origin and destination')
    
    route = Routes(origin=origin, destination=destination, distance=distance)

    try:
        db.session.add(route)
        db.session.commit()
    except:
        abort(400)
    
    return jsonify({"message": "route created", "route": route.to_dict()}), 201


@routes_bp.route('/routes', methods=["GET"])
def get_routes():
    """ Get all routes """

    routes = Routes.query.all()
    if routes == []:
        return jsonify({"message": "routes not found", "routes": []}), 200

    return jsonify({"routes": [route.to_dict() for route in routes]}), 200

