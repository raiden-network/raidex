import pytest
import gevent

from raidex.tests.utils import float_isclose

from raidex.commitment_service.client import CommitmentService as CommitmentServiceClient
from raidex.commitment_service.server import CommitmentService
from raidex.raidex_node.trader.trader import Trader, TraderClient
from raidex import messages
from raidex.message_broker.message_broker import MessageBroker
from raidex.utils import timestamp, make_privkey_address
from raidex.raidex_node.raidex_service import Raidex
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.offer_book import Offer, OfferType


@pytest.fixture()
def token_pair(assets):
    return TokenPair(assets[0], assets[1])


@pytest.fixture()
def message_broker():
    # global singleton message broker
    return MessageBroker()


@pytest.fixture()
def trader():
    # global singleton trader, will get reinitialised after every test in order to teardown old listeners etc
    return Trader()


@pytest.fixture()
def commitment_service(message_broker, trader):
    privkey, _ = make_privkey_address()
    commitment_service = CommitmentService(message_broker, privkey, 0.01)
    # manually set member to singleton trader:
    commitment_service.trader_client.trader = trader
    return commitment_service


@pytest.fixture()
def raidex_nodes(token_pair, trader, accounts, message_broker, commitment_service):
    nodes = []
    for account in accounts:
        node_address = account.address
        privkey = account.privatekey
        cs_address = commitment_service.address

        trader_client = TraderClient(node_address, commitment_balance=10, trader=trader)

        def _sign(message, privkey_):
            message.sign(privkey_)

        cs_client = CommitmentServiceClient(node_address, token_pair,
                                            lambda message, privkey_=privkey: _sign(message, privkey_),
                                            trader_client,
                                            message_broker,
                                            cs_address)

        nodes.append(Raidex(token_pair, privkey, message_broker, trader_client, cs_client))
    return nodes


def test_node_to_commitment_service_integration(raidex_nodes, commitment_service):
    commitment_service.start()
    [node.start() for node in raidex_nodes]
    maker = raidex_nodes[0]
    taker = raidex_nodes[1]
    failed_taker = raidex_nodes[2]

    # this are the initial commitment balances
    maker_commitment_balance = maker.trader_client.commitment_balance
    taker_commitment_balance = taker.trader_client.commitment_balance
    failed_taker_commitment_balance = failed_taker.trader_client.commitment_balance
    cs_commitment_balance = commitment_service.trader_client.commitment_balance

    assert maker_commitment_balance == 10
    assert taker_commitment_balance == 10
    assert failed_taker_commitment_balance == 10
    assert cs_commitment_balance == 10

    assert maker.message_broker == taker.message_broker == commitment_service.message_broker

    offer = Offer(OfferType.SELL, 100, 1000, offer_id=123, timeout=timestamp.time_plus(seconds=0, milliseconds=500))
    maker_commit_result = maker.commitment_service.maker_commit_async(offer, commitment_amount=5)
    gevent.sleep(0.01)
    assert commitment_service.trader_client.commitment_balance == 15
    assert maker.trader_client.commitment_balance == 5

    maker_proven_offer = maker_commit_result.get()
    assert isinstance(maker_proven_offer, messages.ProvenOffer)

    # CommitmentProof has to be signed by the CS
    assert maker_proven_offer.commitment_proof.sender == commitment_service.address
    # ProvenOffer has to be signed by the maker
    assert maker_proven_offer.sender == maker.address

    # broadcast the ProvenOffer

    maker.message_broker.broadcast(maker_proven_offer)
    gevent.sleep(0.01)

    # the taker needs to have the additional information from the ProvenOffer (commitment-amount and offer_hash)
    # he should have got it from the broadcasted ProvenOffer
    taker_internal_offer = taker.offer_book.get_offer_by_id(offer.offer_id)

    assert taker_internal_offer.hash
    assert taker_internal_offer.commitment_amount

    taker_commit_result = taker.commitment_service.taker_commit_async(taker_internal_offer)
    gevent.sleep(0.01)
    assert commitment_service.trader_client.commitment_balance == 20
    assert taker.trader_client.commitment_balance == 5

    taker_proven_commitment = taker_commit_result.get()
    assert isinstance(taker_proven_commitment, messages.ProvenCommitment)
    assert taker_proven_commitment.commitment_proof.sender == commitment_service.address
    assert taker_proven_commitment.sender == taker.address

    failed_taker_internal_offer = failed_taker.offer_book.get_offer_by_id(offer.offer_id)
    # CS published the OfferTaken already, so it should be deleted from the OfferBook
    assert failed_taker_internal_offer is None

    # but we reuse the offer-object from the successful taker to induce an unsuccessful taker-commit
    failed_taker_commit_result = failed_taker.commitment_service.taker_commit_async(taker_internal_offer)
    gevent.sleep(0.01)

    failed_taker_proven_offer = failed_taker_commit_result.get()

    # The second taker fails to receive the proof
    assert failed_taker_proven_offer is False
    # but the CS should have received the commitment
    cs_swap = commitment_service.swaps[offer.offer_id]
    assert cs_swap.commitment_exists_for(failed_taker.address)

    # failed taker should be refunded by now
    assert failed_taker.trader_client.commitment_balance == 10

    # Now the Maker and taker say they executed the swap
    maker_swap_exec = messages.SwapExecution(offer.offer_id, timestamp.time())
    maker_swap_exec.sign(maker.priv_key)
    taker_swap_exec = messages.SwapExecution(offer.offer_id, timestamp.time())
    taker_swap_exec.sign(taker.priv_key)

    maker.message_broker.send(commitment_service.address, maker_swap_exec)
    taker.message_broker.send(commitment_service.address, taker_swap_exec)

    gevent.sleep(0.01)

    # the CS should have received and processed the SwapExecution messages
    assert cs_swap.is_completed

    # check if all the Clients got the SwapCompleted from the CS
    maker_trade = maker.trades.trade_by_id.get(offer.offer_id)
    taker_trade = taker.trades.trade_by_id.get(offer.offer_id)
    failed_taker_trade = failed_taker.trades.trade_by_id.get(offer.offer_id)

    for trade in [maker_trade, taker_trade, failed_taker_trade]:
        assert trade is not None
        assert trade.offer.offer_id == offer.offer_id

    assert maker.offer_book.get_offer_by_id(offer.offer_id) is None
    assert taker.offer_book.get_offer_by_id(offer.offer_id) is None
    assert failed_taker.offer_book.get_offer_by_id(offer.offer_id) is None

    # Check the earnings and refunds
    assert float_isclose(maker.trader_client.commitment_balance, 10 - (5 * commitment_service.fee_rate))
    assert float_isclose(taker.trader_client.commitment_balance, 10 - (5 * commitment_service.fee_rate))
    assert failed_taker.trader_client.commitment_balance == 10
    assert float_isclose(commitment_service.trader_client.commitment_balance, 10 + 2 * (5 * commitment_service.fee_rate))

    # overall balance shouldn't have changed
    assert maker_commitment_balance + taker_commitment_balance + failed_taker_commitment_balance \
           + cs_commitment_balance == 40
