import random
from collections import namedtuple

import pytest

from ethereum.utils import sha3, privtoaddr, big_endian_to_int
from ethereum import slogging


from raiden.network.discovery import Discovery as RaidenDiscovery

from raidex import messages
from raidex.utils import milliseconds, DEFAULT_RAIDEX_PORT
from raidex.commitment_service.server import CommitmentService
from raidex.network import DummyTransport
from raidex.protocol import BroadcastProtocol, RaidexProtocol


@pytest.fixture(autouse=True)
def logging_level():
    slogging.configure(':INFO')


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


@pytest.fixture(params=[2])
def cs_accounts():
    Account = namedtuple('Account', 'privatekey address')
    privkeys = [sha3("cs_account:{}".format(i)) for i in range(2)]
    accounts = [Account(pk, privtoaddr(pk)) for pk in privkeys]
    return accounts


@pytest.fixture()
def dummy_discovery():
    # the discovery will use the raiden discovery
    dummy_discovery = RaidenDiscovery()
    return dummy_discovery


@pytest.fixture()
def commitment_services(cs_accounts, dummy_discovery):
    Raiden = namedtuple('Raiden', ['api'] )
    commitment_services = []
    for i, acc in enumerate(cs_accounts):
        host, port = '{}'.format(i), DEFAULT_RAIDEX_PORT
        dummy_transport = DummyTransport(host=host, port=port)
        raiden = Raiden(None) # only to satisfy the argument
        # TODO: create a DummyRaiden for easy client-CS interaction
        fee_rate = int(random.random() * 2 ** 32)

        commitment_service = CommitmentService(
            raiden,
            acc.privatekey,
            fee_rate,
            RaidexProtocol,
            dummy_transport,
            dummy_discovery,
            None,
            BroadcastProtocol
        )
        # emulate the raiden port-mapping here
        dummy_discovery.register(commitment_service.address, host, port - 1)
        commitment_services.append(commitment_service)
    return commitment_services





