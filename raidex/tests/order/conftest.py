import pytest
import structlog

from raidex.utils.random import create_random_32_bytes_id
from raidex.utils.timestamp import time_plus
from raidex.raidex_node.order.offer import OfferType, BasicOffer, OfferFactory, TraderRole


@pytest.fixture(autouse=True)
def logging_level():
    structlog.configure(':DEBUG')

@pytest.fixture
def random_id():
    return create_random_32_bytes_id()


@pytest.fixture
def offer_type():
    return OfferType.BUY


@pytest.fixture
def base_amount():
    return 1


@pytest.fixture
def quote_amount():
    return 1


@pytest.fixture
def lifetime():
    return 60


@pytest.fixture
def timeout_date(lifetime):
    return time_plus(seconds=lifetime)


@pytest.fixture
def basic_offer(random_id, offer_type, base_amount, quote_amount, timeout_date):

    return BasicOffer(offer_id=random_id,
                      offer_type=offer_type,
                      base_amount=base_amount,
                      quote_amount=quote_amount,
                      timeout_date=timeout_date)


@pytest.fixture
def internal_offer(basic_offer):
    return OfferFactory.create_from_basic(basic_offer, TraderRole.MAKER)


