import decimal

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
        return self._price.to_eng_string()

    @property
    def price_decimal(self):
        return self._price

    @property
    def price(self):
        return float(self._price)

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


def group_offers(offers, price_group_precision=PRICE_GROUP_PRECISION):
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


class GroupedTrade(object):

    def __init__(self, price_decimal, timestamp_bin, type_):
        self._price = price_decimal
        self.type_ = type_
        self.amount = 0
        self.timestamp = timestamp_bin  # int, representing ms

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


def group_trades(trades, price_group_precision=PRICE_GROUP_PRECISION, time_group_interval=TIME_GROUP_INTERVAL_MS):
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
                                                                 trade.offer.type_))
        if grouped_offer is None:
            grouped_offer = GroupedTrade(quantized_price, trade_bucket_time_int, trade.offer.type_)
            grouped_offer.add(trade.offer.amount, )
            quantized_offers_by_price_time_type[(quantized_price, trade_bucket_time_int, trade.offer.type_)] = grouped_offer
        else:
            grouped_offer.add(trade.offer.amount)

    unsorted_list = quantized_offers_by_price_time_type.values()
    return sorted(unsorted_list)