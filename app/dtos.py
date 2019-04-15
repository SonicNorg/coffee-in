from sqlalchemy.orm import join

from app import db

from app.models import IndividualOrder, OrderRow, CoffeeSort, CoffeePrice
from app.util import get_open_price


class IndividualOrderWithPrices:

    def __init__(self, order) -> None:
        self.order = order
        cur_price = get_open_price()
        if cur_price and order and order.rows:
            # .add_entity(CoffeePrice) \

            # TODO possible automapping to OrderRow in row 20, try to uncomment row 18
            self.rows = db.session.query(OrderRow, CoffeePrice).select_from(
                join(OrderRow, CoffeePrice, OrderRow.coffee_type_id == CoffeePrice.coffee_type_id)) \
                .filter(OrderRow.id.in_([row.id for row in order.rows])).all()

            # self.rows = OrderRow.query.filter(OrderRow.id.in_([row.id for row in order.rows])).from_self() \
            #    .join(CoffeePrice, CoffeePrice.coffee_type_id == OrderRow.coffee_type_id).filter(
            #    CoffeePrice.price_id == cur_price.id)
            # .with_entities(CoffeePrice.price25, CoffeePrice.price50))
        else:
            self.rows = []
