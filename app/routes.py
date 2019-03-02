# -*- coding: utf-8 -*-
from flask import render_template, url_for, flash
from flask_login import current_user
from flask_user import login_required
from werkzeug.utils import redirect

from app import app
from app.forms import OrderRowForm


@app.route('/')
@app.route('/index')
@login_required
def index():
    current_buy = {'close_date': '5 марта', 'coffee': 'Бразилия Серрадо',
                   'amount': '26', 'price': '560', 'total': '18 000'}
    my_office_order = {'my_office_order': '1,6 кг'}
    my_own_order = [{'name': 'Бразилия Серрадо', 'description': 'низкая кислотность',
                     'amount': '1', 'price25': '520', 'price50': '490'},
                    {'name': 'Коста-Рика Азалия', 'description': 'низкая кислотность',
                     'amount': '0,5', 'price25': '880', 'price50': '770'}]
    return render_template('index.html', title='Home', user=current_user,
                           current_buy=current_buy, my_office_order=my_office_order, my_own_order=my_own_order)


@app.route('/price')
@login_required
def price():
    date_to = '9 марта'
    coffee_with_prices = [{'name': 'Бразилия Серрадо', 'description': 'низкая кислотность',
                           'price25': '520', 'price50': '490', 'id': '1'},
                          {'name': 'Коста-Рика Азалия', 'description': 'высокая кислотность',
                           'price25': '880', 'price50': '770', 'id': '2'}
                          ]
    form = OrderRowForm()
    return render_template('price.html', coffee_with_prices=coffee_with_prices, date_to=date_to, form=form)


@app.route('/order', methods=['POST'])
@login_required
def order():
    form = OrderRowForm()
    coffee_id = form.id.data
    amount = form.amount.data
    flash("Added to order: {}, {} kg".format(coffee_id, amount), 'success')
    return redirect(url_for('price'))
