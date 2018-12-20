import gc
import gevent
from collections import namedtuple

import pytest

from eth_utils import keccak
from eth_keys import keys
import structlog

from raidex.raidex_node.market import TokenPair
from raidex.signing import generate_random_privkey


@pytest.fixture(autouse=True)
def logging_level():
    structlog.configure(':DEBUG')


def number_of_greenlets_running():
    return len([obj for obj in gc.get_objects() if isinstance(obj, gevent.Greenlet) and obj])


@pytest.fixture(autouse=True)
def shutdown_greenlets():
    assert number_of_greenlets_running() == 0
    yield
    gevent.killall([obj for obj in gc.get_objects() if isinstance(obj, gevent.Greenlet)])
    assert number_of_greenlets_running() == 0


# TODO remove / factor out
@pytest.fixture()
def assets():
    assets = [keys.PrivateKey(keccak("asset{}".format(i))).public_key.to_address() for i in range(2)]
    return assets


@pytest.fixture()
def accounts():
    Account = namedtuple("Account", "privatekey address")
    private_keys = [generate_random_privkey() for _ in range(4)]
    return [Account(privkey, keys.PrivateKey(privkey).public_key.to_address()) for privkey in private_keys]


@pytest.fixture()
def token_pair():
    return TokenPair.random()
