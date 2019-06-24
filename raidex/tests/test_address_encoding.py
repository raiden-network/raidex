import pytest

from eth_utils import to_normalized_address
from raidex.utils import make_address
from raidex.utils.address import *


@pytest.fixture
def random_address():
    return make_address()


@pytest.fixture
def random_string():
    return "topic"


@pytest.fixture()
def random(request):
    return request.getfixturevalue(request.param)


def test_encode_decode_address(random_address):
    checksum_address = encode_address(random_address)
    assert is_checksum_address(checksum_address)

    assert random_address == binary_address(checksum_address)


def test_binary_decoding(random_address):

    assert binary_address(random_address) == random_address

    with pytest.raises(TypeError):
        binary_address("Not a valid address")


def test_topic_encoding(random_address):

    assert encode_topic(random_address) == to_checksum_address(random_address)

    normalized_address = to_normalized_address(random_address)
    assert encode_topic(normalized_address) == to_checksum_address(random_address)

    some_topic_string = "topic"
    assert encode_topic(some_topic_string) == some_topic_string


@pytest.mark.parametrize('param', [bytes(21), int(23)])
def test_topic_encoding_failures(param):

    with pytest.raises(TypeError):
        encode_topic(param)


@pytest.mark.parametrize('random', ['random_address', 'random_string'], indirect=True)
def test_decode_topic(random):

    encoded = encode_topic(random)
    assert decode_topic(encoded) == random

