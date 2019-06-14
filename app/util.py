from datetime import datetime

from flask_login import current_user
from flask_mail import Message
from sqlalchemy import and_, join

from app import db, mail, app
from app.models import Price, OfficeOrderRow, States, Buyin, NewsItem, UserViewedNews, User


def get_price_or_current(price_id=None):
    if not price_id:
        return Price.query \
            .filter(and_(Price.date_from <= datetime.now().date(), datetime.now().date() <= Price.date_to)) \
            .order_by(Price.date_from.desc()) \
            .first()
    else:
        return Price.query.get(price_id)


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


def post_news(header, content):
    db.session.add(NewsItem(header=header, content=content))
    db.session.flush()
    send_mail("emails/news.txt", header, content)


def send_mail(template, subject, content, buyin=None):
    import logging
    logging.info("Sending mails %s to users...", subject)
    if buyin is None:
        users = User.query.filter(User.active).all()
    else:
        # todo отправлять письма только участникам закупки
        users = User.query.filter(User.active).all()

    from flask import render_template
    with mail.connect() as conn:
        for u in users:
            recipients = [(u.username, u.email)]
            try:
                body = render_template(template, states=States, buyin=buyin, content=content, user=u,
                                       app_name=app.config['USER_APP_NAME'])
                msg = Message(subject=subject,
                              sender=(app.config['USER_EMAIL_SENDER_NAME'], app.config['USER_EMAIL_SENDER_EMAIL']),
                              reply_to=(app.config['USER_EMAIL_SENDER_NAME'], app.config['USER_EMAIL_SENDER_EMAIL']),
                              recipients=recipients,
                              body=body)
                conn.send(msg)
                logging.info("Mail %s to %s sent.", subject, msg.recipients)

            except Exception:
                logging.exception("Failed to send mail %s to %s!", subject, recipients)
