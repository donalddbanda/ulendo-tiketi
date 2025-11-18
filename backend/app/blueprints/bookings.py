from app import db
from datetime import datetime, timezone
from ..utils.payments import create_payment_link
from app.models import Bookings, Schedules, Users
from flask_login import current_user
from flask import Blueprint, request, jsonify, abort, send_file
from ..utils.qr_generator import generate_qr_code_image, parse_qr_reference
from .auth import passenger_required, passenger_or_admin_required, conductor_required


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
        
        if not Users.query.filter_by(id=user_id).first():
            abort(404, description='user not found')
        
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


@bookings_bp.route('/qr-code/<int:booking_id>', methods=['GET'])
@passenger_or_admin_required
def download_qr_code(booking_id: int):
    """
    Download QR code for a confirmed booking as PNG image.
    This endpoint allows users to download the QR code to their device.
    """
    booking = Bookings.query.filter_by(id=booking_id).first()
    if not booking:
        abort(404, description='Booking not found')
    
    # Authorization check
    if current_user.role.lower() != 'admin' and booking.user_id != current_user.id:
        abort(403, description='Unauthorized access')
    
    # Only generate QR for confirmed bookings
    if booking.status != 'confirmed':
        abort(400, description=f'QR code only available for confirmed bookings. Current status: {booking.status}')
    
    # Generate QR reference if not exists
    if not booking.qr_code_reference:
        booking.generate_qr_reference()
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(500, description='Failed to generate QR reference')
    
    # Prepare booking information for QR code
    schedule = booking.schedule
    route = schedule.route
    
    booking_info = {
        'booking_id': booking.id,
        'route': f"{route.origin} to {route.destination}",
        'departure_date': schedule.departure_time.strftime('%Y-%m-%d %H:%M')
    }
    
    # Generate QR code image
    try:
        qr_image = generate_qr_code_image(booking.qr_code_reference, booking_info)
        
        # Return as downloadable file
        return send_file(
            qr_image,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'ulendo-tiketi-{booking.id}.png'
        )
    except Exception as e:
        abort(500, description=f'Failed to generate QR code: {str(e)}')


@bookings_bp.route('/qr-code-data/<int:booking_id>', methods=['GET'])
@passenger_or_admin_required
def get_qr_code_data(booking_id: int):
    """
    Get QR code reference data (for displaying in mobile app without download).
    Returns the QR reference that can be encoded into QR by frontend.
    """
    booking = Bookings.query.filter_by(id=booking_id).first()
    if not booking:
        abort(404, description='Booking not found')
    
    # Authorization check
    if current_user.role.lower() != 'admin' and booking.user_id != current_user.id:
        abort(403)
    
    if booking.status != 'confirmed':
        abort(400, description='QR code only available for confirmed bookings')
    
    # Generate QR reference if not exists
    if not booking.qr_code_reference:
        booking.generate_qr_reference()
        try:
            db.session.commit()
        except:
            db.session.rollback()
            abort(500)
    
    schedule = booking.schedule
    route = schedule.route
    
    return jsonify({
        'booking_id': booking.id,
        'qr_reference': booking.qr_code_reference,
        'qr_status': booking.qr_code_reference_status,
        'booking_status': booking.status,
        'passenger': {
            'name': booking.user.name,
            'phone': booking.user.phone_number
        },
        'schedule': {
            'departure_time': schedule.departure_time.isoformat(),
            'arrival_time': schedule.arrival_time.isoformat(),
            'route': f"{route.origin} to {route.destination}",
            'bus_number': schedule.bus.bus_number
        }
    }), 200


@bookings_bp.route('/verify-qr', methods=['POST'])
@conductor_required
def verify_qr_code():
    """
    Verify QR code for boarding (terminal verification).
    This endpoint is used by bus company staff to scan and verify passenger tickets.
    
    Request body:
    {
        "qr_data": "UTK-123-1699123456-abc123def456"
    }
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    qr_data = data.get('qr_data', '').strip()
    if not qr_data:
        abort(400, description='QR data required')
    
    # Parse QR reference
    parsed = parse_qr_reference(qr_data)
    
    if not parsed.get('valid'):
        return jsonify({
            'success': False,
            'message': 'Invalid QR code',
            'error': parsed.get('error')
        }), 400
    
    # Get booking
    qr_reference = parsed['qr_reference']
    booking = Bookings.query.filter_by(qr_code_reference=qr_reference).first()
    
    if not booking:
        return jsonify({
            'success': False,
            'message': 'Booking not found with this QR code'
        }), 404
    
    # Check company authorization
    if current_user.role.lower() == 'company':
        if booking.schedule.bus.company_id != current_user.id:
            abort(403, description='Unauthorized: This booking is not for your company')
    
    # Validate QR code
    is_valid, validation_message = booking.is_qr_valid()
    
    if not is_valid:
        return jsonify({
            'success': False,
            'message': validation_message,
            'booking': {
                'id': booking.id,
                'status': booking.status,
                'qr_status': booking.qr_code_reference_status
            }
        }), 400
    
    # Mark as used and boarded
    booking.qr_code_reference_status = 'used'
    booking.status = 'boarded'
    booking.boarded_at = datetime.now(timezone.utc)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to update booking',
            'error': str(e)
        }), 500
    
    # Return success with passenger details
    schedule = booking.schedule
    route = schedule.route
    
    return jsonify({
        'success': True,
        'message': 'Passenger verified successfully - Boarding approved',
        'booking': {
            'id': booking.id,
            'status': booking.status,
            'qr_status': booking.qr_code_reference_status,
            'boarded_at': booking.boarded_at.isoformat()
        },
        'passenger': {
            'name': booking.user.name,
            'phone': booking.user.phone_number,
            'email': booking.user.email
        },
        'schedule': {
            'departure_time': schedule.departure_time.isoformat(),
            'arrival_time': schedule.arrival_time.isoformat(),
            'route': f"{route.origin} to {route.destination}",
            'bus_number': schedule.bus.bus_number,
            'company': schedule.bus.company.name
        }
    }), 200


@bookings_bp.route('/verify-reference', methods=['POST'])
def verify_by_reference():
    """
    Verify booking using QR reference (alternative verification method).
    Useful when passenger doesn't have QR code on phone.
    
    Request body:
    {
        "qr_reference": "UTK-123-1699123456-abc123def456",
        "phone_number": "0999123456"  // Optional additional verification
    }
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    qr_reference = data.get('qr_reference', '').strip()
    phone_number = data.get('phone_number', '').strip()
    
    if not qr_reference:
        abort(400, description='QR reference required')
    
    # Find booking
    booking = Bookings.query.filter_by(qr_code_reference=qr_reference).first()
    
    if not booking:
        return jsonify({
            'success': False,
            'message': 'Invalid QR reference'
        }), 404
    
    # Optional phone verification for added security
    if phone_number and booking.user.phone_number != phone_number:
        return jsonify({
            'success': False,
            'message': 'Phone number does not match booking'
        }), 400
    
    # Check validity
    is_valid, message = booking.is_qr_valid()
    
    schedule = booking.schedule
    route = schedule.route
    
    return jsonify({
        'success': is_valid,
        'message': message,
        'booking': {
            'id': booking.id,
            'status': booking.status,
            'qr_status': booking.qr_code_reference_status
        },
        'passenger': {
            'name': booking.user.name,
            'phone': booking.user.phone_number
        },
        'schedule': {
            'departure_time': schedule.departure_time.isoformat(),
            'route': f"{route.origin} to {route.destination}",
            'bus_number': schedule.bus.bus_number
        }
    }), 200 if is_valid else 400


@bookings_bp.route('/qr-status/<int:booking_id>', methods=['GET'])
@passenger_or_admin_required
def check_qr_status(booking_id: int):
    """
    Check the current status of a booking's QR code.
    """
    booking = Bookings.query.filter_by(id=booking_id).first()
    if not booking:
        abort(404, description='Booking not found')
    
    # Authorization
    if current_user.role.lower() != 'admin' and booking.user_id != current_user.id:
        abort(403)
    
    is_valid, message = booking.is_qr_valid()
    
    return jsonify({
        'booking_id': booking.id,
        'qr_reference': booking.qr_code_reference,
        'qr_status': booking.qr_code_reference_status,
        'booking_status': booking.status,
        'is_valid': is_valid,
        'message': message,
        'boarded_at': booking.boarded_at.isoformat() if booking.boarded_at else None
    }), 200

