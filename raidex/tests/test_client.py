import time
import pytest
import gevent

from ethereum.utils import int_to_big_endian, sha3

from raidex.raidex_node.offer_book import Offer, OfferBook, OfferType, OfferBookTask, OfferView
from raidex.message_broker.listeners import OfferListener
from raidex.utils import get_market_from_asset_pair, milliseconds
from raidex.message_broker.message_broker import MessageBroker
from raidex.commitment_service.commitment_service import CommitmentService
from raidex.raidex_node.market import TokenPair


@pytest.fixture()
def token_pair(assets):
    return TokenPair(assets[0], assets[1])


@pytest.fixture()
def message_broker():
    return MessageBroker()


@pytest.fixture()
def commitment_service(token_pair):
    return CommitmentService(token_pair, sha3("test1"))


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


def test_offer_comparison():
    timeouts = [int(time.time() + i) for i in range(0, 4)]
    offer_ids = list(range(0, 4))
    offer1 = Offer(OfferType.BUY, 50, 5, timeout=timeouts[0], offer_id=offer_ids[0])
    offer2 = Offer(OfferType.BUY, 100, 1, timeout=timeouts[1], offer_id=offer_ids[1])
    offer3 = Offer(OfferType.BUY, 100, 2, timeout=timeouts[2], offer_id=offer_ids[2])
    offer4 = Offer(OfferType.BUY, 100, 1, timeout=timeouts[3], offer_id=offer_ids[3])
    offers = OfferView()
    for offer in [offer1, offer2, offer3, offer4]:
        offers.add_offer(offer)
    assert list(offers.values()) == [offer2, offer4, offer3, offer1]


def test_offer_book_task(message_broker, commitment_service, token_pair):
    offerbook = OfferBook()
    OfferBookTask(offerbook, OfferListener(token_pair, message_broker)).start()
    gevent.sleep(0.001)
    offer = Offer(OfferType.SELL, 100, 1000, offer_id=123, timeout=milliseconds.time_plus(2))
    proof = commitment_service.maker_commit_async(offer).get()
    message_broker.broadcast(proof)
    gevent.sleep(0.001)
    assert len(offerbook.sells) == 1



