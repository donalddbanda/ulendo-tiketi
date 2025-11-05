import os
from datetime import timedelta
from dotenv import load_dotenv


load_dotenv()

class BaseConfig:
    """Base configuration with common settings."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 24)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 30)))
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    
    # PayChangu Configuration
    PAYCHANGU_API_KEY = os.getenv('PAYCHANGU_API_KEY', '')
    PAYCHANGU_WEBHOOK_SECRET = os.getenv('PAYCHANGU_WEBHOOK_SECRET', '')
    PAYCHANGU_CALLBACK_URL = os.getenv('PAYCHANGU_CALLBACK_URL', 'http://localhost:8000')
    PAYCHANGU_BASE_URL = os.getenv('PAYCHANGU_BASE_URL', 'https://api.paychangu.com/v1')
    PAYCHANGU_MODE = os.getenv('PAYCHANGU_MODE', 'sandbox')  # 'sandbox' or 'live'
    
    # Platform Settings
    PLATFORM_FEE = float(os.getenv('PLATFORM_FEE', '3000'))  # MWK 3000
    
    # Frontend URL (for redirects and CORS)
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # Mail Configuration (Flask-Mail)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@ulendotiketi.com')
    MAIL_MAX_EMAILS = int(os.getenv('MAIL_MAX_EMAILS', 50))
    MAIL_ASCII_ATTACHMENTS = False
    
    # Email Templates
    MAIL_TEMPLATES_FOLDER = 'app/templates/email'
    
    # File Upload Configuration (for future use)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Rate Limiting (optional for MVP)
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'False').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '100 per minute')
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # QR Code Configuration
    QR_CODE_VERSION = 1
    QR_CODE_ERROR_CORRECTION = 'H'  # High error correction
    QR_CODE_BOX_SIZE = 10
    QR_CODE_BORDER = 4
    
    # Booking Configuration
    BOOKING_CANCELLATION_HOURS = int(os.getenv('BOOKING_CANCELLATION_HOURS', 24))
    
    # Timezone
    TIMEZONE = os.getenv('TIMEZONE', 'Africa/Blantyre')


class DevelopmentConfig(BaseConfig):
    """Development configuration."""
    
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL',)
    SQLALCHEMY_ECHO = False
    
    # Mail (use console backend for development)
    MAIL_SUPPRESS_SEND = os.getenv('MAIL_SUPPRESS_SEND', 'True').lower() == 'true'
    MAIL_DEBUG = True
    
    # CORS - allow all origins in development
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173', 'http://127.0.0.1:3000']
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    # Session
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class ProductionConfig(BaseConfig):
    """Production configuration."""
    
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Ensure critical environment variables are set
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable must be set in production")
    
    if BaseConfig.SECRET_KEY == 'dev-secret-key-change-in-production':
        raise ValueError("SECRET_KEY must be set to a secure value in production")
    
    if BaseConfig.JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
        raise ValueError("JWT_SECRET_KEY must be set to a secure value in production")
    
    # Database connection pooling
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20))
    }
    
    # Mail
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = False
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Logging
    LOG_LEVEL = 'WARNING'
    LOG_FILE = '/var/log/ulendo-tiketi/app.log'
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')


class TestingConfig(BaseConfig):
    """Testing configuration."""
    
    DEBUG = True
    TESTING = True
    
    # Use separate test database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'TEST_DATABASE_URL',
        'postgresql://postgres:password@localhost:5432/ulendo_tiketi_test'
    )
    
    # Disable CSRF protection in tests
    WTF_CSRF_ENABLED = False
    
    # Mail
    MAIL_SUPPRESS_SEND = True
    MAIL_DEBUG = False
    
    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)
    
    # PayChangu - use sandbox mode
    PAYCHANGU_MODE = 'sandbox'
    
    # Session
    SESSION_COOKIE_SECURE = False
    
    # Disable rate limiting in tests
    RATELIMIT_ENABLED = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> BaseConfig:
    """
    Get configuration based on environment.
    
    Args:
        env: Environment name ('development', 'production', 'testing')
             If None, reads from FLASK_ENV environment variable
    
    Returns:
        Configuration class instance
    """
    if env is None:
        env = os.getenv('FLASK_ENV', 'development')
    
    return config.get(env, config['default'])