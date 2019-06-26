# -*- coding: utf-8 -*-
import logging
import copy
from datetime import datetime

from flask import render_template, url_for, flash, request
from flask_login import current_user
from flask_user import login_required, roles_required
from sqlalchemy import and_, outerjoin, func
from werkzeug.utils import redirect

from app import app, db
from app.forms import OrderRowForm, AddToPriceForm, AddCoffeeForm, CreatePriceForm, BuyinForm, DeleteByIdForm, \
    ProceedBuyinForm, AddOfficeOrderForm, AddCupsToOfficeForm, AddNewsItemForm, SetUserPaymentForm, EditBuyinForm, \
    DeleteByIdForm, EmptyForm
from app.models import CoffeePrice, CoffeeSort, Price, Buyin, States, OrderRow, OfficeOrder, \
    OfficeOrderRow, UserViewedNews, NewsItem, User, UserPayment, HelpItem
from app.util import get_price_or_current, get_cups_for_current_user, get_current_buyin, get_open_buyin, \
    get_unread_news, \
    get_old_news, post_news

# TODO: split GETs and POSTs to two files


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


@app.route('/')
@app.route('/index')
@app.route('/status')
@login_required
def status():
    delete_row_form = DeleteByIdForm()
    current_buyin = get_current_buyin()
    if current_buyin:
        rows = current_buyin.individual_rows_with_prices(current_user.id)
    else:
        rows = []
    set_cups_form = AddCupsToOfficeForm()
    set_cups_form.number.data = get_cups_for_current_user(current_buyin)
    return render_template('status.html', title='Мой заказ', user=current_user,
                           current_buyin=current_buyin, delete_row_form=delete_row_form,
                           set_cups_form=set_cups_form, states=States,
                           payed=(0 if not current_buyin else UserPayment.query.filter(and_(
                               UserPayment.buyin_id == current_buyin.id, UserPayment.user_id == current_user.id)).first()),
                           my_own_order=rows)


@app.route('/price', methods=["GET", "POST"])
@login_required
def price():
    logging.info("/price")
    current_price = get_price_or_current()
    add_office_form = AddOfficeOrderForm()
    if current_price:
        add_form = AddToPriceForm()
        coffee_type_id = add_form.coffee.data
        coffee_sorts = CoffeeSort.query.with_entities(CoffeeSort.id, CoffeeSort.name).all()
        add_form.set_choices(coffee_sorts)
        coffee_sorts = CoffeeSort.query.with_entities(CoffeeSort.id, CoffeeSort.name).all()
        add_form.set_choices(coffee_sorts)
        coffee_with_prices = CoffeePrice.query.filter(CoffeePrice.price_id == current_price.id).all()
        if request.method == 'POST':
            if add_form.validate():
                prev_price = CoffeePrice.query.filter(and_(CoffeePrice.coffee_type_id == coffee_type_id,
                                                           CoffeePrice.price_id == current_price.id)).first()
                if prev_price:
                    prev_price.price25 = add_form.price25.data
                    prev_price.price50 = add_form.price50.data
                else:
                    prev_price = CoffeePrice(coffee_type_id=coffee_type_id, price_id=current_price.id,
                                             price25=add_form.price25.data, price50=add_form.price50.data)
                db.session.add(prev_price)
                db.session.commit()
                return redirect(url_for('price'))
            else:
                for fieldName, errorMessages in add_form.errors.items():
                    for err in errorMessages:
                        logging.error("Error in %s: %s", fieldName, err)
                        flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
    else:
        add_form = None
        coffee_with_prices = []
    logging.info("Current price: %s", current_price)
    # TODO если нет текущего прайса, то и заказ сделать нельзя!
    form = OrderRowForm()
    return render_template('price.html', title='Выбрать кофе', coffee_with_prices=coffee_with_prices,
                           date_to=current_price.date_to if current_price else None,
                           form=form, add_form=add_form, add_office_form=add_office_form)


@app.route('/price/delete', methods=["POST"])
@roles_required('Босс')
def delete_price():
    form = DeleteByIdForm()
    if get_open_buyin() and form.validate():
        CoffeePrice.query.filter(CoffeePrice.id == form.id.data).delete()
        db.session.commit()
        flash('Кофе удален из прайса', 'success')
    else:
        flash('Нет открытой закупки!', 'error')
    return redirect(url_for('price'))


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
            return redirect(url_for('coffee'))
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
    if not current_buyin:
        flash("Закупка не открыта, нельзя добавить в заказ: {}, {} kg".format(coffee_type.name, amount), 'danger')
        return redirect(url_for('price'))
    if row_form.validate():
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
        flash("Некорректный заказ!: {}, {} kg".format(coffee_type.name, amount), 'danger')
    return redirect(url_for('price'))


@app.route('/order/delete', methods=['POST'])
@login_required
def delete_order_row():
    delete_row_form = DeleteByIdForm()
    logging.debug("Try to delete row id=%s", delete_row_form.id.data)
    current_buyin = get_open_buyin()
    if not current_buyin:
        flash('Закупка закрыта, заказ изменить нельзя!', 'danger')
        return redirect(url_for('status'))
    try:
        OrderRow.query.filter(OrderRow.id == delete_row_form.id.data).delete()
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
    duplicate = EmptyForm()
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
    return render_template('manage_prices.html', add_form=add_form, prices=prices, duplicate=duplicate)


@app.route('/price/duplicate', methods=['POST'])
@roles_required('Босс')
def duplicate_price():
    current = get_price_or_current()
    current_buyin = get_current_buyin()
    logging.info("Entered duplicate_price! Current price: %s", current)
    if current and (not current_buyin or
                    current_buyin.state in [States.PLANNING, States.OPEN, States.AWAITING, States.FINISHED]):
        old_price = Price.query.filter(Price.id != current.id).order_by(Price.id.desc()).first()
        logging.info("Old price: %s", old_price)
        if old_price:
            logging.info("Old prices: %s", old_price.coffee_prices)
            CoffeePrice.query.filter(CoffeePrice.price_id == current.id).delete()
            db.session.flush()
            db.session.refresh(current)
            for coffee_price in old_price.coffee_prices:
                logging.info("ENTERED LOOP: Current prices: %s", current.coffee_prices)
                logging.info("coffee_price: %s", coffee_price)
                logging.info("Current prices: %s", current.coffee_prices)
                current.coffee_prices.append(CoffeePrice(
                    id=None,
                    coffee_type_id=coffee_price.coffee_type_id,
                    price_id=current.id,
                    price25=coffee_price.price25,
                    price50=coffee_price.price50
                ))
                logging.info("Current prices: %s", current.coffee_prices)
            logging.info("LOOP FINISHED: Current prices: %s", current.coffee_prices)
            db.session.commit()
            flash('Прайс заполнен по предыдущему. Отличные цены можно просто внести, не удаляя, они заменят старые.',
                  'success')
            logging.info("SUCCESS: Current prices: %s", current.coffee_prices)
        return redirect(url_for('price'))
    else:
        flash('Нет текущего прайса, или закупка закрыта для изменений!', 'error')
    return redirect(url_for('manage_prices'))


@app.route('/buyin/all', methods=['GET', 'POST'])
@roles_required('Босс')
def buyin():
    buyin_form = BuyinForm()
    delete_office_order_form = DeleteByIdForm()
    if request.method == 'POST':
        new_buyin = Buyin(state=States.OPEN, next_step=buyin_form.next_step.data, created_at=datetime.now())
        post_news("Создана новая закупка!", "Статус новой закупки - {}".format(new_buyin.state.value[0]))
        db.session.add(new_buyin)
        db.session.commit()
    buyins = Buyin.query.order_by(Buyin.created_at.desc()).all()
    current_buyin = get_current_buyin()
    edit_buyin_form = EditBuyinForm(days=current_buyin.days,
                                    next_date=current_buyin.next_step,
                                    shipment=current_buyin.shipment_price) if current_buyin else EditBuyinForm()
    logging.info('Current buyin = %s', current_buyin)
    proceed_buyin_form = ProceedBuyinForm()
    set_cups_form = AddCupsToOfficeForm()
    set_cups_form.number.data = get_cups_for_current_user(current_buyin)
    return render_template('buyins.html', title='Управление закупкой', buyin_form=buyin_form,
                           buyins=buyins, current_buyin=current_buyin, set_cups_form=set_cups_form,
                           proceed_buyin_form=proceed_buyin_form, edit_buyin_form=edit_buyin_form,
                           delete_office_order_form=delete_office_order_form)


@app.route('/buyin/proceed', methods=['POST'])
@roles_required('Босс')
def proceed_buyin():
    form = ProceedBuyinForm()
    if form.validate():
        current_buyin = Buyin.query.get(form.id.data)
        if not current_buyin.proceed(form.next_date.data):
            logging.error("Failed to proceed buyin")
            flash('Ошибка при изменении статуса закупки: возможно, отсутствует текущий прайс!', 'error')
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
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
    if not current_buyin:
        return render_template('buyin_by_users.html', current_buyin=current_buyin, total_sum=0,
                               users_costs=[], set_payment_form=SetUserPaymentForm())
    individual_subquery = db.session.query(OrderRow.user_id) \
        .filter(OrderRow.buyin_id == current_buyin.id).distinct()
    office_subquery = db.session.query(OfficeOrderRow.user_id) \
        .filter(OfficeOrderRow.buyin_id == current_buyin.id).distinct()
    users_ids = individual_subquery.union(office_subquery).distinct()
    users_costs = []
    total_sum = 0
    users_with_payments_query_result = db.session.query(User, UserPayment) \
        .select_from(outerjoin(User, UserPayment, and_(UserPayment.user_id == User.id,
                                                       UserPayment.buyin_id == current_buyin.id), False)) \
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
    if not current_buyin:
        return render_template('buyin_by_sorts.html', current_buyin=current_buyin,
                               sorts_all_weights=[], total_sum=0)
    sorts_all_weights, total_sum = current_buyin.sorts_all_weights()
    return render_template('buyin_by_sorts.html', current_buyin=current_buyin,
                           sorts_all_weights=sorts_all_weights, total_sum=total_sum)


@app.route('/news/add', methods=['POST'])
@roles_required('Босс')
def add_news_item():
    form = AddNewsItemForm()
    if form.validate():
        post_news(form.header.data, form.content.data)
        db.session.commit()
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
        return redirect(url_for('news'))
    return redirect(url_for('status'))


@app.route('/help/add', methods=['POST'])
@roles_required('Босс')
def add_help_item():
    form = AddNewsItemForm()
    if form.validate():
        db.session.add(HelpItem(question=form.header.data, answer=form.content.data))
        db.session.commit()
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
        return redirect(url_for('news'))
    return redirect(url_for('helps'))


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


@app.route('/buyin/edit', methods=['POST'])
@roles_required('Босс')
def edit_buyin():
    form = EditBuyinForm()
    current_buyin = get_current_buyin()
    if form.validate():
        current_buyin.days = form.days.data
        current_buyin.next_date = form.next_date.data
        current_buyin.shipment_price = form.shipment.data
        db.session.add(current_buyin)
        db.session.commit()
        flash('Текущая закупка успешно изменена.', 'success')
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                logging.error("Error in %s: %s", fieldName, err)
                flash('Ошибка в {}: {}'.format(fieldName, err), 'error')
    return redirect(url_for('buyin'))


@app.route('/officeorder/delete', methods=['POST'])
@roles_required('Босс')
def delete_office_order():
    delete_office_order_form = DeleteByIdForm()
    if get_open_buyin() and delete_office_order_form.validate():
        OfficeOrder.query.filter(OfficeOrder.id == delete_office_order_form.id.data).delete()
        db.session.commit()
        flash('Кофе удален из офиса', 'success')
    else:
        flash('Нет открытой закупки!', 'error')
    return redirect(url_for('buyin'))


@app.route('/help')
@login_required
def helps():
    form = AddNewsItemForm()
    return render_template('help.html', add_form=form, help_items=HelpItem.query.order_by(HelpItem.id).all())


@app.route('/all_order')
@login_required
def all_order():
    current_buyin = get_current_buyin()
    if not current_buyin:
        return render_template('all_order.html', current_buyin=current_buyin,
                               sorts_all_weights=[])
    sorts_all_weights, total_sum = current_buyin.sorts_all_weights()
    return render_template('all_order.html', current_buyin=current_buyin, sorts_all_weights=sorts_all_weights)


@app.context_processor
def inject_unread_count():
    return dict(unread_count=len(get_unread_news()) if current_user.is_authenticated else 0)


@app.context_processor
def inject_now():
    return dict(now=datetime.now, today=datetime.today)
