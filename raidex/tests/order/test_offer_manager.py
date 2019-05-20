import pytest

from queue import Queue

from raidex.raidex_node.order.events import \
    OfferInitStateChange

from raidex.raidex_node.order.offer import OfferType, OfferFactory
from raidex.raidex_node.order.offer_manager import OfferManager


@pytest.fixture
def event_queue():
    return Queue()


@pytest.fixture
def offer_manager(event_queue):
    return OfferManager(event_queue)


@pytest.fixture
def offer_init_event():
    return OfferInitStateChange(OfferType.BUY, 1, 1, 10)


@pytest.fixture
def offer(offer_init_event):
    return OfferFactory.create_offer_from_event(offer_init_event)


def test_timeout_offer(offer):
    offer.timeout()

    assert offer.state == 'cancelled'


def test_receive_commitment_prove(offer):
    offer.receive_commitment_prove()
    assert offer.state == 'proved'

    offer.timeout()
    assert offer.state == 'cancelled'


def test_receive_published_offer(offer):
    offer.receive_commitment_prove()
    assert offer.state == 'proved'

    offer.received_offer()
    assert offer.state == 'published'
