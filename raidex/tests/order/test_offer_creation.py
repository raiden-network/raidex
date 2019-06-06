import pytest

from raidex.raidex_node.order.offer import *


def test_factory_create_from_basic(basic_offer):

    offer = OfferFactory.create_from_basic(basic_offer, TraderRole.MAKER)

    assert isinstance(offer, Offer)
    assert offer == basic_offer


def test_factory_create_offer(offer_type, base_amount, quote_amount, lifetime):

    offer = OfferFactory.create_offer(offer_type, base_amount, quote_amount, lifetime, TraderRole.MAKER)

    assert isinstance(offer, Offer)