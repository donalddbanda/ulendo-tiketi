from app import db
from app.models import BusCompanies, Users, Branches
from flask_login import current_user
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, request, jsonify, abort, current_app
from ..utils.paychangu_payouts import get_available_banks
from .auth import admin_required, company_owner_or_admin_required


companies_bp = Blueprint('companies', __name__)


@companies_bp.route('/register', methods=["POST"])
@admin_required
def register_bus_company():
    """
    Register a new bus company with owner account.
    Only admins can register companies.
    
    This creates:
    1. The company record
    2. The company owner user account
    3. A default branch (optional)
    
    Request body:
    {
        "company": {
            "name": "ABC Bus Company",
            "description": "Premium bus services"
        },
        "owner": {
            "full_name": "John Doe",
            "email": "john@abcbus.com",
            "phone_number": "+265991234567",
            "password": "SecurePassword123"
        },
        "contact_info": {
            "phone_numbers": ["+265999123456", "+265888123456"],
            "email": "contact@abcbus.com"
        },
        "bank_account": {
            "bank_name": "National Bank of Malawi",
            "account_number": "1234567890",
            "account_name": "ABC Bus Company"
        },
        "create_default_branch": true,  // Optional
        "default_branch_name": "Main Branch"  // Optional, defaults to "Main Branch"
    }
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    # Extract company data
    company_data = data.get('company', {})
    owner_data = data.get('owner', {})
    bank_data = data.get('bank_account', {})
    
    # Validate required company data
    company_name = company_data.get('name')
    description = company_data.get('description')
    phone_numbers = company_data.get('phone_numbers', [])
    company_email = company_data.get('email')

    if not all([company_name, description, phone_numbers, company_email]):
        abort(400, description='Company name, description, phone numbers, and email are required')

    # Validate required owner data
    owner_name = owner_data.get('full_name') or owner_data.get('name')
    owner_email = owner_data.get('email')
    owner_phone = owner_data.get('phone_number') or owner_data.get('phone')
    owner_password = owner_data.get('password')

    if not all([owner_name, owner_email, owner_phone, owner_password]):
        abort(400, description='Owner full name, email, phone number, and password are required')

    # Validate bank account data
    bank_name = bank_data.get('bank_name')
    account_number = bank_data.get('account_number')
    account_name = bank_data.get('account_name')

    if not all([bank_name, account_number, account_name]):
        abort(400, description='Bank name, account number, and account name are required')

    # Check if company name already exists
    if BusCompanies.query.filter_by(name=company_name).first():
        abort(400, description=f'A company named "{company_name}" already exists')

    # Check if owner email or phone already exists
    if Users.query.filter_by(email=owner_email).first():
        abort(400, description=f'An account with email {owner_email} already exists')
    
    if Users.query.filter_by(phone_number=owner_phone).first():
        abort(400, description=f'An account with phone number {owner_phone} already exists')

    # Get PayChangu supported banks and validate
    supported_banks = get_available_banks(currency='MWK')
    
    if supported_banks.get('status') != 'success':
        abort(500, description='Could not verify bank details at this time. Please try again later.')
    
    # Find matching bank UUID
    bank_uuid = None
    matched_bank_name = bank_name
    
    for supported_bank in supported_banks.get('data', []):
        # Check if the provided bank name matches any supported bank
        if bank_name[5].lower() in supported_bank['name'][5].lower() or \
           supported_bank['name'][5].lower() in bank_name[5].lower():
            bank_uuid = supported_bank['uuid']
            matched_bank_name = supported_bank['name']
            break
    
    if not bank_uuid:
        # List available banks for user reference
        available_banks = [bank['name'] for bank in supported_banks.get('data', [])]
        abort(400, description=f'Bank "{bank_name}" is not supported. Available banks: {", ".join(available_banks[:5])}...')

    # Prepare contact info
    contact_info = {
        'phone_numbers': phone_numbers if isinstance(phone_numbers, list) else [phone_numbers],
        'email': company_email
    }

    # Prepare account details
    account_details = {
        "bank_uuid": bank_uuid,
        "bank_name": matched_bank_name,
        "account_type": bank_data.get('account_type', 'bank'),
        "account_number": account_number,
        "account_name": account_name
    }

    try:
        # Step 1: Create the company owner user account
        owner_user = Users(
            name=owner_name,
            email=owner_email,
            phone_number=owner_phone,
            role='company_owner'
        )
        owner_user.set_password(owner_password)
        
        db.session.add(owner_user)
        db.session.flush()  # Get the owner user ID without committing

        # Step 2: Create the company
        bus_company = BusCompanies(
            name=company_name,
            description=description,
            contact_info=contact_info,
            account_details=account_details,
            status='registered',  # Auto-approve since admin is creating it
            owner_id=owner_user.id
        )
        
        db.session.add(bus_company)
        db.session.flush()  # Get the company ID without committing

        # Step 3: Update owner's company_id
        owner_user.company_id = bus_company.id

        # Step 4: Create default branch if requested
        default_branch = None
        if data.get('create_default_branch', False):
            branch_name = data.get('default_branch_name', 'Main Branch')
            
            default_branch = Branches(
                name=branch_name,
                company_id=bus_company.id,
                manager_id=owner_user.id  # Owner manages the default branch initially
            )
            
            db.session.add(default_branch)
            db.session.flush()
            
            # Update owner's branch_id
            owner_user.branch_id = default_branch.id

        # Commit all changes
        db.session.commit()

        # Prepare response
        response_data = {
            "message": "Bus company and owner account created successfully",
            "company": bus_company.to_dict(),
            "owner": {
                "id": owner_user.id,
                "name": owner_user.name,
                "email": owner_user.email,
                "phone_number": owner_user.phone_number,
                "role": owner_user.role
            }
        }

        if default_branch:
            response_data["default_branch"] = default_branch.to_dict()

        return jsonify(response_data), 201

    except IntegrityError as e:
        db.session.rollback()
        # Check what caused the integrity error
        error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        if 'name' in error_msg or 'company' in error_msg.lower():
            abort(400, description='A company with this name already exists')
        elif 'email' in error_msg:
            abort(400, description='An account with this email already exists')
        elif 'phone' in error_msg:
            abort(400, description='An account with this phone number already exists')
        else:
            abort(400, description='A company or user with these details already exists')
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "message": "An unexpected error occurred during registration",
            "error": str(e)
        }), 500


@companies_bp.route('/get', methods=["GET"])
def get_companies():
    """Get all registered bus companies"""
    companies = BusCompanies.query.filter_by(status='registered').all()

    if not companies:
        return jsonify({"message": "No registered bus companies", "companies": []}), 200
    
    return jsonify({
        "companies": [company.to_dict() for company in companies],
        "count": len(companies)
    }), 200


@companies_bp.route('/pending', methods=["GET"])
@admin_required
def get_pending_companies():
    """Get all pending company registrations (admin only)"""
    companies = BusCompanies.query.filter_by(status='pending').all()

    if not companies:
        return jsonify({"message": "No pending company registrations", "companies": []}), 200
    
    return jsonify({
        "companies": [company.to_dict() for company in companies],
        "count": len(companies)
    }), 200


@companies_bp.route('/<int:id>', methods=["GET"])
def view_company(id: int):
    """View a specific bus company"""
    company = BusCompanies.query.filter_by(id=id).first()
    
    if not company:
        abort(404, description='Company not found')
    
    # Get additional company info
    response = company.to_dict()
    
    # Add owner info
    owner = Users.query.filter_by(id=company.owner_id).first()
    if owner:
        response['owner'] = {
            'id': owner.id,
            'name': owner.name,
            'email': owner.email,
            'phone_number': owner.phone_number
        }
    
    # Add branch count
    branch_count = Branches.query.filter_by(company_id=id).count()
    response['branch_count'] = branch_count
    
    # Add bus count
    from app.models import Buses
    bus_count = Buses.query.filter_by(company_id=id).count()
    response['bus_count'] = bus_count
    
    return jsonify({"company": response}), 200


@companies_bp.route('/review/<int:id>/<action>', methods=['POST', "PUT"])
@admin_required
def review_company_registration(id: int, action: str):
    """
    Approve or reject company registration (admin only).
    This is for companies registered through other means (not through admin panel).
    """
    if action.strip().lower() not in ['reject', 'approve']:
        abort(400, description='Action must be "approve" or "reject"')
    
    company = BusCompanies.query.filter_by(id=id).first()
    if not company:
        abort(404, description='Company not found')

    if company.status == 'registered':
        abort(400, description='Company already registered')
    
    company.status = "registered" if action.lower().strip() == 'approve' else 'rejected'
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))

    # TODO: Send approval/rejection email to the company owner

    return jsonify({
        "message": f"Company registration {action}ed successfully",
        "company": company.to_dict()
    }), 200


@companies_bp.route('/update/<int:id>', methods=["PUT", "POST"])
@company_owner_or_admin_required
def update_company_info(id: int):
    """Update company details"""
    company = BusCompanies.query.filter_by(id=id).first()
    
    if not company:
        abort(404, description='Company not found')

    # Authorization check
    if current_user.role != 'admin' and current_user.id != company.owner_id:
        abort(403, description='You can only update your own company info')

    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    # Update allowed fields
    if 'name' in data:
        new_name = data['name']
        # Check if new name is already taken by another company
        existing = BusCompanies.query.filter(
            BusCompanies.name == new_name,
            BusCompanies.id != company.id
        ).first()
        
        if existing:
            abort(400, description='Another company with this name already exists')
        
        company.name = new_name

    if 'description' in data:
        company.description = data['description']

    if 'contact_info' in data:
        company.contact_info = data['contact_info']

    if 'account_details' in data:
        company.account_details = data['account_details']

    try:
        db.session.commit()
        return jsonify({
            "message": "Company info updated successfully",
            "company": company.to_dict()
        }), 200
    
    except IntegrityError:
        db.session.rollback()
        abort(400, description='Company with this name already exists')
    
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


@companies_bp.route('/deactivate/<int:id>', methods=['POST'])
@admin_required
def deactivate_company(id: int):
    """Deactivate a company (admin only)"""
    company = BusCompanies.query.filter_by(id=id).first()
    
    if not company:
        abort(404, description='Company not found')
    
    company.status = 'inactive'
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Company deactivated successfully",
            "company": company.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


@companies_bp.route('/activate/<int:id>', methods=['POST'])
@admin_required
def activate_company(id: int):
    """Reactivate a company (admin only)"""
    company = BusCompanies.query.filter_by(id=id).first()
    
    if not company:
        abort(404, description='Company not found')
    
    company.status = 'registered'
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Company activated successfully",
            "company": company.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


