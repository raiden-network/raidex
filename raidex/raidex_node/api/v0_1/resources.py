from flask import jsonify, request, abort
from flask.views import MethodView

# API-Resources - the json encoding and decoding is handled manually for simplicity and readability
# Type-checking, encoding/decoding and error-responses are kept very basic


class Offers(MethodView):

    def __init__(self, interface):
        self.interface = interface

    def get(self):
        offer_book = self.interface.offer_book
        buys = list(offer_book.buys.values())
        sells = list(offer_book.sells.values())
        dict_ = dict(
            data=dict(
                buys=[
                    dict(
                        amount=offer.amount,
                        price=offer.price,
                        timeout=offer.timeout
                    ) for offer in buys
                ],

                sells=[
                    dict(
                        amount=offer.amount,
                        price=offer.price,
                        timeout=offer.timeout
                    ) for offer in sells
                ],
            ),
        )
        return jsonify(dict_)


class Trades(MethodView):

    def __init__(self, interface):
        self.interface = interface

    def get(self):
        trades = self.interface.trades
        dict_ = dict(
            data=[
                dict(
                    timestamp=trade.timestamp,
                    amount=trade.offer.amount,
                    price=trade.offer.price,
                    type=trade.offer.type_
                    ) for trade in trades
            ]
        )
        return jsonify(dict_)


class LimitOrders(MethodView):

    def __init__(self, interface):
        self.interface = interface

    def post(self):
        kwargs = request.get_json()

        type_ = kwargs['type']
        if type_ not in ('BUY', 'SELL'):
            abort(400)

        amount = kwargs['amount']
        if not isinstance(amount, int) or amount < 1:
            abort(400)

        price = kwargs['price']
        if not isinstance(price, float):
            abort(400)

        order_id = self.interface.limit_order(self, type_, amount, price)
        dict_ = dict(
            data=order_id
        )
        return jsonify(dict_)
