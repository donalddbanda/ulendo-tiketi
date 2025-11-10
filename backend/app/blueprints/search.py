from app import db
from datetime import datetime, timezone
from sqlalchemy import and_, func
from app.models import Schedules, Routes, Buses, BusCompanies
from flask import Blueprint, request, jsonify, abort


search_bp = Blueprint('search', __name__)


@search_bp.route('/schedules', methods=['GET'])
def search_schedules():
    """
    Search for available bus schedules.
    
    Query Parameters:
        - origin: Departure location
        - destination: Arrival location
        - date: Travel date (YYYY-MM-DD)
        - min_price: Minimum price filter (optional)
        - max_price: Maximum price filter (optional)
        - company_id: Filter by specific company (optional)
    """
    # Get query parameters
    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    date_str = request.args.get('date', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    company_id = request.args.get('company_id', type=int)
    
    # Validate required parameters
    if not origin or not destination:
        abort(400, description='Origin and destination are required')
    
    # Parse date
    travel_date = None
    if date_str:
        try:
            travel_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            abort(400, description='Invalid date format. Use YYYY-MM-DD')
    
    # Build query
    query = db.session.query(Schedules).join(Routes).join(Buses).join(BusCompanies)
    
    # Apply filters
    query = query.filter(
        and_(
            Routes.origin.ilike(f'%{origin}%'),
            Routes.destination.ilike(f'%{destination}%'),
            Schedules.available_seats > 0,
            Schedules.departure_time > datetime.now(timezone.utc),
            BusCompanies.status == 'registered'
        )
    )
    
    # Date filter
    if travel_date:
        query = query.filter(
            func.date(Schedules.departure_time) == travel_date
        )
    
    # Price filters
    if min_price is not None:
        query = query.filter(Schedules.price >= min_price)
    if max_price is not None:
        query = query.filter(Schedules.price <= max_price)
    
    # Company filter
    if company_id:
        query = query.filter(Buses.company_id == company_id)
    
    # Order by departure time
    query = query.order_by(Schedules.departure_time.asc())
    
    # Execute query
    schedules = query.all()
    
    # Format response
    results = []
    for schedule in schedules:
        results.append({
            'schedule_id': schedule.id,
            'departure_time': schedule.departure_time.isoformat(),
            'arrival_time': schedule.arrival_time.isoformat(),
            'price': schedule.price,
            'available_seats': schedule.available_seats,
            'route': {
                'id': schedule.route.id,
                'origin': schedule.route.origin,
                'destination': schedule.route.destination,
                'distance': schedule.route.distance
            },
            'bus': {
                'id': schedule.bus.id,
                'bus_number': schedule.bus.bus_number,
                'seating_capacity': schedule.bus.seating_capacity
            },
            'company': {
                'id': schedule.bus.company.id,
                'name': schedule.bus.company.name,
                'description': schedule.bus.company.description
            }
        })
    
    return jsonify({
        'count': len(results),
        'schedules': results
    }), 200


@search_bp.route('/routes', methods=['GET'])
def search_routes():
    """
    Search for available routes.
    
    Query Parameters:
        - origin: Starting point (partial match)
        - destination: End point (partial match)
    """
    origin = request.args.get('origin', '').strip()
    destination = request.args.get('destination', '').strip()
    
    query = Routes.query
    
    if origin:
        query = query.filter(Routes.origin.ilike(f'%{origin}%'))
    if destination:
        query = query.filter(Routes.destination.ilike(f'%{destination}%'))
    
    routes = query.all()
    
    return jsonify({
        'count': len(routes),
        'routes': [route.to_dict() for route in routes]
    }), 200


@search_bp.route('/companies', methods=['GET'])
def search_companies():
    """
    Search for bus companies.
    
    Query Parameters:
        - name: Company name (partial match)
    """
    name = request.args.get('name', '').strip()
    
    query = BusCompanies.query
    
    if name:
        query = query.filter(BusCompanies.name.ilike(f'%{name}%'))
    
    companies = query.all()
    
    return jsonify({
        'count': len(companies),
        'companies': [company.to_dict() for company in companies]
    }), 200

