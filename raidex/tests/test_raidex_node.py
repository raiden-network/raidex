import time
import pytest
import gevent

from eth_utils import int_to_big_endian, keccak

from raidex.raidex_node.offer_book import OfferDeprecated, OfferBook, OfferType, OfferView
from raidex.raidex_node.listener_tasks import OfferBookTask, SwapCompletedTask, OfferTakenTask
from raidex.utils import timestamp
from raidex.utils import get_market_from_asset_pair
from raidex.message_broker.message_broker import MessageBroker
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.commitment_service.mock import CommitmentServiceClientMock

from raidex.raidex_node.trades import TradesView
from raidex.signing import Signer


@pytest.fixture()
def token_pair(assets):
    return TokenPair(assets[0], assets[1])


@pytest.fixture()
def message_broker():
    return MessageBroker()


@pytest.fixture()
def commitment_service(token_pair, message_broker):
    return CommitmentServiceClientMock(Signer.random(), token_pair, message_broker)


def test_offer_comparison():
    timeouts = [int(time.time() + i) for i in range(0, 4)]
    offer_ids = list(range(0, 4))
    offer1 = OfferDeprecated(OfferType.BUY, 50, 5, timeout=timeouts[0], offer_id=offer_ids[0])
    offer2 = OfferDeprecated(OfferType.BUY, 100, 1, timeout=timeouts[1], offer_id=offer_ids[1])
    offer3 = OfferDeprecated(OfferType.BUY, 100, 2, timeout=timeouts[2], offer_id=offer_ids[2])
    offer4 = OfferDeprecated(OfferType.BUY, 100, 1, timeout=timeouts[3], offer_id=offer_ids[3])
    offers = OfferView()
    for offer in [offer1, offer2, offer3, offer4]:
        offers.add_offer(offer)
    assert list(offers.values()) == [offer2, offer4, offer3, offer1]


def test_offer_book_task(message_broker, commitment_service, token_pair):
    offer_book = OfferBook()
    OfferBookTask(offer_book, token_pair, message_broker).start()
    gevent.sleep(0.001)
    offer = OfferDeprecated(OfferType.SELL, 100, 1000, offer_id=123, timeout=timestamp.time_plus(20))
    proof = commitment_service.maker_commit_async(offer).get()
    message_broker.broadcast(proof)
    gevent.sleep(0.001)
    assert len(offer_book.sells) == 1


def test_taken_task(message_broker, commitment_service):
    offer_book = OfferBook()
    trades = TradesView()
    OfferTakenTask(offer_book, trades, message_broker).start()
    gevent.sleep(0.001)
    offer = OfferDeprecated(OfferType.SELL, 100, 1000, offer_id=123, timeout=timestamp.time_plus(2))
    # insert manually for the first time
    offer_book.insert_offer(offer)
    assert len(offer_book.sells) == 1
    offer_taken = commitment_service.create_taken(offer.offer_id)
    # send offer_taken
    message_broker.broadcast(offer_taken)
    gevent.sleep(0.001)
    assert len(offer_book.sells) == 0
    assert len(trades.pending_offer_by_id) == 1


def test_swap_completed_task(message_broker, commitment_service):
    trades = TradesView()
    SwapCompletedTask(trades, message_broker).start()
    gevent.sleep(0.001)
    offer = OfferDeprecated(OfferType.SELL, 100, 1000, offer_id=123, timeout=timestamp.time_plus(2))
    # set it to pending, as it was taken
    trades.add_pending(offer)
    assert len(trades.pending_offer_by_id) == 1
    swap_completed = commitment_service.create_swap_completed(offer.offer_id)
    # send swap_completed
    message_broker.broadcast(swap_completed)
    gevent.sleep(0.001)
    assert len(trades) == 1
