import os
import logging
from flask import Flask, jsonify
from app.config import get_config
from logging.handlers import RotatingFileHandler
from .extensions import db, migrate, cors, mail, login


def create_app(config_name: str = None) -> Flask:
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    config = get_config(config_name)
    app.config.from_object(config)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    # register_blueprints(app)
    
    # Setup logging
    # setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register shell context
    register_shell_context(app)
    
    # Create upload folders if they don't exist
    create_directories(app)
    
    return app


def initialize_extensions(app: Flask) -> None:
    """Initialize Flask extensions with app context."""
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        origins=app.config['CORS_ORIGINS'],
        supports_credentials=app.config['CORS_SUPPORTS_CREDENTIALS']
    )
    login.init_app(app)
    mail.init_app(app)


def register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.blueprints.auth import auth_bp
    from app.blueprints.users import users_bp
    from app.blueprints.companies import companies_bp
    from app.blueprints.buses import buses_bp
    # from app.blueprints.routes import routes_bp
    # from app.blueprints.schedules import schedules_bp
    # from app.blueprints.bookings import bookings_bp
    # from app.blueprints.search import search_bp
    # from app.blueprints.payments import payments_bp
    # from app.blueprints.payouts import payouts_bp
    
    # Register blueprints with URL prefix
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(companies_bp, url_prefix='/api/companies')
    app.register_blueprint(buses_bp, url_prefix='/api/buses')
    # app.register_blueprint(routes_bp, url_prefix='/api/routes')
    # app.register_blueprint(schedules_bp, url_prefix='/api/schedules')
    # app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
    # app.register_blueprint(search_bp, url_prefix='/api/search')
    # app.register_blueprint(payments_bp, url_prefix='/api/payments')
    # app.register_blueprint(payouts_bp, url_prefix='/api/payouts')
    
    # Register root endpoint
    @app.route('/')
    def index():
        """API root endpoint."""
        return jsonify({
            'message': 'Ulendo Tiketi API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/health',
                'auth': '/api/auth',
                'companies': '/api/companies',
                'buses': '/api/buses',
                'routes': '/api/routes',
                'schedules': '/api/schedules',
                'bookings': '/api/bookings',
                'search': '/api/search',
                'payments': '/api/payments',
                'payouts': '/api/payouts'
            }
        })
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        db_status = check_database_connection()
        return jsonify({
            'status': 'healthy' if db_status else 'unhealthy',
            'database': 'connected' if db_status else 'disconnected',
            'environment': app.config.get('ENV', 'unknown')
        }), 200 if db_status else 503


def setup_logging(app: Flask) -> None:
    """Configure application logging."""
    if not app.debug and not app.testing:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # File handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
        ))
        file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        # Add handler to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
        
        app.logger.info('Ulendo Tiketi startup')


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for this endpoint'
        }), 405
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors."""
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': str(error.description) if hasattr(error, 'description') else str(error)
        }), 422
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        app.logger.error(f'Internal Server Error: {error}')
        db.session.rollback()  # Rollback any failed database transactions
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected exceptions."""
        app.logger.error(f'Unexpected error: {error}', exc_info=True)
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500


def register_shell_context(app: Flask) -> None:
    """Register shell context for flask shell command."""
    @app.shell_context_processor
    def make_shell_context():
        """Make database models available in flask shell."""
        from app.models import (
            Users, BusCompanies, Buses, Routes, Schedules,
            Bookings, Payments, Payouts,
        )
        return {
            'db': db,
            'Users': Users,
            'BusCompanies': BusCompanies,
            'Buses': Buses,
            'Routes': Routes,
            'Schedules': Schedules,
            'Bookings': Bookings,
            'Payments': Payments,
            'Payouts': Payouts,
        }


def create_directories(app: Flask) -> None:
    """Create necessary directories if they don't exist."""
    directories = [
        app.config.get('UPLOAD_FOLDER'),
        os.path.dirname(app.config.get('LOG_FILE', 'logs/app.log'))
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)


def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        db.session.execute(db.text('SELECT 1'))
        return True
    except Exception:
        return False
