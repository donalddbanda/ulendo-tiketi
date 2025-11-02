from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'

