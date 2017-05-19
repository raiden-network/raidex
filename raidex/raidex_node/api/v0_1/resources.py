import decimal

from flask import jsonify, request, abort
from flask.views import MethodView

from raidex.raidex_node.offer_book import OfferType


# API-Resources - the json encoding and decoding is handled manually for simplicity and readability
# Type-checking, encoding/decoding and error-responses are kept very basic

PRICE_GROUP_PRECISION = 3  # default price-group precision are 3 digits after 0
TIME_GROUP_INTERVAL_MS = 10000  # default timestamp bucket size for trades is 10s


class GroupedOffer(object):

    def __init__(self, price_decimal):
        self._price = price_decimal
        self.amount = 0
        self._timeouts = list()

    @property
    def price_string(self):
        # return the decimal string
        return self._price.to_eng_string

    @property
    def price_decimal(self):
        return self._price

    @property
    def avg_timeout(self):
        # TODO make python3 compatible
        return reduce(lambda x, y: x + y, self._timeouts) / len(self._timeouts)

    @property
    def max_timeout(self):
        return max(self._timeouts)

    @property
    def min_timeout(self):
        return min(self._timeouts)

    def add(self, amount, timeout):
        self.amount += amount
        self._timeouts.append(timeout)

    def __cmp__(self, other):
        if self.price_decimal < other.price_decimal:
            return -1
        elif self.price_decimal > other.price_decimal:
            return 1
        else:
            return 0


def group_offers(offers, price_group_precision):
    quantized_offers_by_price = dict()
    for offer in offers:
        # converts the float to a decimal obj
        price_decimal = decimal.Decimal(offer.price)
        quantized = price_decimal.quantize(decimal.Decimal(10) ** -price_group_precision)
        grouped_offer = quantized_offers_by_price.get(quantized)
        if grouped_offer is None:
            grouped_offer = GroupedOffer(quantized)
            grouped_offer.add(offer.amount, offer.timeout)
            quantized_offers_by_price[quantized] = grouped_offer
        else:
            grouped_offer.add(offer.amount, offer.timeout)

    unsorted_list = quantized_offers_by_price.values()
    return sorted(unsorted_list)


class Offers(MethodView):

    def __init__(self, interface):
        self.interface = interface

    def get(self):
        offer_book = self.interface.offer_book
        # the offers are sorted, with lowest price first
        buys = group_offers(list(offer_book.buys.values()), PRICE_GROUP_PRECISION)
        sells = group_offers(list(offer_book.sells.values()), PRICE_GROUP_PRECISION)
        dict_ = dict(
            data=dict(
                buys=[
                    dict(
                        amount=offer.amount,
                        price=offer.price_string,  # XXX careful, is decimal-string now
                        timeout=offer.avg_timeout
                    ) for offer in buys
                ],

                sells=[
                    dict(
                        amount=offer.amount,
                        price=offer.price_string,  # XXX careful, is decimal-string now
                        timeout=offer.avg_timeout
                    ) for offer in sells
                ],
            ),
        )
        return jsonify(dict_)


class GroupedTrade(object):

    def __init__(self, price_decimal, timestamp_bin, type_):
        self._price = price_decimal
        self.type = type_
        self.amount = 0
        self.timestamp = timestamp_bin  # int, representing ms

    @property
    def price_string(self):
        # return the decimal string
        return self.price_decimal.to_eng_string

    @property
    def price_decimal(self):
        return self._price

    @property
    def price_int(self):
        return int(self.price_decimal.to_integral())

    def add(self, amount):
        self.amount += amount

    def __cmp__(self, other):
        # first cmp timestamp, then price
        if self.timestamp < other.timestamp:
            return -1
        elif self.timestamp > other.timestamp:
            return 1
        else:
            if self.price_decimal < other.price_decimal:
                return -1
            elif self.price_decimal > other.price_decimal:
                return 1
            else:
                return 0


def group_trades(trades, price_group_precision, time_group_interval):
    quantized_offers_by_price_time_type = dict()
    # very high precision context for large positives, always rounds to floor
    context_ = decimal.Context(rounding=decimal.ROUND_FLOOR, Emax=decimal.Decimal('9'*28), Emin=0, prec=28)

    for trade in trades:
        price_decimal = decimal.Decimal(trade.offer.price)
        quantized_price = price_decimal.quantize(decimal.Decimal(10) ** -price_group_precision)
        timestamp_decimal = context_.create_decimal(trade.timestamp)
        bucket_size_decimal = context_.create_decimal(time_group_interval)

        # round_floor to nearest integral to find the bin-number where the trade is in:
        # then multiply with the binsize again to find the bin's time-value
        trade_bucket_time_int = int((timestamp_decimal / bucket_size_decimal).to_integral(context=context_) *
                                    bucket_size_decimal)

        grouped_offer = quantized_offers_by_price_time_type.get((quantized_price, trade_bucket_time_int,
                                                                 trade.offer.type))
        if grouped_offer is None:
            grouped_offer = GroupedTrade(quantized_price, trade_bucket_time_int, trade.offer.type)
            grouped_offer.add(trade.offer.amount, )
            quantized_offers_by_price_time_type[(quantized_price, trade_bucket_time_int, trade.offer.type)] = grouped_offer
        else:
            grouped_offer.add(trade.offer.amount)

    unsorted_list = quantized_offers_by_price_time_type.values()
    return sorted(unsorted_list)


class Trades(MethodView):
    # NOTE if you query multiple times within a time-interval smaller than the timestamp-bucket,
    # the amount of the trades will change when matching trades are added to that bucket
    def __init__(self, interface):
        self.interface = interface

    def get(self):
        trades = group_trades(list(self.interface.trades.values()), PRICE_GROUP_PRECISION, TIME_GROUP_INTERVAL_MS)
        dict_ = dict(
            data=[
                dict(
                    timestamp=trade.timestamp,
                    amount=trade.amount,
                    price=trade.price_string, # XXX careful, is decimal-string now
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

