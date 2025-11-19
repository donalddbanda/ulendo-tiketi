from app import db
from app.models import BusCompanies, Users
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, request, jsonify, abort, current_app
from ..utils.paychangu_payouts import get_available_banks
from ..utils.email_services import send_password_reset_code_email
from .auth import admin_required, company_or_admin_required, create_password_reset_code
import threading


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

    # Contact details
    phone_numbers = data.get('phone_numbers')
    email = data.get('email')

    # Bank account deatails for payouts
    bank_name = data.get('bank_name')
    bank_account_number = data.get('bank_account_number')
    bank_account_name = data.get('bank_account_name')

    if not all([name, description]):
        abort(400, description='name and description are required')
    
    if BusCompanies.query.filter_by(name=name).first():
        abort(400, description=f'A company named "{name}" already exists.')

    if all([bank_name, bank_account_number, bank_account_name]):
        abort(400, description='bank_name, bank_account_number, and bank_account_name are required in account_details')
    
    if not phone_numbers:
        abort(400, description='phone_numbers is required')
    # email is optional

    contact_info = {
        'phone_numbers': phone_numbers,
        'email': email
    }

    account_details = {
        "bank_uuid": None,
        'bank_name': bank_name,
        "account_type": 'bank',
        'bank_account_number': bank_account_number,
        'bank_account_name': bank_account_name
    }

    # Get PayChangu suppported banks
    supported_banks = get_available_banks(currency='MWK')

    if supported_banks.get('status') != 'success':
        abort(500, description='Could not verify bank details at this time. Please try again later.')
    
    # set bank uuid and bank name to Paychangu's suported bank name if bank is supported
    for supported_bank in supported_banks.get('data', []):
        if supported_bank['name'].lower().startswith(bank_name[7].lower()):
            account_details['bank_uuid'] = supported_bank['uuid']
            bank_name = supported_bank['name']
    
    # Create an associated user for the company (no public password)
    # Expect admin to provide company contact phone and optional email
    company_user = Users(
        name=name,
        email=email or f"company_{name.lower().replace(' ', '_')}@ulendo.local",  # generate placeholder if not provided
        phone_number=phone_numbers[0] if isinstance(phone_numbers, list) and phone_numbers else (phone_numbers if isinstance(phone_numbers, str) else None),
        role='company'
    )
    # set a temporary random password so account exists; company will use password reset link
    import secrets
    company_user.set_password(secrets.token_urlsafe(16))

    bus_company = BusCompanies(
        name=name, description=description,
        contact_info=contact_info, account_details=account_details,
        user=company_user
    )

    try:
        db.session.add(company_user)
        db.session.add(bus_company)
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error('IntegrityError creating company: %s', e)
        abort(400, description='A company with this name or unique details already exists.')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error creating company')
        return jsonify({"message": "An unexpected error occurred during database operation.", "error": str(e)}), 500

    # Create a password reset code and email it to the company contact
    # Use provided email if available, otherwise use placeholder (but won't send)
    try:
        contact_email = email or f"company_{name.lower().replace(' ', '_')}@ulendo.local"
        code = create_password_reset_code(email=contact_email)
        # send email in background (only if real email provided)
        if email:
            thread = threading.Thread(target=send_password_reset_code_email, args=(code, email))
            thread.start()
    except Exception as e:
        current_app.logger.exception('Failed to create/send password reset code')

    return jsonify({"message": "bus company created", "company": bus_company.to_dict()}), 201


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

    if company.status == 'registered':
        abort(400, description='Bus company already registered')
    
    company.status = "registered" if action.lower().strip() == 'approve' else 'rejected'
    try:
        db.session.commit()
    except:
        abort(500)

    # TODO: send rejection or approveal email to the bus company

    return jsonify({"message": f"{action}ed bus company registration"})


@companies_bp.route('/update/<int:id>', methods=["PUT", "POST"])
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

    if BusCompanies.query.filter(BusCompanies.name==name, BusCompanies.id!=company.id).first():
        abort(400, description='Another company with this name already exists.')

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


@companies_bp.route('/whoami', methods=["GET"])
@company_or_admin_required
def get_company_info():
    """Get current user's company information."""
    from flask_login import current_user
    
    if current_user.role.lower() == 'admin':
        # For admin, return info about a specific company or the first company
        company_id = request.args.get('company_id', type=int)
        if company_id:
            company = BusCompanies.query.filter_by(id=company_id).first()
        else:
            company = BusCompanies.query.first()
        
        if not company:
            return jsonify({'error': 'No company found'}), 404
    else:
        # For company owner, get their company
        company = BusCompanies.query.filter_by(owner_id=current_user.id).first()
        if not company:
            return jsonify({'error': 'Company not found'}), 404
    
    return jsonify({'company': company.to_dict()}), 200