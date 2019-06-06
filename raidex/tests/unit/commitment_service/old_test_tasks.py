import pytest

from raidex import messages
from raidex.utils.gevent_helpers import switch_context
from raidex.message_broker.message_broker import MessageBroker
from raidex.raidex_node.trader.trader import TraderClientMock, TransferReceipt
from raidex.commitment_service.refund import Refund
from raidex.commitment_service.swap import SwapCommitment
from raidex.commitment_service.tasks import (
    RefundTask,
    MessageSenderTask,
    TransferReceivedTask,
    CommitmentTask,
    CancellationRequestTask,
    SwapExecutionTask
)
from raidex.utils import timestamp


@pytest.fixture
def commitment_service_trader_client(trader, commitment_service_account):
    return TraderClientMock(commitment_service_account.address, trader=trader)


@pytest.fixture
def maker_trader_client(trader, maker_account):
    return TraderClientMock(maker_account.address, trader=trader)


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
def maker_commitment_msg_signed(maker_account, maker_commitment_msg):
    maker_commitment_msg.sign(maker_account.privatekey)
    return maker_commitment_msg


@pytest.fixture
def taker_commitment_msg_signed(taker_account, taker_commitment_msg):
    taker_commitment_msg.sign(taker_account.privatekey)
    return taker_commitment_msg


def test_maker_commitment_task(mocker, swaps, factory, maker_commitment_msg_signed, message_broker, commitment_service_account):
    commitment_service_address = commitment_service_account.address

    assert len(swaps) == 0

    hand_maker_commitment_func_mock = mocker.patch.object(SwapCommitment, 'hand_maker_commitment_msg', autospect=True)

    maker_commitment_task = CommitmentTask(factory.swaps, factory.refund_queue, factory.message_queue,
                                           message_broker, commitment_service_address)
    maker_commitment_task.start()
    switch_context()

    message_broker.send(commitment_service_address, maker_commitment_msg_signed)
    switch_context()

    assert len(swaps) == 1

    hand_maker_commitment_func_mock.assert_called_once_with(maker_commitment_msg_signed)


def test_maker_commitment_task_fail(mocker, swaps, factory, maker_commitment_msg_signed, message_broker,
                                    commitment_service_account):
    commitment_service_address = commitment_service_account.address
    offer_id = maker_commitment_msg_signed.offer_id

    hand_maker_commitment_func_mock = mocker.patch.object(SwapCommitment, 'hand_maker_commitment_msg', autospect=True)

    # TODO generalise the filled swaps in fixture
    assert len(swaps) == 0
    # set a non-finished Swap a the offer_id
    existing_swap = factory.make_swap(offer_id)
    assert len(swaps) == 1

    maker_commitment_task = CommitmentTask(factory.swaps, factory.refund_queue, factory.message_queue,
                                           message_broker, commitment_service_address)
    maker_commitment_task.start()

    # try to send a commitment at the existing offer_id
    message_broker.send(commitment_service_address, maker_commitment_msg_signed)
    switch_context()

    # the only swap registered should still be the existing swap
    assert len(swaps) == 1
    assert swaps[offer_id] is existing_swap

    assert not hand_maker_commitment_func_mock.called


def test_taker_commitment_task(mocker, swaps, factory, taker_commitment_msg_signed, commitment_service_account, message_broker,
                               ):
    commitment_service_address = commitment_service_account.address
    offer_id = taker_commitment_msg_signed.offer_id

    hand_taker_commitment_func_mock = mocker.patch.object(SwapCommitment, 'hand_taker_commitment_msg', autospect=True)

    assert len(swaps) == 0
    swap = factory.make_swap(offer_id)
    assert len(swaps) == 1

    taker_commitment_task = CancellationRequestTask(swaps, message_broker, commitment_service_address)
    taker_commitment_task.start()
    switch_context()

    # try to send a commitment at the existing offer_id
    message_broker.send(commitment_service_address, taker_commitment_msg_signed)
    switch_context()

    # the only swap registered should still be the existing swap
    assert len(swaps) == 1
    assert swaps[offer_id] is swap

    hand_taker_commitment_func_mock.assert_called_once_with(taker_commitment_msg_signed)


def test_swap_execution_task(mocker, swaps, factory, swap_execution_msg, message_broker, commitment_service_account,
                             maker_account):
    commitment_service_address = commitment_service_account.address
    swap_execution_msg.sign(maker_account.privatekey)
    offer_id = swap_execution_msg.offer_id

    hand_swap_execution_func_mock = mocker.patch.object(SwapCommitment, 'hand_swap_execution_msg', autospect=True)

    assert len(swaps) == 0
    swap = factory.make_swap(offer_id)
    assert len(swaps) == 1

    swap_execution_task = SwapExecutionTask(swaps, message_broker, commitment_service_address)
    swap_execution_task.start()
    switch_context()

    # try to send a commitment at the existing offer_id
    message_broker.send(commitment_service_address, swap_execution_msg)
    switch_context()

    # the only swap registered should still be the existing swap
    assert len(swaps) == 1
    assert swaps[offer_id] is swap

    hand_swap_execution_func_mock.assert_called_once_with(swap_execution_msg)


def test_transfer_received_task(mocker, swaps, factory, commitment_service_trader_client, commitment_service_account,
                                maker_account, maker_trader_client):
    commitment_service_address = commitment_service_account.address

    offer_id = 123
    assert len(swaps) == 0
    swap = factory.make_swap(offer_id)
    assert len(swaps) == 1

    hand_transfer_receipt_func_mock = mocker.patch.object(SwapCommitment, 'hand_transfer_receipt', autospect=True)

    # set static time
    time_func = mocker.patch.object(timestamp, 'time', autospect=True)
    time_func.return_value = 1

    maker_commitment_task = TransferReceivedTask(swaps, commitment_service_trader_client)
    maker_commitment_task.start()
    switch_context()

    maker_trader_client.transfer(commitment_service_address, 1, identifier=offer_id)
    switch_context()

    hand_transfer_receipt_func_mock.assert_called_once()

    args, kwargs = hand_transfer_receipt_func_mock.call_args

    transfer_receipt = args[0]
    assert transfer_receipt.sender == maker_account.address
    assert transfer_receipt.amount == 1
    assert transfer_receipt.identifier == offer_id
    assert transfer_receipt.timestamp == 1


def test_refund_task(mocker, maker_account, refund_queue, commitment_service_trader_client):
    sender_address = maker_account.address
    receipt = TransferReceipt(sender=sender_address, amount=1, identifier=123, received_timestamp=1)
    refund = Refund(receipt, priority=1, claim_fee=False)

    trader_client_transfer_mock = mocker.patch.object(TraderClientMock, 'transfer', autospect=True, return_value=True)

    refund_task = RefundTask(commitment_service_trader_client, refund_queue, fee_rate=0.1)
    refund_task.start()
    switch_context()

    refund_queue.put(refund)

    assert len(refund_queue) == 1
    switch_context()

    assert len(refund_queue) == 0
    trader_client_transfer_mock.assert_called_once_with(sender_address, 1, 123)


def test_refund_task_claim_fee(mocker, maker_account, refund_queue, commitment_service_trader_client):
    transfer_amount = 1
    fee_rate = 0.1
    sender_address = maker_account.address
    offer_id = 123

    receipt = TransferReceipt(sender=sender_address, amount=transfer_amount, identifier=offer_id,
                              received_timestamp=1)

    refund = Refund(receipt, priority=1, claim_fee=True)

    trader_client_transfer_mock = mocker.patch.object(TraderClientMock, 'transfer', autospect=True, return_value=True)

    refund_task = RefundTask(commitment_service_trader_client, refund_queue, fee_rate=fee_rate)
    refund_task.start()
    switch_context()

    refund_queue.put(refund)
    switch_context()

    expected_amount = transfer_amount - (transfer_amount * fee_rate)
    trader_client_transfer_mock.assert_called_once_with(sender_address, expected_amount, 123)


def test_message_sender_task_send(mocker, message_broker, message_queue, maker_account, commitment_service_account ):

    def sign_func(msg):
        msg.sign(commitment_service_account.privatekey)

    # use some arbitrary message and receiver:
    message = messages.SwapCompleted(123, 1)
    receiver = maker_account.address

    message_broker_send_mock = mocker.patch.object(MessageBroker, 'send', autospect=True)

    message_sender_task = MessageSenderTask(message_broker, message_queue, sign_func=sign_func)
    message_sender_task.start()
    switch_context()

    data = (message, receiver)
    message_queue.put(data)

    assert len(message_queue) == 1
    switch_context()
    assert len(message_queue) == 0

    message_broker_send_mock.assert_called_once_with(topic=receiver, message=message)


def test_message_sender_task_broadcast(mocker, message_broker, message_queue, commitment_service_account):
    def sign_func(msg):
        msg.sign(commitment_service_account.privatekey)

    # use some arbitrary message and receiver:
    message = messages.SwapCompleted(123, 1)
    receiver = None

    message_broker_broadcast_mock = mocker.patch.object(MessageBroker, 'broadcast', autospect=True)

    message_sender_task = MessageSenderTask(message_broker, message_queue, sign_func=sign_func)
    message_sender_task.start()
    switch_context()

    data = (message, receiver)
    message_queue.put(data)

    assert len(message_queue) == 1
    switch_context()
    assert len(message_queue) == 0

    message_broker_broadcast_mock.assert_called_once_with(message)
