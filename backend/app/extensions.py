import os
from dotenv import load_dotenv
from flask_mail import Mail
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager
from paychangu import PayChanguClient
from flask_sqlalchemy import SQLAlchemy


load_dotenv()

mail = Mail()
cors = CORS()
db = SQLAlchemy()
login = LoginManager()
login.login_view = 'auth.login'
migrate = Migrate()
paychangu_client = PayChanguClient(secret_key=os.getenv('PAYCHANGU_API_KEY'))


