from ..extensions import paychangu_client
from paychangu.models.payout import Payout
from paychangu.models.payment import Payment


def initiate_payment(amount, trans_reference):
    payment = Payment(
        currency="MWK",
        amount=amount,
        tx_ref=trans_reference,
        callback_url='http://127.0.0.1:5000/api',
        return_url='http://127.0.0.1:5000/api'
    )