import os
from flask import Flask, jsonify
from app.config import get_config
from .extensions import db, migrate, cors, mail, login
from paychangu import PayChanguClient

def create_app(config_name: str = None) -> Flask:
    """Application factory for Ulendo Tiketi API."""
    app = Flask(__name__)

    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    app.config.from_object(get_config(config_name))

    # Initialize extensions
    initialize_extensions(app)
    
    # Initialize PayChangu client
    initialize_paychangu(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Create upload folders if they don't exist
    create_directories(app)

    # Simple index
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Ulendo Tiketi API',
            'status': 'running'
        })

    return app


def initialize_extensions(app: Flask):
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config['CORS_ORIGINS'],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
        }
    )
    login.init_app(app)
    mail.init_app(app)


def initialize_paychangu(app: Flask):
    """Initialize PayChangu client with API key from config."""
    from app import extensions
    
    api_key = app.config.get('PAYCHANGU_API_KEY')
    if api_key:
        extensions.paychangu_client = PayChanguClient(api_key)
        app.logger.info("PayChangu client initialized successfully")
    else:
        app.logger.warning("PayChangu API key not found - payment functionality will not work")


def register_blueprints(app: Flask):
    from app.blueprints.auth import auth_bp
    from app.blueprints.users import users_bp
    from app.blueprints.companies import companies_bp
    from app.blueprints.buses import buses_bp
    from app.blueprints.routes import routes_bp
    from app.blueprints.schedules import schedules_bp
    from app.blueprints.bookings import bookings_bp
    from app.blueprints.search import search_bp
    from app.blueprints.payments import payments_bp
    from app.blueprints.payouts import payouts_bp
    from app.blueprints.banks import banks_bp
    from app.blueprints.branches import branches_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.employees import employees_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(companies_bp, url_prefix='/api/companies')
    app.register_blueprint(buses_bp, url_prefix='/api/buses')
    app.register_blueprint(routes_bp, url_prefix='/api/routes')
    app.register_blueprint(schedules_bp, url_prefix='/api/schedules')
    app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    app.register_blueprint(search_bp, url_prefix='/api/search')
    app.register_blueprint(payments_bp, url_prefix='/api/payments')
    app.register_blueprint(payouts_bp, url_prefix='/api/payouts')
    app.register_blueprint(banks_bp, url_prefix='/api/banks')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(branches_bp, url_prefix='/api/branches')
    app.register_blueprint(employees_bp, url_prefix='/api/employees')


def register_error_handlers(app: Flask):
    @app.errorhandler(400)
    def bad_request(e):
        # Rollback any pending database transactions
        db.session.rollback()
        return jsonify({'error': 'Bad Request', 'message': str(e)}), 400
    
    @app.errorhandler(403)
    def forbidden(e):
        # Rollback any pending database transactions
        db.session.rollback()
        return jsonify({'error': 'Forbidden', 'message': str(e)}), 403
    
    @app.errorhandler(404)
    def not_found(e):
        # Rollback any pending database transactions
        db.session.rollback()
        return jsonify({'error': 'Not Found', 'message': str(e)}), 404

    @app.errorhandler(500)
    def internal_error(e):
        # Rollback any pending database transactions
        db.session.rollback()
        app.logger.error(f"Internal server error: {str(e)}")
        return jsonify({'error': 'Internal Server Error', 'message': str(e)}), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Catch any unhandled exceptions
        db.session.rollback()
        app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


def create_directories(app: Flask):
    folders = [app.config['UPLOAD_FOLDER']]
    for folder in folders:
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)