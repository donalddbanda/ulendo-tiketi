from app import db
from app.models import Bookings, Schedules
from datetime import datetime, timezone
from ..utils.payments import create_payment_link
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

    if schedule.available_seats <= 0:
        abort(400, description="No available seats for this schedule.")

    # Create booking with pending status
    booking = Bookings(
        schedule_id=schedule_id,
        user_id=current_user.id,
        qrcode=f"{current_user.id}-{schedule_id}-{datetime.now().timestamp()}",
        status='pending'
    )
    
    # Reserve seat temporarily
    schedule.available_seats -= 1

    try:
        db.session.add(booking)
        db.session.commit()
        
        # Create payment link after booking is saved
        payment_result = create_payment_link(
            booking_id=booking.id,
            amount=schedule.price,
            user_email=current_user.email,
            user_name=current_user.name
        )
        
        if payment_result.get('status') == 'success':
            booking.payment_link = payment_result['checkout_url']
            booking.tx_ref = payment_result['tx_ref']
            db.session.commit()
            
            return jsonify({
                "message": "Booking created successfully",
                "booking": booking.to_dict(),
                "payment_link": booking.payment_link,
                "tx_ref": booking.tx_ref
            }), 201
        else:
            # Rollback booking if payment link creation fails
            schedule.available_seats += 1
            db.session.delete(booking)
            db.session.commit()
            
            return jsonify({
                "error": "Failed to create payment link",
                "details": payment_result.get('error')
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


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
    booking.schedule.available_seats += 1
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
    
    if bookings == []:
        return jsonify({"message": "No bookings found", "bookings": []}), 200

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