<<<<<<< HEAD
from app import create_app
from app.extensions import db

app = create_app(config_class="development")

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run()
=======
import os
from app import create_app

# Get environment from FLASK_ENV or default to development
env = os.getenv('FLASK_ENV', 'development')

app = create_app(env)

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
>>>>>>> 8d0becc (feat: Enhance backend configuration and application setup and created database tables in the models.py file)
