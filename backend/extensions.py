#! /usr/bin/env python3


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_principal import Principal
from flask_cors import CORS
from flask_socketio import SocketIO
from flask_security import Security

# Initialize extensions without binding to a Flask app yet
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()
principal = Principal()
cors = CORS()
socketio = SocketIO()
security = Security()
