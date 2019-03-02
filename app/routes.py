# -*- coding: utf-8 -*-
import flask_user
from flask import render_template
from flask_login import current_user
from flask_user import login_required

from app import app


@app.route('/')
@app.route('/index')
@login_required
def index():
    flask_user.current_user
    return render_template("index.html", title='Home', user=current_user)
