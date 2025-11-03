import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .extensions import db
from . import login
from datetime import timezone, datetime, timedelta


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='user')

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class BusCompany(db.Model):
    __tablename__ = 'bus_company'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    contact_info = db.Column(db.String(255))
    account_details = db.Column(db.String(255))

    # Relationships
    buses = db.relationship('Bus', backref='bus_company', lazy=True)
    cashouts = db.relationship('Cashout', backref='company', lazy=True)

    def __repr__(self):
        return f'<BusCompany {self.name}>'


class Bus(db.Model):
    __tablename__ = 'bus'

    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(50), nullable=False)
    seating_capacity = db.Column(db.Integer, nullable=False)

    bus_company_id = db.Column(db.Integer, db.ForeignKey('bus_company.id'), nullable=False)

    # Relationships
    schedules = db.relationship('Schedule', backref='bus', lazy=True)

    def __repr__(self):
        return f'<Bus {self.bus_number}>'


class Route(db.Model):
    __tablename__ = 'route'

    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(120), nullable=False)
    destination = db.Column(db.String(120), nullable=False)
    distance = db.Column(db.Float)

    # Relationships
    schedules = db.relationship('Schedule', backref='route', lazy=True)

    def __repr__(self):
        return f'<Route {self.origin} - {self.destination}>'


class Schedule(db.Model):
    __tablename__ = 'schedule'

    id = db.Column(db.Integer, primary_key=True)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)

    bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)

    # Relationships
    bookings = db.relationship('Booking', backref='schedule', lazy=True)

    def __repr__(self):
        return f'<Schedule BusID={self.bus_id}, RouteID={self.route_id}>'


class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.String(10), nullable=False)
    booking_status = db.Column(db.String(50), nullable=False, default='pending')
    qr_code = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedule.id'), nullable=False)

    # Relationships
    payment = db.relationship('Payment', backref='booking', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Booking {self.id} - User {self.user_id}>'


class Payment(db.Model):
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    payment_reference = db.Column(db.String(120), unique=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)

    def __repr__(self):
        return f'<Payment {self.payment_reference}>'


class Cashout(db.Model):
    __tablename__ = 'cashout'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime)

    company_id = db.Column(db.Integer, db.ForeignKey('bus_company.id'), nullable=False)

    def __repr__(self):
        return f'<Cashout {self.id} - Company {self.company_id}>'


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_token'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, email):
        self.email = email
        self.expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    def set_token(self):
        self.token = secrets.token_urlsafe(32)

    def is_valid(self):
        return datetime.now(timezone.utc) < self.expires_at

    def __repr__(self):
        return f"<PasswordResetToken {self.email}>"