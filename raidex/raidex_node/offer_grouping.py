
from functools import total_ordering
import decimal
from decimal import Decimal, getcontext

from raidex.utils import timestamp

PRICE_GROUP_PRECISION = 1  # default price-group precision are 1s digits after 0
TIME_GROUP_INTERVAL_MS = 10000  # default timestamp bucket size for trades is 60s

getcontext().rounding = decimal.ROUND_FLOOR
# getcontext().Emax = decimal.Decimal('9'*15)
# getcontext().Emin = 0
getcontext().prec = 28

@total_ordering
class GroupedOffer(object):

    def __init__(self, price_decimal):
        self._price = price_decimal
        self.amount = 0
        self._timeouts = list()

    @property
    def price_string(self):
        # return the decimal string
        return self._price.to_eng_string()

    @property
    def price_decimal(self):
        return self._price

    @property
    def price(self):
        return float(self._price)

    @property
    def avg_timeout(self):
        return sum(self._timeouts) / len(self._timeouts)

    @property
    def max_timeout(self):
        return max(self._timeouts)

    @property
    def min_timeout(self):
        return min(self._timeouts)

    def add(self, amount, timeout):
        self.amount += amount
        self._timeouts.append(timeout)

    def __eq__(self, other):
        return self.price_decimal == other.price_decimal

    def __lt__(self, other):
        return self.price_decimal < other.price_decimal


def group_offers(offers, price_group_precision=None):
    if price_group_precision is None:
        price_group_precision = PRICE_GROUP_PRECISION
    quantized_offers_by_price = dict()
    for offer in offers:
        # converts the float to a decimal obj
        quantized = Decimal(offer.price).quantize(Decimal(10) ** -price_group_precision)
        grouped_offer = quantized_offers_by_price.get(quantized)
        if grouped_offer is None:
            grouped_offer = GroupedOffer(quantized)
            grouped_offer.add(offer.amount, offer.timeout)
            quantized_offers_by_price[quantized] = grouped_offer
        else:
            grouped_offer.add(offer.amount, offer.timeout)
    unsorted_list = quantized_offers_by_price.values()
    return sorted(unsorted_list)

@total_ordering
class GroupedTrade(object):

    def __init__(self, price_decimal, timestamp_bin, offer_id, type_):
        self._price = price_decimal
        self.type = type_
        self.amount = 0
        self.timestamp = timestamp_bin  # int, representing ms
        # identifier to remove changing trades
        #  FIXME better hash
        self.hash = hash(offer_id + self.timestamp + self.amount)

    @property
    def price_string(self):
        # return the decimal string
        return self.price_decimal.to_eng_string()

    @property
    def price_decimal(self):
        return self._price

    @property
    def price_int(self):
        return int(self.price_decimal.to_integral())

    @property
    def price(self):
        return float(self._price)

    def add(self, amount):
        self.amount += amount

    def __eq__(self, other):
        return (self.timestamp, self.price_decimal) == (other.timestamp, other.price_decimal)

    def __lt__(self, other):
        return (self.timestamp, self.price_decimal) < (other.timestamp, other.price_decimal)


def group_trades(iterable, chunk_size=None, price_group_precision=None,
                 time_group_interval=None):
    if price_group_precision is None:
        price_group_precision = PRICE_GROUP_PRECISION
    if time_group_interval is None:
        time_group_interval = TIME_GROUP_INTERVAL_MS

    quantized_offers_by_price_time_type = dict()

    for trade in iterable:
        unquantized = Decimal(trade.offer.price)
        quantized_price = unquantized.quantize(Decimal(10) ** -price_group_precision)
        trade_bucket_time_int, _ = find_time_bin(trade.timestamp, time_group_interval=time_group_interval)

        grouped_offer = quantized_offers_by_price_time_type.get((float(quantized_price), trade_bucket_time_int,
                                                                 trade.offer.type))

        if grouped_offer is None:
            grouped_offer = GroupedTrade(quantized_price, trade_bucket_time_int, trade.offer.offer_id, trade.offer.type)
            grouped_offer.add(trade.offer.amount)

            quantized_offers_by_price_time_type[(float(quantized_price), trade_bucket_time_int, trade.offer.type)] = grouped_offer
        else:
            grouped_offer.add(trade.offer.amount)

        if chunk_size is not None:
                if len(quantized_offers_by_price_time_type) == chunk_size + 1:
                    del quantized_offers_by_price_time_type[(float(quantized_price), trade_bucket_time_int, trade.offer.type)]
                    break

    unsorted_list = quantized_offers_by_price_time_type.values()

    return sorted(unsorted_list)


def group_trades_from(trades_gen_func, from_timestamp=None, price_group_precision=None,
                      time_group_interval=None):
    if price_group_precision is None:
        price_group_precision = PRICE_GROUP_PRECISION
    if time_group_interval is None:
        time_group_interval = TIME_GROUP_INTERVAL_MS
    from_time = None
    if from_timestamp is not None:
        from_time, _ = find_time_bin(from_timestamp, time_group_interval=time_group_interval)

    return group_trades(trades_gen_func(from_timestamp=from_time), chunk_size=None,
                        price_group_precision=price_group_precision, time_group_interval=time_group_interval)


class PriceBin(object):

    def __init__(self, open_price, timestamp_bin):
        self._open_price = open_price
        self._close_prices = []
        self._close_timestamp = None
        self._min_price = None
        self._max_price = None
        self.amount = 0
        self.timestamp = timestamp_bin  # int, representing ms

    @property
    def open_price(self):
        return float(self._open_price)

    @property
    def close_price_decimal(self):
        close_price = sum(self._close_prices) / Decimal(len(self._close_prices))
        assert isinstance(close_price, Decimal)
        return close_price

    @property
    def close_price(self):
        if self._close_timestamp is None:
            price = self._open_price
        else:
            price = self.close_price_decimal
        return float(price)

    @property
    def min_price(self):
        price = self._min_price or self._open_price
        return float(price)

    @property
    def max_price(self):
        price = self._max_price or self._open_price
        return float(price)

    def add(self, timestmp, amount, price):
        # Trades should be added in strictly increasing timestamp order!
        if price < self._min_price or self._min_price is None:
            self._min_price = price
        if price > self._max_price or self._max_price is None:
            self._max_price = price
        self.amount += amount
        if timestmp > self._close_timestamp or self._close_timestamp is None:
            self._close_timestamp = timestmp
            self._close_prices = [price]
        elif timestmp == self._close_timestamp:
            self._close_prices.append(price)

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp

def get_n_recent_trades(trades_list, nof_trades):
    return group_trades(reversed(trades_list), chunk_size=nof_trades)


def make_price_bins(trades_gen_func, nof_buckets, interval):
    price_group_precision = PRICE_GROUP_PRECISION
    time_group_interval = int(timestamp.to_milliseconds(interval))
    price_bins = {}  # timestamp_bin -> price_bin
    last_close_price = 0.

    current_timestamp = timestamp.time()
    from_start_time, to_start_time = tuple(time_bin_gen(current_timestamp, 2, time_group_interval))
    from_time_gen = time_bin_gen(from_start_time, nof_buckets + 1, time_group_interval)
    to_time_gen = time_bin_gen(to_start_time, nof_buckets + 1, time_group_interval)

    for from_time, to_time in zip(from_time_gen, to_time_gen):
        price_bin = PriceBin(last_close_price, from_time)
        price_bins[from_time] = price_bin
        for trade in trades_gen_func(from_timestamp=from_time, to_timestamp=to_time):
            quantized_price = Decimal(trade.offer.price).quantize(Decimal(10) ** -price_group_precision)
            price_bin.add(trade.timestamp, trade.offer.amount, quantized_price)
        last_close_price = price_bin.close_price

    assert len(price_bins) == nof_buckets + 1
    unsorted_list = price_bins.values()
    sorted_list = sorted(unsorted_list)
    # throw away the first bin again, it was there just to determine the first open price
    return sorted_list[1:]


def find_time_bin(timestmp, offset=None, time_group_interval=None):
    # round_floor to nearest integral to find the bin-number where the trade is in:
    # then multiply with the binsize again to find the bin's time-value

    if time_group_interval is None:
        time_group_interval = TIME_GROUP_INTERVAL_MS

    if offset is None:
        offset = 0
    timestamp_decimal = Decimal(timestmp)
    bucket_size_decimal = Decimal(time_group_interval)
    assert isinstance(offset, int)
    offset_decimal = Decimal(offset)
    stop_offset_decimal = offset_decimal + Decimal(1)
    # also add offset to the found bin`
    start_time_decimal = ((timestamp_decimal / bucket_size_decimal).to_integral() *
                           bucket_size_decimal) + bucket_size_decimal * offset_decimal
    stop_time = int(start_time_decimal + bucket_size_decimal * stop_offset_decimal)
    # stop time is the start time of the next bin
    start_time = int(start_time_decimal)
    return start_time, stop_time


def time_bin_gen(current_timestamp, nof_bins, time_group_interval=None):
    if time_group_interval is None:
        time_group_interval = TIME_GROUP_INTERVAL_MS

    offset = - nof_bins
    bucket_size_decimal = Decimal(time_group_interval)
    stop_time_decimal = ((Decimal(current_timestamp) / bucket_size_decimal).to_integral() *
                         bucket_size_decimal)
    start_time_decimal = stop_time_decimal + bucket_size_decimal * Decimal(offset)

    for _ in range(0, nof_bins):
        time = start_time_decimal + bucket_size_decimal
        yield int(time)
        start_time_decimal = time
