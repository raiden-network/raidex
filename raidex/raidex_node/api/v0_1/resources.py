from flask import jsonify, request, abort
from flask.views import MethodView

from raidex.raidex_node.offer_book import OfferType


# API-Resources - the json encoding and decoding is handled manually for simplicity and readability
# Type-checking, encoding/decoding and error-responses are kept very basic


class Offers(MethodView):

    def __init__(self, interface):
        self.interface = interface

    def get(self):
        # the offers are sorted, with lowest price first
        buys = self.interface.grouped_buys()
        sells = self.interface.grouped_sells()
        dict_ = dict(
            data=dict(
                buys=[
                    dict(
                        amount=offer.amount,
                        price=offer.price,
                        timeout=offer.avg_timeout
                    ) for offer in buys
                ],

                sells=[
                    dict(
                        amount=offer.amount,
                        price=offer.price,
                        timeout=offer.avg_timeout
                    ) for offer in sells
                ],
            ),
        )
        return jsonify(dict_)


class Trades(MethodView):
    # NOTE if you query multiple times within a time-interval smaller than the timestamp-bucket,
    # the amount of the trades will change when matching trades are added to that bucket
    def __init__(self, interface):
        self.interface = interface

    def get(self):
        trades = self.interface.grouped_trades()
        dict_ = dict(
            data=[
                dict(
                    timestamp=trade.timestamp,
                    amount=trade.amount,
                    price=trade.price,
                    type=trade.type_.value
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

