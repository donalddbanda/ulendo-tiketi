from app import db
from .auth import admin_required
from app.models import BusCompanies
from flask import Blueprint, request, jsonify, abort


companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/bus-companies', methods=["POST"])
@admin_required
def register_bus_company():
    """ Register bus company """

    data = request.get_json()
    if not data:
        abort(400, description='data not provided')

    name = data.get('name')
    description = data.get('description')
    contact_info = data.get('contact_info')
    account_details = data.get('account_details')

    if not all([name, description, contact_info, account_details]):
        abort(400, description='name, description, conatact_info, and account_details required')
    
    bus_company = BusCompanies(
        name=name, descrption=description,
        contact_info=contact_info, account_details=account_details
    )

    try:
        db.session.add(bus_company)
        db.session.commit()
    except:
        abort(500)
    
    return jsonify({"message": "bus company created", "company": bus_company.to_dict()})
