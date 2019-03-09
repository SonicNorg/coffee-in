# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from flask import render_template, url_for, flash, request
from flask_login import current_user
from flask_user import login_required, roles_required
from sqlalchemy import and_
from werkzeug.utils import redirect

from app import app, db
from app.forms import OrderRowForm, AddToPriceForm, AddCoffeeForm, CreatePriceForm
from app.models import CoffeePrice, CoffeeSort, Price


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


@app.route('/price', methods=["GET", "POST"])
@login_required
def price():
    current_price = Price.query\
        .order_by(Price.date_to.desc())\
        .filter(and_(Price.date_from <= datetime.now().date(), datetime.now().date() <= Price.date_to))\
        .first()
    if current_price:
        add_form = AddToPriceForm()
        coffee_type_id = add_form.coffee.data
        coffee_sorts = CoffeeSort.query.with_entities(CoffeeSort.id, CoffeeSort.name).all()
        add_form.set_choices(coffee_sorts)
        logging.info("/price")
        if request.method == 'POST':
            if add_form.validate():
                new_price = CoffeePrice(coffee_type_id=coffee_type_id, price_id=current_price.id,
                                        price25=add_form.price25.data, price50=add_form.price50.data)
                db.session.add(new_price)
                db.session.commit()
            else:
                for fieldName, errorMessages in add_form.errors.items():
                    for err in errorMessages:
                        logging.error("Error in %s: %s", fieldName, err)
                flash('Invalid data', 'error')
        coffee_sorts = CoffeeSort.query.with_entities(CoffeeSort.id, CoffeeSort.name).all()
        add_form.set_choices(coffee_sorts)
        coffee_with_prices = CoffeePrice.query.filter(CoffeePrice.price_id == current_price.id).all()
    else:
        add_form = None
        coffee_with_prices = []
    logging.info("%s", current_price)
    form = OrderRowForm()
    return render_template('price.html', coffee_with_prices=coffee_with_prices,
                           date_to=current_price.date_to if current_price else None,
                           form=form, add_form=add_form)


@app.route('/coffee', methods=["GET", "POST"])
@login_required
def coffee():
    add_form = AddCoffeeForm()
    logging.info("/price")
    if request.method == 'POST':
        if add_form.validate():
            new_sort = CoffeeSort(name=add_form.name.data,
                                  description=add_form.description.data)
            db.session.add(new_sort)
            db.session.commit()
        else:
            for fieldName, errorMessages in add_form.errors.items():
                for err in errorMessages:
                    logging.error("Error in %s: %s", fieldName, err)
            flash('Invalid data', 'error')
    coffee_sorts = CoffeeSort.query.all()
    return render_template('coffee.html', coffee_sorts=coffee_sorts, add_form=add_form)


@app.route('/order', methods=['POST'])
@login_required
def order():
    form = OrderRowForm()
    coffee_id = form.id.data
    amount = form.amount.data
    flash("Added to order: {}, {} kg".format(coffee_id, amount), 'success')
    return redirect(url_for('price'))


@app.route('/price/manage', methods=['GET', 'POST'])
@roles_required('Босс')
def manage_prices():
    add_form = CreatePriceForm()
    if request.method == 'POST' and add_form.validate():
        new_price = Price(date_from=add_form.date_from.data, date_to=add_form.date_to.data)
        db.session.add(new_price)
        db.session.commit()
    prices = Price.query.order_by(Price.date_to.desc()).all()
    return render_template('manage_prices.html', add_form=add_form, prices=prices)
