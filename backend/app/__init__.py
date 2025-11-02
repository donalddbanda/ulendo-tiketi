from flask import Flask
from .extensions import db, migrate
from .config import DevelopmentConfig
from app.models import User, BusCompany, Bus, Route, Schedule, Booking, Payment, Cashout

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)

    # Initialize extensions here (e.g., database, migrations, etc.)
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints here

    # --- Shell Context ---
    @app.shell_context_processor
    def make_shell_context():
        return {
            'db': db,
            'User': User,
            'BusCompany': BusCompany,
            'Bus': Bus,
            'Route': Route,
            'Schedule': Schedule,
            'Booking': Booking,
            'Payment': Payment,
            'Cashout': Cashout
        }

    return app

