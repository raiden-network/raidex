from raidex import messages
from raidex.utils import timestamp
from raidex.commitment_service.refund import Refund
from raidex.commitment_service.swap_state_machine import SwapStateMachine


class SwapFactory(object):

    def __init__(self, swaps, refund_queue, message_queue):
        self.swaps = swaps
        self.refund_queue = refund_queue
        self.message_queue = message_queue

    def make_swap(self, offer_id):
        swap = None
        if not self.id_collides(offer_id):
            swap = SwapCommitment(offer_id, send_func=self._queue_send, refund_func=self._queue_refund,
                                  cleanup_func=lambda id_=offer_id: self.cleanup_swap(id_))

            self.swaps[offer_id] = swap

        return swap

    def cleanup_swap(self, offer_id):
        del self.swaps[offer_id]

    def id_collides(self, offer_id):
        return offer_id in self.swaps

    def _queue_refund(self, transfer_receipt, priority, claim_fee):
        refund = Refund(transfer_receipt, priority, claim_fee)
        self.refund_queue.put(refund)

    def _queue_send(self, msg, topic):
        self.message_queue.put((msg, topic))


class SwapCommitment(object):

    def __init__(self, offer_id, send_func, refund_func, cleanup_func=None, auto_spawn_timeout=True):
        self._send_func = send_func
        self._refund_func = refund_func
        self._cleanup_func = cleanup_func

        self.offer_id = offer_id
        self.maker_commitment_msg = None
        self.taker_commitment_msg = None
        self.maker_swap_execution_msg = None
        self.taker_swap_execution_msg = None
        self.maker_transfer_receipt = None
        self.taker_transfer_receipt = None
        self.terminated_state = None

        self._state_machine = SwapStateMachine(self, auto_spawn_timeout)

    @property
    def state(self):
        return self._state_machine.state

    @property
    def maker_address(self):
        if self.maker_commitment_msg is None:
            return None
        return self.maker_commitment_msg.sender

    @property
    def taker_address(self):
        if self.taker_commitment_msg is None:
            return None
        return self.taker_commitment_msg.sender

    def is_maker(self, address):
        return address == self.maker_address

    def is_taker(self, address):
        return address == self.taker_address

    def cleanup(self):
        if self._cleanup_func is not None:
            self._cleanup_func()

    def queue_send(self, msg, topic):
        self._send_func(msg, topic)

    def queue_refund(self, transfer_receipt, priority=1, claim_fee=False):
        self._refund_func(transfer_receipt, priority, claim_fee)

    def trigger_timeout(self):
        self._state_machine.timeout()

    def hand_swap_execution_msg(self, message):
        self._state_machine.swap_execution_msg(msg=message)

    def hand_maker_commitment_msg(self, message):
        self._state_machine.maker_commitment_msg(msg=message)

    def hand_taker_commitment_msg(self, message):
        self._state_machine.taker_commitment_msg(msg=message)

    def hand_transfer_receipt(self, transfer_receipt):
        # TODO check here if offer_id's match?
        self._state_machine.transfer_receipt(receipt=transfer_receipt)

    def send_offer_taken(self):
        offer_taken_msg = messages.OfferTaken(self.offer_id)
        self.queue_send(offer_taken_msg, None)

    def send_swap_completed(self):
        swap_completed_message = messages.SwapCompleted(self.offer_id, timestamp.time())
        self.queue_send(swap_completed_message, None)

    def send_maker_commitment_proof(self):
        commitment_proof_msg = messages.CommitmentProof(self.maker_commitment_msg.signature)
        self.queue_send(commitment_proof_msg, self.maker_address)

    def send_taker_commitment_proof(self):
        commitment_proof_msg = messages.CommitmentProof(self.taker_commitment_msg.signature)
        self.queue_send(commitment_proof_msg, self.taker_address)

    def punish_maker(self):
        # do nothing here and keep the fee
        # TODO logging output
        return

    def punish_taker(self):
        # do nothing here and keep the fee
        # TODO logging output
        return

    def refund_maker(self):
        # This has to go through!
        self.queue_refund(self.maker_transfer_receipt)

    def refund_maker_with_fee(self):
        self.queue_refund(self.maker_transfer_receipt, claim_fee=True)

    def refund_taker_with_fee(self):
        self.queue_refund(self.taker_transfer_receipt, claim_fee=True)
