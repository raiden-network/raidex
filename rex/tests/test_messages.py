from collections import namedtuple
import pytest
from ethereum.utils import privtoaddr, sha3
from rex.messages import Offer


@pytest.fixture()
def assets():
    assets = [privtoaddr(sha3("asset{}".format(i))) for i in range(2)]
    return assets


@pytest.fixture()
def accounts():
    Account = namedtuple('Account', 'privatekey address')
    privkeys = [sha3("account:{}".format(i)) for i in range(2)]
    accounts = [Account(pk, privtoaddr(pk)) for pk in privkeys]
    return accounts


def test_offer(assets):
    o = Offer(assets[0], 100, assets[1], 110, sha3('offer id'), 10)
    assert isinstance(o, Offer)
    serial = o.serialize(o)
    assert Offer.deserialize(serial) == o


def test_hashable(assets):
    o = Offer(assets[0], 100, assets[1], 110, sha3('offer id'), 10)
    assert o.hash


def test_signed(accounts, assets):
    o = Offer(assets[0], 100, assets[1], 110, sha3('offer id'), 10)
    o.sign(accounts[0].privatekey)
