from collections import namedtuple
import time

import pytest
import gevent
from ethereum.utils import sha3, privtoaddr

from raidex.raidex_node.offer_book import Offer, OfferView, OfferBook, OfferType
from raidex.messages import Offer


@pytest.fixture()
def assets():
    assets = [privtoaddr(sha3("asset{}".format(i))) for i in range(2)]
    return assets


@pytest.fixture()
def accounts():
    Account = namedtuple('Account', 'privatekey address')
    privkeys = [sha3("account:{}".format(i)) for i in range(3)]
    accounts = [Account(pk, privtoaddr(pk)) for pk in privkeys]
    return accounts


def test_offer_comparison(assets):
    pair = (assets[0], assets[1])
    timeouts = [time.time() + i for i in range(0, 4)]
    order1 = Offer(pair=pair, type_=OfferType.BID, amount=50, price=5., timeout=timeouts[0])
    order2 = Offer(pair=pair, type_=OfferType.BID, amount=100, price=1., timeout=timeouts[1])
    order3 = Offer(pair=pair, type_=OfferType.BID, amount=100, price=2., timeout=timeouts[2])
    order4 = Offer(pair=pair, type_=OfferType.BID, amount=100, price=1., timeout=timeouts[3])

    assert order1 == order1
    assert order2 != order4
    assert order2 < order4 < order3 < order1
    assert order1 >= order3 >= order4 >= order2


def test_offerview_ordering(offers, assets):
    # filter correct asset_pair and add type_ manually
    compare_pair = (assets[0], assets[1])
    bid_orders = [Offer.from_message(offer)
                  for offer in offers if offer.bid_token == assets[0]]
    offers = OfferView(market=compare_pair, type_=OfferType.BID)
    offer_ids = [offers.add_offer(order) for order in bid_orders]

    assert len(offers) == len(bid_orders)
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))

    # test removal
    offers.remove_offer(offers.offers.min_item()[0].order_id)
    offers.remove_offer(offers.offers.min_item()[0].order_id)
    offers.remove_offer(offers.offers.min_item()[0].order_id)

    assert len(offers) == len(bid_orders) - 3
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))

