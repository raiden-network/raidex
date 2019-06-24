import gc
import gevent
from collections import namedtuple

import pytest

from eth_utils import keccak, decode_hex
from eth_keys import keys
import structlog
from raidex.raidex_node.market import TokenPair
from raidex.utils import make_address
from raidex.signing import generate_random_privkey



@pytest.fixture(autouse=True)
def configure_structlog():
    """
    Configures cleanly structlog for each test method.
    """
    structlog.reset_defaults()
    structlog.configure(
        processors=[
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.KeyValueRenderer(),
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        #logger_factory=LoggerFactory(),
        cache_logger_on_first_use=False,
    )


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
    assets = [decode_hex(keys.PrivateKey(keccak(text="asset{}".format(i))).public_key.to_checksum_address()) for i in range(2)]
    return assets


@pytest.fixture()
def accounts():
    Account = namedtuple("Account", "privatekey address")
    private_keys = [generate_random_privkey() for _ in range(4)]
    return [Account(privkey, decode_hex(keys.PrivateKey(privkey).public_key.to_checksum_address())) for privkey in private_keys]


@pytest.fixture
def token_set():
    return {
        'base': {
            'address': make_address(),
            'decimal': 3
        },
        'quote': {
            'address': make_address(),
            'decimal': 18
        },
    }


@pytest.fixture()
def market(token_set):
    return TokenPair(base_token=token_set['base']['address'],
                     base_decimal=token_set['base']['decimal'],
                     quote_token=token_set['quote']['address'],
                     quote_decimal=token_set['quote']['decimal'])
