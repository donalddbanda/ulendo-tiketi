from app import db
from ..utils.payments import verify_payment
from app.models import Bookings, Transactions
from flask import Blueprint, jsonify, request, abort, current_app

payments_bp = Blueprint('payments', __name__)


@payments_bp.route('/callback', methods=['POST', 'GET'])
def payment_callback():
    """
    Handle successful payment callbacks from PayChangu.
    Query params: tx_ref, status
    """
    try:
        # Get transaction reference from query params
        tx_ref = request.args.get('tx_ref')
        status = request.args.get('status', 'pending')
        
        if not tx_ref:
            abort(400, description='Transaction reference is required')
        
        # Extract booking_id from tx_ref (format: BOOKING-{id}-{timestamp})
        try:
            booking_id = int(tx_ref.split('-')[1])
        except (IndexError, ValueError):
            abort(400, description='Invalid transaction reference format')
        
        # Find the booking
        booking = Bookings.query.filter_by(id=booking_id).first()
        if not booking:
            abort(404, description='Booking not found')
        
        # Verify payment with PayChangu
        verification = verify_payment(tx_ref)
        
        # Update booking status based on payment status
        if verification.get('status') == 'success' or status == 'success':
            booking.status = 'confirmed'
            
            # Create or update transaction record
            transaction = Transactions.query.filter_by(reference=tx_ref).first()
            if not transaction:
                transaction = Transactions(
                    amount=booking.schedule.price,
                    status='completed',
                    method='paychangu',
                    reference=tx_ref,
                    payment_status='success',
                    booking_id=booking.id
                )
                db.session.add(transaction)
            else:
                transaction.status = 'completed'
                transaction.payment_status = 'success'
            
            # Update company balance (schedule.price - platform fee)
            platform_fee = current_app.config.get('PLATFORM_FEE', 3000)
            company_earnings = booking.schedule.price - platform_fee
            
            bus_company = booking.schedule.bus.company
            bus_company.balance += company_earnings
            
            db.session.commit()
            
            return jsonify({
                "message": "Payment confirmed successfully",
                "booking_id": booking.id,
                "status": booking.status,
                "tx_ref": tx_ref
            }), 200
        else:
            # Payment failed or pending
            transaction = Transactions.query.filter_by(reference=tx_ref).first()
            if not transaction:
                transaction = Transactions(
                    amount=booking.schedule.price,
                    status='failed',
                    method='paychangu',
                    reference=tx_ref,
                    payment_status='failed',
                    booking_id=booking.id
                )
                db.session.add(transaction)
            else:
                transaction.status = 'failed'
                transaction.payment_status = 'failed'
            
            booking.status = 'payment_failed'
            db.session.commit()
            
            return jsonify({
                "message": "Payment verification failed",
                "booking_id": booking.id,
                "status": booking.status
            }), 400
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Payment callback error: {str(e)}")
        return jsonify({"error": "Payment processing failed", "details": str(e)}), 500


@payments_bp.route('/failed', methods=['GET'])
def payment_failed():
    """
    Handle failed payment callbacks from PayChangu.
    Query params: tx_ref, status
    """
    tx_ref = request.args.get('tx_ref')
    status = request.args.get('status', 'failed')
    
    if not tx_ref:
        return jsonify({"message": "Payment cancelled or failed"}), 400
    
    try:
        # Extract booking_id from tx_ref
        booking_id = int(tx_ref.split('-')[1])
        
        booking = Bookings.query.filter_by(id=booking_id).first()
        if booking:
            booking.status = 'payment_failed'
            
            # Record failed transaction
            transaction = Transactions.query.filter_by(reference=tx_ref).first()
            if not transaction:
                transaction = Transactions(
                    amount=booking.schedule.price,
                    status='failed',
                    method='paychangu',
                    reference=tx_ref,
                    payment_status='failed',
                    booking_id=booking.id
                )
                db.session.add(transaction)
            else:
                transaction.status = 'failed'
                transaction.payment_status = 'failed'
            
            # Restore available seat
            booking.schedule.available_seats += 1
            
            db.session.commit()
            
            return jsonify({
                "message": "Payment failed or cancelled",
                "booking_id": booking.id,
                "status": booking.status
            }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Payment failure handling error: {str(e)}")
    
    return jsonify({"message": "Payment failed or was cancelled"}), 400


@payments_bp.route('/verify/<tx_ref>', methods=['GET'])
def verify_payment_status(tx_ref: str):
    """
    Manually verify payment status.
    """
    try:
        verification = verify_payment(tx_ref)
        return jsonify(verification), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@payments_bp.route('/webhook', methods=['POST'])
def payment_webhook():
    """
    Handle PayChangu webhook notifications.
    """
    try:
        data = request.get_json()
        
        if not data:
            abort(400, description='No data received')
        
        # Verify webhook signature if configured
        webhook_secret = current_app.config.get('PAYCHANGU_WEBHOOK_SECRET')
        if webhook_secret:
            # Implement signature verification here
            pass
        
        tx_ref = data.get('tx_ref')
        status = data.get('status')
        
        if not tx_ref:
            abort(400, description='Transaction reference is required')
        
        # Extract booking_id
        booking_id = int(tx_ref.split('-')[1])
        booking = Bookings.query.filter_by(id=booking_id).first()
        
        if not booking:
            abort(404, description='Booking not found')
        
        # Update based on webhook data
        if status == 'success':
            booking.status = 'confirmed'
            
            transaction = Transactions.query.filter_by(reference=tx_ref).first()
            if transaction:
                transaction.status = 'completed'
                transaction.payment_status = 'success'
            
            # Update company balance
            platform_fee = current_app.config.get('PLATFORM_FEE', 3000)
            company_earnings = booking.schedule.price - platform_fee
            booking.schedule.bus.company.balance += company_earnings
            
        elif status == 'failed':
            booking.status = 'payment_failed'
            booking.schedule.available_seats += 1
            
            transaction = Transactions.query.filter_by(reference=tx_ref).first()
            if transaction:
                transaction.status = 'failed'
                transaction.payment_status = 'failed'
        
        db.session.commit()
        
        return jsonify({"message": "Webhook processed successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({"error": "Webhook processing failed"}), 500
    
