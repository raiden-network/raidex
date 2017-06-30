import gevent.hub
import pytest

from ethereum.utils import sha3
from raidex.raidex_node.offer_book import OfferType
from raidex.raidex_node.trader.trader import Trader, TraderClientMock, TransferReceivedListener


@pytest.fixture()
def trader():
    # global singleton trader, will get reinitialised after every test in order to teardown old listeners etc
    return Trader()


@pytest.fixture()
def trader_client1(accounts, trader):
    return TraderClientMock(accounts[1].address, commitment_balance=10, trader=trader)


@pytest.fixture()
def trader_client2(accounts, trader):
    return TraderClientMock(accounts[2].address, commitment_balance=10, trader=trader)


def test_atomic_exchange(trader_client1, trader_client2):
    result1 = trader_client1.expect_exchange_async(OfferType.SELL, 100, 10, trader_client2.address, 1)
    gevent.sleep(0.001)  # give chance to execute async function
    result2 = trader_client2.exchange_async(OfferType.SELL, 100, 10, trader_client1.address, 1)
    gevent.sleep(0.001)  # give chance to execute async function

    assert result1.get()
    assert result2.get()

    assert trader_client1.base_amount == 200
    assert trader_client2.base_amount == 0
    assert trader_client1.counter_amount == 90
    assert trader_client2.counter_amount == 110


def test_false_price_atomic_exchange(trader_client1, trader_client2):
    with pytest.raises(gevent.hub.LoopExit, message="Should block forever"):
        result1 = trader_client1.expect_exchange_async(OfferType.SELL, 100, 10, trader_client2.address, 1)
        result2 = trader_client2.exchange_async(OfferType.SELL, 100, 11, trader_client1.address, 1)

        result1.wait()
        result2.wait()

    assert True


def test_false_type_atomic_exchange(trader_client1, trader_client2):
    with pytest.raises(gevent.hub.LoopExit, message="Should block forever"):
        result1 = trader_client1.expect_exchange_async(OfferType.SELL, 100, 10, trader_client2.address, 1)
        result2 = trader_client2.exchange_async(OfferType.BUY, 100, 10, trader_client1.address, 1)

        result1.wait()
        result2.wait()

    assert True


def test_transfer(trader_client1, trader_client2):
    identifier = sha3('id')
    amount = 5

    # start the balanceupdate tasks
    trader_client1.start()
    trader_client2.start()

    received_listener = TransferReceivedListener(trader_client2)
    received_listener.start()

    assert trader_client2.commitment_balance == 10
    result1 = trader_client1.transfer(trader_client2.address, amount, identifier)
    gevent.sleep(0.1)

    assert result1

    receipt = received_listener.get()

    assert trader_client1.commitment_balance == 5
    assert trader_client2.commitment_balance == 15

    assert receipt.sender == trader_client1.address
    assert receipt.amount == 5
    assert receipt.identifier == identifier
