from app import db
from app.models import Branches, BusCompanies, Users, Buses
from flask import Blueprint, request, jsonify, abort
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from .auth import admin_required, company_owner_or_admin_required, branch_manager_required


branches_bp = Blueprint('branches', __name__)


@branches_bp.route('/create', methods=['POST'])
@company_owner_or_admin_required
def create_branch():
    """
    Create a new branch for a company.
    Company owners can create branches for their company.
    Admins can create branches for any company.
    
    Request body:
    {
        "name": "Blantyre Branch",
        "company_id": 1,  // Optional for company owners, required for admins
        "manager_id": 5   // Optional - can assign manager later
    }
    """
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    branch_name = data.get('name')
    company_id = data.get('company_id')
    manager_id = data.get('manager_id')
    
    if not branch_name:
        abort(400, description='Branch name is required')
    
    # Determine company_id based on user role
    if current_user.role.lower() == 'company_owner':
        if not current_user.company_id:
            abort(400, description='Company owner must be associated with a company')
        company_id = current_user.company_id
    elif current_user.role.lower() == 'admin':
        if not company_id:
            abort(400, description='company_id is required for admin users')
    
    # Verify company exists and is registered
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')
    
    if company.status != 'registered':
        abort(400, description='Only registered companies can create branches')
    
    # If manager_id is provided, verify the manager
    if manager_id:
        manager = Users.query.filter_by(id=manager_id).first()
        if not manager:
            abort(404, description='Manager not found')
        
        # Verify manager belongs to the same company
        if manager.company_id != company_id:
            abort(400, description='Manager must belong to the same company')
        
        # Verify manager has appropriate role
        if manager.role.lower() not in ['branch_manager', 'company_owner']:
            abort(400, description='Manager must have branch_manager or company_owner role')
    
    # Check for duplicate branch name within the same company
    existing_branch = Branches.query.filter_by(
        name=branch_name,
        company_id=company_id
    ).first()
    
    if existing_branch:
        abort(400, description=f'Branch "{branch_name}" already exists in this company')
    
    # Create the branch
    branch = Branches(
        name=branch_name,
        company_id=company_id,
        manager_id=manager_id
    )
    
    try:
        db.session.add(branch)
        db.session.commit()
        
        # If manager was assigned, update their branch_id
        if manager_id:
            manager = Users.query.filter_by(id=manager_id).first()
            if manager and not manager.branch_id:
                manager.branch_id = branch.id
                db.session.commit()
        
        return jsonify({
            "message": "Branch created successfully",
            "branch": branch.to_dict()
        }), 201
    
    except IntegrityError:
        db.session.rollback()
        abort(400, description='Branch with this name already exists in the company')
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to create branch",
            "details": str(e)
        }), 500


@branches_bp.route('/list', methods=['GET'])
@login_required
def list_branches():
    """
    List branches based on user role.
    - Admins: See all branches
    - Company owners: See all branches in their company
    - Branch managers and employees: See only their branch
    - Passengers: Not allowed
    
    Query parameters:
    - company_id: Filter by company (admin only)
    """
    if current_user.role.lower() == 'passenger':
        abort(403, description='Passengers cannot access branch information')
    
    company_id = request.args.get('company_id', type=int)
    
    # Build query based on role
    if current_user.role.lower() == 'admin':
        query = Branches.query
        if company_id:
            query = query.filter_by(company_id=company_id)
    
    elif current_user.role.lower() == 'company_owner':
        if not current_user.company_id:
            abort(400, description='User not associated with any company')
        query = Branches.query.filter_by(company_id=current_user.company_id)
    
    else:
        # Branch managers and other employees
        if not current_user.branch_id:
            abort(400, description='User not associated with any branch')
        query = Branches.query.filter_by(id=current_user.branch_id)
    
    branches = query.all()
    
    # Enhance branch data with additional info
    branches_data = []
    for branch in branches:
        branch_dict = branch.to_dict()
        
        # Add manager name
        if branch.manager_id:
            manager = Users.query.filter_by(id=branch.manager_id).first()
            branch_dict['manager_name'] = manager.name if manager else None
        
        # Add employee count
        employee_count = Users.query.filter_by(branch_id=branch.id).count()
        branch_dict['employee_count'] = employee_count
        
        # Add bus count
        bus_count = Buses.query.filter_by(branch_id=branch.id).count()
        branch_dict['bus_count'] = bus_count
        
        branches_data.append(branch_dict)
    
    return jsonify({
        "branches": branches_data,
        "count": len(branches_data)
    }), 200


@branches_bp.route('/<int:branch_id>', methods=['GET'])
@login_required
def get_branch(branch_id: int):
    """
    Get detailed information about a specific branch.
    Authorization: Admin, company owner, or employees of the branch.
    """
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')
    
    # Authorization check
    if current_user.role.lower() == 'passenger':
        abort(403, description='Passengers cannot access branch information')
    
    if current_user.role.lower() not in ['admin']:
        # Check if user belongs to the same company
        if current_user.company_id != branch.company_id:
            abort(403, description='You can only view branches in your company')
        
        # For non-owners, check if they belong to this branch
        if current_user.role.lower() != 'company_owner':
            if current_user.branch_id != branch_id:
                abort(403, description='You can only view your own branch')
    
    # Build detailed response
    branch_data = branch.to_dict()
    
    # Add company info
    company = BusCompanies.query.filter_by(id=branch.company_id).first()
    branch_data['company'] = {
        'id': company.id,
        'name': company.name
    } if company else None
    
    # Add manager info
    if branch.manager_id:
        manager = Users.query.filter_by(id=branch.manager_id).first()
        branch_data['manager'] = {
            'id': manager.id,
            'name': manager.name,
            'email': manager.email,
            'phone_number': manager.phone_number
        } if manager else None
    
    # Add statistics
    branch_data['statistics'] = {
        'total_employees': Users.query.filter_by(branch_id=branch_id).count(),
        'total_buses': Buses.query.filter_by(branch_id=branch_id).count(),
        'conductors': Users.query.filter_by(branch_id=branch_id, role='conductor').count(),
        'managers': Users.query.filter_by(branch_id=branch_id, role='branch_manager').count()
    }
    
    return jsonify({"branch": branch_data}), 200


@branches_bp.route('/<int:branch_id>/update', methods=['PUT', 'PATCH'])
@branch_manager_required
def update_branch(branch_id: int):
    """
    Update branch information.
    Company owners can update any branch in their company.
    Branch managers can update their own branch.
    """
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if current_user.company_id != branch.company_id:
            abort(403, description='You can only update branches in your company')
    elif current_user.role.lower() == 'branch_manager':
        if current_user.branch_id != branch_id:
            abort(403, description='You can only update your own branch')
    
    data = request.get_json()
    if not data:
        abort(400, description='Data not provided')
    
    # Update allowed fields
    if 'name' in data:
        new_name = data['name']
        # Check for duplicate names in the same company
        existing = Branches.query.filter(
            Branches.name == new_name,
            Branches.company_id == branch.company_id,
            Branches.id != branch_id
        ).first()
        
        if existing:
            abort(400, description='Branch with this name already exists in the company')
        
        branch.name = new_name
    
    # Only company owners can change branch manager
    if 'manager_id' in data and current_user.role.lower() == 'company_owner':
        new_manager_id = data['manager_id']
        
        if new_manager_id:
            manager = Users.query.filter_by(id=new_manager_id).first()
            if not manager:
                abort(404, description='Manager not found')
            
            if manager.company_id != branch.company_id:
                abort(400, description='Manager must belong to the same company')
            
            if manager.role.lower() not in ['branch_manager', 'company_owner']:
                abort(400, description='User must have branch_manager or company_owner role')
            
            # Update old manager's branch_id if they were managing only this branch
            if branch.manager_id:
                old_manager = Users.query.filter_by(id=branch.manager_id).first()
                if old_manager and old_manager.branch_id == branch_id:
                    old_manager.branch_id = None
            
            branch.manager_id = new_manager_id
            
            # Update new manager's branch_id
            manager.branch_id = branch_id
    
    try:
        db.session.commit()
        return jsonify({
            "message": "Branch updated successfully",
            "branch": branch.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to update branch",
            "details": str(e)
        }), 500


@branches_bp.route('/<int:branch_id>/delete', methods=['DELETE'])
@company_owner_or_admin_required
def delete_branch(branch_id: int):
    """
    Delete/deactivate a branch.
    Only company owners and admins can delete branches.
    Cannot delete a branch that has buses or employees assigned to it.
    """
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if current_user.company_id != branch.company_id:
            abort(403, description='You can only delete branches in your company')
    
    # Check if branch has buses
    bus_count = Buses.query.filter_by(branch_id=branch_id).count()
    if bus_count > 0:
        abort(400, description=f'Cannot delete branch with {bus_count} buses assigned. Reassign or remove buses first.')
    
    # Check if branch has employees (excluding the manager)
    employee_count = Users.query.filter(
        Users.branch_id == branch_id,
        Users.id != branch.manager_id
    ).count()
    
    if employee_count > 0:
        abort(400, description=f'Cannot delete branch with {employee_count} employees assigned. Reassign or remove employees first.')
    
    # Clear manager's branch_id
    if branch.manager_id:
        manager = Users.query.filter_by(id=branch.manager_id).first()
        if manager:
            manager.branch_id = None
    
    try:
        db.session.delete(branch)
        db.session.commit()
        return jsonify({
            "message": "Branch deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to delete branch",
            "details": str(e)
        }), 500


@branches_bp.route('/<int:branch_id>/employees', methods=['GET'])
@branch_manager_required
def get_branch_employees(branch_id: int):
    """
    Get all employees in a branch.
    Company owners can view employees in any branch of their company.
    Branch managers can view employees in their branch.
    """
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if current_user.company_id != branch.company_id:
            abort(403, description='You can only view branches in your company')
    elif current_user.role.lower() == 'branch_manager':
        if current_user.branch_id != branch_id:
            abort(403, description='You can only view employees in your branch')
    
    # Get employees
    employees = Users.query.filter_by(branch_id=branch_id).all()
    
    employees_data = []
    for employee in employees:
        employee_dict = employee.to_dict()['user']
        
        # Add assigned bus info for conductors
        if employee.role.lower() == 'conductor':
            assigned_bus = Buses.query.filter_by(conductor_id=employee.id).first()
            employee_dict['assigned_bus'] = {
                'id': assigned_bus.id,
                'bus_number': assigned_bus.bus_number
            } if assigned_bus else None
        
        employees_data.append(employee_dict)
    
    return jsonify({
        "branch": {
            "id": branch.id,
            "name": branch.name
        },
        "employees": employees_data,
        "count": len(employees_data)
    }), 200


@branches_bp.route('/<int:branch_id>/buses', methods=['GET'])
@login_required
def get_branch_buses(branch_id: int):
    """
    Get all buses in a branch.
    Accessible by company owners, branch managers, and employees of the branch.
    """
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')
    
    # Authorization check
    if current_user.role.lower() == 'passenger':
        abort(403, description='Passengers cannot access branch bus information')
    
    if current_user.role.lower() not in ['admin']:
        if current_user.company_id != branch.company_id:
            abort(403, description='You can only view branches in your company')
        
        if current_user.role.lower() not in ['company_owner', 'branch_manager']:
            if current_user.branch_id != branch_id:
                abort(403, description='You can only view buses in your branch')
    
    # Get buses
    buses = Buses.query.filter_by(branch_id=branch_id).all()
    
    buses_data = []
    for bus in buses:
        bus_dict = bus.to_dict()
        
        # Add conductor info
        if bus.conductor_id:
            conductor = Users.query.filter_by(id=bus.conductor_id).first()
            bus_dict['conductor'] = {
                'id': conductor.id,
                'name': conductor.name,
                'phone_number': conductor.phone_number
            } if conductor else None
        
        buses_data.append(bus_dict)
    
    return jsonify({
        "branch": {
            "id": branch.id,
            "name": branch.name
        },
        "buses": buses_data,
        "count": len(buses_data)
    }), 200


@branches_bp.route('/<int:branch_id>/statistics', methods=['GET'])
@branch_manager_required
def get_branch_statistics(branch_id: int):
    """
    Get detailed statistics for a branch.
    Includes employee counts by role, bus counts, and recent activity.
    """
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')
    
    # Authorization check
    if current_user.role.lower() == 'company_owner':
        if current_user.company_id != branch.company_id:
            abort(403)
    elif current_user.role.lower() == 'branch_manager':
        if current_user.branch_id != branch_id:
            abort(403)
    
    # Gather statistics
    stats = {
        "branch_info": branch.to_dict(),
        "employees": {
            "total": Users.query.filter_by(branch_id=branch_id).count(),
            "by_role": {
                "branch_manager": Users.query.filter_by(branch_id=branch_id, role='branch_manager').count(),
                "accounts_manager": Users.query.filter_by(branch_id=branch_id, role='accounts_manager').count(),
                "bus_manager": Users.query.filter_by(branch_id=branch_id, role='bus_manager').count(),
                "schedule_manager": Users.query.filter_by(branch_id=branch_id, role='schedule_manager').count(),
                "conductor": Users.query.filter_by(branch_id=branch_id, role='conductor').count()
            }
        },
        "buses": {
            "total": Buses.query.filter_by(branch_id=branch_id).count(),
            "with_conductor": Buses.query.filter(
                Buses.branch_id == branch_id,
                Buses.conductor_id.isnot(None)
            ).count(),
            "without_conductor": Buses.query.filter(
                Buses.branch_id == branch_id,
                Buses.conductor_id.is_(None)
            ).count()
        }
    }
    
    return jsonify(stats), 200