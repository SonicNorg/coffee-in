# -*- coding: utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SEC_COFFEE_KEY') or 'you-will-never-guessslkdjflkslkjflkjsdlkjsdf'
    FLASK_ENV = os.environ.get('FLASK_ENV') or 'production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app-test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_APP_NAME = 'Кофе-Ин'
    BABEL_DEFAULT_LOCALE = 'ru'
    BABEL_DEFAULT_TIMEZONE = 'UTC+7'

    APP_VERSION = '0.82'

    USER_EMAIL_SENDER_EMAIL = os.environ.get('USER_EMAIL_SENDER_EMAIL') or "nepavel.k@yandex.ru"
    MAIL_SERVER = os.environ.get('MAIL_SERVER')  # 'smtp.yandex.ru'
    MAIL_PORT = os.environ.get('MAIL_PORT')  # 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = FLASK_ENV == 'development'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # 'nepavel.k'
    MAIL_PASSWORD = os.environ.get('YA_NEPAVEL_PWD')

    USER_EMAIL_SENDER_NAME = USER_APP_NAME
    MAIL_DEFAULT_SENDER = '"Кофе-Ин" {}'.format(USER_EMAIL_SENDER_EMAIL)
