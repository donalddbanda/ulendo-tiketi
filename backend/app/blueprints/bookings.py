from app import db
from app.models import Bookings, Schedules
from datetime import datetime, timezone
from ..utils.payments import initiate_payment
from flask_login import login_required, current_user
from flask import Blueprint, request, jsonify, abort
from .auth import passenger_required, passenger_or_admin_required


bookings_bp = Blueprint('bookings', __name__)

@bookings_bp.route('/book', methods=["POST"])
@passenger_required
def book_a_seat():
    """ book a seat """
    data = request.get_json()

    schedule_id = data.get('schedule_id')

    if not schedule_id:
        abort(400, description="Missing required booking information.")
    
    schedule = Schedules.query.filter_by(id=schedule_id).first()
    if not schedule:
        abort(400, description='invalid schedule_id')


    qrcode = f"{current_user.id}-{schedule_id}-{datetime.now().timestamp()}"

    booking = Bookings(
        schedule_id=schedule_id,
        user_id=current_user.id,
        qrcode=qrcode
    )

    if schedule.available_seats <= 0:
        abort(400, description="No available seats for this schedule.")
    
    schedule.available_seats -= 1


    try:
        db.session.add(booking)
        db.session.commit()
        # return initiate_payment(amount=booking.schedule.price, trans_reference=f"BOOKING-{current_user.id}-{booking.id}")
    except Exception as e:
        # abort(500)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

    return jsonify(booking.to_dict()), 201


@bookings_bp.route('/cancel/<int:booking_id>', methods=["POST"])
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
    booking.cancelled_at = datetime.now(timezone.utc)

    try:
        db.session.commit()
    except:
        abort(500)
    
    return jsonify({"message": "Booking cancelled", "status": booking.status}), 200
    

@bookings_bp.route('/get', methods=["GET"])
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


@bookings_bp.route('/get/<int:booking_id>', methods=["GET"])
@passenger_or_admin_required
def get_booking(booking_id: int):
    """ Get a specific booking by ID """

    booking = Bookings.query.filter_by(id=booking_id).first()
    if not booking:
        abort(404, description='booking not found')
    
    if current_user.role.lower().strip() != 'admin' and booking.user_id != current_user.id:
        abort(403)

    return jsonify(booking.to_dict()), 200


