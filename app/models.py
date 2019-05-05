# -*- coding: utf-8 -*-
from datetime import datetime
from enum import Enum

import sqlalchemy
from flask_user import UserMixin
from sqlalchemy import and_, func
from sqlalchemy.orm import relationship, join

from app import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120, collation='NOCASE'), index=True, unique=True)
    email = db.Column(db.String(120, collation='NOCASE'), index=True, unique=True)
    password = db.Column(db.String(128))
    active = db.Column(db.Boolean())
    email_confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary='user_roles')

    first_name = db.Column(db.String(50), nullable=False, default='Аноним')
    last_name = db.Column(db.String(60), nullable=False, default='Анонимов')

    def __repr__(self):
        return '<User {} - {}>'.format(self.username, self.email)


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

    def __repr__(self):
        return '<Role {}>'.format(self.name)


# Связь юзеров с ролями
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id', ondelete='CASCADE'))


class CoffeeSort(db.Model):
    __tablename__ = 'coffee_sorts'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(150), unique=True)
    description = db.Column(db.String(250))

    def __repr__(self) -> str:
        return 'Coffee sort id={}, name={}, description={}'.format(self.id, self.name, self.description)


class Price(db.Model):
    __tablename__ = 'prices'
    id = db.Column(db.Integer(), primary_key=True)
    date_from = db.Column(db.Date(), nullable=False)
    date_to = db.Column(db.Date(), nullable=False)


class CoffeePrice(db.Model):
    __tablename__ = 'coffee_prices'
    id = db.Column(db.Integer(), primary_key=True)
    coffee_type_id = db.Column(db.Integer, db.ForeignKey('coffee_sorts.id', ondelete='CASCADE'), nullable=False,
                               index=True)
    coffee_type = relationship("CoffeeSort", backref="coffee_sorts")
    price_id = db.Column(db.Integer, db.ForeignKey('prices.id', ondelete='CASCADE'), nullable=False)
    price_ref = relationship(Price, backref="prices")
    price25 = db.Column(db.Integer())
    price50 = db.Column(db.Integer())
    __table_args__ = (db.UniqueConstraint(coffee_type_id, price_id),)


class States(Enum):
    PLANNING = ('Планируется', 'Откроется', 'Открыть')
    OPEN = ('Открыта', 'Сбор денег начнется', 'Закрыть и начать сбор денег')
    FIXED = ('Зафиксирована, сбор денег', 'Заказ отправится', 'Оплатить')
    ORDERED = ('Заказ отправлен и оплачен', 'Кофе приедет', 'Подтвердить получение')
    FINISHED = ('Закончена', 'Закончена', 'Закупка завершена')


class Buyin(db.Model):
    __tablename__ = 'buyins'
    id = db.Column(db.Integer(), primary_key=True)
    state = db.Column(sqlalchemy.types.Enum(States), index=True)
    created_at = db.Column(db.DateTime())
    next_step = db.Column(db.Date())
    days = db.Column(db.Integer(), nullable=False, default=25)
    shipment_price = db.Column(db.Integer(), nullable=False, default=900)
    order_rows = relationship('OrderRow', back_populates='buyin')
    office_orders = relationship('OfficeOrder')
    office_order_rows = relationship('OfficeOrderRow', back_populates='buyin')

    def orders_total(self, user_id=None):
        return self.office_total(user_id) + self.individual_total(user_id)

    def individual_total(self, user_id=None):
        total = 0
        for order_row in self.order_rows:
            if not user_id or order_row.user_id == user_id:
                total += order_row.amount
        return total

    def office_total(self, user_id=None):
        total = 0
        for office_order_row in self.office_order_rows:
            if not user_id or office_order_row.user_id == user_id:
                total += (office_order_row.cups_per_day * self.days * 0.008)
        return total

    def total_cost_without_shipment(self):
        total_weight = self.orders_total()
        of_total = self.office_total()
        each_sort_weight = of_total / len(self.office_orders) if self.office_orders else 0
        cost = 0
        for order_row, coffee_price in self.individual_rows_with_prices():
            cost += order_row.amount * (coffee_price.price25 if total_weight < 50 else coffee_price.price50)

        for office_order, coffee_price in self.office_coffee_prices():
            cost += (each_sort_weight * (coffee_price.price25 if total_weight < 50
                                         else coffee_price.price50))
        return cost

    def office_cost(self):
        total_weight = self.orders_total()
        of_total = self.office_total()
        each_sort_weight = of_total / len(self.office_orders) if self.office_orders else 0
        cost = 0
        for office_order, coffee_price in self.office_coffee_prices():
            cost += (each_sort_weight * (coffee_price.price25 if total_weight < 50
                                         else coffee_price.price50))
        return cost

    def individual_cost(self, user_id=None):
        total_weight = self.orders_total()
        cost = 0
        for order_row, coffee_price in self.individual_rows_with_prices():
            if not user_id or order_row.user_id == user_id:
                cost += order_row.amount * (coffee_price.price25 if total_weight < 50 else coffee_price.price50)

        return cost

    def office_coffee_prices(self):
        from app.util import get_open_price
        cur_price = get_open_price()
        rows = []
        if cur_price:
            rows = db.session.query(OfficeOrder, CoffeePrice).select_from(
                join(OfficeOrder, CoffeePrice,
                     and_(OfficeOrder.coffee_type_id == CoffeePrice.coffee_type_id,
                          CoffeePrice.price_id == cur_price.id))
            ).filter(OfficeOrder.buyin_id == self.id).order_by(OfficeOrder.id).all()
        return rows

    def individual_rows_with_prices(self, user_id=None):
        from app.util import get_open_price
        cur_price = get_open_price()
        rows = []
        if cur_price:
            query = db.session.query(OrderRow, CoffeePrice).select_from(
                join(OrderRow, CoffeePrice,
                     and_(OrderRow.coffee_type_id == CoffeePrice.coffee_type_id,
                          CoffeePrice.price_id == cur_price.id))
            ).filter(OrderRow.buyin_id == self.id).order_by(OrderRow.id)
            rows = query.filter(OrderRow.user_id == user_id).all() if user_id else query.all()
        return rows

    def total_cups_per_day(self):
        query = db.session.query(
            func.sum(OfficeOrderRow.cups_per_day).label('cups_per_day')
        ).filter(OfficeOrderRow.buyin_id == self.id)
        return query.first().cups_per_day

    def costs_per_user(self, user_id):
        of_cost = self.office_cost()
        total_cups = self.total_cups_per_day()
        user_office_order_rows = OfficeOrderRow.query.filter(
            and_(OfficeOrderRow.buyin_id == self.id, OfficeOrderRow.user_id == user_id)).first()
        user_cups = user_office_order_rows.cups_per_day if user_office_order_rows else 0
        office_cost = (of_cost / total_cups * user_cups) if total_cups and total_cups > 0 else 0

        total_cost = self.individual_cost(user_id) + office_cost + \
                     (self.shipment_price / self.orders_total() * self.orders_total(user_id)
                      if self.orders_total() > 0 else 0)
        return office_cost, self.individual_cost(user_id), total_cost

    def proceed(self):
        # todo check state
        # todo check if not round?
        # todo persist
        # todo post news via util method
        # db.session.add(self)
        # db.session.commit()
        self.state = States.OPEN


class OrderRow(db.Model):
    __tablename__ = 'order_rows'
    id = db.Column(db.Integer(), primary_key=True)
    buyin_id = db.Column(db.Integer, db.ForeignKey('buyins.id'), nullable=False, index=True)
    buyin = relationship(Buyin, back_populates='order_rows')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = relationship(User)
    coffee_type_id = db.Column(db.Integer, db.ForeignKey('coffee_sorts.id', ondelete='CASCADE'), nullable=False,
                               index=True)
    coffee_type = relationship(CoffeeSort)
    amount = db.Column(db.Float())
    __table_args__ = (db.UniqueConstraint(buyin_id, user_id, coffee_type_id),)


class OfficeOrder(db.Model):
    __tablename__ = 'office_orders'
    id = db.Column(db.Integer(), primary_key=True)
    buyin_id = db.Column(db.Integer, db.ForeignKey('buyins.id'), nullable=False, index=True)
    buyin = relationship(Buyin)
    coffee_type_id = db.Column(db.Integer, db.ForeignKey('coffee_sorts.id', ondelete='CASCADE'), nullable=False,
                               index=True)
    coffee_type = relationship(CoffeeSort)
    __table_args__ = (db.UniqueConstraint(buyin_id, coffee_type_id),)


class OfficeOrderRow(db.Model):
    __tablename__ = 'office_rows'
    id = db.Column(db.Integer(), primary_key=True)
    buyin_id = db.Column(db.Integer, db.ForeignKey('buyins.id'), nullable=False, index=True)
    buyin = relationship(Buyin, back_populates='office_order_rows')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user = relationship(User)
    cups_per_day = db.Column(db.Float())
    __table_args__ = (db.UniqueConstraint(buyin_id, user_id),)


class NewsItem(db.Model):
    __tablename__ = 'news'
    id = db.Column(db.Integer(), primary_key=True)
    timestamp = db.Column(db.DateTime(), default=datetime.now)
    header = db.Column(db.String(120, collation='NOCASE'))
    content = db.Column(db.String(1024, collation='NOCASE'))


class UserViewedNews(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    news_id = db.Column(db.Integer, db.ForeignKey('news.id'), nullable=False, index=True)
    viewed_at = db.Column(db.DateTime(), default=datetime.now)


class UserPayment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    buyin_id = db.Column(db.Integer, db.ForeignKey('buyins.id'), nullable=False, index=True)
    amount = db.Column(db.Float(), nullable=False)
    __table_args__ = (db.UniqueConstraint(buyin_id, user_id),)
