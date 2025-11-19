import threading
from app import db
from datetime import datetime, timezone
from app.models import Users, EmployeeInvitation, BusCompanies, Branches, Buses
from flask import Blueprint, request, jsonify, abort, current_app
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from .auth import (
    admin_required, company_owner_or_admin_required, 
    branch_manager_required, company_owner_required
)
from ..utils.email_services import send_employee_invitation_email


employees_bp = Blueprint('employees', __name__)


@employees_bp.route('/invite', methods=['POST'])
@branch_manager_required
def invite_employee():
    """
    Invite an employee to join the company/branch.
    Company owners can invite to any branch in their company.
    Branch managers can only invite to their branch.
    
    Request body:
    {
        "email": "employee@example.com",
        "phone_number": "+265991234567",
        "full_name": "John Doe",
        "role": "conductor",  // conductor, bus_manager, schedule_manager, accounts_manager, branch_manager
        "branch_id": 1  // Optional for company owners, auto-assigned for branch managers
    }
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    email = data.get('email')
    phone_number = data.get('phone_number') or data.get('phone')
    full_name = data.get('full_name') or data.get('name')
    role = data.get('role', '').lower()
    branch_id = data.get('branch_id')
    
    # Validate required fields
    if not all([email, phone_number, full_name, role]):
        abort(400, description='email, phone_number, full_name, and role are required')
    
    # Validate role
    valid_roles = ['conductor', 'bus_manager', 'schedule_manager', 
                   'accounts_manager', 'branch_manager']
    if role not in valid_roles:
        abort(400, description=f'Invalid role. Must be one of: {", ".join(valid_roles)}')
    
    # Determine branch_id and company_id based on user role
    if current_user.role.lower() == 'company_owner':
        if not current_user.company_id:
            abort(400, description='Company owner must be associated with a company')
        
        company_id = current_user.company_id
        
        # Company owner must specify branch_id or it defaults to their branch
        if not branch_id:
            if not current_user.branch_id:
                abort(400, description='branch_id is required')
            branch_id = current_user.branch_id
        
        # Verify branch belongs to the company
        branch = Branches.query.filter_by(id=branch_id).first()
        if not branch or branch.company_id != company_id:
            abort(400, description='Branch not found or does not belong to your company')
    
    elif current_user.role.lower() == 'branch_manager':
        if not current_user.branch_id:
            abort(400, description='Branch manager must be associated with a branch')
        
        branch_id = current_user.branch_id
        company_id = current_user.company_id
    
    else:
        abort(403, description='Only company owners and branch managers can invite employees')
    
    # Check if user already exists
    existing_user = Users.query.filter(
        (Users.email == email) | (Users.phone_number == phone_number)
    ).first()
    
    if existing_user:
        if existing_user.email == email:
            abort(400, description='An account with this email already exists')
        else:
            abort(400, description='An account with this phone number already exists')
    
    # Check if there's already a pending invitation
    pending_invitation = EmployeeInvitation.query.filter(
        EmployeeInvitation.email == email,
        EmployeeInvitation.status == 'pending',
        EmployeeInvitation.company_id == company_id
    ).first()
    
    if pending_invitation:
        abort(400, description='A pending invitation already exists for this email')
    
    # Create invitation
    invitation = EmployeeInvitation(
        email=email,
        phone_number=phone_number,
        role=role,
        company_id=company_id,
        branch_id=branch_id,
        invited_by=current_user.id
    )
    invitation.generate_invitation_code()
    
    try:
        db.session.add(invitation)
        db.session.commit()
        
        # Send invitation email in background
        company = BusCompanies.query.filter_by(id=company_id).first()
        branch = Branches.query.filter_by(id=branch_id).first()
        
        invitation_data = {
            'full_name': full_name,
            'email': email,
            'role': role,
            'company_name': company.name if company else 'Unknown',
            'branch_name': branch.name if branch else 'Unknown',
            'invitation_code': invitation.invitation_code,
            'invitation_link': f"{current_app.config.get('FRONTEND_URL')}/accept-invitation/{invitation.invitation_code}",
            'expires_at': invitation.expires_at.isoformat()
        }
        
        # Send email in background thread
        thread = threading.Thread(
            target=send_employee_invitation_email,
            args=(invitation_data,)
        )
        thread.start()
        
        return jsonify({
            "message": "Employee invitation sent successfully",
            "invitation": invitation.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to create invitation",
            "details": str(e)
        }), 500


@employees_bp.route('/accept-invitation', methods=['POST'])
def accept_invitation():
    """
    Accept an employee invitation and create account.
    This is a public endpoint (no authentication required).
    
    Request body:
    {
        "invitation_code": "abc123...",
        "password": "SecurePassword123",
        "confirm_password": "SecurePassword123"
    }
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    invitation_code = data.get('invitation_code')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    
    if not all([invitation_code, password, confirm_password]):
        abort(400, description='invitation_code, password, and confirm_password are required')
    
    if password != confirm_password:
        abort(400, description='Passwords do not match')
    
    # Find invitation
    invitation = EmployeeInvitation.query.filter_by(
        invitation_code=invitation_code
    ).first()
    
    if not invitation:
        abort(404, description='Invitation not found')
    
    # Validate invitation
    is_valid, message = invitation.is_valid()
    if not is_valid:
        abort(400, description=message)
    
    # Check if user already exists (double-check)
    existing_user = Users.query.filter(
        (Users.email == invitation.email) | 
        (Users.phone_number == invitation.phone_number)
    ).first()
    
    if existing_user:
        invitation.status = 'expired'
        db.session.commit()
        abort(400, description='An account with this email or phone number already exists')
    
    # Create user account
    user = Users(
        name=data.get('full_name', invitation.email.split('@')[0]),  # Use email prefix if name not provided
        email=invitation.email,
        phone_number=invitation.phone_number,
        role=invitation.role,
        company_id=invitation.company_id,
        branch_id=invitation.branch_id
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        
        # Update invitation status
        invitation.status = 'accepted'
        invitation.accepted_at = datetime.now(timezone.utc)
        
        db.session.commit()
        
        return jsonify({
            "message": "Account created successfully. You can now log in.",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "company_id": user.company_id,
                "branch_id": user.branch_id
            }
        }), 201
    
    except IntegrityError:
        db.session.rollback()
        abort(400, description='Account creation failed. User may already exist.')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to create account",
            "details": str(e)
        }), 500


@employees_bp.route('/invitations', methods=['GET'])
@branch_manager_required
def list_invitations():
    """
    List employee invitations.
    Company owners see all invitations in their company.
    Branch managers see invitations for their branch.
    
    Query parameters:
    - status: Filter by status (pending, accepted, expired, cancelled)
    - branch_id: Filter by branch (company owners only)
    """
    status = request.args.get('status')
    branch_id = request.args.get('branch_id', type=int)
    
    # Build query based on role
    if current_user.role.lower() == 'company_owner':
        query = EmployeeInvitation.query.filter_by(company_id=current_user.company_id)
        if branch_id:
            query = query.filter_by(branch_id=branch_id)
    elif current_user.role.lower() == 'branch_manager':
        query = EmployeeInvitation.query.filter_by(branch_id=current_user.branch_id)
    else:
        abort(403)
    
    if status:
        query = query.filter_by(status=status)
    
    invitations = query.order_by(EmployeeInvitation.created_at.desc()).all()
    
    invitations_data = []
    for invitation in invitations:
        inv_dict = invitation.to_dict()
        
        # Add inviter info
        inviter = Users.query.filter_by(id=invitation.invited_by).first()
        inv_dict['invited_by_name'] = inviter.name if inviter else 'Unknown'
        
        # Add branch info
        branch = Branches.query.filter_by(id=invitation.branch_id).first()
        inv_dict['branch_name'] = branch.name if branch else 'Unknown'
        
        invitations_data.append(inv_dict)
    
    return jsonify({
        "invitations": invitations_data,
        "count": len(invitations_data)
    }), 200


@employees_bp.route('/invitations/<int:invitation_id>/cancel', methods=['DELETE', 'POST'])
@branch_manager_required
def cancel_invitation(invitation_id: int):
    """
    Cancel a pending invitation.
    Company owners can cancel any invitation in their company.
    Branch managers can cancel invitations for their branch.
    """
    invitation = EmployeeInvitation.query.filter_by(id=invitation_id).first()
    if not invitation:
        abort(404, description='Invitation not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if invitation.company_id != current_user.company_id:
            abort(403, description='You can only cancel invitations in your company')
    elif current_user.role.lower() == 'branch_manager':
        if invitation.branch_id != current_user.branch_id:
            abort(403, description='You can only cancel invitations for your branch')
    
    if invitation.status != 'pending':
        abort(400, description=f'Cannot cancel invitation with status: {invitation.status}')
    
    invitation.status = 'cancelled'
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Invitation cancelled successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to cancel invitation",
            "details": str(e)
        }), 500


@employees_bp.route('/list', methods=['GET'])
@login_required
def list_employees():
    """
    List employees based on user role.
    - Admins: See all employees
    - Company owners: See all employees in their company
    - Branch managers: See employees in their branch
    - Other roles: Cannot access
    
    Query parameters:
    - role: Filter by role
    - branch_id: Filter by branch (company owners only)
    """
    if current_user.role.lower() not in ['admin', 'company_owner', 'branch_manager']:
        abort(403, description='You do not have permission to view employees')
    
    role_filter = request.args.get('role')
    branch_id = request.args.get('branch_id', type=int)
    
    # Build query
    if current_user.role.lower() == 'admin':
        query = Users.query.filter(Users.role != 'passenger')
    elif current_user.role.lower() == 'company_owner':
        query = Users.query.filter_by(company_id=current_user.company_id)
        if branch_id:
            query = query.filter_by(branch_id=branch_id)
    else:  # branch_manager
        query = Users.query.filter_by(branch_id=current_user.branch_id)
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    employees = query.order_by(Users.name).all()
    
    employees_data = []
    for employee in employees:
        emp_dict = employee.to_dict()['user']
        
        # Add branch info
        if employee.branch_id:
            branch = Branches.query.filter_by(id=employee.branch_id).first()
            emp_dict['branch_name'] = branch.name if branch else None
        
        # Add company info
        if employee.company_id:
            company = BusCompanies.query.filter_by(id=employee.company_id).first()
            emp_dict['company_name'] = company.name if company else None
        
        # Add assigned bus for conductors
        if employee.role.lower() == 'conductor':
            bus = Buses.query.filter_by(conductor_id=employee.id).first()
            emp_dict['assigned_bus'] = {
                'id': bus.id,
                'bus_number': bus.bus_number,
                'name': bus.name
            } if bus else None
        
        employees_data.append(emp_dict)
    
    return jsonify({
        "employees": employees_data,
        "count": len(employees_data)
    }), 200


@employees_bp.route('/<int:employee_id>', methods=['GET'])
@login_required
def get_employee(employee_id: int):
    """
    Get detailed information about an employee.
    """
    employee = Users.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')
    
    # Authorization check
    if current_user.role.lower() == 'admin':
        pass  # Admins can view anyone
    elif current_user.role.lower() == 'company_owner':
        if employee.company_id != current_user.company_id:
            abort(403, description='You can only view employees in your company')
    elif current_user.role.lower() == 'branch_manager':
        if employee.branch_id != current_user.branch_id:
            abort(403, description='You can only view employees in your branch')
    else:
        if employee.id != current_user.id:
            abort(403, description='You can only view your own information')
    
    emp_data = employee.to_dict()['user']
    
    # Add branch info
    if employee.branch_id:
        branch = Branches.query.filter_by(id=employee.branch_id).first()
        emp_data['branch'] = branch.to_dict() if branch else None
    
    # Add company info
    if employee.company_id:
        company = BusCompanies.query.filter_by(id=employee.company_id).first()
        emp_data['company'] = {
            'id': company.id,
            'name': company.name,
            'status': company.status
        } if company else None
    
    # Add assigned bus for conductors
    if employee.role.lower() == 'conductor':
        bus = Buses.query.filter_by(conductor_id=employee.id).first()
        emp_data['assigned_bus'] = bus.to_dict() if bus else None
    
    # Add managed branch for branch managers
    if employee.role.lower() == 'branch_manager':
        managed_branch = Branches.query.filter_by(manager_id=employee.id).first()
        emp_data['managed_branch'] = managed_branch.to_dict() if managed_branch else None
    
    return jsonify({"employee": emp_data}), 200


@employees_bp.route('/<int:employee_id>/update', methods=['PUT', 'PATCH'])
@branch_manager_required
def update_employee(employee_id: int):
    """
    Update employee information.
    Company owners can update any employee in their company.
    Branch managers can update employees in their branch.
    
    Updatable fields:
    - role (company owner only)
    - branch_id (company owner only)
    - name
    - email
    - phone_number
    """
    employee = Users.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if employee.company_id != current_user.company_id:
            abort(403, description='You can only update employees in your company')
    elif current_user.role.lower() == 'branch_manager':
        if employee.branch_id != current_user.branch_id:
            abort(403, description='You can only update employees in your branch')
    
    # Cannot update company owner accounts
    if employee.role.lower() == 'company_owner':
        abort(403, description='Cannot update company owner accounts through this endpoint')
    
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    # Update basic fields (accessible to branch managers)
    if 'name' in data:
        employee.name = data['name']
    
    if 'email' in data:
        new_email = data['email']
        existing = Users.query.filter(Users.email == new_email, Users.id != employee_id).first()
        if existing:
            abort(400, description='Email already in use by another account')
        employee.email = new_email
    
    if 'phone_number' in data:
        new_phone = data['phone_number']
        existing = Users.query.filter(Users.phone_number == new_phone, Users.id != employee_id).first()
        if existing:
            abort(400, description='Phone number already in use by another account')
        employee.phone_number = new_phone
    
    # Company owner only fields
    if current_user.role.lower() == 'company_owner':
        if 'role' in data:
            new_role = data['role'].lower()
            valid_roles = ['conductor', 'bus_manager', 'schedule_manager', 
                          'accounts_manager', 'branch_manager']
            if new_role not in valid_roles:
                abort(400, description=f'Invalid role. Must be one of: {", ".join(valid_roles)}')
            employee.role = new_role
        
        if 'branch_id' in data:
            new_branch_id = data['branch_id']
            branch = Branches.query.filter_by(id=new_branch_id).first()
            if not branch or branch.company_id != current_user.company_id:
                abort(400, description='Branch not found or does not belong to your company')
            employee.branch_id = new_branch_id
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Employee updated successfully",
            "employee": employee.to_dict()
        }), 200
    except IntegrityError:
        db.session.rollback()
        abort(400, description='Email or phone number already in use')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to update employee",
            "details": str(e)
        }), 500


@employees_bp.route('/<int:employee_id>/remove', methods=['DELETE', 'POST'])
@company_owner_or_admin_required
def remove_employee(employee_id: int):
    """
    Remove an employee from the company.
    Only company owners and admins can remove employees.
    Cannot remove if employee has active assignments.
    """
    employee = Users.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if employee.company_id != current_user.company_id:
            abort(403, description='You can only remove employees from your company')
    
    # Cannot remove company owner
    if employee.role.lower() == 'company_owner':
        abort(403, description='Cannot remove company owner')
    
    # Check for active assignments
    if employee.role.lower() == 'conductor':
        assigned_bus = Buses.query.filter_by(conductor_id=employee_id).first()
        if assigned_bus:
            abort(400, description='Cannot remove conductor with assigned bus. Unassign bus first.')
    
    if employee.role.lower() == 'branch_manager':
        managed_branch = Branches.query.filter_by(manager_id=employee_id).first()
        if managed_branch:
            abort(400, description='Cannot remove branch manager. Assign new manager first.')
    
    # Clear associations
    employee.company_id = None
    employee.branch_id = None
    employee.role = 'passenger'  # Demote to passenger
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Employee removed from company successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to remove employee",
            "details": str(e)
        }), 500


@employees_bp.route('/<int:employee_id>/assign-bus', methods=['POST', 'PUT'])
@branch_manager_required
def assign_bus_to_conductor(employee_id: int):
    """
    Assign a bus to a conductor.
    Company owners can assign buses in their company.
    Branch managers can assign buses in their branch.
    
    Request body:
    {
        "bus_id": 5
    }
    """
    employee = Users.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')
    
    if employee.role.lower() != 'conductor':
        abort(400, description='Employee must be a conductor')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if employee.company_id != current_user.company_id:
            abort(403)
    elif current_user.role.lower() == 'branch_manager':
        if employee.branch_id != current_user.branch_id:
            abort(403)
    
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    bus_id = data.get('bus_id')
    if not bus_id:
        abort(400, description='bus_id is required')
    
    bus = Buses.query.filter_by(id=bus_id).first()
    if not bus:
        abort(404, description='Bus not found')
    
    # Verify bus belongs to same company/branch
    if current_user.role.lower() == 'company_owner':
        if bus.company_id != current_user.company_id:
            abort(403, description='Bus must belong to your company')
    else:
        if bus.branch_id != current_user.branch_id:
            abort(403, description='Bus must belong to your branch')
    
    # Check if bus already has a conductor
    if bus.conductor_id and bus.conductor_id != employee_id:
        current_conductor = Users.query.filter_by(id=bus.conductor_id).first()
        abort(400, description=f'Bus already assigned to {current_conductor.name}. Unassign first.')
    
    # Check if conductor already has a bus
    current_bus = Buses.query.filter_by(conductor_id=employee_id).first()
    if current_bus and current_bus.id != bus_id:
        abort(400, description=f'Conductor already assigned to bus {current_bus.bus_number}')
    
    bus.conductor_id = employee_id
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Bus assigned to conductor successfully",
            "bus": bus.to_dict(),
            "conductor": employee.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to assign bus",
            "details": str(e)
        }), 500


@employees_bp.route('/<int:employee_id>/unassign-bus', methods=['POST', 'DELETE'])
@branch_manager_required
def unassign_bus_from_conductor(employee_id: int):
    """
    Unassign a bus from a conductor.
    """
    employee = Users.query.filter_by(id=employee_id).first()
    if not employee:
        abort(404, description='Employee not found')
    
    if employee.role.lower() != 'conductor':
        abort(400, description='Employee must be a conductor')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if employee.company_id != current_user.company_id:
            abort(403)
    elif current_user.role.lower() == 'branch_manager':
        if employee.branch_id != current_user.branch_id:
            abort(403)
    
    bus = Buses.query.filter_by(conductor_id=employee_id).first()
    if not bus:
        abort(400, description='Conductor does not have an assigned bus')
    
    bus.conductor_id = None
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Bus unassigned from conductor successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to unassign bus",
            "details": str(e)
        }), 500