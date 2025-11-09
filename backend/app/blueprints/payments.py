from flask import Blueprint, jsonify, abort, request
from .auth import passenger_required

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/payments/successful', methods=['GET'])
@passenger_required
def payment_successful():
    """
    Endpoint to handle successful payment callbacks from PayChangu.
    """
    data = request.get_json()
    payment_link = data['data']['checkout_url']
    return jsonify({"message": "Payment successfully initiated", "payment_link": payment_link}), 200

@payments_bp.route('/payments/failed', methods=['GET'])
@passenger_required
def payment_failed():
    """
    Endpoint to handle failed payment callbacks from PayChangu.
    """
    return jsonify({"message": "Payment failed or was cancelled"}), 400