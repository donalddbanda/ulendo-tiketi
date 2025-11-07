from app import db
from app.models import BusCompanies
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, request, jsonify, abort
from .auth import admin_required, company_or_admin_required


companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/register', methods=["POST"])
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
    
    if BusCompanies.query.filter_by(name=name).first():
        abort(400, description=f'A company named "{name}" already exists.')
    
    bus_company = BusCompanies(
        name=name, description=description,
        contact_info=contact_info, account_details=account_details
    )

    try:
        db.session.add(bus_company)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, description='A company with this name or unique details already exists.')
    except Exception as e:
        db.session.rollback()
        # abort(500, description='An unexpected error occurred during database operation.')
        return jsonify({"message": "An unexpected error occurred during database operation.", "error": str(e)}), 500
    
    return jsonify({"message": "bus company created", "company": bus_company.to_dict()})


@companies_bp.route('/get', methods=["GET"])
def get_companies():
    """ Get registered bus companies """

    companies = BusCompanies.query.filter_by(status='registered').all()

    if companies == []:
        return jsonify({"message": "No registered bus companies"}), 200
    
    return jsonify({"bus_companies": [company.to_dict() for company in companies]}), 200


@companies_bp.route('/bus-companies/<int:id>', methods=["GET"])
def view_company(id: int):
    """ View a specific bus company """

    company = BusCompanies.query.filter_by(id=id).first()
    if not company:
        return abort(400)
    return jsonify({"bus_compnay": company.to_dict()}), 200


@companies_bp.route('/review/<int:id>/<action>', methods=['POST', "PUT"])
@admin_required
def approve_company_registration(id: int, action: str):
    """ Approve or reject company registration """
    
    if action.strip().lower() not in ['reject', 'approve']:
        abort(400, description='action must be "approve" or "reject"')
    
    company = BusCompanies.query.filter_by(id=id).first()
    if not company:
        abort(400, description='bus company not found')
    
    company.status = "registered" if action.lower().strip() == 'approve' else 'rejected'
    try:
        db.session.commit()
    except:
        abort(500)

    # TODO: send rejection or approveal email to the bus company

    return jsonify({"message": f"{action}ed {company.id} registration"})


@companies_bp.route('/get/<int:id>', methods=["PUT", "POST"])
@company_or_admin_required
def update_company_info(id: int):
    """ update company details """

    company = BusCompanies.query.filter_by(id=id).first()
    if not company:
        abort(400, description='company not found')

    if current_user.role == 'company' and current_user.id != company.id:
        abort(403, description='You can only update your own company info.')

    data = request.get_json()
    if not data:
        abort(400, description='data not provided')

    name = data.get('name', company.name)
    description = data.get('description', company.description)
    account_details = data.get('account_details', company.account_details)
    contact_info = data.get('contact_info', company.contact_info)

    company.name, company.description, company.account_details, company.contact_info = name, description, account_details, contact_info

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        abort(400, description='Company with this name already exists.')
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))

    return jsonify({"message": "company info updated", "company": company.to_dict()}), 200