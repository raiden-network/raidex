import pytest
from eth_utils import to_checksum_address
from raidex.utils import make_address
from raidex.raidex_node.market import TokenPair
from contextlib import ExitStack as does_not_raise
from raidex.raidex_node.order.offer import OfferType


@pytest.fixture
def valid_binary_address():
    return make_address()


@pytest.mark.parametrize('first_address', [
    pytest.lazy_fixture('valid_binary_address'),
    bytes(21),
    to_checksum_address(make_address())])
@pytest.mark.parametrize('second_address', [
    pytest.lazy_fixture('valid_binary_address'),
    bytes(21),
    to_checksum_address(make_address())])
def test_market_initialization(valid_binary_address, first_address, second_address):

    exception = pytest.raises(ValueError)

    if valid_binary_address == first_address == second_address:
        exception = does_not_raise()

    with exception:
        TokenPair(base_token=first_address, quote_token=second_address)


def test_checksum_addresses(market):

    assert market.checksum_base_address == to_checksum_address(market.base_token)
    assert market.checksum_quote_address == to_checksum_address(market.quote_token)


def test_get_offer_type(market, token_set, valid_binary_address):

    assert market.get_offer_type(token_set['base']['address'], token_set['quote']['address']) == OfferType.BUY
    assert market.get_offer_type(token_set['quote']['address'], token_set['base']['address']) == OfferType.SELL

    assert market.get_offer_type(to_checksum_address(valid_binary_address), token_set['base']['address']) is None


