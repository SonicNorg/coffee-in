# -*- coding: utf-8 -*-
from datetime import datetime

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_babelex import Babel

from app.service.Customizing import EmailManagerWithDomainValidation, CustomUserManager
from config import Config

import logging

logging.basicConfig(filename='coffee_in.log', level=logging.DEBUG)

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from app.models import User, Role
from app import routes, models

babel = Babel(app)
user_manager = CustomUserManager(app, db, User)

# Init roles and admin

roles = Role.query.all()
logging.info('Roles: {}'.format(roles))
if not roles:
    dealer = Role(name='Дилер')
    boss = Role(name='Босс')
    db.session.add(dealer)
    db.session.add(boss)
    db.session.commit()
    admin = User(username='Norg',
                 email='pavel.proger@gmail.com',
                 password=user_manager.hash_password('1qaz@WSX'),
                 email_confirmed_at=datetime.now(),
                 active=True, roles=[dealer, boss])
    db.session.add(admin)
    db.session.commit()
