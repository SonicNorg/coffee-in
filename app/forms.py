# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, IntegerField
from wtforms.validators import DataRequired


class OrderRowForm(FlaskForm):
    id = IntegerField('id', validators=[DataRequired()])
    amount = FloatField('amount', validators=[DataRequired()])
    submit = SubmitField('+')
