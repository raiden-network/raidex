from ethereum.utils import sha3
from rex.messages import Offer


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
    assert o.sender == accounts[0].address


def test_offers(offers, accounts):
    senders = [acc.address for acc in accounts]
    for offer in offers:
        assert offer.sender in senders
