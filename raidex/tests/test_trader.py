import gevent.hub
import pytest
from raidex.raidex_node.offer_book import OfferType
from raidex.raidex_node.trader.trader import TraderClient


@pytest.fixture()
def trader1(accounts):
    return TraderClient(accounts[1].address)


@pytest.fixture()
def trader2(accounts):
    return TraderClient(accounts[2].address)


def test_atomic_exchange(trader1, trader2):
    result1 = trader1.expect_exchange_async(OfferType.SELL, 100, 10, trader2.address, 1)
    gevent.sleep(0.001)  # give chance to execute async function
    result2 = trader2.exchange_async(OfferType.SELL, 100, 10, trader1.address, 1)
    gevent.sleep(0.001)  # give chance to execute async function

    assert result1.get()
    assert result2.get()

    assert trader1.base_amount == 200
    assert trader2.base_amount == 0
    assert trader1.counter_amount == 90
    assert trader2.counter_amount == 110


def test_false_price_atomic_exchange(trader1, trader2):
    with pytest.raises(gevent.hub.LoopExit, message="Should block forever"):
        result1 = trader1.expect_exchange_async(OfferType.SELL, 100, 10, trader2.address, 1)
        result2 = trader2.exchange_async(OfferType.SELL, 100, 11, trader1.address, 1)

        result1.wait()
        result2.wait()

    assert True


def test_false_type_atomic_exchange(trader1, trader2):
    with pytest.raises(gevent.hub.LoopExit, message="Should block forever"):
        result1 = trader1.expect_exchange_async(OfferType.SELL, 100, 10, trader2.address, 1)
        result2 = trader2.exchange_async(OfferType.BUY, 100, 10, trader1.address, 1)

        result1.wait()
        result2.wait()

    assert True
