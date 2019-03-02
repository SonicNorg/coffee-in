# -*- coding: utf-8 -*-
import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get('SEC_COFFEE_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app-test.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_APP_NAME = 'Кофе-Ин'
    BABEL_DEFAULT_LOCALE = 'ru'
    BABEL_DEFAULT_TIMEZONE = 'UTC+4'

    APP_VERSION = '0.1a'

    MAIL_SERVER = 'smtp.yandex.ru'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_DEBUG = True
    MAIL_USERNAME = 'nepavel.k'
    MAIL_PASSWORD = os.environ.get('YA_NEPAVEL_PWD')
    MAIL_DEFAULT_SENDER = '"Кофе-Ин" nepavel.k@yandex.ru'

    USER_EMAIL_SENDER_EMAIL = "nepavel.k@yandex.ru"
    USER_EMAIL_SENDER_NAME = USER_APP_NAME
