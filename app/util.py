from datetime import datetime

from flask_login import current_user
from sqlalchemy import and_, outerjoin, join

from app import db
from app.models import Price, OfficeOrderRow, States, Buyin, NewsItem, UserViewedNews


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


#
# def get_unread_news():
#     return [None, None]
#
#
# def get_old_news():
#     return [None, None]


def get_unread_news():
    subquery = db.session.query(UserViewedNews.news_id).filter(UserViewedNews.user_id == current_user.id)
    return NewsItem.query.filter(NewsItem.id.notin_(subquery)) \
        .order_by(NewsItem.timestamp.desc()) \
        .all()


def get_old_news():
    return db.session.query(NewsItem, UserViewedNews).select_from(join(NewsItem, UserViewedNews, and_(
        UserViewedNews.user_id == current_user.id, NewsItem.id == UserViewedNews.news_id))) \
        .order_by(NewsItem.timestamp.desc()) \
        .all()
