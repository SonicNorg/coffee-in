# -*- coding: utf-8 -*-
from enum import Enum

import sqlalchemy
from flask_user import UserMixin
from sqlalchemy.orm import relationship

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
    coffee_type_id = db.Column(db.Integer, db.ForeignKey('coffee_sorts.id', ondelete='CASCADE'), nullable=False)
    coffee_type = relationship("CoffeeSort", backref="coffee_sorts")
    price_id = db.Column(db.Integer, db.ForeignKey('prices.id', ondelete='CASCADE'), nullable=False)
    price_ref = relationship(Price, backref="prices")
    price = db.Column(db.Integer())
    price10 = db.Column(db.Integer())
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
    state = db.Column(sqlalchemy.types.Enum(States))
    created_at = db.Column(db.DateTime())
    next_step = db.Column(db.Date())
    orders = relationship('IndividualOrder')

    def orders_total(self):
        total = 0
        for order in self.orders:
            for order_row in order.rows:
                total += order_row.amount
        return total


class OfficeOrder(db.Model):
    __tablename__ = 'office_orders'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    buyin_id = db.Column(db.Integer, db.ForeignKey('buyins.id'), nullable=False)
    amount = db.Column(db.Float(), nullable=False)
    __table_args__ = (db.UniqueConstraint(user_id, buyin_id),)


class IndividualOrder(db.Model):
    __tablename__ = 'individual_orders'
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = relationship(User)
    buyin_id = db.Column(db.Integer, db.ForeignKey('buyins.id'), nullable=False)
    buyin = relationship(Buyin)
    rows = relationship("OrderRow", back_populates="order")
    __table_args__ = (db.UniqueConstraint(user_id, buyin_id),)


class OrderRow(db.Model):
    __tablename__ = 'order_rows'
    id = db.Column(db.Integer(), primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('individual_orders.id'))
    order = relationship("IndividualOrder", back_populates="rows")
    coffee_type_id = db.Column(db.Integer, db.ForeignKey('coffee_sorts.id', ondelete='CASCADE'), nullable=False)
    coffee_type = relationship(CoffeeSort)
    amount = db.Column(db.Float())
