import pytest

from raidex.raidex_node.order_task import LimitOrderTask
from raidex.message_broker.message_broker import MessageBroker
from raidex.raidex_node.trader.trader import TraderClient
from raidex.commitment_service.mock import CommitmentServiceMock, NonFailingCommitmentServiceGlobal
from raidex.raidex_node.offer_book import OfferBook, OfferType, Offer
from raidex.raidex_node.trades import TradesView
from raidex.raidex_node.listener_tasks import OfferBookTask, OfferTakenTask, SwapCompletedTask
from raidex.utils.gevent_helpers import switch_context
from raidex.utils import timestamp
from raidex.signing import Signer
from gevent import sleep


@pytest.fixture()
def offers(accounts):
    return [Offer(OfferType.SELL, 5, 20, offer_id=123, timeout=timestamp.time_plus(1),
                  maker_address=accounts[1].address),
            Offer(OfferType.SELL, 2, 5, offer_id=124, timeout=timestamp.time_plus(1),
                  maker_address=accounts[1].address),
            Offer(OfferType.BUY, 4, 20, offer_id=125, timeout=timestamp.time_plus(1),
                  maker_address=accounts[1].address),
            Offer(OfferType.SELL, 3, 60, offer_id=126, timeout=timestamp.time_plus(1),
                  maker_address=accounts[1].address)]


@pytest.fixture()
def message_broker():
    return MessageBroker()


@pytest.fixture()
def cs_global():
    return NonFailingCommitmentServiceGlobal()


@pytest.fixture()
def commitment_service(accounts, message_broker, cs_global, token_pair):
    signer = Signer(accounts[0].privatekey)
    return CommitmentServiceMock(signer, token_pair, message_broker, cs_global=cs_global)


@pytest.fixture()
def commitment_service2(accounts, message_broker, cs_global, token_pair):
    signer = Signer(accounts[1].privatekey)
    return CommitmentServiceMock(signer, token_pair, message_broker, cs_global=cs_global)


@pytest.fixture()
def trader(accounts):
    return TraderClient(accounts[0].address)


@pytest.fixture()
def trader2(accounts):
    return TraderClient(accounts[1].address)


@pytest.fixture()
def empty_offer_book():
    return OfferBook()


@pytest.fixture()
def offer_book(offers):
    offer_book = OfferBook()
    for offer in offers:
        offer_book.insert_offer(offer)
    return offer_book


@pytest.fixture()
def trades():
    return TradesView()


def test_amount_of_offers_spawned(empty_offer_book, trades, accounts, commitment_service, message_broker, trader):
    order_task = LimitOrderTask(empty_offer_book, trades, OfferType.BUY, 20, 10, accounts[0].address,
                                commitment_service, message_broker, trader, 2, 1)
    order_task.start()
    switch_context()
    assert order_task.number_open_trades == 10


def test_amount_of_offers_taken_and_spawned(offer_book, trades, accounts, commitment_service, message_broker, trader):
    order_task = LimitOrderTask(offer_book, trades, OfferType.BUY, 10, 10, accounts[0].address, commitment_service,
                                message_broker, trader, 2, 1)
    order_task.start()
    switch_context()
    assert order_task.number_open_trades == 4


def test_amount_of_offers_taken(offer_book, trades, accounts, commitment_service, message_broker, trader):
    order_task = LimitOrderTask(offer_book, trades, OfferType.BUY, 5, 10, accounts[0].address, commitment_service,
                                message_broker, trader, 2, 0.2)
    order_task.start()
    switch_context()
    assert order_task.number_open_trades == 3
    order_task.cancel()
    assert not order_task.get()


def test_of_respawn(empty_offer_book, trades, accounts, commitment_service, message_broker, trader):
    order_task = LimitOrderTask(empty_offer_book, trades, OfferType.BUY, 10, 10, accounts[0].address,
                                commitment_service, message_broker, trader, 2, 0.5)
    order_task.start()
    switch_context()
    assert order_task.number_open_trades == 5
    empty_offer_book.insert_offer(
        Offer(OfferType.SELL, 5, 9, 1234, timestamp.time_plus(3), maker_address=accounts[1].address))
    sleep(0.5)
    assert order_task.number_open_trades == 4


def test_of_token_swap(accounts, token_pair, commitment_service, commitment_service2, message_broker, trader, trader2):
    offer_book1 = OfferBook()
    offer_book2 = OfferBook()
    trades1 = TradesView()
    trades2 = TradesView()
    OfferBookTask(offer_book1, token_pair, message_broker).start()
    OfferTakenTask(offer_book1, trades1, message_broker).start()
    SwapCompletedTask(trades1, message_broker).start()
    order_task1 = LimitOrderTask(offer_book1, trades1, OfferType.BUY, 10, 10, accounts[0].address, commitment_service,
                                 message_broker, trader, 2, 1)
    order_task2 = LimitOrderTask(offer_book2, trades2, OfferType.SELL, 10, 10, accounts[1].address, commitment_service2,
                                 message_broker, trader2, 2, 10)

    OfferBookTask(offer_book2, token_pair, message_broker).start()
    OfferTakenTask(offer_book2, trades2, message_broker).start()
    SwapCompletedTask(trades2, message_broker).start()

    order_task1.start()
    sleep(1)  # time to place orders and to fill order books
    assert len(offer_book1.buys) == 5
    assert len(offer_book2.buys) == 5
    order_task2.start()
    assert order_task2.get()
    assert order_task1.get()

    assert len(offer_book1.sells) == 0
    assert len(offer_book1.buys) == 0
    assert len(offer_book2.sells) == 0
    assert len(offer_book2.buys) == 0

    sleep(1)  # time to fill trades

    assert len(trades1) == 5
    assert len(trades2) == 5
