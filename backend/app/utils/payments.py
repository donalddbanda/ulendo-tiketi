from flask import current_app
from datetime import datetime
from ..extensions import paychangu_client
from paychangu.models.payment import Payment


def create_payment_link(booking_id: int, amount: float, user_email: str = None, user_name: str = None):
    """
    Create a payment link using PayChangu.
    
    Args:
        booking_id: The booking ID for transaction reference
        amount: Payment amount
        user_email: User's email (optional)
        user_name: User's name (optional)
    
    Returns:
        dict: Contains checkout_url and tx_ref
    """

    # Generate unique transaction reference
    tx_ref = f"BOOKING-{booking_id}-{int(datetime.now().timestamp() * 1000)}"
    
    # Get callback and return URLs from config
    base_url = current_app.config.get('PAYCHANGU_CALLBACK_URL', 'http://localhost:5000')
    callback_url = current_app.config.get('PAYCHANGU_CALLBACK_URL', f"{base_url}/api/payments/successful")
    return_url = "127.0.0.1:500/api/bookings/get"
    
    # Create payment object
    payment = Payment(
        amount=amount,
        currency="MWK",
        tx_ref=tx_ref,
        email=user_email,
        first_name=user_name,
        last_name=None,
        callback_url=callback_url,
        return_url=return_url,
        customization={
            "title": "Bus Ticket Payment",
            "description": f"Payment for booking #{booking_id}"
        },
        meta={
            "booking_id": str(booking_id),
            "timestamp": datetime.now().isoformat()
        }
    )
    
    try:
        response = paychangu_client.initiate_transaction(payment)
        
        if response.get('status') == 'success':
            return {
                'checkout_url': response['data']['checkout_url'],
                'tx_ref': response['data']['data']['tx_ref'],
                'status': 'success'
            }
        else:
            return {
                'error': response.get('message', 'Payment initialization failed'),
                'status': 'failed'
            }
    except Exception as e:
        current_app.logger.error(f"PayChangu payment creation error: {str(e)}")
        return {
            'error': str(e),
            'status': 'failed'
        }


def verify_payment(tx_ref: str):
    """
    Verify payment status with PayChangu.
    
    Args:
        tx_ref: Transaction reference
    
    Returns:
        dict: Payment verification details
    """
    try:
        # You'll need to implement this based on PayChangu's verification endpoint
        # This is a placeholder for the verification logic
        response = paychangu_client.verify_transaction(tx_ref)
        return response
    except Exception as e:
        current_app.logger.error(f"Payment verification error: {str(e)}")
        return {
            'error': str(e),
            'status': 'failed'
        }