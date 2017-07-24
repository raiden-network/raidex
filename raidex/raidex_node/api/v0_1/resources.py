from flask import jsonify, request, abort
from flask.views import MethodView

from raidex.raidex_node.offer_book import OfferType

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
        trades = list(self.interface.trades.values())
        dict_ = dict(
            data=[
                dict(
                    timestamp=trade.timestamp,
                    amount=trade.offer.amount,
                    price=trade.offer.price,
                    type=trade.offer.type.value
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
            abort(400, 'Invalid type')

        amount = kwargs['amount']
        if not isinstance(amount, (int, long)) or amount < 1:
            abort(400, 'Invalid amount or type: {}'.format(type(amount)))

        price = kwargs['price']
        if not isinstance(price, (float, int, long)):
            abort(400, 'Invalid price')
        price = float(price)

        order_id = self.interface.limit_order(OfferType[type_], amount, price)
        dict_ = dict(
            data=order_id
        )
        return jsonify(dict_)

    def get(self):
        # TODO
        dict_ = dict(
            data=[]
        )
        return jsonify(dict_)

