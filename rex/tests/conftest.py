import random
from collections import namedtuple

import pytest
from ethereum.utils import privtoaddr, sha3

from rex.messages import Offer, CommitmentServiceAdvertisement
from rex.utils import milliseconds
from rex.commitment_service import CommitmentService


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

@pytest.fixture()
def commitment_services():
    privkeys = [sha3("cs_account:{}".format(i)) for i in range(2)]
    fee_rates = [random.random() for _ in privkeys] # XXX check range
    commitment_services = [CommitmentService(pk, fr)
                           for pk, fr in zip(privkeys, fee_rates)]
    return commitment_services

@pytest.fixture(params=[10])
def offers(request, accounts, assets):
    """
    This fixture generates `num_offers` with more or less random values.
    """
    random.seed(42)
    offers = []
    for i in range(request.param):
        maker = accounts[i % 2]
        offer = Offer(assets[i % 2],
                      random.randint(1, 100),
                      assets[1 - i % 2],
                      random.randint(1, 100),
                      sha3('offer {}'.format(i)),
                      milliseconds.time_int() + i * 1000
                      )
        offer.sign(maker.privatekey)
        offers.append(offer)
    return offers

@pytest.fixture()
def commitment_service_advertisements(commitment_services):
    commitment_service_advertisements = [
        CommitmentServiceAdvertisement(
            cs.address,
            cs.commitment_asset,
            cs.fee_rate
        ) for cs in commitment_services
    ]
    return commitment_service_advertisements
