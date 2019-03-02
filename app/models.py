# -*- coding: utf-8 -*-
from flask_user import UserMixin

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


class CoffeePrice(db.Model):
    __tablename__ = 'coffee_prices'
    id = db.Column(db.Integer(), primary_key=True)
    date_from = db.Column(db.Date())
    date_to = db.Column(db.Date())
    coffee_type = db.Column(db.Integer, db.ForeignKey('coffee_prices.id'), nullable=False)
    price = db.Column(db.Integer())
    price10 = db.Column(db.Integer())
    price25 = db.Column(db.Integer())
    price50 = db.Column(db.Integer())
