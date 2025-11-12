from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
mail = Mail()
login = LoginManager()
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail
from flask_login import LoginManager

# Flask extensions
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
mail = Mail()
login = LoginManager()

# PayChangu client placeholder
# You can initialize it later with API key from config
paychangu_client = None
