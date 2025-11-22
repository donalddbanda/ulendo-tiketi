import secrets
from .extensions import db
from .extensions import login
from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash


class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='passenger', index=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.Text, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)

    bookings = db.relationship('Bookings', backref='user', lazy=True)
    companies_owned = db.relationship('BusCompanies', backref='owner', lazy=True, foreign_keys='BusCompanies.owner_id')
    managed_branches = db.relationship('Branches', backref='manager', lazy=True, foreign_keys='Branches.manager_id')
    assigned_buses = db.relationship('Buses', backref='conductor', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "user": {
                "id": self.id,
                "name": self.name,
                "role": self.role,
                "phone_number": self.phone_number,
                "email": self.email,
                "company_id": self.company_id,
                "branch_id": self.branch_id
            }
        }
    
    def is_company_owner(self):
        """Check if user is a company owner"""
        return self.role.lower() == 'company_owner'
    
    def is_branch_manager(self):
        """Check if user is a branch manager"""
        return self.role.lower() == 'branch_manager'
    
    def is_accounts_manager(self):
        """Check if user is an accounts/finance manager"""
        return self.role.lower() == 'accounts_manager'
    
    def is_bus_manager(self):
        """Check if user is a bus manager"""
        return self.role.lower() == 'bus_manager'
    
    def is_conductor(self):
        """Check if user is a bus conductor"""
        return self.role.lower() == 'conductor'
    
    def is_schedule_manager(self):
        """Check if user is a schedule manager"""
        return self.role.lower() == 'schedule_manager'
    
    def has_company_role(self):
        """Check if user has any company-related role"""
        company_roles = ['company_owner', 'branch_manager', 'accounts_manager', 
                        'bus_manager', 'conductor', 'schedule_manager']
        return self.role.lower() in company_roles
    
    def can_manage_branch(self, branch_id):
        """Check if user can manage a specific branch"""
        if self.is_company_owner() and self.company_id:
            # Company owners can manage all branches in their company
            return True
        if self.is_branch_manager() and self.branch_id == branch_id:
            # Branch managers can only manage their assigned branch
            return True
        return False
    
    def can_access_company_data(self, company_id):
        """Check if user can access company data"""
        return self.company_id == company_id and self.has_company_role()

    def __repr__(self):
        return f"<User {self.id}|{self.name}>"


@login.user_loader
def load_user(user_id:int):
    return Users.query.get(int(user_id))


class BusCompanies(db.Model):
    __tablename__ = 'bus_companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(100), nullable=False)
    contact_info = db.Column(db.JSON, nullable=False)
    account_details = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(50), default='pending', index=True)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    buses = db.relationship('Buses', backref='company', lazy=True)
    payouts = db.relationship('Payouts', backref='company', lazy=True)
    branches = db.relationship('Branches', backref='company', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "owner_id": self.owner_id
        }
    
    def can_add_bus(self):
        return self.status == 'registered'
    
    def __repr__(self):
        return f"<Company {self.id}|{self.name}>"


class Branches(db.Model):
    __tablename__ = 'branches'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False, index=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    buses = db.relationship('Buses', backref='branch', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "company_id": self.company_id,
            "manager_id": self.manager_id
        }

    def __repr__(self):
        return f"<Branch {self.id}|{self.name}>"


class Buses(db.Model):
    __tablename__ = 'buses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    bus_number = db.Column(db.String(100), nullable=False, unique=True, index=True)
    seating_capacity = db.Column(db.Integer, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False, index=True)
    conductor_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)

    schedules = db.relationship('Schedules', backref='bus', lazy=True)

    def __repr__(self):
        return f"<Bus {self.id}|{self.bus_number}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "bus_number": self.bus_number,
            "seating_capacity": self.seating_capacity,
            "company_id": self.company_id,
            "branch_id": self.branch_id,
            "conductor_id": self.conductor_id
        }


class Routes(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(100), nullable=False, index=True)
    destination = db.Column(db.String(100), nullable=False, index=True)
    distance = db.Column(db.Float, nullable=True)

    schedules = db.relationship('Schedules', backref='route', lazy=True)

    # Composite index for origin-destination pair
    __table_args__ = (
        db.Index('ix_routes_origin_destination', 'origin', 'destination'),
    )

    def __repr__(self):
        return f"<Route {self.id} | {self.origin} to {self.destination}>"

    def to_dict(self):
        return {
            "id": self.id,
            "origin": self.origin,
            "destination": self.destination,
            "distance": self.distance
        }


class Schedules(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    departure_time = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    arrival_time = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False, index=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False, index=True)

    bookings = db.relationship('Bookings', backref='schedule', lazy=True)

    __table_args__ = (
        db.Index('ix_schedules_route_departure', 'route_id', 'departure_time', 'arrival_time'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "departure_time": self.departure_time.isoformat(),
            "arrival_time": self.arrival_time.isoformat(),
            "price": self.price,
            "available_seats": self.available_seats,
            "route_id": self.route_id,
            "bus_id": self.bus_id,
            "bus": self.bus.to_dict() if self.bus else None,
            "route": self.route.to_dict() if self.route else None
        }


class Bookings(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100), nullable=False, default='pending', index=True)
    seat_number = db.Column(db.String(20), nullable=True, index=True)
    
    qr_code_reference = db.Column(db.String(100), nullable=True, unique=True, index=True)
    qr_code_reference_status = db.Column(db.String(20), nullable=False, default='unused', index=True)
    # Status values: 'unused', 'used', 'expired'
    
    payment_link = db.Column(db.String(200), nullable=True)
    tx_ref = db.Column(db.String(100), nullable=True, unique=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)
    cancelled_at = db.Column(db.DateTime, nullable=True)
    boarded_at = db.Column(db.DateTime, nullable=True)  # Track when passenger boarded

    # Relationships
    transactions = db.relationship('Transactions', backref='booking', lazy=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    def generate_qr_reference(self):
        """Generate unique QR code reference"""
        import secrets
        timestamp = int(datetime.now(timezone.utc).timestamp())
        random_part = secrets.token_hex(8)
        self.qr_code_reference = f"UTK-{self.id}-{timestamp}-{random_part}"
        return self.qr_code_reference

    def can_cancel(self):
        """Check if booking can be cancelled"""
        if not self.schedule or not self.schedule.departure_time:
            return False
        
        if self.status != 'confirmed':
            return False

        departure_time = self.schedule.departure_time
        if departure_time.tzinfo is None:
            departure_time = departure_time.replace(tzinfo=timezone.utc)

        cancellation_deadline = departure_time - timedelta(hours=24)
        now = datetime.now(timezone.utc)

        return now < cancellation_deadline

    def is_qr_valid(self):
        """Check if QR code is still valid for boarding"""
        if self.status != 'confirmed':
            return False, f"Booking status is {self.status}"
        
        if self.qr_code_reference_status == 'used':
            return False, "QR code already used"
        
        if self.qr_code_reference_status == 'expired':
            return False, "QR code expired"
        
        # Check if departure time has passed
        departure_time = self.schedule.departure_time
        if departure_time.tzinfo is None:
            departure_time = departure_time.replace(tzinfo=timezone.utc)
        
        # Allow boarding up to 30 minutes after departure
        boarding_deadline = departure_time + timedelta(minutes=30)
        now = datetime.now(timezone.utc)
        
        if now > boarding_deadline:
            return False, "Boarding time has passed"
        
        return True, "Valid"

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "qr_code_reference": self.qr_code_reference,
            "qr_code_status": self.qr_code_reference_status,
            "payment_link": self.payment_link,
            "tx_ref": self.tx_ref,
            "schedule_id": self.schedule_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "boarded_at": self.boarded_at.isoformat() if self.boarded_at else None
        }

    def __repr__(self):
        return f"<Booking {self.id} | {self.qr_code_reference}>"
    

class Payouts(db.Model):
    __tablename__ = 'payouts'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    # Status values: 'pending', 'processing', 'completed', 'failed', 'cancelled', 'rejected'
    
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    
    # PayChangu integration fields
    paychangu_charge_id = db.Column(db.String(100), nullable=True, unique=True)
    paychangu_ref_id = db.Column(db.String(100), nullable=True, unique=True, index=True)
    paychangu_status = db.Column(db.String(50), nullable=True)
    # PayChangu status values: 'pending', 'successful', 'failed', 'cancelled'

    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False, index=True)

    def to_dict(self):
        return {
            'payout': {
                "id": self.id,
                "amount": self.amount,
                "status": self.status,
                "requested_at": self.requested_at.isoformat(),
                "processed_at": self.processed_at.isoformat() if self.processed_at else None,
                "company_id": self.company_id,
                "paychangu_ref_id": self.paychangu_ref_id,
                "paychangu_status": self.paychangu_status
            }
        }
    
    def __repr__(self):
        return f"<Payout {self.id} | {self.amount} | {self.status}>"
    

class Transactions(db.Model): 
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    method = db.Column(db.String(50), nullable=False, default='paychangu')
    reference = db.Column(db.String(100), nullable=False, unique=True, index=True)  # tx_ref from PayChangu
    payment_status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "amount": self.amount,
            "status": self.status,
            "method": self.method,
            "reference": self.reference,
            "payment_status": self.payment_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "booking_id": self.booking_id
        }

    def __repr__(self):
        return f"<Transaction {self.id} | {self.amount}>"


class PasswordResetCode(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc) + timedelta(minutes=10), index=True)

    def create_code(self):
        self.code = str(secrets.randbelow())
    
    def is_code_valid(self):
        return datetime.now(timezone.utc) < self.expires_at
    
    def __repr__(self):
        return f"<PasswordResetToken {self.id} | {self.email}>"


class EmployeeInvitation(db.Model):
    """Model to track employee invitations to join a company/branch"""
    __tablename__ = 'employee_invitations'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    phone_number = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False, index=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True, index=True)
    invited_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    invitation_code = db.Column(db.String(100), nullable=False, unique=True)
    status = db.Column(db.String(50), default='pending', index=True)
    # Status values: 'pending', 'accepted', 'expired', 'cancelled'
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc) + timedelta(days=7), index=True)
    accepted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    company = db.relationship('BusCompanies', backref='invitations')
    branch = db.relationship('Branches', backref='invitations')
    inviter = db.relationship('Users', backref='sent_invitations')

    def generate_invitation_code(self):
        """Generate unique invitation code"""
        import secrets
        self.invitation_code = secrets.token_urlsafe(32)
        return self.invitation_code
    
    def is_valid(self):
        """Check if invitation is still valid"""
        if self.status != 'pending':
            return False, f"Invitation already {self.status}"
        
        now = datetime.now(timezone.utc)
        if now > self.expires_at:
            self.status = 'expired'
            return False, "Invitation has expired"
        
        return True, "Valid"

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "phone_number": self.phone_number,
            "role": self.role,
            "company_id": self.company_id,
            "branch_id": self.branch_id,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None
        }

    def __repr__(self):
        return f"<EmployeeInvitation {self.id} | {self.email} | {self.role}>"