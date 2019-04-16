from sqlalchemy.orm import join

from app import db

from app.models import IndividualOrder, OrderRow, CoffeeSort, CoffeePrice
from app.util import get_open_price


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
            total += getattr(row[1], price_type)

        return total
