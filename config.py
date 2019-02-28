import os


class Config(object):
    SECRET_KEY = os.environ.get('SEC_COFFEE_KEY') or 'you-will-never-guess'
