from app import db
from app.models import Payouts
from .auth import company_or_admin_required
from flask import request, jsonify, abort, Blueprint, current_app


payouts_bp = Blueprint('payoutts', __name__)

@payouts_bp.route('/payouts/request', methods=["POST"])
@company_or_admin_required
def request_payout():
    """ Request payouts to company """
    pass