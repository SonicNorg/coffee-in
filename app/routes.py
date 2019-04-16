# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from flask import render_template, url_for, flash, request
from flask_login import current_user
from flask_user import login_required, roles_required
from sqlalchemy import and_
from werkzeug.utils import redirect

from app import app, db
from app.dtos import IndividualOrderWithPrices
from app.forms import OrderRowForm, AddToPriceForm, AddCoffeeForm, CreatePriceForm, BuyinForm, DeleteOrderRowForm, \
    ProceedBuyinForm
from app.models import CoffeePrice, CoffeeSort, Price, IndividualOrder, Buyin, States, OrderRow
from app.util import get_open_price


@app.route('/')
@app.route('/index')
@login_required
def index():
    current_buy = {'close_date': '5 марта', 'coffee': 'Бразилия Серрадо',
                   'amount': '26', 'price': '560', 'total': '18 000'}
    delete_row_form = DeleteOrderRowForm()
    my_office_order = {'my_office_order': '1,6 кг'}
    open_buyin = Buyin.query.filter(Buyin.state == States.OPEN).order_by(Buyin.created_at.desc()).first()
    if open_buyin:
        my_own_order = IndividualOrder.query.filter(and_(IndividualOrder.buyin_id == open_buyin.id,
                                                         IndividualOrder.user_id == current_user.id)).first()
    else:
        my_own_order = None
    return render_template('index.html', title='Home', user=current_user, current_buyin=open_buyin,
                           my_office_order=my_office_order, delete_row_form=delete_row_form,
                           my_own_order=None if not my_own_order else IndividualOrderWithPrices(my_own_order))


@app.route('/price', methods=["GET", "POST"])
@login_required
def price():
    current_price = get_open_price()
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
    # TODO если нет текущего прайса, то и заказ сделать нельзя!
    form = OrderRowForm()
    return render_template('price.html', coffee_with_prices=coffee_with_prices,
                           date_to=current_price.date_to if current_price else None,
                           form=form, add_form=add_form)


@app.route('/coffee', methods=["GET", "POST"])
@login_required
def coffee():
    add_form = AddCoffeeForm()
    logging.info("/coffee")
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
    current_buyin = Buyin.query.filter(Buyin.state == States.OPEN).first()
    row_form = OrderRowForm()
    logging.info("Form: coffee = %s, amount = %s", row_form.id.data, row_form.amount.data)

    coffee_type = CoffeeSort.query.get(row_form.id.data)
    amount = row_form.amount.data
    logging.info("Current buyin: %s", current_buyin)
    if current_buyin and row_form.validate():
        logging.info("Form is valid, processing order: coffee = %s, amount = %s", coffee_type, amount)
        user_order = IndividualOrder.query.filter(and_(IndividualOrder.user_id == current_user.id,
                                                       IndividualOrder.buyin_id == current_buyin.id)).first()
        if not user_order:
            user_order = IndividualOrder(user=current_user,
                                         buyin=current_buyin)
            db.session.add(user_order)
            db.session.flush()
            db.session.refresh(user_order)
            db.session.commit()
            logging.info("Saving order, id=%s", user_order.id)
        new_order_row = OrderRow(order=user_order, coffee_type=coffee_type, amount=amount)
        db.session.add(new_order_row)
        db.session.commit()
        flash("Добавлено в заказ: {}, {} kg".format(coffee_type.name, amount), 'success')
    else:
        logging.info("Form is invalid, or current buyin is not found! coffee = %s, amount = %s", coffee_type.name,
                     amount)
        flash("Нет текущей закупки, или некорректный заказ!: {}, {} kg".format(coffee_type.name, amount), 'danger')
    return redirect(url_for('price'))


@app.route('/order/delete', methods=['POST'])
@login_required
def delete_order_row():
    delete_row_form = DeleteOrderRowForm()
    logging.debug("Try to delete row id=%s", delete_row_form.id.data)
    try:
        OrderRow.query.filter_by(id=delete_row_form.id.data).delete()
        db.session.commit()
        flash('Удалено', 'success')
    except Exception:
        logging.exception("Failed to delete order row id=%s", delete_row_form.id.data)
        flash('Кофе уже удален из заказа', 'danger')
    return redirect(url_for('index'))


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


@app.route('/buyin/all', methods=['GET', 'POST'])
@roles_required('Босс')
def buyin():
    buyin_form = BuyinForm()
    if request.method == 'POST':
        new_buyin = Buyin(state=States.OPEN, next_step=buyin_form.next_step.data, created_at=datetime.now())
        db.session.add(new_buyin)
        db.session.commit()
    buyins = Buyin.query.order_by(Buyin.created_at.desc()).all()
    open_buyin = Buyin.query.filter(Buyin.state == States.OPEN).order_by(Buyin.created_at.desc()).first()
    proceed_buyin_form = ProceedBuyinForm()
    return render_template('buyins.html', buyin_form=buyin_form, buyins=buyins, current_buyin=open_buyin,
                           proceed_buyin_form=proceed_buyin_form)


@app.route('/buyin/proceed', methods=['POST'])
@roles_required('Босс')
def proceed_buyin():
    current_buyin = Buyin.query.get(ProceedBuyinForm().id.data)
    if current_buyin.state != States.FINISHED:
        current_buyin.state = States[current_buyin.state.ordinal() + 1]
        db.session.add(current_buyin)
        db.session.commit()
    return redirect(url_for('buyin'))

