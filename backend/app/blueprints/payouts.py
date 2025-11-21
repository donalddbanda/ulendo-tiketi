from app import db
from flask_login import current_user
from datetime import datetime, timezone
from app.models import Payouts, BusCompanies
from .auth import accounts_manager_required, admin_required
from flask import request, jsonify, abort, Blueprint, current_app
from ..utils.paychangu_payouts import initiate_bank_payout, initiate_mobile_money_payout


payouts_bp = Blueprint('payouts', __name__)


@payouts_bp.route('/request', methods=["POST"])
@accounts_manager_required
def request_payout():
    """
    Request payout for company earnings.
    Companies can only request their own payouts.
    Admins can request for any company.
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    amount = data.get('amount', type=float)
    company_id = data.get('company_id', type=int)
    
    if not amount or amount <= 0:
        abort(400, description='Valid amount is required')
    
    # Determine company ID based on user role
    if current_user.role.lower() == 'company_owner':
        company_id = current_user.id
    elif not company_id:
        abort(400, description='Company ID required for admin requests')
    
    # Get company
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')
    
    # Check if company is registered
    if company.status != 'registered':
        abort(403, description='Only registered companies can request payouts')
    
    # Check if company has sufficient balance
    if company.balance < amount:
        return jsonify({
            'error': 'Insufficient balance',
            'requested': amount,
            'available': company.balance
        }), 400
    
    # Create payout request
    payout = Payouts(
        amount=amount,
        company_id=company_id,
        status='pending'
    )
    
    try:
        db.session.add(payout)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'message': 'Payout request created successfully',
        'payout': payout.to_dict(),
        'company_balance': company.balance
    }), 201


@payouts_bp.route('/list', methods=['GET'])
@accounts_manager_required
def list_payouts():
    """
    Get payout history.
    Companies see their own payouts, admins see all.
    """
    # Filter parameters
    status = request.args.get('status', type=str)
    company_id = request.args.get('company_id', type=int)
    
    # Build query
    query = Payouts.query
    
    # Apply filters based on role
    if current_user.role.lower() == 'company_owner':
        query = query.filter_by(company_id=current_user.id)
    elif company_id:
        query = query.filter_by(company_id=company_id)
    
    if status:
        query = query.filter_by(status=status)
    
    # Order by most recent first
    payouts = query.order_by(Payouts.requested_at.desc()).all()
    
    return jsonify({
        'count': len(payouts),
        'payouts': [payout.to_dict() for payout in payouts]
    }), 200


@payouts_bp.route('/<int:payout_id>', methods=['GET'])
@accounts_manager_required
def get_payout(payout_id: int):
    """Get specific payout details"""
    
    payout = Payouts.query.filter_by(id=payout_id).first()
    if not payout:
        abort(404, description='Payout not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner' and payout.company_id != current_user.id:
        abort(403)
    
    return jsonify(payout.to_dict()), 200


@payouts_bp.route('/process/<int:payout_id>', methods=['POST', 'PUT'])
@admin_required
def process_payout(payout_id: int):
    """
    Process a payout request (admin only).
    Marks payout as completed and deducts from company balance.
    """
    data = request.get_json()
    action = data.get('action', '').lower()  # 'approve' or 'reject'
    notes = data.get('notes', '')
    
    if action not in ['approve', 'reject']:
        abort(400, description='Action must be "approve" or "reject"')
    
    payout = Payouts.query.filter_by(id=payout_id).first()
    if not payout:
        abort(404, description='Payout not found')
    
    if payout.status != 'pending':
        return jsonify({
            'error': f'Cannot process payout with status: {payout.status}'
        }), 400
    
    company = payout.company
    
    if action == 'approve':
        # Check balance again
        if company.balance < payout.amount:
            return jsonify({
                'error': 'Insufficient company balance',
                'requested': payout.amount,
                'available': company.balance
            }), 400
        
        # Get company bank details
        account_details = company.account_details
        if not account_details or not account_details.get('bank_uuid'):
            return jsonify({'error': 'Company bank account not configured'}), 400
        
        # Generate unique charge_id
        charge_id = f"PAYOUT-{payout_id}-{int(datetime.now(timezone.utc).timestamp())}"
        
        # Initiate payout via PayChangu
        account_type = account_details.get('account_type', 'bank')
        
        if account_type == 'mobile_money':
            result = initiate_mobile_money_payout(
                amount=payout.amount,
                mobile_number=account_details['account_number'],
                bank_uuid=account_details['bank_uuid'],
                charge_id=charge_id,
                account_name=account_details.get('account_name')
            )

        else:
            result = initiate_bank_payout(
                amount=payout.amount,
                bank_uuid=account_details['bank_uuid'],
                account_name=account_details['account_name'],
                account_number=account_details['account_number'],
                charge_id=charge_id
            )
        
        if result.get('status') == 'success':
            payout.paychangu_charge_id = charge_id
            payout.paychangu_ref_id = result.get('data', {}).get('ref_id')
            payout.status = 'processing'
            payout.paychangu_status = 'pending'
            company.balance -= payout.amount # Deduct amount 
            db.session.commit()

            # TODO: Send email notification to company

            return jsonify({
                'message': 'Payout initiated successfully',
                'payout': payout.to_dict()
            }), 200
        
        else:
            return jsonify({
                'error': 'Failed to initiate payout',
                'details': result.get('message')
            }), 500


@payouts_bp.route('/cancel/<int:payout_id>', methods=['POST', 'DELETE'])
@accounts_manager_required
def cancel_payout(payout_id: int):
    """
    Cancel a pending payout request.
    Companies can cancel their own, admins can cancel any.
    """
    payout = Payouts.query.filter_by(id=payout_id).first()
    if not payout:
        abort(404, description='Payout not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner' and payout.company_id != current_user.id:
        abort(403)
    
    if payout.status != 'pending':
        return jsonify({
            'error': f'Cannot cancel payout with status: {payout.status}'
        }), 400
    
    payout.status = 'cancelled'
    payout.processed_at = datetime.now(timezone.utc)
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
    return jsonify({
        'message': 'Payout request cancelled',
        'payout': payout.to_dict()
    }), 200


@payouts_bp.route('/balance', methods=['GET'])
@accounts_manager_required
def get_balance():
    """
    Get company balance and payout summary.
    """
    if current_user.role.lower() == 'company_owner':
        company_id = current_user.id
    else:
        company_id = request.args.get('company_id', type=int)
        if not company_id:
            abort(400, description='Company ID required')
    
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')
    
    # Calculate payout statistics
    total_requested = db.session.query(
        db.func.sum(Payouts.amount)
    ).filter(
        Payouts.company_id == company_id,
        Payouts.status == 'pending'
    ).scalar() or 0
    
    total_paid = db.session.query(
        db.func.sum(Payouts.amount)
    ).filter(
        Payouts.company_id == company_id,
        Payouts.status == 'completed'
    ).scalar() or 0
    
    return jsonify({
        'company_id': company.id,
        'company_name': company.name,
        'current_balance': company.balance,
        'pending_payouts': total_requested,
        'total_paid_out': total_paid,
        'available_for_payout': company.balance - total_requested
    }), 200


@payouts_bp.route('/webhook', methods=['POST'])
def payout_webhook():
    """Handle PayChangu payout status webhooks"""
    data = request.get_json()
    
    ref_id = data.get('ref_id')
    status = data.get('status')  # 'successful', 'failed', 'cancelled'
    
    payout = Payouts.query.filter_by(paychangu_ref_id=ref_id).first()
    if not payout:
        abort(404, description='Payout not found')
    
    payout.paychangu_status = status
    
    if status == 'successful':
        payout.status = 'completed'
        payout.processed_at = datetime.now(timezone.utc)
    elif status in ['failed', 'cancelled']:
        payout.status = status
        payout.processed_at = datetime.now(timezone.utc)
        # Refund company balance
        payout.company.balance += payout.amount
    
    db.session.commit()
    return jsonify({'message': 'Webhook processed'}), 200

