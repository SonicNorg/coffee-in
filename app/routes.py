# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, url_for
from flask_login import current_user
from flask_user import login_required

from app import app
from app.forms.log_reg import LoginForm


@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username': 'Norg'}
    return render_template("index.html", title='Home', user=user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Вход в Кофе-Ин', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Login requested for user {}, remember_me={}'.format(
            form.username.data, form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Вход в Кофе-Ин', form=form)
