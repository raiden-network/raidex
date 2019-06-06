import pytest
import gevent
from copy import deepcopy

from raidex.utils import timestamp
from raidex import messages
from raidex.trader_mock.trader import TransferReceipt
from raidex.commitment_service.swap import SwapCommitment


def deepcopy_and_sign(rlp_signable, privatekey):
    msg = deepcopy(rlp_signable)
    msg.sign(privatekey)
    return msg


def set_state(swap, state_name):
    swap._state_machine.set_state(state_name)


def sign(message, privatekey):
    message.sign(privatekey)


@pytest.fixture
def default_swap(mocker, factory):

    cleanup_func = mocker.Mock(spec=lambda: None)
    refund_func = mocker.Mock(spec=factory._queue_refund )
    send_func = mocker.Mock(spec=factory._queue_send)
    return SwapCommitment(123, send_func, refund_func, cleanup_func, auto_spawn_timeout=False)


@pytest.fixture
def swap_wait_for_maker(default_swap, maker_commitment_msg_signed):
    set_state(default_swap, 'wait_for_maker')  # FIXME naming is weird, since 'maker' is known already theoretically
    default_swap.maker_commitment_msg = maker_commitment_msg_signed
    return default_swap


@pytest.fixture
def swap_wait_for_taker(swap_wait_for_maker, maker_transfer_receipt):
    set_state(swap_wait_for_maker, 'wait_for_taker')
    swap_wait_for_maker.maker_transfer_receipt = maker_transfer_receipt
    return swap_wait_for_maker


@pytest.fixture
def swap_wait_for_execution(swap_wait_for_taker, taker_commitment_msg_signed, taker_transfer_receipt):
    set_state(swap_wait_for_taker, 'wait_for_execution')
    swap_wait_for_taker.taker_commitment_msg = taker_commitment_msg_signed
    swap_wait_for_taker.taker_transfer_receipt = taker_transfer_receipt
    return swap_wait_for_taker


@pytest.fixture
def swap_wait_for_maker_execution(swap_wait_for_execution, taker_swap_execution_msg_signed):
    set_state(swap_wait_for_execution, 'wait_for_maker_execution')
    swap_wait_for_execution.taker_swap_execution_msg = taker_swap_execution_msg_signed
    return swap_wait_for_execution


@pytest.fixture
def swap_wait_for_taker_execution(swap_wait_for_execution, maker_swap_execution_msg_signed):
    set_state(swap_wait_for_execution, 'wait_for_taker_execution')
    swap_wait_for_execution.maker_swap_execution_msg = maker_swap_execution_msg_signed
    return swap_wait_for_execution


@pytest.fixture
def swap_traded(swap_wait_for_taker_execution, taker_swap_execution_msg_signed):
    set_state(swap_wait_for_taker_execution, 'traded')
    swap_wait_for_taker_execution.taker_swap_execution = taker_swap_execution_msg_signed
    return swap_wait_for_taker_execution


@pytest.fixture
def swap_uncommitted(default_swap):
    set_state(default_swap, 'uncommitted')
    return default_swap


@pytest.fixture
def swap_untraded(swap_wait_for_taker):
    set_state(swap_wait_for_taker, 'untraded')
    return swap_wait_for_taker


@pytest.fixture
def swap_failed(swap_wait_for_execution):
    set_state(swap_wait_for_execution, 'failed')
    return swap_wait_for_execution


@pytest.fixture
def swap_processed(swap_failed):
    set_state(swap_failed, 'processed')
    return swap_failed


@pytest.fixture
def maker_transfer_receipt(maker_account, maker_commitment_msg_signed):
    amount = maker_commitment_msg_signed.amount
    received_timestamp = timestamp.time()
    identifier = maker_commitment_msg_signed.offer_id
    return TransferReceipt(maker_account.address, identifier, amount, received_timestamp)


@pytest.fixture
def taker_transfer_receipt(taker_account, maker_commitment_msg_signed):
    amount = maker_commitment_msg_signed.amount
    received_timestamp = timestamp.time()
    identifier = maker_commitment_msg_signed.offer_id
    return TransferReceipt(taker_account.address, identifier, amount, received_timestamp)


@pytest.fixture
def other_transfer_receipt(other_account, maker_commitment_msg_signed):
    amount = maker_commitment_msg_signed.amount
    # FIXME checkme
    received_timestamp = timestamp.time() + 1
    identifier = maker_commitment_msg_signed.offer_id
    return TransferReceipt(other_account.address, identifier, amount, received_timestamp)


@pytest.fixture
def maker_commitment_msg_signed(maker_account, maker_commitment_msg):
    return deepcopy_and_sign(maker_commitment_msg, maker_account.privatekey)


@pytest.fixture
def taker_commitment_msg_signed(taker_account, taker_commitment_msg):
    return deepcopy_and_sign(taker_commitment_msg, taker_account.privatekey)


@pytest.fixture
def other_taker_commitment_msg_signed(other_account, taker_commitment_msg):
    return deepcopy_and_sign(taker_commitment_msg, other_account.privatekey)


@pytest.fixture
def maker_swap_execution_msg_signed(maker_account, swap_execution_msg):
    return deepcopy_and_sign(swap_execution_msg, maker_account.privatekey)


@pytest.fixture
def taker_swap_execution_msg_signed(taker_account, swap_execution_msg):
    return deepcopy_and_sign(swap_execution_msg, taker_account.privatekey)


def assert_other_transfer_refund(swap, other_transfer_receipt):
    # check that unfitting transfer will get refunded
    swap._refund_func.reset_mock()
    print(swap._refund_func.call_args_list)
    print(swap._refund_func.call_count)
    swap.hand_transfer_receipt(other_transfer_receipt)
    # swap._refund_func.assert_called_once_with(other_transfer_receipt, False, 1)
    swap._refund_func.assert_called_once()


def assert_terminated_state(swap, state_name):
    assert swap.state == 'processed'
    assert swap.terminated_state == state_name

    swap._cleanup_func.assert_called_once()


def test_commitment_factory(swaps, factory):
    offer_id = 123
    assert len(swaps) == 0
    swap1 = factory.make_swap(offer_id)
    assert len(swaps) == 1
    assert swaps[offer_id] is swap1

    swap2 = factory.make_swap(offer_id)

    assert swap2 is None
    assert len(swaps) == 1
    assert swaps[offer_id] is swap1


def test_auto_spawn_timeout(mocker, factory, maker_commitment_msg_signed):
    swap_auto_timeout = factory.make_swap(maker_commitment_msg_signed.offer_id)

    trigger_timeout_mock = mocker.patch.object(SwapCommitment, 'trigger_timeout', autospect=True)

    # now triggering the timeout should get spawned in time the timeout hits:
    swap_auto_timeout.hand_maker_commitment_msg(maker_commitment_msg_signed)

    gevent.sleep(timestamp.seconds_to_timeout(maker_commitment_msg_signed.timeout) + 0.1)

    trigger_timeout_mock.assert_called_once()


def test_state_initializing(default_swap, maker_commitment_msg_signed):
    swap = default_swap
    assert swap.state == 'initializing'
    swap.hand_maker_commitment_msg(maker_commitment_msg_signed)

    assert swap.state == 'wait_for_maker'
    assert swap.maker_commitment_msg == maker_commitment_msg_signed


def test_state_initializing_timeout(default_swap):
    swap = default_swap
    swap.trigger_timeout()
    assert_terminated_state(swap, 'uncommitted')


def test_state_wait_for_maker(swap_wait_for_maker, maker_transfer_receipt, maker_account):
    swap = swap_wait_for_maker
    assert swap.is_maker(maker_account.address)

    swap.hand_transfer_receipt(maker_transfer_receipt)
    assert swap.is_maker(maker_account.address)
    assert swap.maker_transfer_receipt == maker_transfer_receipt
    assert swap.state == 'wait_for_taker'


def test_state_wait_for_maker_refund(swap_wait_for_maker, other_transfer_receipt):
    swap = swap_wait_for_maker
    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_wait_for_maker_timeout(swap_wait_for_maker):
    swap = swap_wait_for_maker
    swap.trigger_timeout()

    assert_terminated_state(swap, 'uncommitted')


def test_state_wait_for_taker(swap_wait_for_taker, taker_commitment_msg_signed, other_taker_commitment_msg_signed,
                              taker_transfer_receipt, taker_account):
    swap = swap_wait_for_taker

    swap.hand_taker_commitment_msg(taker_commitment_msg_signed)
    swap.hand_taker_commitment_msg(other_taker_commitment_msg_signed)
    swap.hand_transfer_receipt(taker_transfer_receipt)

    assert swap.is_taker(taker_account.address)
    assert swap.taker_transfer_receipt is taker_transfer_receipt
    assert swap.taker_commitment_msg is taker_commitment_msg_signed
    assert swap.state == 'wait_for_execution'


def test_state_wait_for_taker_refund(swap_wait_for_taker, other_transfer_receipt):
    swap = swap_wait_for_taker
    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_wait_for_taker_timeout(swap_wait_for_taker):
    swap = swap_wait_for_taker
    swap.trigger_timeout()

    assert_terminated_state(swap, 'untraded')


def test_state_wait_for_execution_maker_input(swap_wait_for_execution, maker_swap_execution_msg_signed, maker_account):
    swap = swap_wait_for_execution
    swap.hand_swap_execution_msg(maker_swap_execution_msg_signed)

    assert swap.is_maker(maker_account.address)
    assert swap.maker_swap_execution_msg is maker_swap_execution_msg_signed
    assert swap.state == 'wait_for_taker_execution'


def test_state_wait_for_execution_taker_input(swap_wait_for_execution, taker_swap_execution_msg_signed, taker_account):
    swap = swap_wait_for_execution
    swap.hand_swap_execution_msg(taker_swap_execution_msg_signed)

    assert swap.is_taker(taker_account.address)
    assert swap.taker_swap_execution_msg is taker_swap_execution_msg_signed
    assert swap.state == 'wait_for_maker_execution'


def test_state_wait_for_execution_refund(swap_wait_for_execution, other_transfer_receipt):
    swap = swap_wait_for_execution
    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_wait_for_execution_timeout(swap_wait_for_execution):
    swap = swap_wait_for_execution
    swap.trigger_timeout()

    assert_terminated_state(swap, 'failed')


def test_state_wait_for_maker_execution(swap_wait_for_maker_execution, maker_swap_execution_msg_signed):
    swap = swap_wait_for_maker_execution
    swap.hand_swap_execution_msg(maker_swap_execution_msg_signed)

    assert swap.maker_swap_execution_msg is maker_swap_execution_msg_signed
    assert_terminated_state(swap, 'traded')


def test_state_wait_for_maker_execution_refund(swap_wait_for_maker_execution, other_transfer_receipt):
    swap = swap_wait_for_maker_execution
    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_wait_for_maker_execution_timeout(swap_wait_for_maker_execution):
    swap = swap_wait_for_maker_execution
    swap.trigger_timeout()

    assert_terminated_state(swap, 'failed')


def test_state_wait_for_taker_execution(swap_wait_for_taker_execution, taker_swap_execution_msg_signed):
    swap = swap_wait_for_taker_execution
    swap.hand_swap_execution_msg(taker_swap_execution_msg_signed)

    assert swap.taker_swap_execution_msg is taker_swap_execution_msg_signed
    assert_terminated_state(swap, 'traded')


def test_state_wait_for_taker_execution_refund(swap_wait_for_taker_execution, other_transfer_receipt):
    swap = swap_wait_for_taker_execution
    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_wait_for_taker_execution_timeout(swap_wait_for_taker_execution):
    swap = swap_wait_for_taker_execution
    swap.trigger_timeout()

    assert_terminated_state(swap, 'failed')


def test_state_traded(mocker, swap_wait_for_taker_execution, taker_swap_execution_msg_signed, maker_transfer_receipt,
                      taker_transfer_receipt):
    # transition into the state again, because the actions are coupled with succesful transitions

    swap = swap_wait_for_taker_execution

    # mock timestamp.time() to a fixed value
    mocker.patch.object(timestamp, "time", autospec=True, return_value=1)

    swap.hand_swap_execution_msg(taker_swap_execution_msg_signed)

    assert_terminated_state(swap, 'traded')

    # swap completed should be broadcasted
    expected_swap_completed_msg = messages.SwapCompleted(123, timestamp=1)

    swap._send_func.assert_called_once_with(expected_swap_completed_msg, None)

    # maker/taker should be refunded, commitment_service should claim fee

    assert swap._refund_func.call_count == 2
    expected_calls = [mocker.call(taker_transfer_receipt, 1, True),
                      mocker.call(maker_transfer_receipt, 1, True)]
    # call order unimportant
    swap._refund_func.assert_has_calls(expected_calls, any_order=True)


def test_state_traded_refund(swap_traded, other_transfer_receipt):
    swap = swap_traded
    swap.hand_transfer_receipt(other_transfer_receipt)

    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_uncommitted(swap_wait_for_maker):
    swap = swap_wait_for_maker

    swap.trigger_timeout()
    assert_terminated_state(swap, 'uncommitted')
    # no refunds, since the maker didn't send a commitment_transfer
    assert not swap._refund_func.called


def test_state_uncommitted_refund(swap_uncommitted, other_transfer_receipt):
    swap = swap_uncommitted
    swap.hand_transfer_receipt(other_transfer_receipt)

    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_untraded(swap_wait_for_taker, maker_transfer_receipt):
    swap = swap_wait_for_taker

    # maker should be refunded, commitment_service should not claim fee

    swap.trigger_timeout()
    assert_terminated_state(swap, 'untraded')
    swap._refund_func.assert_called_once_with(maker_transfer_receipt, 1, False)


def test_state_untraded_refund(swap_untraded, other_transfer_receipt):
    swap = swap_untraded
    swap.hand_transfer_receipt(other_transfer_receipt)

    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_failed(swap_wait_for_execution):
    swap = swap_wait_for_execution

    swap.trigger_timeout()
    assert_terminated_state(swap, 'failed')

    # no refunds should have taken place, because we want to punish maker and taker
    assert not swap._refund_func.called


def test_state_failed_refund(swap_failed, other_transfer_receipt):
    swap = swap_failed
    swap.hand_transfer_receipt(other_transfer_receipt)

    assert_other_transfer_refund(swap, other_transfer_receipt)


def test_state_processed(swap_wait_for_maker):
    swap = swap_wait_for_maker

    swap.trigger_timeout()
    assert swap.state == 'processed'

    swap._cleanup_func.assert_called_once()
