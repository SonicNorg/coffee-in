from datetime import datetime

from sqlalchemy import and_

from app.models import Price


def get_open_price():
    return Price.query \
        .filter(and_(Price.date_from <= datetime.now().date(), datetime.now().date() <= Price.date_to)) \
        .order_by(Price.date_from.desc()) \
        .first()
