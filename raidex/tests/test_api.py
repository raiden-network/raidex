import decimal

from collections import namedtuple

from raidex.raidex_node.api.v0_1.resources import GroupedOffer, group_offers, group_trades
from raidex.utils import milliseconds
from raidex.raidex_node.trades import Trade
from raidex.raidex_node.offer_book import OfferType

Offer = namedtuple("Offer", "amount, price, timeout type")


def test_offer_grouping():
    price_group_precision = 3

    # 1) Test same grouping

    offer1 = Offer(100, 0.12349, timeout=milliseconds.time_plus(1), type=OfferType.BUY)
    offer2 = Offer(100, 0.12341, timeout=milliseconds.time_plus(1), type=OfferType.BUY)

    # test group_offers
    grouped = group_offers([offer1, offer2], price_group_precision=price_group_precision)
    assert len(grouped) == 1

    # test manually
    price1 = decimal.Decimal(offer1.price)
    price1 = price1.quantize(decimal.Decimal(10) ** -price_group_precision)
    price2 = decimal.Decimal(offer2.price)
    price2 = price2.quantize(decimal.Decimal(10) ** -price_group_precision)

    grouped1 = GroupedOffer(price1)
    grouped1.add(offer1.amount, offer1.timeout)
    grouped2 = GroupedOffer(price2)
    grouped2.add(offer2.amount, offer2.timeout)

    # Compare the price, should be equal
    assert grouped1 == grouped2

    # 2) Test different grouping, round half up

    offer1 = Offer(100, 0.123501, timeout=milliseconds.time_plus(1), type=OfferType.BUY)
    offer2 = Offer(100, 0.123401, timeout=milliseconds.time_plus(1), type=OfferType.BUY)

    # test group_offers
    grouped = group_offers([offer1, offer2], price_group_precision=price_group_precision)
    assert len(grouped) == 2

    # test manually
    price1 = decimal.Decimal(offer1.price)
    price1 = price1.quantize(decimal.Decimal(10) ** -price_group_precision)
    price2 = decimal.Decimal(offer2.price)
    price2 = price2.quantize(decimal.Decimal(10) ** -price_group_precision)

    grouped1 = GroupedOffer(price1)
    grouped1.add(offer1.amount, offer1.timeout)
    grouped2 = GroupedOffer(price2)
    grouped2.add(offer2.amount, offer2.timeout)

    # Compare the price, should be equal
    assert grouped1 > grouped2


def test_trade_gouping():
    price_group_precision = 3
    time_group_interval_ms = 100

    offer1 = Offer(100, 0.12349, timeout=milliseconds.time_plus(milliseconds=1), type=OfferType.BUY)
    offer2 = Offer(100, 0.12501, timeout=milliseconds.time_plus(milliseconds=1), type=OfferType.SELL)

    # don't work with epoch based timestamps here
    trade1 = Trade(offer1, timestamp=100) # should be in 100 ms bucket
    trade2 = Trade(offer1, timestamp=199) # should be in 100 ms bucket, gets grouped with trade1
    trade3 = Trade(offer1, timestamp=201) # should be in 200 ms bucket (next highest bucket)
    trade4 = Trade(offer2, timestamp=201) # should be in 200 ms bucket, but not grouped with trade3

    grouped = group_trades([trade1, trade2, trade3, trade4], price_group_precision, time_group_interval_ms)
    print(grouped[0].amount)
    print(grouped[0].timestamp)
    assert len(grouped) == 3

    # grouped is sorted by (timestamp, price) (priority: smaller values)

    # trade1 and trade2 combined (BUY):
    assert grouped[0].amount == 200
    assert grouped[0].timestamp == 100

    # trade3 (same timestamp-bucket as trade4, but smaller price and different type) (BUY):
    assert grouped[1].amount == 100
    assert grouped[1].timestamp == 200

    # trade4 (SELL):
    assert grouped[2].amount == 100
    assert grouped[2].timestamp == 200
