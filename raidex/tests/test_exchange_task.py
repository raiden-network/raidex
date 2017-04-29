import pytest
import raidex.utils.milliseconds as milliseconds
from raidex.commitment_service.commitment_service import CommitmentService
from raidex.message_broker.message_broker import MessageBroker
from raidex.raidex_node.exchange_task import MakerExchangeTask, TakerExchangeTask
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.offer_book import Offer, OfferType
from raidex.raidex_node.trader.trader import TraderClient


@pytest.fixture()
def offers():
    return [Offer(OfferType.BUY, 100, 1000, offer_id=123, timeout=milliseconds.time_plus(1)),
            Offer(OfferType.BUY, 200, 2000, offer_id=124, timeout=milliseconds.time_plus(1))]


@pytest.fixture()
def message_broker():
    return MessageBroker()


@pytest.fixture()
def commitment_service_maker(assets, accounts, message_broker):
    return CommitmentService(TokenPair(assets[0], assets[1]), accounts[0].privatekey, message_broker)


@pytest.fixture()
def commitment_service_taker(assets, accounts, message_broker):
    return CommitmentService(TokenPair(assets[0], assets[1]), accounts[1].privatekey, message_broker)


@pytest.fixture()
def trader_maker(accounts):
    return TraderClient(accounts[0].address)


@pytest.fixture()
def trader_taker(accounts):
    return TraderClient(accounts[1].address)


def test_exchange_task(offers, accounts, commitment_service_taker, commitment_service_maker, message_broker,
                       trader_maker, trader_taker):
    offer = offers[0]
    offer.maker_address = accounts[0].address
    maker_exchange_task = MakerExchangeTask(offer, accounts[0].address, commitment_service_maker, message_broker,
                                            trader_maker)
    taker_exchange_task = TakerExchangeTask(offer, commitment_service_taker, message_broker, trader_taker)

    maker_exchange_task.start()
    taker_exchange_task.start()

    assert maker_exchange_task.get()
    assert taker_exchange_task.get()


def test_not_possible_exchange_task(offers, accounts, commitment_service_taker, commitment_service_maker,
                                    message_broker, trader_maker, trader_taker):
    offer = offers[0]
    offer.maker_address = accounts[0].address
    maker_exchange_task = MakerExchangeTask(offers[1], accounts[0].address, commitment_service_maker, message_broker,
                                            trader_maker)
    taker_exchange_task = TakerExchangeTask(offer, commitment_service_taker, message_broker, trader_taker)

    maker_exchange_task.start()
    taker_exchange_task.start()

    assert not maker_exchange_task.get()
    assert not taker_exchange_task.get()
