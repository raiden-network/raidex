import pytest
from raidex.utils import timestamp
from raidex.commitment_service.mock import CommitmentServiceClientMock, NonFailingCommitmentServiceGlobal
from raidex.message_broker.message_broker import MessageBroker
from raidex.raidex_node.exchange_task import MakerExchangeTask, TakerExchangeTask
from raidex.raidex_node.offer_book import Offer, OfferType
from raidex.raidex_node.trader.trader import TraderClientMock
from raidex.signing import Signer


@pytest.fixture()
def offers():
    return [Offer(OfferType.BUY, 100, 1000, offer_id=123, timeout=timestamp.time_plus(1)),
            Offer(OfferType.BUY, 200, 2000, offer_id=124, timeout=timestamp.time_plus(1))]


@pytest.fixture()
def message_broker():
    return MessageBroker()


@pytest.fixture()
def cs_global():
    return NonFailingCommitmentServiceGlobal()


@pytest.fixture()
def commitment_service_maker(accounts, message_broker, cs_global, token_pair):
    signer = Signer(accounts[0].privatekey)
    return CommitmentServiceClientMock(signer, token_pair, message_broker, cs_global=cs_global)


@pytest.fixture()
def commitment_service_taker(accounts, message_broker, cs_global, token_pair):
    signer = Signer(accounts[1].privatekey)
    return CommitmentServiceClientMock(signer, token_pair, message_broker, cs_global=cs_global)


@pytest.fixture()
def trader_maker(accounts):
    return TraderClientMock(accounts[0].address)


@pytest.fixture()
def trader_taker(accounts):
    return TraderClientMock(accounts[1].address)


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
