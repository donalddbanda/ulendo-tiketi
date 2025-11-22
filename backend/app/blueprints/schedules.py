from app import db
from app.models import Schedules, Buses, Routes, BusCompanies
from datetime import datetime, timezone
from dateutil import parser as date_parser
from .auth import schedule_manager_required, schedule_or_bus_manager_required
from flask import Blueprint, jsonify, request, abort
from flask_login import current_user

schedules_bp = Blueprint('schedules', __name__)

def parse_datetime_to_utc(datetime_string):
    """
    Parse datetime string to UTC timezone-aware datetime.
    Accepts multiple formats:
    - ISO 8601: "2024-03-15T14:30:00Z" or "2024-03-15T14:30:00+02:00"
    - ISO without timezone: "2024-03-15T14:30:00" (assumes UTC)
    - Date only: "2024-03-15" (assumes midnight UTC)
    """
    try:
        # Use dateutil parser for flexible parsing
        dt = date_parser.parse(datetime_string)
        
        # If naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            # Convert to UTC
            dt = dt.astimezone(timezone.utc)
        
        return dt
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid datetime format: {datetime_string}. Expected ISO 8601 format.") from e


@schedules_bp.route('/create', methods=["POST"])
@schedule_manager_required
def schedule_bus():
    """
    Create a schedule for a bus.
    
    Request body:
    {
        "bus_id": 1,
        "route_id": 1,
        "departure_time": "2024-03-15T06:00:00Z",  // ISO 8601 format
        "arrival_time": "2024-03-15T10:30:00Z",    // ISO 8601 format
        "price": 15000,
        "available_seats": 45
    }
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    departure_time_str = data.get('departure_time')
    arrival_time_str = data.get('arrival_time')
    price = data.get('price')
    route_id = data.get('route_id')
    available_seats = data.get('available_seats')
    bus_id = data.get('bus_id')

    # Validate required fields
    if not all([departure_time_str, arrival_time_str, price, available_seats, bus_id, route_id]):
        abort(400, description='All fields are required: departure_time, arrival_time, price, available_seats, bus_id, route_id')

    # Validate bus belongs to user's company
    bus = Buses.query.filter_by(id=bus_id).first()
    if not bus:
        abort(404, description='Bus not found')
    
    if current_user.company_id != bus.company_id:
        abort(403, description='You can only create schedules for buses in your company')
    
    # Validate route exists
    route = Routes.query.filter_by(id=route_id).first()
    if not route:
        abort(404, description='Route not found')
    
    # Validate bus capacity
    if available_seats > bus.seating_capacity:
        abort(400, description=f'Available seats ({available_seats}) cannot exceed bus capacity ({bus.seating_capacity})')

    # Parse datetime strings to UTC
    try:
        departure_time = parse_datetime_to_utc(departure_time_str)
        arrival_time = parse_datetime_to_utc(arrival_time_str)
    except ValueError as e:
        return jsonify({
            "error": "Invalid datetime format",
            "message": str(e),
            "expected_format": "ISO 8601 (e.g., '2024-03-15T14:30:00Z' or '2024-03-15T14:30:00+02:00')"
        }), 400

    # Business logic validations
    now = datetime.now(timezone.utc)
    
    # Departure must be in the future
    if departure_time <= now:
        abort(400, description='Departure time must be in the future')
    
    # Arrival must be after departure
    if arrival_time <= departure_time:
        abort(400, description='Arrival time must be after departure time')
    
    # Check for reasonable travel time (optional, adjust as needed)
    travel_duration = (arrival_time - departure_time).total_seconds() / 3600  # hours
    if travel_duration > 24:
        abort(400, description='Travel duration cannot exceed 24 hours')
    
    # Check for schedule conflicts (same bus, overlapping times)
    conflicting_schedule = Schedules.query.filter(
        Schedules.bus_id == bus_id,
        Schedules.departure_time < arrival_time,
        Schedules.arrival_time > departure_time
    ).first()
    
    if conflicting_schedule:
        abort(400, description=f'Bus is already scheduled during this time period (Schedule ID: {conflicting_schedule.id})')

    # Validate price
    if price <= 0:
        abort(400, description='Price must be greater than 0')

    # Create schedule
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
        return jsonify({"error": "Failed to create schedule", "details": str(e)}), 500

    return jsonify({
        "message": "Schedule created successfully",
        "schedule": schedule.to_dict()
    }), 201


@schedules_bp.route('/get', methods=["GET"])
def get_schedules():
    """
    Get all available schedules.
    Optionally filter by date range.
    
    Query parameters:
    - from_date: ISO date string (e.g., "2024-03-15")
    - to_date: ISO date string (e.g., "2024-03-20")
    - route_id: Filter by specific route
    """
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    route_id = request.args.get('route_id', type=int)
    
    query = Schedules.query
    
    # Filter by date range if provided
    if from_date_str:
        try:
            from_date = parse_datetime_to_utc(from_date_str)
            query = query.filter(Schedules.departure_time >= from_date)
        except ValueError:
            abort(400, description='Invalid from_date format')
    
    if to_date_str:
        try:
            to_date = parse_datetime_to_utc(to_date_str)
            # Add one day to include the entire to_date
            query = query.filter(Schedules.departure_time < to_date)
        except ValueError:
            abort(400, description='Invalid to_date format')
    
    # Filter by route
    if route_id:
        query = query.filter(Schedules.route_id == route_id)
    
    # Only show future schedules by default
    if not from_date_str:
        query = query.filter(Schedules.departure_time > datetime.now(timezone.utc))
    
    schedules = query.order_by(Schedules.departure_time.asc()).all()
    
    if not schedules:
        return jsonify({"message": "No schedules found", "schedules": []}), 200

    return jsonify({"schedules": [schedule.to_dict() for schedule in schedules]}), 200


@schedules_bp.route('/<int:schedule_id>', methods=["GET"])
def get_schedule(schedule_id: int):
    """Get a specific schedule by ID."""
    schedule = Schedules.query.filter_by(id=schedule_id).first()
    if not schedule:
        abort(404, description='Schedule not found')
    
    return jsonify(schedule.to_dict()), 200


@schedules_bp.route('/company/schedules', methods=["GET"])
@schedule_or_bus_manager_required
def get_company_schedules():
    """
    Get all schedules for the user's company buses.
    
    Query parameters:
    - from_date: ISO date string
    - to_date: ISO date string
    - branch_id: Filter by specific branch
    """
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    branch_id = request.args.get('branch_id', type=int)
    
    if not current_user.company_id:
        abort(400, description='User must be associated with a company')
    
    company_id = current_user.company_id

    # Get all buses for this company
    buses_query = Buses.query.filter_by(company_id=company_id)
    
    if branch_id:
        buses_query = buses_query.filter_by(branch_id=branch_id)
    
    buses = buses_query.all()
    bus_ids = [bus.id for bus in buses]
    
    if not bus_ids:
        return jsonify({"message": "No buses found", "schedules": []}), 200

    # Get all schedules for these buses
    query = Schedules.query.filter(Schedules.bus_id.in_(bus_ids))
    
    # Apply date filters
    if from_date_str:
        try:
            from_date = parse_datetime_to_utc(from_date_str)
            query = query.filter(Schedules.departure_time >= from_date)
        except ValueError:
            abort(400, description='Invalid from_date format')
    
    if to_date_str:
        try:
            to_date = parse_datetime_to_utc(to_date_str)
            query = query.filter(Schedules.departure_time < to_date)
        except ValueError:
            abort(400, description='Invalid to_date format')
    
    schedules = query.order_by(Schedules.departure_time.desc()).all()
    
    return jsonify({
        "schedules": [schedule.to_dict() for schedule in schedules],
        "count": len(schedules)
    }), 200


@schedules_bp.route('/<int:schedule_id>/update', methods=["PUT", "PATCH"])
@schedule_manager_required
def update_schedule(schedule_id: int):
    """
    Update an existing schedule.
    Can only update future schedules and only if no bookings exist.
    """
    schedule = Schedules.query.filter_by(id=schedule_id).first()
    if not schedule:
        abort(404, description='Schedule not found')

    # Verify permission
    bus = Buses.query.filter_by(id=schedule.bus_id).first()
    if not bus or bus.company_id != current_user.company_id:
        abort(403, description='Unauthorized to update this schedule')
    
    # Don't allow updates to past schedules
    if schedule.departure_time <= datetime.now(timezone.utc):
        abort(400, description='Cannot update past schedules')
    
    # Don't allow updates if bookings exist
    if schedule.bookings:
        abort(400, description='Cannot update schedule with existing bookings. Cancel schedule instead.')
    
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    # Update allowed fields
    if 'departure_time' in data:
        try:
            schedule.departure_time = parse_datetime_to_utc(data['departure_time'])
        except ValueError as e:
            abort(400, description=str(e))
    
    if 'arrival_time' in data:
        try:
            schedule.arrival_time = parse_datetime_to_utc(data['arrival_time'])
        except ValueError as e:
            abort(400, description=str(e))
    
    # Re-validate times
    if schedule.arrival_time <= schedule.departure_time:
        abort(400, description='Arrival time must be after departure time')
    
    if 'price' in data:
        if data['price'] <= 0:
            abort(400, description='Price must be greater than 0')
        schedule.price = data['price']
    
    if 'available_seats' in data:
        if data['available_seats'] > bus.seating_capacity:
            abort(400, description='Available seats cannot exceed bus capacity')
        schedule.available_seats = data['available_seats']
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
    return jsonify({
        "message": "Schedule updated successfully",
        "schedule": schedule.to_dict()
    }), 200


@schedules_bp.route('/<int:schedule_id>/cancel', methods=["POST", "DELETE"])
@schedule_manager_required
def cancel_schedule(schedule_id: int):
    """
    Cancel a schedule.
    If bookings exist, they will be cancelled and seats refunded.
    """
    schedule = Schedules.query.filter_by(id=schedule_id).first()
    if not schedule:
        abort(404, description='Schedule not found')

    # Verify permission
    bus = Buses.query.filter_by(id=schedule.bus_id).first()
    if not bus or bus.company_id != current_user.company_id:
        abort(403, description='Unauthorized to cancel this schedule')
    
    # Cancel all associated bookings
    cancelled_bookings = 0
    for booking in schedule.bookings:
        if booking.status in ['confirmed', 'pending']:
            booking.status = 'cancelled'
            booking.cancelled_at = datetime.now(timezone.utc)
            cancelled_bookings += 1
            # TODO: Process refunds here
    
    try:
        db.session.delete(schedule)
        db.session.commit()
        
        return jsonify({
            "message": "Schedule cancelled successfully",
            "cancelled_bookings": cancelled_bookings
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

