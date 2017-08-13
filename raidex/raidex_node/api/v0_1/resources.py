from flask import jsonify, request, abort
from flask.views import MethodView

from raidex.raidex_node.offer_book import OfferType


# API-Resources - the json encoding and decoding is handled manually for simplicity and readability
# Type-checking, encoding/decoding and error-responses are kept very basic


class Offers(MethodView):

    def __init__(self, raidex_node):
        self.raidex_node = raidex_node

    def get(self):
        # the offers are sorted, with lowest price first
        buys = self.raidex_node.grouped_buys()
        sells = self.raidex_node.grouped_sells()
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
    def __init__(self, raidex_node):
        self.raidex_node = raidex_node

    def get(self):
        chunk_size = request.args.get('chunk_size')
        if chunk_size is not None:
            chunk_size = int(chunk_size)

        trades = self.raidex_node.recent_grouped_trades(chunk_size)
        assert isinstance(trades, list)
        dict_ = dict(
            data=[
                dict(
                    timestamp=trade.timestamp,
                    amount=trade.amount,
                    price=trade.price,
                    type=trade.type.value,
                    hash=trade.hash
                ) for trade in trades
            ]
        )
        return jsonify(dict_)


class PriceChartBin(MethodView):
    def __init__(self, raidex_node):
        self.raidex_node = raidex_node

    def get(self):
        nof_buckets = request.args.get('nof_buckets')
        interval = request.args.get('interval')  # the interval in seconds
        if nof_buckets is not None:
            nof_buckets = int(nof_buckets)
        if interval is not None:
            interval = int(interval)
        price_bins = self.raidex_node.price_chart_bins(nof_buckets, interval)
        assert isinstance(price_bins, list)
        dict_ = dict(
            data=[
                dict(
                    open=price_bin.open_price,
                    close=price_bin.close_price,
                    max=price_bin.max_price,
                    min=price_bin.min_price,
                    amount=price_bin.amount,
                    timestamp=price_bin.timestamp,
                ) for price_bin in price_bins
            ]
        )
        return jsonify(dict_)


class LimitOrders(MethodView):

    def __init__(self, raidex_node):
        self.raidex_node = raidex_node

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

        order_id = self.raidex_node.limit_order(OfferType[type_], amount, price)
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
