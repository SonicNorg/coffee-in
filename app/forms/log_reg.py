# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email

from app.service.validators import CertainDomains


class LoginForm(FlaskForm):
    username = StringField('Почта', validators=[DataRequired(message="Это поле обязательно."),
                                                Email(message="Неверный e-mail"), CertainDomains()])
    password = PasswordField('Пароль', validators=[DataRequired(message="Это поле обязательно.")])
    submit = SubmitField('Войти в Кофе-Ин!')
