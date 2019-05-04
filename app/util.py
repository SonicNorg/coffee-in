from datetime import datetime

from flask_login import current_user
from sqlalchemy import and_
from wtforms import ValidationError

from app.models import Price, OfficeOrderRow, States, Buyin


def get_open_price():
    return Price.query \
        .filter(and_(Price.date_from <= datetime.now().date(), datetime.now().date() <= Price.date_to)) \
        .order_by(Price.date_from.desc()) \
        .first()


def get_current_buyin():
    return Buyin.query.filter(Buyin.state != States.FINISHED).order_by(Buyin.created_at.desc()).first()


def get_open_buyin():
    return Buyin.query.filter(Buyin.state == States.OPEN).order_by(Buyin.created_at.desc()).first()


def get_cups_for_current_user(current_buyin):
    if not current_buyin:
        current_buyin = get_current_buyin()
    if not current_buyin:
        return 0
    office_order_row = OfficeOrderRow.query.filter(and_(
        OfficeOrderRow.buyin_id == current_buyin.id,
        OfficeOrderRow.user_id == current_user.id
    )).first()
    cups = 0
    if office_order_row:
        cups = office_order_row.cups_per_day
    return cups
