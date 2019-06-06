import pytest

from eth_utils import keccak

from gevent.queue import PriorityQueue
from raidex import messages
from raidex.utils import timestamp
from raidex.commitment_service.swap import SwapFactory
from raidex.message_broker.message_broker import MessageBroker
from raidex.signing import Signer
from raidex.trader_mock.trader import (
    TraderClientMock,
    Trader,
)
from raidex.commitment_service.node import CommitmentService


@pytest.fixture
def commitment_service_account(accounts):
    return accounts[0]


@pytest.fixture
def maker_account(accounts):
    return accounts[1]


@pytest.fixture
def taker_account(accounts):
    return accounts[2]


@pytest.fixture
def other_account(accounts):
    return accounts[3]


@pytest.fixture
def message_broker():
    return MessageBroker()


@pytest.fixture()
def trader():
    return Trader()


@pytest.fixture
def swaps():
    return {}


@pytest.fixture
def message_queue():
    return PriorityQueue()


@pytest.fixture
def refund_queue():
    return PriorityQueue()


@pytest.fixture
def factory(swaps, refund_queue, message_queue):
    return SwapFactory(swaps, refund_queue, message_queue)


@pytest.fixture()
def trader_client1(accounts, trader):
    return TraderClientMock(accounts[1].address, commitment_balance=10, trader=trader)


@pytest.fixture()
def trader_client2(accounts, trader):
    return TraderClientMock(accounts[2].address, commitment_balance=10, trader=trader)


@pytest.fixture()
def commitment_service(message_broker, trader):
    signer = Signer.random()
    trader_client = TraderClientMock(signer.address, trader=trader)
    return CommitmentService(signer, message_broker, trader_client, fee_rate=0.01)


@pytest.fixture
def maker_commitment_msg():
    seconds_to_timeout = 0.1
    timeout = timestamp.time_plus(seconds_to_timeout)
    offer_id = 123
    maker_commitment_msg = messages.MakerCommitment(offer_id=offer_id, offer_hash=keccak(offer_id),
                                                    timeout=timeout, amount=5)
    return maker_commitment_msg


@pytest.fixture
def taker_commitment_msg():
    seconds_to_timeout = 0.1
    timeout = timestamp.time_plus(seconds_to_timeout)
    offer_id = 123
    taker_commitment_msg = messages.Commitment(offer_id=offer_id, offer_hash=keccak(offer_id),
                                                    timeout=timeout, amount=5)
    return taker_commitment_msg


@pytest.fixture
def swap_execution_msg():
    swap_execution_msg = messages.SwapExecution(123, timestamp.time())
    return swap_execution_msg