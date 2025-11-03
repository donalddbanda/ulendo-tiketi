import os
from dotenv import load_dotenv

load_dotenv()

def _to_bool(val):
    """Convert env string to boolean."""
    return str(val).strip().lower() in ('1', 'true', 'yes', 'on')

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-secret-change-me"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '465'))
    MAIL_USE_TLS = _to_bool(os.getenv('MAIL_USE_TLS', 'False'))
    MAIL_USE_SSL = _to_bool(os.getenv('MAIL_USE_SSL', 'True'))
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@ulendo-tiketi.com')

    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DEV_DATABASE_URL", "sqlite:///dev.db")


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///ulendo.db")