from app import db
from app.models import Bookings
from flask_login import login_required, current_user
from flask import Blueprint, request, jsonify, abort
from .auth import passenger_required, passenger_or_admin_required


bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/bookings', methods=["POST"])
@passenger_required
def book_a_seat():
    """ book a seat """
    data = request.get_json()

    bus_id = data.get('bus_id')
    schedule_id = data.get('schedule_id')

    if not bus_id or not schedule_id:
        abort(400, description="Missing required booking information.")

    booking = Bookings(
        schedule_id=schedule_id,
        user_id=current_user.id,
        bus_id=bus_id
    )
    booking.qrcode = booking.create_qrcode(booking.user_id, booking.schedule_id)

    try:
        db.session.add(booking)
        db.session.commit()
    except:
        abort(500)

    return jsonify(booking.to_dict()), 201


@bookings_bp.route('/bookings/<int:booking_id>/cancel', methods=["POST"])
@passenger_required
def cancel_booking(booking_id: int):
    """ Cancel a booking """

    booking = Bookings.query.filter_by(id=booking_id).first()
    if not booking:
        abort(400, description='booking not found')
    
    if booking.user_id != current_user.id:
        abort(403, description='forbidden action')
    
    if not booking.can_cancel():
        return abort(400, description='cancellation window has passed')

    booking.status = 'cancelled'

    try:
        db.session.commit()
    except:
        return jsonify({"message": "Booking cancelled", "status": booking.status}), 200
    

@bookings_bp.route('/bookings', methods=["GET"])
@passenger_or_admin_required
def get_bookings():
    """" Get all user bookings """

    if current_user.role.lower().strip() == 'admin':
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id or not data:
            abort(404, description='data or user_id is missing')
        
        bookings = Bookings.query.filter_by(user_id=user_id).all()
    else:
        bookings = Bookings.query.filter_by(user_id=current_user.id).all()

    return jsonify({"bookings": [booking.to_dict() for booking in bookings]}), 200


@bookings_bp.route('/bookings/<int:booking_id>', methods=["GET"])
@passenger_or_admin_required
def get_booking(booking_id: int):
    """ Get a specific booking by ID """

    booking = Bookings.query.filter_by(id=booking_id).first()
    if not booking:
        abort(404, description='booking not found')
    
    if current_user.role.lower().strip() != 'admin' and booking.user_id != current_user.id:
        abort(403)

    return jsonify(booking.to_dict()), 200


