from app import db
from app.models import BusCompanies
from flask import Blueprint, request, jsonify, abort
from flask_login import current_user
from .auth import company_owner_or_admin_required
from ..utils.paychangu_payouts import get_available_banks


banks_bp = Blueprint('banks', __name__)


@banks_bp.route('/available', methods=['GET'])
def get_banks_list():
    """
    Get list of available banks from PayChangu.
    This includes both traditional banks and mobile money providers.
    Public endpoint - no authentication required.
    
    Query Parameters:
        - currency: Currency code (default: MWK)
    """
    currency = request.args.get('currency', 'MWK').upper()
    
    # Validate currency code
    if currency not in ['MWK']:  # Add more currencies as needed
        return jsonify({
            'error': 'Invalid currency',
            'message': f'Currency {currency} is not supported. Use MWK for Malawi Kwacha.'
        }), 400
    
    try:
        banks_response = get_available_banks(currency)
        
        if banks_response.get('status') == 'success':
            # Format the response for easier use
            banks_data = banks_response.get('data', [])
            
            # Categorize banks and mobile money
            banks = []
            mobile_money = []
            
            for bank in banks_data:
                bank_name = bank.get('name', '')
                bank_info = {
                    'uuid': bank.get('uuid'),
                    'name': bank_name
                }
                
                # Categorize based on name
                if 'Mpamba' in bank_name or 'Airtel Money' in bank_name:
                    mobile_money.append(bank_info)
                else:
                    banks.append(bank_info)
            
            return jsonify({
                'status': 'success',
                'message': banks_response.get('message'),
                'data': {
                    'currency': currency,
                    'banks': banks,
                    'mobile_money': mobile_money,
                    'all': banks_data  # Original list
                }
            }), 200
        else:
            return jsonify({
                'error': 'Failed to fetch banks',
                'message': banks_response.get('message', 'Unknown error')
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@banks_bp.route('/account/update', methods=['POST', 'PUT'])
@company_owner_or_admin_required
def update_bank_account():
    """
    Update company bank account details.
    Companies can update their own, admins can update any.
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    # Determine company ID
    if current_user.role.lower().strip() == 'company_owner':
        company_id = current_user.id
    else:
        company_id = data.get('company_id')
        if not company_id:
            abort(400, description='Company ID required for admin users')
    
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')
    
    # Extract bank account details
    bank_uuid = data.get('bank_uuid')
    account_name = data.get('account_name')
    account_number = data.get('account_number')
    bank_name = data.get('bank_name')  # Optional, for display
    account_type = data.get('account_type', 'bank')  # 'bank' or 'mobile_money'
    
    if not all([bank_uuid, account_name, account_number]):
        abort(400, description='bank_uuid, account_name, and account_number are required')
    
    # Update or create account_details
    if not company.account_details:
        company.account_details = {}
    
    company.account_details.update({
        'bank_uuid': bank_uuid,
        'account_name': account_name,
        'account_number': account_number,
        'bank_name': bank_name,
        'account_type': account_type,
        'updated_at': db.func.now()
    })
    
    # Mark the column as modified for JSON fields
    db.session.query(BusCompanies).filter_by(id=company_id).update(
        {'account_details': company.account_details},
        synchronize_session=False
    )
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'message': 'Bank account details updated successfully',
        'company_id': company.id,
        'account_details': {
            'bank_name': bank_name,
            'account_name': account_name,
            'account_number': account_number,
            'account_type': account_type
        }
    }), 200


@banks_bp.route('/account', methods=['GET'])
@company_owner_or_admin_required
def get_bank_account():
    """
    Get company bank account details.
    """
    # Determine company ID
    if current_user.role.lower().strip() == 'company_owner':
        company_id = current_user.id
    else:
        company_id = request.args.get('company_id', type=int)
        if not company_id:
            abort(400, description='Company ID required')
    
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')
    
    account_details = company.account_details or {}
    
    # Don't expose sensitive full account numbers to non-admins
    if current_user.role.lower().strip() != 'admin':
        account_number = account_details.get('account_number', '')
        if account_number and len(account_number) > 4:
            # Mask account number except last 4 digits
            account_details['account_number'] = '*' * (len(account_number) - 4) + account_number[-4:]
    
    return jsonify({
        'company_id': company.id,
        'company_name': company.name,
        'account_configured': bool(account_details.get('bank_uuid')),
        'account_details': {
            'bank_uuid': account_details.get('bank_uuid'),
            'bank_name': account_details.get('bank_name'),
            'account_name': account_details.get('account_name'),
            'account_number': account_details.get('account_number'),
            'account_type': account_details.get('account_type', 'bank')
        }
    }), 200


@banks_bp.route('/account/delete', methods=['DELETE', 'POST'])
@company_owner_or_admin_required
def delete_bank_account():
    """
    Remove bank account details.
    Requires confirmation as this affects payout ability.
    """
    data = request.get_json() or {}
    confirm = data.get('confirm', False)
    
    if not confirm:
        return jsonify({
            'error': 'Confirmation required',
            'message': 'Set "confirm": true to delete bank account details'
        }), 400
    
    # Determine company ID
    if current_user.role.lower().strip() == 'company_owner':
        company_id = current_user.id
    else:
        company_id = data.get('company_id')
        if not company_id:
            abort(400, description='Company ID required for admin users')
    
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')
    
    # Clear account details
    company.account_details = {}
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'message': 'Bank account details removed',
        'company_id': company.id
    }), 200

