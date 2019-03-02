from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_user import UserManager
from flask_babelex import Babel

from app.service.EmailManagerWithDomainValidation import EmailManagerWithDomainValidation
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


from app.models import User
import logging

babel = Babel(app)
user_manager = UserManager(app, db, User)
user_manager.email_manager = EmailManagerWithDomainValidation(app)

from app import routes, models

logging.basicConfig(filename='coffee-in.log', level=logging.DEBUG)
logging.info('MAIL MANAGER: {}'.format(user_manager.email_manager))
