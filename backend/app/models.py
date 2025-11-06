import random
from .extensions import db
from .extensions import login
from flask_login import UserMixin
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash


class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False, default='passenger')
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)

    bookings = db.relationship('Bookings', backref='user', lazy=True)

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
                "email": self.email
            }
        }

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
    status = db.Column(db.Boolean, default='pending', index=True)

    buses = db.relationship('Buses', backref='company', lazy=True)
    payouts = db.relationship('Payouts', backref='company', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "contact_info": self.contact_info,
            "account_details": self.account_details,
            "status": self.status,
            "buses": self.buses.count()
        }
    
    def can_add_bus(self):
        return self.status == 'registered'
    
    def __repr__(self):
        return f"<Company {self.id}|{self.name}>"


class Buses(db.Model):
    __tablename__ = 'buses'

    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(100), nullable=False)
    seating_capacity = db.Column(db.Integer, nullable=False)

    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False)
    schedules = db.relationship('Schedules', backref='bus', lazy=True)


    def __repr__(self):
        return f"<Bus {self.id}|{self.bus_number}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "bus_number": self.bus_number,
            "seating_capacity": self.seating_capacity,
            "company_id": self.company_id
        }


class Routes(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    distance = db.Column(db.Float, nullable=True)

    schedules = db.relationship('Schedules', backref='route', lazy=True)


    def __repr__(self):
        return f"<>Route {self.id} | {self.origin} to {self.destination}>"

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
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)


    bookings = db.relationship('Bookings', backref='schedule', lazy=True)

    def __repr__(self):
        return f"<Schedule {self.id} | {self.departure_time} to {self.arrival_time}>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "departure_time": self.departure_time.isoformat(),
            "arrival_time": self.arrival_time.isoformat(),
            "route_id": self.route_id,
            "bus_id": self.bus_id,
            "price": self.price,
            "available_seats": self.available_seats
        }


class Bookings(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(100), nullable=False, default='pending', index=True)
    qrcode = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    cancelled_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    transactions = db.relationship('Transactions', backref='booking', lazy=True)

    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def create_qrcode(self, user_id, schedule_id):
        self.qrcode = f"{user_id}-{schedule_id}-{datetime.now().timestamp()}"

    def can_cancel(self):
        return self.created_at < datetime.now(timezone.utc) - timedelta(hours=24)


    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "qrcode": self.qrcode,
            "schedule_id": self.schedule_id,
            "user_id": self.user_id
        }

    def __repr__(self):
        return f"<Booking {self.id} | {self.qrcode}>"
    

class Payouts(db.Model):
    __tablename__ = 'payouts'

    id = db.Column(db.Integer, primary_key=True)
    ammount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    requested_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime, nullable=True)

    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False)

    def to_dict(self):
        return {
            'payout': {
                "id": self.id,
                "ammount": self.ammount,
                "status": self.status,
                "requested_at": self.requested_at.isoformat(),
                "processed_at": self.processed_at.isoformat() if self.processed_at else None,
                "company_id": self.company_id
            }
        }
    
    def __repr__(self):
        return f"<Payout {self.id} | {self.ammount}>"
    

class Transactions(db.Model): 
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    method = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(100), nullable=False)
    payment_status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)

    def to_dict(self):
        return {
            'transaction': {
                "id": self.id,
                "amount": self.amount,
                "status": self.status,
                "method": self.method,
                "reference": self.reference,
                "payment_status": self.payment_status,
                "created_at": self.created_at,
                "booking_id": self.booking_id
            }
        }

    def __repr__(self):
        return f"<Transaction {self.id} | {self.amount}>"


class PasswordResetCode(db.Model):
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc) + timedelta(minutes=10))

    def create_code(self):
        self.code = random.randrange(100000, 999999)
    
    def is_code_valid(self):
        return self.created_at < self.expires_at
    
    def __repr__(self):
        return f"<PasswordResetToken {self.id} | {self.token}>"
