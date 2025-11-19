from app import db
from app.models import Employees, Branches, Users, BusCompanies
from flask_login import current_user
from flask import Blueprint, request, jsonify, abort, current_app
from .auth import company_or_admin_required, login_required, branch_manager_required
import threading
import secrets
from ..utils.email_services import send_password_reset_code_email
from .auth import create_password_reset_code


employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/invite', methods=['POST'])
@company_or_admin_required
def invite_employee():
    """Invite an employee to a branch"""
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    branch_id = data.get('branch_id')
    employee_role = data.get('employee_role')  # e.g., 'branch_manager', 'accounts_manager', 'bus_manager', 'schedule_manager', 'conductor'

    if not all([name, phone, branch_id, employee_role]):
        abort(400, description='Name, phone, branch_id, and employee_role are required')

    # Get branch and verify access
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')

    # Verify permissions
    if current_user.role.lower() == 'company' and branch.company_id != current_user.id:
        abort(403, description='Not authorized to invite employees to this branch')

    # Check if user already exists or create new user
    existing_user = Users.query.filter_by(phone_number=phone).first()
    if existing_user:
        # Check if already an employee
        existing_emp = Employees.query.filter_by(user_id=existing_user.id, branch_id=branch_id).first()
        if existing_emp:
            return jsonify({'error': 'Employee already exists in this branch'}), 400
        employee_user = existing_user
    else:
        # Create new user for employee
        generated_email = email or f"emp_{phone.replace('+', '').replace(' ', '')}@ulendo.local"
        employee_user = Users(
            name=name,
            phone_number=phone,
            email=generated_email,
            role=employee_role
        )
        # Set a temporary password
        employee_user.set_password(secrets.token_urlsafe(16))

        try:
            db.session.add(employee_user)
            db.session.flush()  # Get the ID without committing
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Create employee record
    employee = Employees(
        user_id=employee_user.id,
        branch_id=branch_id,
        employee_role=employee_role,
        status='pending'  # Pending approval
    )

    try:
        db.session.add(employee)
        db.session.commit()

        # Generate password reset code for new user
        if not existing_user:
            code = create_password_reset_code(employee_user.email, employee_user.phone_number)
            
            # Send invitation email if email provided
            if email:
                thread = threading.Thread(
                    target=send_password_reset_code_email,
                    args=(code, email, f"Employee Invitation for {branch.name} - {employee_role}")
                )
                thread.start()

        return jsonify({
            'message': 'Employee invited successfully',
            'employee': employee.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@employees_bp.route('/branch/<int:branch_id>/list', methods=['GET'])
@login_required
def list_branch_employees(branch_id: int):
    """Get employees for a branch"""
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')

    employees = Employees.query.filter_by(branch_id=branch_id).all()

    return jsonify({
        'employees': [emp.to_dict() for emp in employees]
    }), 200


@employees_bp.route('/<int:employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id: int):
    """Get employee details"""
    employee = Employees.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')

    return jsonify(employee.to_dict()), 200


@employees_bp.route('/<int:employee_id>/approve', methods=['POST', 'PUT'])
@company_or_admin_required
def approve_employee(employee_id: int):
    """Approve employee (activate)"""
    employee = Employees.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')

    # Verify permissions
    if current_user.role.lower() == 'company' and employee.branch.company_id != current_user.id:
        abort(403, description='Not authorized to approve this employee')

    employee.status = 'active'
    employee.approved_at = db.func.now()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'message': 'Employee approved successfully',
        'employee': employee.to_dict()
    }), 200


@employees_bp.route('/<int:employee_id>/reject', methods=['POST', 'PUT'])
@company_or_admin_required
def reject_employee(employee_id: int):
    """Reject/remove employee"""
    employee = Employees.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')

    # Verify permissions
    if current_user.role.lower() == 'company' and employee.branch.company_id != current_user.id:
        abort(403, description='Not authorized to remove this employee')

    try:
        db.session.delete(employee)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Employee removed successfully'}), 200


@employees_bp.route('/<int:employee_id>/update', methods=['PUT', 'POST'])
@company_or_admin_required
def update_employee(employee_id: int):
    """Update employee details"""
    employee = Employees.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')

    # Verify permissions
    if current_user.role.lower() == 'company' and employee.branch.company_id != current_user.id:
        abort(403, description='Not authorized to update this employee')

    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')

    if 'employee_role' in data:
        employee.employee_role = data['employee_role']
    if 'status' in data:
        employee.status = data['status']

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'message': 'Employee updated successfully',
        'employee': employee.to_dict()
    }), 200
