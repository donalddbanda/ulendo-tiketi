import os
from flask import Flask
from .extensions import db, migrate, login, mail
from .config import DevelopmentConfig, ProductionConfig
from app.models import User, BusCompany, Bus, Route, Schedule, Booking, Payment, Cashout

def create_app(config_class=None):
    
    app = Flask(__name__)

    env = os.getenv('FLASK_ENV', 'production')
    if config_class == "development" or env == 'development':
        app.config.from_object(DevelopmentConfig)
    else:
        app.config.from_object(ProductionConfig)

    # Initialize extensions here (e.g., database, migrations, etc.)
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)

    # Register blueprints here
    from .blueprints.auth import auth

    app.register_blueprint(auth)

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

