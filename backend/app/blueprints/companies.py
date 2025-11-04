import json
from app import db
from flask import Blueprint, request, jsonify
from ..models import BusCompany


company = Blueprint("bookin", __name__)

@company.route('/bus-company', methods=["POST"])
def create_company():
    """ Create a bus company"""

    data = request.get_json()
    if not data:
        return jsonify({"error": "data not provided"}), 400

    name = data.get_json('name')
    description = data.get('description')
    contact_info = data.get_json('contact_info')
    account_details = data.get_json('account_details')

    if not all([name, description, account_details, contact_info]):
        return jsonify({"error": "Provide name, description, contact details, and account details"}), 400

    bus_company = BusCompany(
        name=name,
        account_details=json.dumps(account_details),
        description=description,
        contact_info=json.dumps(contact_info)
    )

    try:
        db.session.add(bus_company)
        db.session.commit()
    
    except Exception as e:
        return jsonify({"error": "Failed to create bus company", "details": str(e)}), 500

    return jsonify({
        "message": "Bus company created",
        "company": {
            "id": bus_company.id,
            "name": bus_company.name,
            "description": bus_company.description,
            "contact_info": bus_company.contact_info,
            "account_details": bus_company.account_details
        }
    }), 201


@company.route('/bus-company', methods=["GET"])
def get_bus_companies():
    bus_companies = BusCompany.query.all()

    return jsonify({
        "bus_companies": [
            {
                "id": bus_company.id,
                "name": bus_company.name,
                "description": bus_company.description,
                "contact_info": bus_company.contact_info,
                "account_details": bus_company.account_details
            } 
            for bus_company in bus_companies
        ]
    }), 200


@company.route('/bus-company/{int:id}')
def get_bus_company(id: int):
    """ Get a specific bus company """

    bus_company = BusCompany.query.get(id)

    if not bus_company:
        return jsonify({"error": "Bus company not found"}), 404
    
    return jsonify({
        "id": bus_company.id,
        "name": bus_company.name,
        "description": bus_company.description,
        "contact_info": bus_company.contact_info,
        "account_details": bus_company.account_details
    }), 200


