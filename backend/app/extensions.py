<<<<<<< HEAD
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'

=======
from flask_mail import Mail
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


mail = Mail()
cors = CORS()
db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
migrate = Migrate()
>>>>>>> 8d0becc (feat: Enhance backend configuration and application setup and created database tables in the models.py file)
