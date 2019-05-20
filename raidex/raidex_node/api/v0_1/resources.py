from flask import jsonify, request, abort
from flask.views import MethodView

from raidex.raidex_node.raidex_node import RaidexNode
from raidex.raidex_node.handle_api_call import on_api_call

# API-Resources - the json encoding and decoding is handled manually for simplicity and readability
# Type-checking, encoding/decoding and error-responses are kept very basic


class Offers(MethodView):

    def __init__(self, raidex_node: RaidexNode):
        self.raidex_node = raidex_node

    def get(self):
        # the grouped offers are sorted, with lowest price first
        buys = self.raidex_node.grouped_buys()
        sells = reversed(self.raidex_node.grouped_sells())
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
                    type=trade.type.name,
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

    def __init__(self, raidex_node: RaidexNode):
        self.raidex_node = raidex_node

    def post(self):
        kwargs = request.get_json()

        order_type = kwargs['type']
        if order_type not in ('BUY', 'SELL'):
            abort(400, 'Invalid type')

        amount = kwargs['amount']

        if not isinstance(amount, (float, int)) or amount <= 0:
            abort(400, 'Invalid amount or type: {}'.format(type(amount)))

        price = kwargs['price']
        print(f'amount: {amount} price: {price}')
        if not isinstance(price, (float, int)) or price <= 0:
            abort(400, 'Invalid price')
        price = float(price)

        data = dict()
        data['event'] = 'NewLimitOrder'
        data['order_type'] = order_type
        data['amount'] = amount
        data['price'] = float(price)

        order_id = on_api_call(self.raidex_node, data)

        dict_ = dict(
            data=order_id
        )
        return jsonify(dict_)

    def get(self):
        orders = self.raidex_node.initiated_orders
        dict_ = dict(
            data=[
                dict(
                    amount=order.amount,
                    price=order.price,
                    order_id=order.order_id,
                    type=order.type_.name,
                    filledAmount=order.amount_traded,
                    canceled=order.canceled
                ) for order in orders
            ]
        )
        return jsonify(dict_)

    def delete(self, order_id):
        self.raidex_node.cancel_limit_order(order_id)
        dict_ = dict(
            data=order_id
        )
        return jsonify(dict_)
