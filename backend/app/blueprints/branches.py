from app import db
from app.models import Branches, Employees, BusCompanies, Users
from flask_login import current_user
from flask import Blueprint, request, jsonify, abort
from .auth import company_or_admin_required, login_required
import threading
from ..utils.email_services import send_employee_invitation_email


branches_bp = Blueprint('branches', __name__)


@branches_bp.route('/create', methods=['POST'])
@company_or_admin_required
def create_branch():
    """Create a new branch for a company"""
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    name = data.get('name')
    location = data.get('location')
    phone = data.get('phone')
    company_id = data.get('company_id')

    if not name or not location:
        abort(400, description='Name and location are required')

    # Only company owners or admins can create branches
    if current_user.role.lower() == 'company':
        company_id = current_user.id
    elif not company_id:
        abort(400, description='Company ID required for admin requests')

    # Verify company exists
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')

    branch = Branches(
        name=name,
        location=location,
        phone=phone,
        company_id=company_id
    )

    try:
        db.session.add(branch)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'message': 'Branch created successfully',
        'branch': branch.to_dict()
    }), 201


@branches_bp.route('/list', methods=['GET'])
@company_or_admin_required
def list_branches():
    """Get branches for a company"""
    company_id = request.args.get('company_id', type=int)

    # Filter by user's company if they're a company owner
    if current_user.role.lower() == 'company':
        company_id = current_user.id
    elif not company_id:
        abort(400, description='Company ID required for admin requests')

    branches = Branches.query.filter_by(company_id=company_id).all()

    return jsonify({
        'branches': [branch.to_dict() for branch in branches]
    }), 200


@branches_bp.route('/<int:branch_id>', methods=['GET'])
@login_required
def get_branch(branch_id: int):
    """Get branch details"""
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')

    return jsonify(branch.to_dict()), 200


@branches_bp.route('/<int:branch_id>/update', methods=['PUT', 'POST'])
@company_or_admin_required
def update_branch(branch_id: int):
    """Update branch details"""
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')

    # Verify permissions
    if current_user.role.lower() == 'company' and branch.company_id != current_user.id:
        abort(403, description='Not authorized to update this branch')

    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    if 'name' in data:
        branch.name = data['name']
    if 'location' in data:
        branch.location = data['location']
    if 'phone' in data:
        branch.phone = data['phone']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'message': 'Branch updated successfully',
        'branch': branch.to_dict()
    }), 200


@branches_bp.route('/<int:branch_id>/delete', methods=['DELETE', 'POST'])
@company_or_admin_required
def delete_branch(branch_id: int):
    """Delete a branch"""
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')

    # Verify permissions
    if current_user.role.lower() == 'company' and branch.company_id != current_user.id:
        abort(403, description='Not authorized to delete this branch')

    try:
        db.session.delete(branch)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Branch deleted successfully'}), 200
