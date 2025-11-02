from .extensions import db, bcrypt
from datetime import timezone, datetime


class User(db.Model):
    __tablename__ = 'users'

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
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password, password)


class BusCompany(db.Model):
    __tablename__ = 'bus_companies'

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
    __tablename__ = 'buses'

    id = db.Column(db.Integer, primary_key=True)
    bus_number = db.Column(db.String(50), nullable=False)
    seating_capacity = db.Column(db.Integer, nullable=False)

    bus_company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False)

    # Relationships
    schedules = db.relationship('Schedule', backref='bus', lazy=True)

    def __repr__(self):
        return f'<Bus {self.bus_number}>'


class Route(db.Model):
    __tablename__ = 'routes'

    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(120), nullable=False)
    destination = db.Column(db.String(120), nullable=False)
    distance = db.Column(db.Float)

    # Relationships
    schedules = db.relationship('Schedule', backref='route', lazy=True)

    def __repr__(self):
        return f'<Route {self.origin} - {self.destination}>'


class Schedule(db.Model):
    __tablename__ = 'schedules'

    id = db.Column(db.Integer, primary_key=True)
    departure_time = db.Column(db.DateTime, nullable=False)
    arrival_time = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.Float, nullable=False)

    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'), nullable=False)

    # Relationships
    bookings = db.relationship('Booking', backref='schedule', lazy=True)

    def __repr__(self):
        return f'<Schedule BusID={self.bus_id}, RouteID={self.route_id}>'


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.String(10), nullable=False)
    booking_status = db.Column(db.String(50), nullable=False, default='pending')
    qr_code = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)

    # Relationships
    payment = db.relationship('Payment', backref='booking', uselist=False, lazy=True)

    def __repr__(self):
        return f'<Booking {self.id} - User {self.user_id}>'


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_reference = db.Column(db.String(120), unique=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)

    def __repr__(self):
        return f'<Payment {self.payment_reference}>'


class Cashout(db.Model):
    __tablename__ = 'cashouts'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    requested_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    processed_at = db.Column(db.DateTime)

    company_id = db.Column(db.Integer, db.ForeignKey('bus_companies.id'), nullable=False)

    def __repr__(self):
        return f'<Cashout {self.id} - Company {self.company_id}>'
