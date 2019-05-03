from sqlalchemy.orm import join

from app import db

from app.models import OrderRow, CoffeePrice, OfficeOrderRow, OfficeOrder
from app.util import get_open_price


def enrich_buyin(buyin):
    buyin.orders_with_prices = individual_orders_with_prices(buyin.id)
    buyin.office_orders_with_prices = office_orders_with_prices(buyin.id)


def office_orders_with_prices(buyin_id):
    cur_price = get_open_price()
    rows = None
    if cur_price:
        rows = db.session.query(OfficeOrderRow, CoffeePrice).select_from(
            join(
                join(OfficeOrder, CoffeePrice, OfficeOrder.coffee_type_id == CoffeePrice.coffee_type_id),
                OfficeOrderRow,
                OfficeOrderRow.order_id == OfficeOrder.id
            )
        ).filter(OfficeOrder.buyin_id == buyin_id).order_by(OfficeOrderRow.user_id).all()
    return rows


def individual_orders_with_prices(buyin_id):
    cur_price = get_open_price()
    rows = None
    # if cur_price:
    #     rows = db.session.query(OrderRow, CoffeePrice).select_from(
    #         join(OrderRow, CoffeePrice, OrderRow.coffee_type_id == CoffeePrice.coffee_type_id)) \
    #         .filter(OrderRow.id.in_([row.id for row in order.rows])).all()
    return rows


class IndividualOrderWithPrices:

    def __init__(self, order) -> None:
        self.order = order
        cur_price = get_open_price()
        if cur_price and order and order.rows:
            self.rows = db.session.query(OrderRow, CoffeePrice).select_from(
                join(OrderRow, CoffeePrice, OrderRow.coffee_type_id == CoffeePrice.coffee_type_id)) \
                .filter(OrderRow.id.in_([row.id for row in order.rows])).all()
            self.total25 = self.calc_total('price25')
            self.total50 = self.calc_total('price50')

        else:
            self.rows = []
            self.total25 = self.calc_total('price25')
            self.total50 = self.calc_total('price50')

    def calc_total(self, price_type):
        total = 0
        for row in self.rows:
            total += getattr(row[1], price_type) * row[0].amount

        return total


class OfficeOrderWithPrices:

    def __init__(self, order) -> None:
        self.order = order
        cur_price = get_open_price()
        if cur_price and order and order.rows:
            self.rows = db.session.query(OfficeOrderRow, CoffeePrice).select_from(
                join(
                    join(OfficeOrder, CoffeePrice, OfficeOrder.coffee_type_id == CoffeePrice.coffee_type_id),
                    OfficeOrderRow,
                    OfficeOrderRow.order_id == OfficeOrder.id
                )
            ).filter(OfficeOrder.id == order.id).all()
            self.total25 = self.calc_total('price25')
            self.total50 = self.calc_total('price50')

        else:
            self.rows = []
            self.total25 = self.calc_total('price25')
            self.total50 = self.calc_total('price50')

    def calc_total(self, price_type):
        total = 0
        for row in self.rows:
            total += getattr(row[1], price_type)

        return total
