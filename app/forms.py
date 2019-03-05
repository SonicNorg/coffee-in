# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired


class OrderRowForm(FlaskForm):
    id = IntegerField('id', validators=[DataRequired()])
    amount = FloatField('amount', validators=[DataRequired()])
    submit = SubmitField('+')


class AddToPriceForm(FlaskForm):
    coffee = SelectField(validators=[DataRequired()])
    price25 = FloatField(validators=[DataRequired()])
    price50 = FloatField(validators=[DataRequired()])
    submit = SubmitField('Добавить в прайс')

    def set_choices(self, choices):
        self.coffee.choices = choices
