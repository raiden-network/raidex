import random
from collections import namedtuple

import pytest

from ethereum.utils import sha3, privtoaddr, big_endian_to_int
from ethereum import slogging

from raidex import messages
from raidex.utils import milliseconds, DEFAULT_RAIDEX_PORT


@pytest.fixture(autouse=True)
def logging_level():
    slogging.configure(':DEBUG')


@pytest.fixture()
def assets():
    assets = [privtoaddr(sha3("asset{}".format(i))) for i in range(2)]
    return assets


@pytest.fixture()
def accounts():
    Account = namedtuple('Account', 'privatekey address')
    privkeys = [sha3("account:{}".format(i)) for i in range(3)]
    accounts = [Account(pk, privtoaddr(pk)) for pk in privkeys]
    return accounts



@pytest.fixture(params=[10])
def offer_msgs(request, accounts, assets):
    """
    This fixture generates `num_offers` with more or less random values.
    """
    random.seed(42)
    offers = []
    for i in range(request.param):
        maker = accounts[i % 2]
        offer = messages.SwapOffer(assets[i % 2],
                                   random.randint(1, 100),
                                   assets[1 - i % 2],
                                   random.randint(1, 100),
                                   big_endian_to_int(sha3('offer {}'.format(i))),
                                   milliseconds.time_int() + i * 1000
                                   )
        offer.sign(maker.privatekey)
        offers.append(offer)
    return offers

