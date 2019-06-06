import pytest

from raidex.raidex_node.order.offer import OfferFactory, TraderRole
from raidex.raidex_node.order.limit_order import LimitOrder
from raidex.raidex_node.order.offer_manager import OfferManager, logger


@pytest.fixture
def offer_manager():
    return OfferManager()


@pytest.fixture
def limit_order(random_id, offer_type, base_amount):
    return LimitOrder(random_id, offer_type, base_amount, 1)


@pytest.fixture
def amount_left(limit_order):
    return limit_order.amount


@pytest.fixture
def internal_offer(basic_offer):
    return OfferFactory.create_from_basic(basic_offer, TraderRole.MAKER)


def test_add_offer(offer_manager, internal_offer):

    assert not offer_manager.has_offer(internal_offer.offer_id)
    assert offer_manager.get_offer(internal_offer.offer_id) is None

    offer_manager.add_offer(internal_offer)

    assert offer_manager.has_offer(internal_offer.offer_id)
    assert offer_manager.get_offer(internal_offer.offer_id) == internal_offer


def test_add_take_offer(offer_manager, basic_offer):

    assert not offer_manager.has_offer(basic_offer.offer_id)
    assert offer_manager.get_offer(basic_offer.offer_id) is None

    take_offer = offer_manager.create_take_offer(basic_offer)

    assert take_offer == basic_offer
    assert offer_manager.has_offer(basic_offer.offer_id)
    assert offer_manager.get_offer(basic_offer.offer_id) == basic_offer


def test_add_make_offer(offer_manager, limit_order, amount_left):

    offer = offer_manager.create_make_offer(limit_order, amount_left)

    assert offer_manager.has_offer(offer.offer_id)
    assert offer_manager.get_offer(offer.offer_id) == offer
    assert offer.quote_amount == int(amount_left * limit_order.price)


