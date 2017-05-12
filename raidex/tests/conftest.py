import random
import gc
import gevent
from collections import namedtuple

import pytest

from ethereum.utils import sha3, privtoaddr, big_endian_to_int
from ethereum import slogging

from raidex import messages
from raidex.utils import timestamp, DEFAULT_RAIDEX_PORT


@pytest.fixture(autouse=True)
def logging_level():
    slogging.configure(':DEBUG')


def number_of_greenlets_running():
    return len([obj for obj in gc.get_objects() if isinstance(obj, gevent.Greenlet) and obj])


@pytest.fixture(autouse=True)
def shutdown_greenlets():
    assert number_of_greenlets_running() == 0
    yield
    gevent.killall([obj for obj in gc.get_objects() if isinstance(obj, gevent.Greenlet)])
    assert number_of_greenlets_running() == 0

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
