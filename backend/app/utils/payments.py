from flask_login import current_user
from datetime import datetime, timezone
from ..extensions import paychangu_client
from paychangu.models.payout import Payout
from paychangu.models.payment import Payment


def create_payment_link(amount: float, tx_ref: None = None, currence: str = "MWK"):
    """
    Create a payment link using PayChangu.
    """
    payment = Payment(
        amount=amount,
        currency=currence,
        tx_ref=tx_ref,
        email=None,
        first_name=current_user.name,
        last_name=None,
        callback_url="https://127:0,o,1:5000/api/api/payments/successful",
        return_url="https://127:0,o,1:5000/api/payments/failed"
    )
    response = paychangu_client.initiate_transaction(payment)
    return response['data']['checkout_url'] # A payment link redirecting to PayChangu's Checkout page