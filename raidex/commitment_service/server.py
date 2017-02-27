import time

from ethereum.utils import privtoaddr, sha3
# from raiden.raiden_service import transfer_async
from raiden.encoding.signing import recover_publickey, GLOBAL_CTX
from raiden.encoding.signing import sign as _sign
from secp256k1 import PrivateKey, ALL_FLAGS

from raidex.utils import ETHER_TOKEN_ADDRESS
from raidex import messages

from raidex.raidex_node.message_abstrations import Commitment, SwapExecution

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


class CommitmentService(object):
    """
    TODO:
        - backlog queue for refunding incoming transfers for an offer_id that is already taken
        -

    """

    def __init__(
        self,
        raiden_api,
        private_key,
        fee_rate,
        communication_protocol_cls,
        communication_transport,  # TODO find better naming like direct_transport or decentralized_transport
        raiden_discovery,
        broadcast_transport,
        broadcast_protocol_cls):

        self.raiden = raiden_api
        self.private_key = private_key
        self.commitment_asset = ETHER_TOKEN_ADDRESS
        self.committed_offers = dict()  # offer_hash -> CommitmentTuple
        self.fee_rate = fee_rate
        self.communication_proto = communication_protocol_cls(self.address, communication_transport, raiden_discovery, MessageHandler(self))
        communication_transport.protocol = self.communication_proto

    @property
    def address(self):
        return privtoaddr(self.private_key)

    def get_swap_commitment_by_offer_id(self, offer_id):
        pass

    def transfer_listener(self):
        # When transfer received trigger method
        # send_back_signed_offer()
        pass

    def maker_commitment_received(self, offer, commitment):

        self.send_maker_commitment_proof(commitment)

        # once the proof is sent (and ack'd), register internally:
        swap_commitment = CommitmentTuple(commitment)

        self.committed_offers[swap_commitment.offer_id] = swap_commitment

        # TODO wait for further events (start task?)
        # once there is a taker also commited, wait for SwapExecuted from taker and maker
        # if both parties posted SwapExecuted within the timeout:
        #   1) broadcast SwapCompleted
        #   2) refund to both with commitment - fees
        # else:
        #   do not refund,
        #   SwapCompleted or some 'SwapNotCompleted' not necessary because clients will be filtering based on the timeout and SwapTaken anyways


    def taker_commitment_received(self, commitment):
        swap_commitment = self.get_swap_commitment_by_offer_id(commitment.offer_id)
        # if offer timed out return commitment
        if swap_commitment.timed_out:
            self.reject_commitment(commitment)

        elif swap_commitment.is_taken:
            self.reject_commitment(commitment)

        else:
            # FIXME there should be a queue for taking the commitment, in case some commitment fails
            # then the ordering is
            try:
                swap_commitment.taker = commitment
            except CommitmentTaken:
                self.reject_commitment(commitment)
            except CommitmentMismatch:
                raise

            # sign and send back commitment proof
            self.send_maker_commitment_proof(commitment)

            successful = True # TODO: when no ack
            if not successful:
                swap_commitment.remove_taker()
                return

            # TODO wait for further events


    def reject_commitment(self, commitment):
        # TODO put in a backlog queue
        # used if unsuccessful commit
        self.raiden.transfer(commitment.token, commitment.amount, commitment.sender)

    def redeem_commitment(self, commitment):
        # from issue#10
        # called when swap was completed successfully
        fee = int(uint32.max_int / self.fee_rate * commitment.amount + 0.5) # CHECKME
        redeem_amount = commitment.amount - fee
        self.raiden.transfer(commitment.token, redeem_amount, commitment.sender)

    def send_maker_commitment_proof(self, commitment):
        commitment_proof = messages.CommitmentProof(commitment.signature)
        commitment_proof.sign(self.private_key)
        receiver = commitment.sender
        self.communication_proto.send(receiver, commitment_proof)

    def send_taker_commitment_proof(self, commitment):
        pass

    def process_offer(self, offer):
        # wait for commitment to be received as a raiden transfer
        # When commitment is received, sign offer and send back to signee
        pass

    def swap_executed(self, message):
        # decode message and match with commitment
        # register sender
        # if only one or none notify burn / keep deposits
        # if both maker and taker notify of successful swap within timeout
        # redeem deposits (keep a small fee) and broadcast swap completed
        swap_execution = SwapExecution.from_message(message)
        self.redeem_commitment(commitment)
        # broadcast that swap was completed. If success returns remove order from dict
        self.broadcast_swap_completed(message.offer_id)
        del self.committed_offers[sha3(self._get_offer_by_id(message.offer_id))]
        pass

    def broadcast_swap_taken(self, offer_id):
        pass

    def broadcast_swap_completed(self, offer_id):
        # send signed message to broadcast channel stating that swap is complete
        pass

    def _get_offer_by_id(offer_id):
        # look up the offer corresponding to an offer_id and return the offer
        # return offer
        pass


class CommitmentTuple(object):
    """
    Container to hold one (not yet taken) or two (taken) commitments and inform about some properties
    """

    # we don't need additional fields, we do not need weakrefs
    __slots__ = ('_maker', '_taker')

    def __init__(self, initial_commitment):
        self._maker = initial_commitment
        self._taker = None

    def __contains__(self, item):
        pass

    @property
    def maker(self):
        return self._maker

    @property
    def taker(self):
        return self._taker

    @property
    def timeout(self):
        return self._maker.timeout

    @property
    def timed_out(self):
        return self.timeout < time.time() * 1000

    @property
    def offer_id(self):
        return self._maker.offer_id

    @property
    def is_taken(self):
        return self._maker and self._taker

    # make shure this gets called when assigning a value to obj.taker
    def set_taker(self, second_commitment):
        if self.is_taken:
            raise Exception()

        # TODO change to Exceptions
        assert second_commitment.timeout == self.timeout
        assert second_commitment.amount == self.maker.amount
        assert second_commitment.offer_hash == self.maker.offer_hash  # CHECKME!
        assert second_commitment.offer_id == self.offer_id
        self._taker = second_commitment

    def remove_taker(self):
        raise Exception('potentially unsafe operation, taker is assumed to be immutable')
        # this gets called when somehow the commitmentproof cannot reach the taker
        # unlocks SwapCommitment for taking again
        self._taker = None

    # make shure this gets called when assigning a value to obj.maker
    def set_maker(self, value):
        raise Exception('maker is immutable')




class MessageHandler(object):

    def __init__(self, cs):
        self.cs = cs

    def on_message(self, message):
        # FIXME make 'on_' methods snake_case
        method = 'on_%s' % message.__class__.__name__.lower()
        getattr(self, method)(message)


    def on_offer(self, message):
        pass

    def on_ping(self, message):
        pass

    def on_commitment(self, message):
        # do accounting, register commitment for further processing
        # wait for incoming transfer from 'sender' with 'amount':
        #   register (sender, amount, commitment) for on_raiden_transaction_cbs
        # once the payment comes in, initiate to sign and send a CommitmentProof

        # register (sender, amount, commitment) to wait for further events

        # sender is a maker
        if message.offer_hash not in self.cs.committed_offers:
            maker_commitment = Commitment.from_message(message)
            self.cs.maker_commitment_received()

        else:
            swap_commitment = self.cs.committed_offers[message.offer_hash]





    def on_swapexecution(self, message):

        raise NotImplementedError



class BroadcastMessageHandler(object):
    """
    This needs only to be implemented if the Commitment Service will also listen to messages from the broadcast!
    """

    def __init__(self, commitment_service):
        self.service = commitment_service