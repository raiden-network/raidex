import pytest
import gevent

from raidex.tests.utils import float_isclose

from raidex.commitment_service.node import CommitmentService
from raidex.raidex_node.commitment_service.client import CommitmentServiceClient
from raidex.raidex_node.trader.trader import Trader, TraderClientMock
from raidex import messages
from raidex.message_broker.message_broker import MessageBroker
from raidex.utils import timestamp
from raidex.raidex_node.raidex_node import RaidexNode
from raidex.raidex_node.offer_book import Offer, OfferType, generate_random_offer_id
from raidex.signing import Signer


@pytest.fixture()
def message_broker():
    return MessageBroker()


@pytest.fixture()
def trader():
    return Trader()


@pytest.fixture()
def commitment_service(message_broker, trader):
    signer = Signer.random()
    trader_client = TraderClientMock(signer.address, trader=trader)
    return CommitmentService(signer, message_broker, trader_client, fee_rate=0.01)


@pytest.fixture()
def raidex_nodes(token_pair, trader, accounts, message_broker, commitment_service):
    nodes = []

    for account in accounts:
        signer = Signer(account.privatekey)
        trader_client = TraderClientMock(signer.address, commitment_balance=10, trader=trader)
        commitment_service_client = CommitmentServiceClient(signer, token_pair, trader_client,
                                                            message_broker, commitment_service.address,
                                                            fee_rate=commitment_service.fee_rate)

        node = RaidexNode(signer.address, token_pair, commitment_service_client, message_broker, trader_client)
        nodes.append(node)
    return nodes


def test_node_to_commitment_service_integration(raidex_nodes, commitment_service):

    commitment_service.start()
    [node.start() for node in raidex_nodes]
    maker_node = raidex_nodes[0]
    taker_node = raidex_nodes[1]
    failed_taker = raidex_nodes[2]

    # this are the initial commitment balances
    initial_maker_balance = maker_node.trader_client.commitment_balance
    initial_taker_balance = taker_node.trader_client.commitment_balance
    initial_commitment_service_balance = commitment_service.trader_client.commitment_balance

    offer_id = generate_random_offer_id()
    offer = Offer(OfferType.SELL, 100, 1000, offer_id=offer_id, timeout=timestamp.time_plus(seconds=0, milliseconds=500))
    maker_commit_result = maker_node.commitment_service.maker_commit_async(offer, commitment_amount=5)
    gevent.sleep(0.01)

    assert commitment_service.trader_client.commitment_balance == initial_commitment_service_balance + 5
    assert maker_node.trader_client.commitment_balance == initial_maker_balance - 5

    commitment_service_balance = commitment_service.trader_client.commitment_balance

    maker_proven_offer = maker_commit_result.get()
    assert isinstance(maker_proven_offer, messages.ProvenOffer)

    # CommitmentProof has to be signed by the CS
    assert maker_proven_offer.commitment_proof.sender == commitment_service.address
    # ProvenOffer has to be signed by the maker
    assert maker_proven_offer.sender == maker_node.address

    # broadcast the ProvenOffer
    maker_node.message_broker.broadcast(maker_proven_offer)
    gevent.sleep(0.01)

    # the taker needs to have the additional commitment-amount information from the ProvenOffer
    # he should have got it from the broadcasted ProvenOffer
    taker_internal_offer = taker_node.offer_book.get_offer_by_id(offer.offer_id)

    taker_commit_result = taker_node.commitment_service.taker_commit_async(taker_internal_offer)
    gevent.sleep(0.01)

    assert commitment_service.trader_client.commitment_balance == commitment_service_balance + 5
    assert taker_node.trader_client.commitment_balance == initial_taker_balance - 5

    taker_proven_commitment = taker_commit_result.get()
    assert isinstance(taker_proven_commitment, messages.ProvenCommitment)
    assert taker_proven_commitment.commitment_proof.sender == commitment_service.address
    assert taker_proven_commitment.sender == taker_node.address

    maker_node.commitment_service.report_swap_executed(offer.offer_id)
    taker_node.commitment_service.report_swap_executed(offer.offer_id)

    gevent.sleep(0.01)

    # should be processed by the commitment_service, offer_id usable again
    assert offer_id not in commitment_service.swaps

    # Check the earnings and refunds
    assert float_isclose(maker_node.trader_client.commitment_balance,
                         initial_maker_balance - (5 * commitment_service.fee_rate))
    assert float_isclose(taker_node.trader_client.commitment_balance,
                         initial_taker_balance - (5 * commitment_service.fee_rate))
    assert float_isclose(commitment_service.trader_client.commitment_balance, 10 + 2 * (5 * commitment_service.fee_rate))

    # overall balance shouldn't have changed
    assert maker_node.trader_client.commitment_balance + taker_node.trader_client.commitment_balance \
        + commitment_service.trader_client.commitment_balance == initial_commitment_service_balance \
        + initial_taker_balance + initial_maker_balance
