import time

import gevent
from gevent.queue import PriorityQueue
from ethereum.utils import privtoaddr
from ethereum import slogging
from raiden.encoding.signing import  GLOBAL_CTX
from raiden.encoding.signing import sign as _sign
from secp256k1 import PrivateKey, ALL_FLAGS

from raidex.utils import timestamp, pex
from raidex import messages
from raidex.raidex_node.trader.trader import TraderClient, TransferReceipt, TransferReceivedListener
from raidex.message_broker.listeners import CommitmentListener, SwapExecutionListener


log = slogging.get_logger('commitment_service')
log_swaps = slogging.get_logger('commitment_service.asset_swaps')
log_messaging = slogging.get_logger('commitment_service.messaging')
log_refunds = slogging.get_logger('commitment_service.refunds')
log_trader = slogging.get_logger('commitment_service.trader')


# string? or PrivateKey -> PrivateKey
def sign(messagedata, private_key):
    if not isinstance(private_key, PrivateKey):
        privkey_instance = PrivateKey(privkey=private_key, flags=ALL_FLAGS, ctx=GLOBAL_CTX)
    else:
        privkey_instance = private_key
    return _sign(messagedata, privkey_instance)


class RaidexException(Exception):
    pass


class CommitmentTaken(RaidexException):
    pass


class CommitmentMismatch(RaidexException):
    pass


class SwapCommitment(object):
    """
    Object oriented Container to hold one (not yet taken) or two (taken) commitments and inform about some properties
    """

    def __init__(self, initial_commitment):
        self._maker_commitment = initial_commitment
        self._taker_commitment = None
        self._maker_swap_execution = None
        self._taker_swap_execution = None
        self._maker_transfer_receipt = None
        self._taker_transfer_receipt = None
        self._taker_commitment_pool = dict()  # commitment.sender -> taker_commitment_msg
        self._commitment_addresses = set([initial_commitment.sender])  # all addresses from the pool + the maker address

    def __contains__(self, item):
        if item is self._maker_commitment or self._taker_commitment:
            return True
        return False

    def __repr__(self):
        taker_commitment = self.taker_commitment
        taker_commitment_sender = None
        if taker_commitment:
            taker_commitment_sender = pex(taker_commitment.sender)
        return 'SwapCommitment<maker={} taker={} timeout={} status={}>'.format(
            pex(self.maker_commitment.sender), taker_commitment_sender,
            self._maker_commitment.timeout,
            self._status_str)

    @property
    def _status_str(self):
        # TODO naming of statuses
        if self.timed_out:
            if self.is_completed:
                return 'completed'
            else:
                if self.is_taken:
                    return 'incomplete'
                else:
                    return 'unsuccessful'
        if self.is_taken:
            return 'taken/committed'
        return 'open'

    @property
    def maker_commitment(self):
        return self._maker_commitment

    @property
    def taker_commitment(self):
        return self._taker_commitment

    @property
    def timeout(self):
        return self._maker_commitment.timeout

    @property
    def timed_out(self):
        return timestamp.timed_out(self.timeout)

    @property
    def offer_id(self):
        return self._maker_commitment.offer_id

    @property
    def is_taken(self):
        if self._maker_commitment and self._taker_commitment:
            return True
        return False

    @property
    def is_completed(self):
        if self._maker_swap_execution and self._taker_swap_execution:
            return True
        return False

    def commitment_exists_for(self, address):
        return address in self._commitment_addresses

    def queue_taker_commitment(self, commitment):
        # type: (messages.Commitment) -> None

        # THis gets called whenever a TakerCommitment for this offer is received.
        # We are still waiting for the Transfer, so this is the only the initial step for committing.
        #
        # You can still queue when the offer is taken already,
        # since the pool will get used to evaluate who tried to commit,
        # thus, provided a commitment-msg before transfering

        if commitment.sender not in self._taker_commitment_pool:
            self._taker_commitment_pool[commitment.sender] = commitment
            self._commitment_addresses.add(commitment.sender)
        else:
            # double sent
            pass

    def construct_proof(self, transfer_receipt):
        # type: (TransferReceipt) -> (messages.CommitmentProof, False)

        assert isinstance(transfer_receipt, TransferReceipt)
        # assert not self._taker_commitment
        assert transfer_receipt.identifier == self._maker_commitment.offer_id

        # FIXME
        if transfer_receipt.sender not in self._commitment_addresses:
            raise Exception('Address mismatch')
        if not transfer_receipt.timestamp <= self.timeout:
            raise Exception('Offer timed out')
        if not transfer_receipt.amount == self._maker_commitment.amount:
            raise Exception('Amount doesn\'t match')

        # don't construct proof if offer is already taken
        if self.is_taken:
            return False

        if transfer_receipt.sender == self._maker_commitment.sender:
            self._maker_transfer_receipt = transfer_receipt
            return messages.CommitmentProof(self._maker_commitment.signature)
        elif transfer_receipt.sender in self._taker_commitment_pool:
            self._taker_transfer_receipt = transfer_receipt
            self._taker_commitment = self._taker_commitment_pool[transfer_receipt.sender]
            return messages.CommitmentProof(self._taker_commitment.signature)

        assert False

    def construct_swap_completed(self, swap_exec_msg):
        # type: (messages.SwapExecution) -> (None, messages.SwapCompleted)

        assert isinstance(swap_exec_msg, messages.SwapExecution)
        assert swap_exec_msg.offer_id == self._maker_commitment.offer_id

        if not self.timed_out:
            if swap_exec_msg.sender == self._maker_commitment.sender:
                self._maker_swap_execution = swap_exec_msg
            elif swap_exec_msg.sender == self._taker_commitment.sender:
                self._taker_swap_execution = swap_exec_msg
            else:
                raise Exception('Address mismatch')

            if self.is_completed:
                # TODO should this be saved as well?
                return messages.SwapCompleted(offer_id=self._maker_commitment.offer_id, timestamp=timestamp.time_int())
            else:
                return None

        raise Exception('Offer timed out')

    def construct_maker_taker_refunds(self):
        refunds = []
        if self.is_completed:
            assert self._taker_transfer_receipt is not None
            assert self._maker_transfer_receipt is not None

            refunds.append(Refund(self._taker_transfer_receipt, 5, claim_fee=True))
            refunds.append(Refund(self._maker_transfer_receipt, 5, claim_fee=True))
        elif not self.is_taken and not self.is_completed:
            assert self._taker_transfer_receipt is None
            assert self._maker_transfer_receipt is not None

            assert not self._taker_transfer_receipt
            # don't claim fee, since the Offer wasn't taken
            refunds.append(Refund(self._maker_transfer_receipt, 5, claim_fee=False))
        else:
            # don't refund in any other case
            return False

        return refunds


class CommitmentTask(gevent.Greenlet):
    """
    Listens on the message-broker to Commitment-messages sent to the CS's address.
    The offer_id from the commitment is matched against existing, not finished Swaps.
    ...
    As soon as a Swap-instance is created, the Task will also spawn a function that get's executed after
    the commitment timeout, which cleans up inclomplete swaps.
    It (implicitly) keeps the commitment-funds by NOT refunding them.
    """

    def __init__(self, swaps, commitment_listener, refund_queue):
        self.swaps = swaps
        self.commitment_listener = commitment_listener
        self.refund_queue = refund_queue
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.commitment_listener.start()
        while True:
            commitment_msg = self.commitment_listener.get()
            assert isinstance(commitment_msg, messages.Commitment)
            log_messaging.info('Received commitment {}'.format(commitment_msg))
            swap = self.swaps.get(commitment_msg.offer_id)

            # committer is the maker
            if swap is None:
                # FIXME if Taker is too late with trying to commit, and Swap is deleted from swaps, he will be seen as a maker
                # -> separate Maker/TakerCommitment Messages
                swap = SwapCommitment(commitment_msg)
                self.swaps[commitment_msg.offer_id] = swap
                log_messaging.debug('Maker registered swap: {}'.format(swap))

                def after_offer_timeout_func(swaps, timedout_swap, refund_backlog):
                    def func():
                        assert timedout_swap.timed_out
                        log_swaps.debug('Swap timed out: {}'.format(timedout_swap))
                        # check if still in swaps, if not, has been handled before
                        if timedout_swap.offer_id not in swaps:
                            return
                        if timedout_swap.is_taken:
                            assert not swap.is_complete
                            # FIXME don't access private member
                            receipt_maker = swap._maker_transfer_receipt
                            receipt_taker = swap._taker_transfer_receipt
                            log_refunds.info('Keeping maker\'s commitment-funds: {}'.format(receipt_maker))
                            log_refunds.info('Keeping taker\'s commitment-funds: {}'.format(receipt_taker))
                        else:
                            assert timedout_swap.taker_commitment is None
                            # medium priority, arbitrary for now
                            # FIXME don't access private member
                            receipt = swap._maker_transfer_receipt
                            if receipt:
                                refund = Refund(swap._maker_transfer_receipt, priority=3, claim_fee=False)
                                log_refunds.info('Refunding maker: {}'.format(refund))
                                refund_backlog.put(refund)

                        # delete from swaps and make room for offer-id reusal
                        log.debug('CODE: Would delete swap now from dict')

                        # FIXME this results in heavy data races!!
                        # del swaps[swap.offer_id]

                    return func

                seconds_to_timeout = timestamp.seconds_to_timeout(commitment_msg.timeout)
                gevent.spawn_later(seconds_to_timeout,
                                   after_offer_timeout_func(self.swaps, swap, self.refund_queue))

            # committer is a taker
            else:
                swap.queue_taker_commitment(commitment_msg)


class Refund(object):

    def __init__(self, receipt, priority, claim_fee):
        # type: (TransferReceipt, int, bool) -> None
        self.receipt = receipt
        self.priority = priority
        self.claim_fee = claim_fee

    def __cmp__(self, other):
        # compare the whole object easily for the Priority-Queue ordering.
        # Higher priority means it will get refunded earlier
        if self.priority < other.priority:
            # lower priority: self > other:
            return 1
        if self.priority > other.priority:
            # higher priority: self < other
            return -1
        return 0


class RefundTask(gevent.Greenlet):
    def __init__(self, trader, refund_queue, fee_rate=None):
        self.trader = trader
        self.refund_queue = refund_queue
        self.fee_rate = fee_rate
        gevent.Greenlet.__init__(self)

    def _run(self):
        while True:
            refund = self.refund_queue.get()
            amount = refund.receipt.amount
            if self.fee_rate is not None and refund.claim_fee is True:
                amount -= refund.receipt.amount * self.fee_rate
            transfer_async_result = self.trader.transfer(refund.receipt.sender, amount, refund.receipt.identifier)

            def wait_and_requeue(async_result, refund_, queue):
                # timeout arbitrary
                success = async_result.wait(timeout=0.5)
                if success is True:
                    log_trader.debug('Refund successful {}'.format(refund_))
                else:
                    queue.put(refund_)
                    log_trader.debug('Refunding failed for {}, retrying'.format(refund_))

            gevent.spawn(wait_and_requeue, transfer_async_result, refund, self.refund_queue)


class MessageSenderTask(gevent.Greenlet):

    def __init__(self, message_broker, message_queue, sign_func):
        self.message_broker = message_broker
        self.message_queue = message_queue
        self._sign_func = sign_func
        gevent.Greenlet.__init__(self)

    def _run(self):
        while True:
            msg, recipient = self.message_queue.get()
            print(msg, pex(recipient))
            self._sign_func(msg)
            # FIXME make async
            # recipient == None is indicating a broadcast
            if recipient is None:
                # careful, may block?
                success = self.message_broker.broadcast(msg)
                if success is True:
                    log_messaging.debug('Broadcast successful: {}'.format(msg))
            else:
                # careful, may block?
                success = self.message_broker.send(topic=recipient, message=msg)
                if success:
                    log_messaging.debug('Sending successful: {} // recipient={}'.format(msg, pex(recipient)))


class TransferReceivedTask(gevent.Greenlet):

    def __init__(self, swaps, message_queue, refund_queue, transfer_received_listener):
        self.swaps = swaps
        self.message_queue = message_queue
        self.refund_queue = refund_queue
        self.listener = transfer_received_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.listener.start()
        while True:
            transfer_receipt = self.listener.get()
            log_trader.info('Received transfer: {}'.format(transfer_receipt))
            swap = self.swaps.get(transfer_receipt.identifier)
            if swap is None:
                # keep funds as spam protection, so do nothing to refund
                log_swaps.debug('No swap registered for transfer: {}'.format(transfer_receipt))
                log_refunds.info('Keeping funds as penalty: {}'.format(transfer_receipt))
                continue
            proof = swap.construct_proof(transfer_receipt)
            if proof:
                assert isinstance(proof, messages.CommitmentProof)
                log_swaps.debug('Commitment-Proof created: {}'.format(proof))

                # send proof to taker
                self.message_queue.put((proof, transfer_receipt.sender))

                # if the transfer originated from a successful Taker:
                if swap.is_taken:
                    log_swaps.info('Swap is taken: {}'.format(swap))
                    # broadcast OfferTaken
                    taken_msg = messages.OfferTaken(swap.offer_id)
                    self.message_queue.put((taken_msg, None))


            # swap was taken already, refund transfer without claiming a fee:
            else:
                assert swap.is_taken
                # put on refund queue with appropriate priority
                refund_priority = 2  # arbitrary for now
                refund = Refund(transfer_receipt, priority=refund_priority, claim_fee=False)
                log.debug('CODE: Received transfer for taken swap, trying to refund: {}'.format(refund))
                self.refund_queue.put(refund)


class SwapExecutionTask(gevent.Greenlet):

    def __init__(self, swaps, message_queue, refund_queue, swap_execution_listener):
        self.swaps = swaps
        self.message_queue = message_queue
        self.refund_queue = refund_queue
        self.swap_execution_listener = swap_execution_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.swap_execution_listener.start()
        while True:
            swap_execution_msg = self.swap_execution_listener.get()
            swap = self.swaps.get(swap_execution_msg.offer_id)
            if swap is not None:
                swap_completed = swap.construct_swap_completed(swap_execution_msg)
                log_messaging.debug('Received swap-excution message: {}'.format(swap))
                if swap_completed is not None:
                    assert isinstance(swap_completed, messages.SwapCompleted)
                    self.message_queue.put((swap_completed, None))
                    refunds = swap.construct_maker_taker_refunds()
                    if refunds:
                        for refund in refunds:
                            self.refund_queue.put(refund)

            else:
                log.debug('Received non-matching swap-excution message: {}'.format(swap))


class CommitmentService(object):

    def __init__(self, message_broker, private_key, fee_rate=None, trader_client=None):
        self._private_key = private_key
        self.swaps = dict()  # offer_hash -> CommitmentTuple
        if not trader_client:
            trader_client = TraderClient(self.address)
        self.trader_client = trader_client
        # FIXME fee_rate should be int representation (int(float_rate/uint32.max_int)) for CSAdvertisements
        self.fee_rate = fee_rate
        self.message_broker = message_broker
        self.refund_queue = PriorityQueue()  # type: (TransferReceipt, substract_fee <bool>)
        self.message_queue = PriorityQueue()  # type: (messages.Signed, recipient (str) or None)

    @property
    def address(self):
        return privtoaddr(self._private_key)

    def start(self):
        CommitmentTask(self.swaps, CommitmentListener(self.message_broker, topic=self.address), self.refund_queue).start()
        SwapExecutionTask(self.swaps, self.message_queue, self.refund_queue,
                          SwapExecutionListener(self.message_broker, topic=self.address)).start()
        TransferReceivedTask(self.swaps, self.message_queue, self.refund_queue, TransferReceivedListener(self.trader_client)).start()
        RefundTask(self.trader_client, self.refund_queue, self.fee_rate).start()
        MessageSenderTask(self.message_broker, self.message_queue, self._sign).start()

    def _sign(self, message):
        message.sign(self._private_key)
