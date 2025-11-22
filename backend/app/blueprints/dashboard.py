from app import db
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone, timedelta
from flask_login import current_user, login_required
from flask import Blueprint, request, jsonify, abort, current_app
from .auth import admin_required, company_owner_or_admin_required, branch_manager_required, passenger_required
from app.models import Users, BusCompanies, Branches, Buses, Routes, Schedules, Bookings, Transactions, Payouts


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/admin', methods=['GET'])
@admin_required
def admin_dashboard():
    """
    Admin dashboard with system-wide statistics.
    Shows overall platform metrics.

    Query parameters:
    - period: today, week, month, year, all (default: all)
    """
    period = request.args.get('period', 'all')

    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = None

    # Build date filter
    date_filter = Bookings.created_at >= start_date if start_date else True
    transaction_date_filter = Transactions.created_at >= start_date if start_date else True

    # Total statistics
    total_stats = {
        'companies': {
            'total': BusCompanies.query.count(),
            'registered': BusCompanies.query.filter_by(status='registered').count(),
            'pending': BusCompanies.query.filter_by(status='pending').count(),
            'rejected': BusCompanies.query.filter_by(status='rejected').count()
        },
        'users': {
            'total': Users.query.count(),
            'passengers': Users.query.filter_by(role='passenger').count(),
            'company_owners': Users.query.filter_by(role='company_owner').count(),
            'employees': Users.query.filter(Users.role != 'passenger').count()
        },
        'branches': Branches.query.count(),
        'buses': Buses.query.count(),
        'routes': Routes.query.count(),
        'schedules': {
            'total': Schedules.query.count(),
            'upcoming': Schedules.query.filter(Schedules.departure_time > now).count(),
            'past': Schedules.query.filter(Schedules.departure_time <= now).count()
        }
    }

    # Booking statistics
    booking_query = Bookings.query.filter(date_filter)
    booking_stats = {
        'total': booking_query.count(),
        'confirmed': booking_query.filter_by(status='confirmed').count(),
        'pending': booking_query.filter_by(status='pending').count(),
        'cancelled': booking_query.filter_by(status='cancelled').count(),
        'boarded': booking_query.filter_by(status='boarded').count()
    }

    # Financial statistics
    platform_fee = current_app.config.get('PLATFORM_FEE', 3000)

    # Total revenue (completed transactions)
    total_revenue = db.session.query(func.sum(Transactions.amount)).filter(
        Transactions.status == 'completed',
        transaction_date_filter
    ).scalar() or 0

    # Platform earnings (fees from bookings)
    confirmed_bookings = booking_query.filter_by(status='confirmed').count()
    boarded_bookings = booking_query.filter_by(status='boarded').count()
    platform_earnings = (confirmed_bookings + boarded_bookings) * platform_fee

    # Total paid out to companies
    total_payouts = db.session.query(func.sum(Payouts.amount)).filter(
        Payouts.status == 'completed'
    ).scalar() or 0

    # Pending payouts
    pending_payouts = db.session.query(func.sum(Payouts.amount)).filter(
        Payouts.status == 'pending'
    ).scalar() or 0

    financial_stats = {
        'total_revenue': total_revenue,
        'platform_earnings': platform_earnings,
        'total_payouts': total_payouts,
        'pending_payouts': pending_payouts,
        'company_balance': total_revenue - platform_earnings - total_payouts
    }

    # Pending company registrations
    pending_company_registrations = BusCompanies.query.filter_by(status='pending').all()

    unapproved_companies = [bus_company.to_dict() for bus_company in pending_company_registrations]

    # Top performing companies (by bookings)
    top_companies = db.session.query(
        BusCompanies.id,
        BusCompanies.name,
        func.count(Bookings.id).label('booking_count'),
        func.sum(Schedules.price).label('total_revenue')
    ).join(
        Buses, BusCompanies.id == Buses.company_id
    ).join(
        Schedules, Buses.id == Schedules.bus_id
    ).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Bookings.status.in_(['confirmed', 'boarded']),
        date_filter
    ).group_by(
        BusCompanies.id, BusCompanies.name
    ).order_by(
        func.count(Bookings.id).desc()
    ).limit(10).all()

    top_companies_data = [{
        'company_id': comp.id,
        'company_name': comp.name,
        'booking_count': comp.booking_count,
        'total_revenue': float(comp.total_revenue) if comp.total_revenue else 0
    } for comp in top_companies]

    # Most popular routes
    popular_routes = db.session.query(
        Routes.id,
        Routes.origin,
        Routes.destination,
        func.count(Bookings.id).label('booking_count')
    ).join(
        Schedules, Routes.id == Schedules.route_id
    ).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Bookings.status.in_(['confirmed', 'boarded']),
        date_filter
    ).group_by(
        Routes.id, Routes.origin, Routes.destination
    ).order_by(
        func.count(Bookings.id).desc()
    ).limit(10).all()

    popular_routes_data = [{
        'route_id': route.id,
        'origin': route.origin,
        'destination': route.destination,
        'booking_count': route.booking_count
    } for route in popular_routes]

    return jsonify({
        'period': period,
        'total_stats': total_stats,
        'bookings': booking_stats,
        'financial': financial_stats,
        'top_companies': top_companies_data,
        'popular_routes': popular_routes_data,
        'unapproved_companies': unapproved_companies
    }), 200


@dashboard_bp.route('/company', methods=['GET'])
@company_owner_or_admin_required
def company_dashboard():
    """
    Company dashboard with company-specific metrics.
    Company owners see their company data.
    Admins can view any company (requires company_id parameter).

    Query parameters:
    - company_id: Company ID (required for admins)
    - period: today, week, month, year, all (default: month)
    """
    # Determine company_id
    if current_user.role.lower().strip() == 'company_owner':
        if not current_user.company_id:
            abort(400, description='Company owner must be associated with a company')
        company_id = current_user.company_id
    else:  # admin
        company_id = request.args.get('company_id', type=int)
        if not company_id:
            abort(400, description='company_id parameter required for admins')

    # Verify company exists
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')

    period = request.args.get('period', 'month')

    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = None

    date_filter = Bookings.created_at >= start_date if start_date else True

    # Company overview
    company_overview = {
        'id': company.id,
        'name': company.name,
        'status': company.status,
        'balance': company.balance,
        'total_branches': Branches.query.filter_by(company_id=company_id).count(),
        'total_buses': Buses.query.filter_by(company_id=company_id).count(),
        'total_employees': Users.query.filter_by(company_id=company_id).count()
    }

    # Employee breakdown
    employee_stats = {
        'company_owners': Users.query.filter_by(company_id=company_id, role='company_owner').count(),
        'branch_managers': Users.query.filter_by(company_id=company_id, role='branch_manager').count(),
        'accounts_managers': Users.query.filter_by(company_id=company_id, role='accounts_manager').count(),
        'bus_managers': Users.query.filter_by(company_id=company_id, role='bus_manager').count(),
        'schedule_managers': Users.query.filter_by(company_id=company_id, role='schedule_manager').count(),
        'conductors': Users.query.filter_by(company_id=company_id, role='conductor').count()
    }

    # Booking statistics
    booking_query = db.session.query(Bookings).join(
        Schedules, Bookings.schedule_id == Schedules.id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).filter(
        Buses.company_id == company_id,
        date_filter
    )

    booking_stats = {
        'total': booking_query.count(),
        'confirmed': booking_query.filter(Bookings.status == 'confirmed').count(),
        'pending': booking_query.filter(Bookings.status == 'pending').count(),
        'cancelled': booking_query.filter(Bookings.status == 'cancelled').count(),
        'boarded': booking_query.filter(Bookings.status == 'boarded').count()
    }

    # Revenue statistics
    platform_fee = current_app.config.get('PLATFORM_FEE', 3000)

    total_revenue = db.session.query(func.sum(Schedules.price)).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).filter(
        Buses.company_id == company_id,
        Bookings.status.in_(['confirmed', 'boarded']),
        date_filter
    ).scalar() or 0

    confirmed_bookings = booking_query.filter(
        Bookings.status.in_(['confirmed', 'boarded'])
    ).count()

    platform_fees = confirmed_bookings * platform_fee
    net_revenue = total_revenue - platform_fees

    revenue_stats = {
        'gross_revenue': total_revenue,
        'platform_fees': platform_fees,
        'net_revenue': net_revenue,
        'current_balance': company.balance
    }

    # Payout statistics
    payout_stats = {
        'total_requested': db.session.query(func.sum(Payouts.amount)).filter(
            Payouts.company_id == company_id
        ).scalar() or 0,
        'pending': db.session.query(func.sum(Payouts.amount)).filter(
            Payouts.company_id == company_id,
            Payouts.status == 'pending'
        ).scalar() or 0,
        'completed': db.session.query(func.sum(Payouts.amount)).filter(
            Payouts.company_id == company_id,
            Payouts.status == 'completed'
        ).scalar() or 0,
        'recent_payouts': Payouts.query.filter_by(company_id=company_id).order_by(
            Payouts.requested_at.desc()
        ).limit(5).all()
    }

    # Branch performance
    branch_performance = db.session.query(
        Branches.id,
        Branches.name,
        func.count(Bookings.id).label('booking_count'),
        func.sum(Schedules.price).label('revenue')
    ).join(
        Buses, Branches.id == Buses.branch_id
    ).join(
        Schedules, Buses.id == Schedules.bus_id
    ).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Branches.company_id == company_id,
        Bookings.status.in_(['confirmed', 'boarded']),
        date_filter
    ).group_by(
        Branches.id, Branches.name
    ).order_by(
        func.count(Bookings.id).desc()
    ).all()

    branch_performance_data = [{
        'branch_id': branch.id,
        'branch_name': branch.name,
        'booking_count': branch.booking_count,
        'revenue': float(branch.revenue) if branch.revenue else 0
    } for branch in branch_performance]

    # Most active routes for this company
    company_routes = db.session.query(
        Routes.id,
        Routes.origin,
        Routes.destination,
        func.count(Bookings.id).label('booking_count')
    ).join(
        Schedules, Routes.id == Schedules.route_id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Buses.company_id == company_id,
        Bookings.status.in_(['confirmed', 'boarded']),
        date_filter
    ).group_by(
        Routes.id, Routes.origin, Routes.destination
    ).order_by(
        func.count(Bookings.id).desc()
    ).limit(10).all()

    routes_data = [{
        'route_id': route.id,
        'origin': route.origin,
        'destination': route.destination,
        'booking_count': route.booking_count
    } for route in company_routes]

    return jsonify({
        'period': period,
        'company': company_overview,
        'employees': employee_stats,
        'bookings': booking_stats,
        'revenue': revenue_stats,
        'payouts': {
            'total_requested': payout_stats['total_requested'],
            'pending': payout_stats['pending'],
            'completed': payout_stats['completed'],
            'recent': [p.to_dict() for p in payout_stats['recent_payouts']]
        },
        'branch_performance': branch_performance_data,
        'popular_routes': routes_data
    }), 200


@dashboard_bp.route('/branch/<int:branch_id>', methods=['GET'])
@branch_manager_required
def branch_dashboard(branch_id: int):
    """
    Branch-specific dashboard with metrics.
    Branch managers can view their branch.
    Company owners can view any branch in their company.

    Query parameters:
    - period: today, week, month, year, all (default: month)
    """
    branch = Branches.query.filter_by(id=branch_id).first()
    if not branch:
        abort(404, description='Branch not found')

    # Authorization check
    if current_user.role.lower().strip() == 'company_owner':
        if branch.company_id != current_user.company_id:
            abort(403, description='You can only view branches in your company')
    elif current_user.role.lower().strip() == 'branch_manager':
        if current_user.branch_id != branch_id:
            abort(403, description='You can only view your own branch')

    period = request.args.get('period', 'month')

    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = None

    date_filter = Bookings.created_at >= start_date if start_date else True

    # Branch overview
    company = BusCompanies.query.filter_by(id=branch.company_id).first()
    branch_overview = {
        'id': branch.id,
        'name': branch.name,
        'company': {
            'id': company.id,
            'name': company.name
        } if company else None,
        'total_buses': Buses.query.filter_by(branch_id=branch_id).count(),
        'total_employees': Users.query.filter_by(branch_id=branch_id).count()
    }

    # Employee breakdown
    employee_stats = {
        'branch_manager': Users.query.filter_by(branch_id=branch_id, role='branch_manager').count(),
        'accounts_managers': Users.query.filter_by(branch_id=branch_id, role='accounts_manager').count(),
        'bus_managers': Users.query.filter_by(branch_id=branch_id, role='bus_manager').count(),
        'schedule_managers': Users.query.filter_by(branch_id=branch_id, role='schedule_manager').count(),
        'conductors': Users.query.filter_by(branch_id=branch_id, role='conductor').count()
    }

    # Bus statistics
    buses = Buses.query.filter_by(branch_id=branch_id).all()
    bus_stats = {
        'total': len(buses),
        'with_conductor': sum(1 for bus in buses if bus.conductor_id),
        'without_conductor': sum(1 for bus in buses if not bus.conductor_id),
        'total_capacity': sum(bus.seating_capacity for bus in buses)
    }

    # Booking statistics
    booking_query = db.session.query(Bookings).join(
        Schedules, Bookings.schedule_id == Schedules.id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).filter(
        Buses.branch_id == branch_id,
        date_filter
    )

    booking_stats = {
        'total': booking_query.count(),
        'confirmed': booking_query.filter(Bookings.status == 'confirmed').count(),
        'pending': booking_query.filter(Bookings.status == 'pending').count(),
        'cancelled': booking_query.filter(Bookings.status == 'cancelled').count(),
        'boarded': booking_query.filter(Bookings.status == 'boarded').count()
    }

    # Revenue statistics
    platform_fee = current_app.config.get('PLATFORM_FEE', 3000)

    total_revenue = db.session.query(func.sum(Schedules.price)).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).filter(
        Buses.branch_id == branch_id,
        Bookings.status.in_(['confirmed', 'boarded']),
        date_filter
    ).scalar() or 0

    confirmed_bookings = booking_query.filter(
        Bookings.status.in_(['confirmed', 'boarded'])
    ).count()

    platform_fees = confirmed_bookings * platform_fee
    net_revenue = total_revenue - platform_fees

    revenue_stats = {
        'gross_revenue': total_revenue,
        'platform_fees': platform_fees,
        'net_revenue': net_revenue
    }

    # Top performing buses
    bus_performance = db.session.query(
        Buses.id,
        Buses.bus_number,
        Buses.name,
        func.count(Bookings.id).label('booking_count'),
        func.sum(Schedules.price).label('revenue')
    ).join(
        Schedules, Buses.id == Schedules.bus_id
    ).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Buses.branch_id == branch_id,
        Bookings.status.in_(['confirmed', 'boarded']),
        date_filter
    ).group_by(
        Buses.id, Buses.bus_number, Buses.name
    ).order_by(
        func.count(Bookings.id).desc()
    ).limit(10).all()

    bus_performance_data = [{
        'bus_id': bus.id,
        'bus_number': bus.bus_number,
        'bus_name': bus.name,
        'booking_count': bus.booking_count,
        'revenue': float(bus.revenue) if bus.revenue else 0
    } for bus in bus_performance]

    # Conductor performance
    conductor_performance = db.session.query(
        Users.id,
        Users.name,
        func.count(Bookings.id).label('tickets_scanned')
    ).join(
        Buses, Users.id == Buses.conductor_id
    ).join(
        Schedules, Buses.id == Schedules.bus_id
    ).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Buses.branch_id == branch_id,
        Bookings.status == 'boarded',
        date_filter
    ).group_by(
        Users.id, Users.name
    ).order_by(
        func.count(Bookings.id).desc()
    ).limit(10).all()

    conductor_performance_data = [{
        'conductor_id': conductor.id,
        'conductor_name': conductor.name,
        'tickets_scanned': conductor.tickets_scanned
    } for conductor in conductor_performance]

    return jsonify({
        'period': period,
        'branch': branch_overview,
        'employees': employee_stats,
        'buses': bus_stats,
        'bookings': booking_stats,
        'revenue': revenue_stats,
        'top_buses': bus_performance_data,
        'conductor_performance': conductor_performance_data
    }), 200


@dashboard_bp.route('/conductor/<int:conductor_id>', methods=['GET'])
@login_required
def conductor_dashboard(conductor_id: int):
    """
    Conductor-specific dashboard showing their performance.
    Conductors can view their own stats.
    Branch managers and company owners can view conductors in their scope.

    Query parameters:
    - period: today, week, month, year, all (default: month)
    """
    if current_user.role.lower().strip() not in ['company_owner', 'conductor', 'branch manager']:
        abort(403, description="Role denied")

    conductor = Users.query.filter_by(id=conductor_id).first()
    if not conductor:
        abort(404, description='Conductor not found')

    # Authorization check
    if current_user.role.lower().strip() == 'conductor':
        if current_user.id != conductor_id:
            abort(403, description='You can only view your own dashboard')
    elif current_user.role.lower().strip() == 'company_owner':
        if conductor.company_id != current_user.company_id:
            abort(403, description='Conductor must be in your company')
    elif current_user.role.lower().strip() == 'branch_manager':
        if conductor.branch_id != current_user.branch_id:
            abort(403, description='Conductor must be in your branch')

    period = request.args.get('period', 'month')

    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = None

    date_filter = Bookings.boarded_at >= start_date if start_date else True

    # Conductor overview
    assigned_bus = Buses.query.filter_by(conductor_id=conductor_id).first()
    branch = Branches.query.filter_by(id=conductor.branch_id).first()
    company = BusCompanies.query.filter_by(id=conductor.company_id).first()

    conductor_overview = {
        'id': conductor.id,
        'name': conductor.name,
        'email': conductor.email,
        'phone_number': conductor.phone_number,
        'assigned_bus': {
            'id': assigned_bus.id,
            'bus_number': assigned_bus.bus_number,
            'name': assigned_bus.name,
            'capacity': assigned_bus.seating_capacity
        } if assigned_bus else None,
        'branch': {
            'id': branch.id,
            'name': branch.name
        } if branch else None,
        'company': {
            'id': company.id,
            'name': company.name
        } if company else None
    }

    # Performance statistics
    if assigned_bus:
        tickets_scanned = db.session.query(func.count(Bookings.id)).join(
            Schedules, Bookings.schedule_id == Schedules.id
        ).filter(
            Schedules.bus_id == assigned_bus.id,
            Bookings.status == 'boarded',
            date_filter
        ).scalar() or 0

        total_trips = db.session.query(func.count(Schedules.id)).filter(
            Schedules.bus_id == assigned_bus.id,
            Schedules.departure_time >= (start_date if start_date else datetime.min),
            Schedules.departure_time <= now
        ).scalar() or 0

        # Revenue generated
        revenue_generated = db.session.query(func.sum(Schedules.price)).join(
            Bookings, Schedules.id == Bookings.schedule_id
        ).filter(
            Schedules.bus_id == assigned_bus.id,
            Bookings.status == 'boarded',
            date_filter
        ).scalar() or 0
    else:
        tickets_scanned = 0
        total_trips = 0
        revenue_generated = 0

    performance_stats = {
        'tickets_scanned': tickets_scanned,
        'total_trips': total_trips,
        'revenue_generated': revenue_generated,
        'average_per_trip': revenue_generated / total_trips if total_trips > 0 else 0
    }

    # Recent scanned tickets
    if assigned_bus:
        recent_scans = db.session.query(Bookings).join(
            Schedules, Bookings.schedule_id == Schedules.id
        ).join(
            Routes, Schedules.route_id == Routes.id
        ).filter(
            Schedules.bus_id == assigned_bus.id,
            Bookings.status == 'boarded'
        ).order_by(
            Bookings.boarded_at.desc()
        ).limit(10).all()

        recent_scans_data = [{
            'booking_id': booking.id,
            'qr_reference': booking.qr_code_reference,
            'boarded_at': booking.boarded_at.isoformat() if booking.boarded_at else None,
            'passenger_name': booking.user.name,
            'route': f"{booking.schedule.route.origin} to {booking.schedule.route.destination}"
        } for booking in recent_scans]
    else:
        recent_scans_data = []

    return jsonify({
        'period': period,
        'conductor': conductor_overview,
        'performance': performance_stats,
        'recent_scans': recent_scans_data
    }), 200


@dashboard_bp.route('/passenger', methods=['GET'])
@passenger_required
def passenger_dashboard():
    """
    Passenger dashboard showing their booking history and statistics.
    """

    # Booking statistics
    total_bookings = Bookings.query.filter_by(user_id=current_user.id).count()
    confirmed_bookings = Bookings.query.filter_by(
        user_id=current_user.id,
        status='confirmed'
    ).count()
    completed_bookings = Bookings.query.filter_by(
        user_id=current_user.id,
        status='boarded'
    ).count()
    cancelled_bookings = Bookings.query.filter_by(
        user_id=current_user.id,
        status='cancelled'
    ).count()

    booking_stats = {
        'total': total_bookings,
        'confirmed': confirmed_bookings,
        'completed': completed_bookings,
        'cancelled': cancelled_bookings,
        'pending': Bookings.query.filter_by(
            user_id=current_user.id,
            status='pending'
        ).count()
    }

    # Spending statistics
    total_spent = db.session.query(func.sum(Schedules.price)).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Bookings.user_id == current_user.id,
        Bookings.status.in_(['confirmed', 'boarded'])
    ).scalar() or 0

    spending_stats = {
        'total_spent': total_spent,
        'average_per_trip': total_spent / completed_bookings if completed_bookings > 0 else 0
    }

    # Favorite routes
    favorite_routes = db.session.query(
        Routes.id,
        Routes.origin,
        Routes.destination,
        func.count(Bookings.id).label('trip_count')
    ).join(
        Schedules, Routes.id == Schedules.route_id
    ).join(
        Bookings, Schedules.id == Bookings.schedule_id
    ).filter(
        Bookings.user_id == current_user.id,
        Bookings.status.in_(['confirmed', 'boarded'])
    ).group_by(
        Routes.id, Routes.origin, Routes.destination
    ).order_by(
        func.count(Bookings.id).desc()
    ).limit(5).all()

    favorite_routes_data = [{
        'route_id': route.id,
        'origin': route.origin,
        'destination': route.destination,
        'trip_count': route.trip_count
    } for route in favorite_routes]

    # Upcoming trips
    now = datetime.now(timezone.utc)
    upcoming_trips = db.session.query(Bookings).join(
        Schedules, Bookings.schedule_id == Schedules.id
    ).join(
        Routes, Schedules.route_id == Routes.id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).join(
        BusCompanies, Buses.company_id == BusCompanies.id
    ).filter(
        Bookings.user_id == current_user.id,
        Bookings.status == 'confirmed',
        Schedules.departure_time > now
    ).order_by(
        Schedules.departure_time.asc()
    ).limit(5).all()

    upcoming_trips_data = [{
        'booking_id': booking.id,
        'qr_reference': booking.qr_code_reference,
        'route': f"{booking.schedule.route.origin} to {booking.schedule.route.destination}",
        'departure_time': booking.schedule.departure_time.isoformat(),
        'arrival_time': booking.schedule.arrival_time.isoformat(),
        'bus_number': booking.schedule.bus.bus_number,
        'company': booking.schedule.bus.company.name,
        'price': booking.schedule.price
    } for booking in upcoming_trips]

    # Recent trips
    recent_trips = db.session.query(Bookings).join(
        Schedules, Bookings.schedule_id == Schedules.id
    ).join(
        Routes, Schedules.route_id == Routes.id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).join(
        BusCompanies, Buses.company_id == BusCompanies.id
    ).filter(
        Bookings.user_id == current_user.id,
        Bookings.status == 'boarded'
    ).order_by(
        Bookings.boarded_at.desc()
    ).limit(5).all()

    recent_trips_data = [{
        'booking_id': booking.id,
        'route': f"{booking.schedule.route.origin} to {booking.schedule.route.destination}",
        'departure_time': booking.schedule.departure_time.isoformat(),
        'boarded_at': booking.boarded_at.isoformat() if booking.boarded_at else None,
        'bus_number': booking.schedule.bus.bus_number,
        'company': booking.schedule.bus.company.name,
        'price': booking.schedule.price
    } for booking in recent_trips]

    return jsonify({
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email,
            'phone_number': current_user.phone_number
        },
        'bookings': booking_stats,
        'spending': spending_stats,
        'favorite_routes': favorite_routes_data,
        'upcoming_trips': upcoming_trips_data,
        'recent_trips': recent_trips_data
    }), 200


@dashboard_bp.route('/summary', methods=['GET'])
@login_required
def user_summary():
    """
    Quick summary for any authenticated user based on their role.
    Returns role-appropriate quick stats.
    """
    user_role = current_user.role.lower().strip()

    if user_role == 'admin':
        # Quick admin stats
        summary = {
            'role': 'admin',
            'total_companies': BusCompanies.query.count(),
            'pending_companies': BusCompanies.query.filter_by(status='pending').count(),
            'total_bookings_today': Bookings.query.filter(
                Bookings.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            ).count(),
            'total_users': Users.query.count()
        }

    elif user_role == 'company_owner':
        if not current_user.company_id:
            abort(400, description='Company owner must be associated with a company')

        company = BusCompanies.query.filter_by(id=current_user.company_id).first()

        # Today's bookings
        today_bookings = db.session.query(func.count(Bookings.id)).join(
            Schedules, Bookings.schedule_id == Schedules.id
        ).join(
            Buses, Schedules.bus_id == Buses.id
        ).filter(
            Buses.company_id == current_user.company_id,
            Bookings.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        ).scalar() or 0

        summary = {
            'role': 'company_owner',
            'company_name': company.name if company else None,
            'company_balance': company.balance if company else 0,
            'total_branches': Branches.query.filter_by(company_id=current_user.company_id).count(),
            'total_buses': Buses.query.filter_by(company_id=current_user.company_id).count(),
            'total_employees': Users.query.filter_by(company_id=current_user.company_id).count(),
            'bookings_today': today_bookings,
            'pending_payouts': Payouts.query.filter_by(
                company_id=current_user.company_id,
                status='pending'
            ).count()
        }

    elif user_role == 'branch_manager':
        if not current_user.branch_id:
            abort(400, description='Branch manager must be associated with a branch')

        branch = Branches.query.filter_by(id=current_user.branch_id).first()

        # Today's bookings
        today_bookings = db.session.query(func.count(Bookings.id)).join(
            Schedules, Bookings.schedule_id == Schedules.id
        ).join(
            Buses, Schedules.bus_id == Buses.id
        ).filter(
            Buses.branch_id == current_user.branch_id,
            Bookings.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        ).scalar() or 0

        summary = {
            'role': 'branch_manager',
            'branch_name': branch.name if branch else None,
            'total_buses': Buses.query.filter_by(branch_id=current_user.branch_id).count(),
            'total_employees': Users.query.filter_by(branch_id=current_user.branch_id).count(),
            'bookings_today': today_bookings,
            'buses_without_conductor': Buses.query.filter(
                Buses.branch_id == current_user.branch_id,
                Buses.conductor_id.is_(None)
            ).count()
        }

    elif user_role == 'conductor':
        assigned_bus = Buses.query.filter_by(conductor_id=current_user.id).first()

        # Today's scanned tickets
        today_scans = 0
        if assigned_bus:
            today_scans = db.session.query(func.count(Bookings.id)).join(
                Schedules, Bookings.schedule_id == Schedules.id
            ).filter(
                Schedules.bus_id == assigned_bus.id,
                Bookings.status == 'boarded',
                Bookings.boarded_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
            ).scalar() or 0

        summary = {
            'role': 'conductor',
            'assigned_bus': {
                'id': assigned_bus.id,
                'bus_number': assigned_bus.bus_number,
                'name': assigned_bus.name
            } if assigned_bus else None,
            'tickets_scanned_today': today_scans
        }

    elif user_role == 'passenger':
        summary = {
            'role': 'passenger',
            'total_bookings': Bookings.query.filter_by(user_id=current_user.id).count(),
            'upcoming_trips': Bookings.query.filter(
                Bookings.user_id == current_user.id,
                Bookings.status == 'confirmed'
            ).join(
                Schedules, Bookings.schedule_id == Schedules.id
            ).filter(
                Schedules.departure_time > datetime.now(timezone.utc)
            ).count(),
            'pending_bookings': Bookings.query.filter_by(
                user_id=current_user.id,
                status='pending'
            ).count()
        }

    else:
        # Other employee roles
        summary = {
            'role': user_role,
            'company_id': current_user.company_id,
            'branch_id': current_user.branch_id
        }

    return jsonify({
        'user': {
            'id': current_user.id,
            'name': current_user.name,
            'email': current_user.email
        },
        'summary': summary
    }), 200


@dashboard_bp.route('/revenue-chart', methods=['GET'])
@company_owner_or_admin_required
def revenue_chart():
    """
    Get revenue data for charting purposes.
    Returns daily/weekly/monthly revenue data.

    Query parameters:
    - company_id: Company ID (required for admins)
    - period: week, month, year (default: month)
    - group_by: day, week, month (default: day)
    """
    # Determine company_id
    if current_user.role.lower().strip() == 'company_owner':
        if not current_user.company_id:
            abort(400, description='Company owner must be associated with a company')
        company_id = current_user.company_id
    else:  # admin
        company_id = request.args.get('company_id', type=int)
        if not company_id:
            abort(400, description='company_id parameter required for admins')

    # Verify company exists
    company = BusCompanies.query.filter_by(id=company_id).first()
    if not company:
        abort(404, description='Company not found')

    period = request.args.get('period', 'month')
    group_by = request.args.get('group_by', 'day')

    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)

    # Query bookings with revenue
    bookings = db.session.query(
        Bookings.created_at,
        Schedules.price
    ).join(
        Schedules, Bookings.schedule_id == Schedules.id
    ).join(
        Buses, Schedules.bus_id == Buses.id
    ).filter(
        Buses.company_id == company_id,
        Bookings.status.in_(['confirmed', 'boarded']),
        Bookings.created_at >= start_date
    ).all()

    # Group data by period
    revenue_data = {}
    platform_fee = current_app.config.get('PLATFORM_FEE', 3000)

    for booking in bookings:
        if group_by == 'day':
            key = booking.created_at.strftime('%Y-%m-%d')
        elif group_by == 'week':
            # Get week number
            key = booking.created_at.strftime('%Y-W%W')
        else:  # month
            key = booking.created_at.strftime('%Y-%m')

        if key not in revenue_data:
            revenue_data[key] = {
                'gross': 0,
                'net': 0,
                'bookings': 0
            }

        revenue_data[key]['gross'] += booking.price
        revenue_data[key]['net'] += booking.price - platform_fee
        revenue_data[key]['bookings'] += 1

    # Convert to sorted list
    chart_data = [
        {
            'period': key,
            'gross_revenue': data['gross'],
            'net_revenue': data['net'],
            'booking_count': data['bookings']
        }
        for key, data in sorted(revenue_data.items())
    ]

    return jsonify({
        'company_id': company_id,
        'period': period,
        'group_by': group_by,
        'data': chart_data
    }), 200


@dashboard_bp.route('/booking-trends', methods=['GET'])
@company_owner_or_admin_required
def booking_trends():
    """
    Get booking trends over time for analysis.

    Query parameters:
    - company_id: Company ID (required for admins)
    - period: week, month, year (default: month)
    """
    # Determine company_id
    if current_user.role.lower().strip() == 'company_owner':
        if not current_user.company_id:
            abort(400, description='Company owner must be associated with a company')
        company_id = current_user.company_id
    else:  # admin
        company_id = request.args.get('company_id', type=int)

    period = request.args.get('period', 'month')

    # Calculate date range
    now = datetime.now(timezone.utc)
    if period == 'week':
        start_date = now - timedelta(days=7)
    elif period == 'month':
        start_date = now - timedelta(days=30)
    elif period == 'year':
        start_date = now - timedelta(days=365)
    else:
        start_date = now - timedelta(days=30)

    # Build base query
    if company_id:
        booking_query = db.session.query(Bookings).join(
            Schedules, Bookings.schedule_id == Schedules.id
        ).join(
            Buses, Schedules.bus_id == Buses.id
        ).filter(
            Buses.company_id == company_id,
            Bookings.created_at >= start_date
        )
    else:
        booking_query = db.session.query(Bookings).filter(
            Bookings.created_at >= start_date
        )

    # Get bookings by status over time
    bookings_by_day = {}
    bookings = booking_query.all()

    for booking in bookings:
        day_key = booking.created_at.strftime('%Y-%m-%d')

        if day_key not in bookings_by_day:
            bookings_by_day[day_key] = {
                'confirmed': 0,
                'pending': 0,
                'cancelled': 0,
                'boarded': 0,
                'total': 0
            }

        bookings_by_day[day_key][booking.status] = bookings_by_day[day_key].get(booking.status, 0) + 1
        bookings_by_day[day_key]['total'] += 1

    # Convert to sorted list
    trends_data = [
        {
            'date': key,
            **data
        }
        for key, data in sorted(bookings_by_day.items())
    ]

    return jsonify({
        'company_id': company_id,
        'period': period,
        'trends': trends_data
    }), 200
