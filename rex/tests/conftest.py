import random
import time
from collections import namedtuple

import pytest
from ethereum.utils import privtoaddr, sha3

from rex.messages import Offer, CommitmentServiceAdvertisement, SwapExecution, SwapCompleted
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
    fee_rates = [int(random.random() * 2 ** 32) for _ in privkeys]
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
def taker_swap_executions(accounts, offers):
    taker_swap_executions = []
    for offer in offers:
        taker = None
        while taker is None or taker.address == offer.sender:
            taker = random.choice(accounts)
        sw_execution = SwapExecution(offer.offer_id, milliseconds.time_int())
        sw_execution.sign(taker.privatekey)
        taker_swap_executions.append(sw_execution)
    return taker_swap_executions


@pytest.fixture()
def maker_swap_executions(accounts, offers):
    maker_swap_executions = []
    for offer in offers:
        maker = None
        for acc in accounts:
            if offer.sender == acc.address:
                maker = acc
                break
        if maker is None:
            continue
        sw_execution = SwapExecution(offer.offer_id, milliseconds.time_int())
        sw_execution.sign(maker.privatekey)
        maker_swap_executions.append(sw_execution)
    return maker_swap_executions


@pytest.fixture()
def swap_completeds(commitment_services, offers):
    swap_completeds = []
    for offer in offers:
        cs = random.choice(commitment_services)
        # TODO eventually construct them in a way, that swap executions have an earlier time
        sw_completed = SwapCompleted(offer.offer_id, milliseconds.time_int())
        sw_completed.sign(cs.private_key)
        swap_completeds.append(sw_completed)
    return swap_completeds


@pytest.fixture()
def commitment_service_advertisements(commitment_services):
    commitment_service_advertisements = []
    for cs in commitment_services:
        csa = CommitmentServiceAdvertisement(
            cs.address,
            cs.commitment_asset,
            cs.fee_rate
        )
        csa.sign(cs.private_key)
        commitment_service_advertisements.append(csa)
    return commitment_service_advertisements
