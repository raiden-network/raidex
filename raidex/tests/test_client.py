from collections import namedtuple
import time

from ethereum.utils import int_to_big_endian

from raidex.raidex_node.offer_book import Offer, OfferView, OfferBook, OfferType
from raidex.utils import get_market_from_asset_pair


def test_market_from_asset_pair():
    # int_to_big_endian converts an int into big_endian binary data

    # smaller int representation of binary data has to come first in the 'market' asset pair (by convention):
    # market := (smaller_int, greater_int)

    # create binary asset pair tuple that is properly ordered:
    asset_pair = tuple(int_to_big_endian(int_) for int_ in (42, 420000))
    market = asset_pair

    # permute the asset pair to (greater_int, smaller_int) ordering
    asset_pair_permuted = asset_pair[::-1]

    # assume correctly ordered asset_pair doesn't get permuted when retrieving the market:
    assert asset_pair == get_market_from_asset_pair(asset_pair) == market

    # assume falsely ordered asset_pair gets permuted when retrieving the market:
    assert get_market_from_asset_pair(asset_pair_permuted) == market != asset_pair_permuted


def test_offer_comparison(assets):
    pair = (assets[0], assets[1])
    timeouts = [time.time() + i for i in range(0, 4)]
    offer_ids = list(range(0, 4))
    order1 = Offer(market=pair, type_=OfferType.BID, amount=50, price=5., timeout=timeouts[0], offer_id=offer_ids[0])
    order2 = Offer(market=pair, type_=OfferType.BID, amount=100, price=1., timeout=timeouts[1], offer_id=offer_ids[1])
    order3 = Offer(market=pair, type_=OfferType.BID, amount=100, price=2., timeout=timeouts[2], offer_id=offer_ids[2])
    order4 = Offer(market=pair, type_=OfferType.BID, amount=100, price=1., timeout=timeouts[3], offer_id=offer_ids[3])

    assert order1 == order1
    assert order2 != order4
    assert order2 < order4 < order3 < order1
    assert order1 >= order3 >= order4 >= order2


def test_offerview_ordering(offer_msgs, assets):
    # filter correct asset_pair and add type_ manually
    asset_pair = (assets[0], assets[1])
    market = get_market_from_asset_pair(asset_pair)

    bid_offers = [Offer.from_message(offer)
                  for offer in offer_msgs if offer.bid_token == market[0]] # TODO CHECKME

    offers = OfferView(market=market, type_=OfferType.BID)
    offer_ids = [offers.add_offer(offer) for offer in bid_offers]

    assert len(offers) == len(bid_offers)
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))

    # test removal
    offers.remove_offer(offers.offers.min_item()[0].offer_id)
    offers.remove_offer(offers.offers.min_item()[0].offer_id)
    offers.remove_offer(offers.offers.min_item()[0].offer_id)

    assert len(offers) == len(bid_offers) - 3

    # checks the ordering of the offers
    assert all(first <= second for first, second in zip(list(offers)[:-1], list(offers)[1:]))

