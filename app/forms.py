# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import FloatField, SubmitField, IntegerField, SelectField, StringField, DateField
from wtforms.validators import DataRequired, NumberRange


class OrderRowForm(FlaskForm):
    id = IntegerField('id', validators=[DataRequired()])
    amount = FloatField('amount', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Беру')


class AddToPriceForm(FlaskForm):
    coffee = SelectField(coerce=int)
    price25 = FloatField(validators=[DataRequired()])
    price50 = FloatField(validators=[DataRequired()])
    submit = SubmitField('Добавить в прайс')

    def set_choices(self, choices):
        self.coffee.choices = choices


class AddCoffeeForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    description = StringField(validators=[DataRequired()])
    submit = SubmitField('Добавить кофе')


class CreatePriceForm(FlaskForm):
    date_from = DateField(validators=[DataRequired()])
    date_to = DateField(validators=[DataRequired()])
    submit = SubmitField('Создать новый прайс')


class BuyinForm(FlaskForm):
    next_step = DateField('Дата закрытия:')
    submit = SubmitField('Создать новую закупку')


class DeleteOrderRowForm(FlaskForm):
    id = IntegerField('id', validators=[DataRequired()])
    submit = SubmitField('Убрать')


class ProceedBuyinForm(FlaskForm):
    id = IntegerField('id')


class AddOfficeOrderForm(FlaskForm):
    id = IntegerField('id', validators=[DataRequired()])
    submit = SubmitField('В офис')


class AddCupsToOfficeForm(FlaskForm):
    number = FloatField('Я пью чашек в день:', validators=[NumberRange(min=0)])
    submit = SubmitField('Сохранить')
