import string
import random

from ethereum.utils import privtoaddr, sha3, big_endian_to_int
from rlp.utils import decode_hex as rlp_decode_hex, encode_hex as rlp_encode_hex
from raidex.exceptions import UntradableAssetPair

ETHER_TOKEN_ADDRESS = privtoaddr(sha3('ether'))
DEFAULT_RAIDEN_PORT = 9999  # no raiden dependency for now
DEFAULT_RAIDEX_PORT = DEFAULT_RAIDEN_PORT + 1


def make_address():
    return bytes(''.join(random.choice(string.printable) for _ in range(20)))


def make_privkey_address():
    privkey = sha3(''.join(random.choice(string.printable) for _ in range(20)))
    address = privtoaddr(privkey)
    return privkey, address


def decode_hex(data):
    return rlp_decode_hex(data)


def encode_hex(data):
    return rlp_encode_hex(data)


def pex(data):
    return str(data).encode('hex')[:8]


def get_market_from_asset_pair(asset_pair):
    """
    Takes a 2-tuple of decoded assets and sorts them based on their int representation.
    This always returns a deterministic `market`-tuple, which is one of the two possible asset_pair permutations.

    The sorting algorithm  could always be changed later, it just has to be used consistently.

    :param asset_pair: decoded 2-tuple of ethereum assets
    :return: decoded 2-tuple of ethereum assets (the deterministic `market` tuple)
    """
    # assume that asset_pair is decoded!
    assert isinstance(asset_pair, tuple)
    assert len(asset_pair) == 2
    list_int = [big_endian_to_int(asset) for asset in asset_pair]

    # sort the int-converted list, so that higher values appear first
    if list_int[0] < list_int[1]:
        market = asset_pair
    elif list_int[0] == list_int[1]:
        raise UntradableAssetPair()
    else:
        market = asset_pair[::-1]  # reverse the tuple

    return market
