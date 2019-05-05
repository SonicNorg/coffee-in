# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from functools import reduce

from flask import render_template, url_for, flash, request
from flask_login import current_user
from flask_user import login_required, roles_required
from sqlalchemy import and_, join, outerjoin, func
from werkzeug.utils import redirect

from app import app, db
from app.forms import OrderRowForm, AddToPriceForm, AddCoffeeForm, CreatePriceForm, BuyinForm, DeleteOrderRowForm, \
    ProceedBuyinForm, AddOfficeOrderForm, AddCupsToOfficeForm, AddNewsItemForm, SetUserPaymentForm
from app.models import CoffeePrice, CoffeeSort, Price, Buyin, States, OrderRow, OfficeOrder, \
    OfficeOrderRow, UserViewedNews, NewsItem, User, UserPayment
from app.util import get_open_price, get_cups_for_current_user, get_current_buyin, get_open_buyin, get_unread_news, \
    get_old_news


@app.route('/')
@app.route('/index')
@app.route('/news')
@login_required
def news():
    unread_news = get_unread_news()
    old_news = get_old_news()
    for news_item in unread_news:
        db.session.add(UserViewedNews(user_id=current_user.id, news_id=news_item.id))
    db.session.commit()
    return render_template('news.html', title='Новости',
                           unread_news=unread_news, old_news=old_news, add_form=AddNewsItemForm())


@app.route('/status')
@login_required
def status():
    delete_row_form = DeleteOrderRowForm()
    current_buyin = get_current_buyin()
    if current_buyin:
        rows = current_buyin.individual_rows_with_prices(current_user.id)
    else:
        rows = []
    set_cups_form = AddCupsToOfficeForm()
    set_cups_form.number.data = get_cups_for_current_user(current_buyin)
    return render_template('status.html', title='Статус закупки', user=current_user,
                           current_buyin=current_buyin, delete_row_form=delete_row_form,
                           set_cups_form=set_cups_form,
                           my_own_order=rows)


@app.route('/price', methods=["GET", "POST"])
@login_required
def price():
    current_price = get_open_price()
    add_office_form = AddOfficeOrderForm()
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
                        flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
        coffee_sorts = CoffeeSort.query.with_entities(CoffeeSort.id, CoffeeSort.name).all()
        add_form.set_choices(coffee_sorts)
        coffee_with_prices = CoffeePrice.query.filter(CoffeePrice.price_id == current_price.id).all()
    else:
        add_form = None
        coffee_with_prices = []
    logging.info("%s", current_price)
    # TODO если нет текущего прайса, то и заказ сделать нельзя!
    form = OrderRowForm()
    return render_template('price.html', title='Прайс и заказ', coffee_with_prices=coffee_with_prices,
                           date_to=current_price.date_to if current_price else None,
                           form=form, add_form=add_form, add_office_form=add_office_form)


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
                    flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
    coffee_sorts = CoffeeSort.query.all()
    return render_template('coffee.html', title='Ассортимент кофе', coffee_sorts=coffee_sorts, add_form=add_form)


@app.route('/officeorder', methods=['POST'])
@roles_required('Босс')
def office_order():
    current_buyin = get_open_buyin()
    add_form = AddOfficeOrderForm()
    coffee_type = CoffeeSort.query.get(add_form.id.data)
    logging.info("Current buyin: %s, coffee_type: %s", current_buyin, coffee_type)
    if current_buyin:
        of_order = OfficeOrder(buyin=current_buyin, coffee_type_id=coffee_type.id)
        db.session.add(of_order)
        db.session.commit()
        flash("Добавлено к офисному заказу: {}".format(of_order.coffee_type.name), 'success')
    return redirect(url_for('price'))


@app.route('/order', methods=['POST'])
@login_required
def order():
    current_buyin = get_open_buyin()
    row_form = OrderRowForm()
    logging.info("Form: coffee = %s, amount = %s", row_form.id.data, row_form.amount.data)

    coffee_type = CoffeeSort.query.get(row_form.id.data)
    amount = row_form.amount.data
    logging.info("Current buyin: %s", current_buyin)
    if current_buyin and row_form.validate():
        logging.info("Form is valid, processing order: coffee = %s, amount = %s", coffee_type, amount)
        order_row = OrderRow.query.filter(and_(OrderRow.user_id == current_user.id,
                                               OrderRow.buyin_id == current_buyin.id,
                                               OrderRow.coffee_type_id == coffee_type.id)).first()
        if order_row:
            order_row.amount = amount
        else:
            order_row = OrderRow(user=current_user, buyin=current_buyin, coffee_type=coffee_type, amount=amount)
        db.session.add(order_row)
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
    current_buyin = get_open_buyin()
    if current_buyin.state != States.OPEN:
        flash('Закупка закрыта, заказ изменить нельзя!', 'danger')
        return redirect(url_for('status'))
    try:
        OrderRow.query.filter_by(id=delete_row_form.id.data).delete()
        db.session.commit()
        flash('Удалено', 'success')
    except Exception:
        logging.exception("Failed to delete order row id=%s", delete_row_form.id.data)
        flash('Кофе уже удален из заказа', 'danger')
    return redirect(url_for('status'))


@app.route('/price/manage', methods=['GET', 'POST'])
@roles_required('Босс')
def manage_prices():
    add_form = CreatePriceForm()
    if request.method == 'POST' and add_form.validate():
        new_price = Price(date_from=add_form.date_from.data, date_to=add_form.date_to.data)
        db.session.add(new_price)
        db.session.commit()
    else:
        for fieldName, errorMessages in add_form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
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
    current_buyin = get_open_buyin()
    logging.info('Current buyin = %s', current_buyin)
    proceed_buyin_form = ProceedBuyinForm()
    set_cups_form = AddCupsToOfficeForm()
    set_cups_form.number.data = get_cups_for_current_user(current_buyin)
    return render_template('buyins.html', title='Управление закупкой', buyin_form=buyin_form,
                           buyins=buyins, current_buyin=current_buyin, set_cups_form=set_cups_form,
                           proceed_buyin_form=proceed_buyin_form)


@app.route('/buyin/proceed', methods=['POST'])
@roles_required('Босс')
def proceed_buyin():
    current_buyin = Buyin.query.get(ProceedBuyinForm().id.data)
    current_buyin.proceed()
    return redirect(url_for('buyin'))


@app.route('/officeorder/my', methods=['POST'])
@login_required
def my_cups():
    current_buyin = get_current_buyin()
    if not current_buyin:
        flash('Нет текущей закупки!', 'danger')
        return redirect(url_for('status'))
    if current_buyin.state != States.OPEN:
        flash('Закупка закрыта, заказ изменить нельзя!', 'danger')
        return redirect(url_for('status'))
    set_cups_form = AddCupsToOfficeForm()
    cups_number = set_cups_form.number.data
    logging.info('Trying to set %s cups for user %s', cups_number, current_user)
    if set_cups_form.validate():
        try:
            office_order_row = OfficeOrderRow.query.filter(and_(
                OfficeOrderRow.buyin_id == current_buyin.id,
                OfficeOrderRow.user_id == current_user.id
            )).first()
            if not office_order_row:
                office_order_row = OfficeOrderRow(buyin=current_buyin, user=current_user, cups_per_day=cups_number)
            else:
                office_order_row.cups_per_day = cups_number
            logging.info('Setting cups, user=%s, buyin=%s, cups=%s', current_user, current_buyin, cups_number)
            db.session.add(office_order_row)
            db.session.commit()
            flash('Ваша дневная офисная норма изменена на {} чашек'.format(cups_number), 'success')
        except Exception:
            logging.exception("Failed to set %s cups, user = %s", cups_number, current_user)
            flash('Ошибка при изменении заказа.', 'danger')
    else:
        for fieldName, errorMessages in set_cups_form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
    return redirect(url_for('status'))


@app.route('/buyin/by_users')
@roles_required('Босс')
def buyin_by_users():
    current_buyin = get_current_buyin()
    individual_subquery = db.session.query(OrderRow.user_id) \
        .filter(OrderRow.buyin_id == current_buyin.id).distinct()
    office_subquery = db.session.query(OfficeOrderRow.user_id) \
        .filter(OfficeOrderRow.buyin_id == current_buyin.id).distinct()
    users_ids = individual_subquery.union(office_subquery).distinct()
    users_costs = []
    total_sum = 0
    users_with_payments_query_result = db.session.query(User, UserPayment) \
        .select_from(outerjoin(User, UserPayment, and_(
        UserPayment.user_id == User.id, UserPayment.buyin_id == current_buyin.id), False)) \
        .filter(User.id.in_(users_ids)) \
        .order_by(User.last_name, User.id).all()
    for user, user_payment in users_with_payments_query_result:
        costs_per_user = current_buyin.costs_per_user(user.id)
        total_sum += costs_per_user[2]
        users_costs.append((user, costs_per_user, user_payment))
    return render_template('buyin_by_users.html', current_buyin=current_buyin, total_sum=total_sum,
                           users_costs=users_costs, set_payment_form=SetUserPaymentForm())


@app.route('/buyin/by_sorts')
@roles_required('Босс')
def buyin_by_sorts():
    # todo refactor all of this shit
    current_buyin = get_current_buyin()
    office_weight_for_each_sort = current_buyin.office_total() / len(current_buyin.office_orders)

    individual_subquery = db.session.query(OrderRow.coffee_type_id) \
        .filter(OrderRow.buyin_id == current_buyin.id).distinct()
    office_subquery = db.session.query(OfficeOrder.coffee_type_id) \
        .filter(OfficeOrder.buyin_id == current_buyin.id).distinct()
    coffee_ids = individual_subquery.union(office_subquery).distinct()
    sorts = dict(map(lambda coffee_sort: (coffee_sort.id, coffee_sort),
                     CoffeeSort.query.filter(CoffeeSort.id.in_(coffee_ids)).all()))
    individual_weights_per_coffee_id = db.session.query(
        OrderRow.coffee_type_id, func.sum(OrderRow.amount).label('total')
    ).filter(and_(OrderRow.buyin_id == current_buyin.id, OrderRow.coffee_type_id.in_(coffee_ids))) \
        .group_by(OrderRow.coffee_type_id)

    individual_ids_weights = dict(individual_weights_per_coffee_id.all())
    office_ids_weights = dict(
        map(lambda of_order: (of_order.coffee_type_id, office_weight_for_each_sort), current_buyin.office_orders))
    total_ids_weights = dict(office_ids_weights)
    for coffee_id, weight in individual_ids_weights.items():
        if coffee_id in office_ids_weights:
            total_ids_weights[coffee_id] = total_ids_weights[coffee_id] + weight
        else:
            total_ids_weights[coffee_id] = weight

    total_sum = 0
    for _, v in total_ids_weights.items():
        total_sum += v
    # individual_ids_weights = list(map(lambda item: (sorts[item[0]], item[1]), individual_ids_weights.items()))
    # office_ids_weights = list(map(lambda item: (sorts[item[0]], item[1]), office_ids_weights.items()))
    # total_ids_weights = list(map(lambda item: (sorts[item[0]], item[1]), total_ids_weights.items()))

    sorts_all_weights = list(
        map(lambda item: (sorts[item[0]], (
            office_ids_weights[item[0]] if item[0] in office_ids_weights else 0,
            individual_ids_weights[item[0]] if item[0] in individual_ids_weights else 0, item[1])),
            total_ids_weights.items()))
    return render_template('buyin_by_sorts.html', current_buyin=current_buyin,
                           sorts_all_weights=sorts_all_weights, total_sum=total_sum)


@app.route('/news/add', methods=['POST'])
@roles_required('Босс')
def add_news_item():
    form = AddNewsItemForm()
    if form.validate():
        db.session.add(NewsItem(header=form.header.data, content=form.content.data))
        db.session.commit()
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
        return redirect(url_for('news'))
    return redirect(url_for('status'))


@app.route('/payment/set', methods=['POST'])
@roles_required('Босс')
def set_payment():
    form = SetUserPaymentForm()
    current_buyin = get_current_buyin()
    if form.validate():
        payment = UserPayment.query.filter(UserPayment.user_id == form.user_id.data,
                                           UserPayment.buyin_id == current_buyin.id).first()
        if not payment:
            payment = UserPayment(user_id=form.user_id.data, buyin_id=current_buyin.id, amount=form.amount.data)
        else:
            payment.amount = form.amount.data
        db.session.add(payment)
        db.session.commit()
        flash('{} оплатил {} руб.'.format(form.user.data, form.amount.data), 'success')
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
    return redirect(url_for('buyin_by_users'))


@app.context_processor
def inject_unread_count():
    return dict(unread_count=len(get_unread_news()) if current_user.is_authenticated else 0)
