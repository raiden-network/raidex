from copy import deepcopy

import pytest
import gevent

from ethereum.utils import sha3, big_endian_to_int
from raidex import messages
from raidex.message_broker.message_broker import MessageBroker
from raidex.message_broker.listeners import MessageListener
from raidex.signing import Signer
from raidex.raidex_node.trader.trader import (
    TraderClient,
    Trader,
    TransferReceipt
)
from raidex.commitment_service.server import (
    CommitmentService,
    SwapExecutionTask,
    TransferReceivedTask,
    CommitmentTask,
    SwapCommitment,
    Refund,
    RefundTask,
    MessageSenderTask,
    TransferReceivedListener
)
from raidex.utils import make_privkey_address, timestamp


@pytest.fixture
def message_broker():
    return MessageBroker()


@pytest.fixture()
def trader():
    # global singleton trader, will get reinitialised after every test in order to teardown old listeners etc
    return Trader()


@pytest.fixture()
def trader_client1(accounts, trader):
    return TraderClient(accounts[1].address, commitment_balance=10, trader=trader)


@pytest.fixture()
def trader_client2(accounts, trader):
    return TraderClient(accounts[2].address, commitment_balance=10, trader=trader)


@pytest.fixture()
def commitment_service(message_broker, trader):
    signer = Signer.random()
    trader_client = TraderClient(signer.address, trader=trader)
    return CommitmentService(signer, message_broker, trader_client, fee_rate=0.01)


def test_commitment_task(commitment_service, accounts):
    CommitmentTask(commitment_service.swaps,
                   commitment_service.message_broker,
                   commitment_service.address,
                   commitment_service.refund_queue).start()
    gevent.sleep(0.01)
    offer_id = big_endian_to_int(sha3('offer1'))
    maker = accounts[0]
    taker1 = accounts[1]
    taker2 = accounts[2]
    # TODO hashes and ID clarification
    seconds_to_timeout = 0.5
    timeout = timestamp.time_plus(seconds_to_timeout)

    commitment_msg = messages.Commitment(offer_id=offer_id, offer_hash=sha3(offer_id),
                                         timeout=timeout, amount=5)

    # let the maker sign and send commitment
    commitment_msg_maker = deepcopy(commitment_msg)
    commitment_msg_maker.sign(maker.privatekey)
    commitment_service.message_broker.send(commitment_service.address, commitment_msg_maker)

    gevent.sleep(0.01)
    swap = commitment_service.swaps[offer_id]
    assert len(commitment_service.swaps.keys()) == 1
    assert isinstance(swap, SwapCommitment)
    assert swap.maker_commitment == commitment_msg_maker
    assert swap.commitment_exists_for(maker.address)

    # FIXME the task is accepting takers for SwapCommitments that haven't been paid by the maker!
    # (although this is implicit, since takers should only accept valid ProvenOffers )

    # first taker sends commitment
    commitment_msg_taker1 = deepcopy(commitment_msg)
    commitment_msg_taker1.sign(taker1.privatekey)
    commitment_service.message_broker.send(commitment_service.address, commitment_msg_taker1)
    gevent.sleep(0.01)

    assert len(commitment_service.swaps.keys()) == 1
    assert swap.commitment_exists_for(taker1.address)

    # second taker sends commitment
    commitment_msg_taker2 = deepcopy(commitment_msg)
    commitment_msg_taker2.sign(taker2.privatekey),
    commitment_service.message_broker.send(commitment_service.address, commitment_msg_taker2)

    gevent.sleep(0.01)

    assert len(commitment_service.swaps.keys()) == 1
    assert swap.commitment_exists_for(taker2.address)

    assert not swap.is_taken

    # wait for the timeout, give a little time to get in the next gevent loop iteration
    while timestamp.time() <= timeout + 10:
        gevent.sleep(0.01)

    assert swap.timed_out
    assert len(commitment_service.swaps.keys()) == 0


def test_swap_execution_task(commitment_service, message_broker, accounts):
    SwapExecutionTask(commitment_service.swaps, commitment_service.message_queue, commitment_service.refund_queue,
                      message_broker, commitment_service.address).start()
    gevent.sleep(0.1)

    maker = accounts[0]
    taker = accounts[1]
    offer_id = big_endian_to_int(sha3('offer1'))
    seconds_to_timeout = 0.5
    commitment_msg = messages.Commitment(offer_id=offer_id, offer_hash=sha3(offer_id),
                                         timeout=timestamp.time_plus(seconds_to_timeout), amount=5)

    gevent.sleep(0.01)

    commitment_maker = deepcopy(commitment_msg).sign(maker.privatekey)
    commitment_taker = commitment_msg.sign(taker.privatekey)
    swap = SwapCommitment(commitment_maker)

    # manually set taker_commitment
    swap._taker_commitment = commitment_taker
    assert swap.is_taken is True

    # manually set the transfer_receipts:
    swap._maker_transfer_receipt = TransferReceipt(maker.address, amount=5, identifier=offer_id,
                                                   timestamp=timestamp.time())
    swap._taker_transfer_receipt = TransferReceipt(taker.address, amount=5, identifier=offer_id,
                                                   timestamp=timestamp.time())

    # inject the swap in the CS's dict
    commitment_service.swaps[offer_id] = swap

    swap_exec_msg_maker = messages.SwapExecution(offer_id, timestamp.time())
    swap_exec_msg_maker.sign(maker.privatekey)
    swap_exec_msg_taker = messages.SwapExecution(offer_id, timestamp.time())
    swap_exec_msg_taker.sign(taker.privatekey)

    commitment_service.message_broker.send(commitment_service.address, swap_exec_msg_maker)
    gevent.sleep(0.01)

    assert not swap.is_completed
    assert not swap.timed_out
    assert swap._maker_swap_execution == swap_exec_msg_maker

    commitment_service.message_broker.send(commitment_service.address, swap_exec_msg_taker)
    sent_time = timestamp.time()
    gevent.sleep(0.01)

    assert swap.is_completed
    assert not swap.timed_out
    assert swap._taker_swap_execution == swap_exec_msg_taker

    assert len(commitment_service.message_queue) == 1
    swap_completed, recipient = commitment_service.message_queue.get()
    assert isinstance(swap_completed, messages.SwapCompleted)
    assert recipient is None
    # NOTE: messages in the message_queue aren't signed yet
    assert swap_completed.offer_id == commitment_msg.offer_id
    assert swap_completed.timestamp <= sent_time + 3

    # CS will refund when the swap was successully executed, subtract the fee:
    assert len(commitment_service.refund_queue) == 2
    refund1 = commitment_service.refund_queue.get()
    refund2 = commitment_service.refund_queue.get()
    assert isinstance(refund1.receipt, TransferReceipt)
    assert isinstance(refund2.receipt, TransferReceipt)
    set([maker.address, taker.address]) == set([refund1.receipt.sender, refund2.receipt.sender])
    set([5]) == set([refund1.receipt.amount, refund2.receipt.amount])

    assert refund1.claim_fee is True
    assert refund2.claim_fee is True


def test_transfer_received_task(commitment_service, accounts, trader):

    TransferReceivedTask(commitment_service.swaps, commitment_service.message_queue,
                         commitment_service.refund_queue, commitment_service.trader_client).start()

    gevent.sleep(0.01)

    offer_id = big_endian_to_int(sha3('offer1'))
    maker = accounts[0]
    amount = 5
    seconds_to_timeout = 0.5
    commitment_msg = messages.Commitment(offer_id=offer_id, offer_hash=sha3(offer_id),
                                         timeout=timestamp.time_plus(seconds_to_timeout), amount=amount)
    commitment_msg.sign(maker.privatekey)
    swap = SwapCommitment(commitment_msg)

    # put in swap manually:
    commitment_service.swaps[offer_id] = swap

    sender_trader = TraderClient(maker.address, trader=trader)

    # check singleton identity
    assert sender_trader.trader is commitment_service.trader_client.trader

    # do the maker commitment transfer
    transfer_successful = sender_trader.transfer(commitment_service.address, amount, offer_id)
    assert transfer_successful
    sent_time = timestamp.time()
    gevent.sleep(0.01)

    receipt = swap._maker_transfer_receipt
    assert isinstance(receipt, TransferReceipt)
    assert receipt.amount == amount
    assert receipt.sender == maker.address
    assert receipt.identifier == offer_id
    # make shure the timestamp is generated within 3ms (arbitrary)
    assert receipt.timestamp <= sent_time + 3


def test_refund_task(commitment_service, trader_client1):
    transfer_amount = 5
    fee_rate = 0.1

    # start the balanceupdate-task of the traders
    trader_client1.start()
    commitment_service.trader_client.start()

    refund_task = RefundTask(commitment_service.trader_client, commitment_service.refund_queue, fee_rate)

    receipt1 = TransferReceipt(sender=trader_client1.address, identifier=sha3('beer'), amount=transfer_amount,
                               timestamp=timestamp.time())

    receipt2 = TransferReceipt(sender=trader_client1.address, identifier=sha3('gin'), amount=transfer_amount,
                               timestamp=timestamp.time())

    # claim fee, higher priority
    refund1 = Refund(receipt1, priority=5, claim_fee=True)
    # don't claim fee, lower priority
    refund2 = Refund(receipt2, priority=1, claim_fee=False)

    transfer_received_listener = TransferReceivedListener(trader_client1)

    commitment_service.refund_queue.put(refund1)
    commitment_service.refund_queue.put(refund2)
    transfer_received_listener.start()
    gevent.sleep(0.01)
    refund_task.start()
    gevent.sleep(0.01)

    received_first = transfer_received_listener.listener.event_queue_async.get()
    received_second = transfer_received_listener.listener.event_queue_async.get()

    assert received_first.identifier == receipt1.identifier
    assert received_first.amount == transfer_amount - (transfer_amount * fee_rate)
    assert received_second is not received_first
    assert received_second.identifier == receipt2.identifier
    assert received_second.amount == transfer_amount
    assert commitment_service.trader_client.commitment_balance == 0.5
    assert trader_client1.commitment_balance == 19.5


def test_message_sender_task(commitment_service, message_broker, accounts):
    message_sender_task = MessageSenderTask(message_broker, commitment_service.message_queue, commitment_service._sign)
    recipient = accounts[0].address
    message_listener = MessageListener(message_broker, topic=recipient)
    message_listener.start()

    # send whatever message to recipient:
    message_unsigned = messages.Commitment(big_endian_to_int(sha3('beer')), sha3('gin'),
                                           timeout=timestamp.time_plus(0.5), amount=10)
    assert not message_unsigned.has_sig
    message_sender_task.start()
    commitment_service.message_queue.put((message_unsigned, recipient))
    gevent.sleep(1)
    message_received = message_listener.get()

    assert message_received.sender == commitment_service.address


@pytest.mark.xfail(reason='Not implemented yet')
def test_client():
    # TODO test the client implementation and tasks
    pass