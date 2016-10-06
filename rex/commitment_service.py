import rlp
import uint32
import time

from ethereum.utils import sha3
from raiden.api import transfer


class CommitmentService(object):

    def __init__(self, cs_address, fee):
        self.cs_address = cs_address
        self.commited_offers = dict()
        self.fee = fee

    def transfer_listener():
        # When transfer received trigger method
        # send_back_signed_offer()
        pass

    def maker_commitment_received(self, offer, commitment):
        # sign and send back commitment_proof = sign(commitment_sig, cs)
        commitment_proof = sign(commitment.signature, self.cs_address)
        self.send_back_commitment_proof(commitment_proof)

    def taker_commitment_received(self, offer, commitment):
        # if offer timed out return commitment
        if commitment.timeout < time.time() * 1000:
            self.return_commitment(commitment)
        # if offer already taken return commitment
        elif sha3(offer) in self.commited_offers:
            self.return_commitment(commitment)
        else:
            # when commitment is received matching a given offer sign it and return to sender
            hashlock = sha3(offer)
            self.commited_offers[hashlock] = commitment
            # sign and send back commitment proof
            commitment_proof = sign(commitment.signature, self.cs_address)
            self.send_back_commitment_proof(commitment_proof)

    def return_commitment(self, commitment):
        # used if unsuccessful commit
        transfer(commitment.token, commitment.amount, commitment.sender)

    def redeem_commitment(self, commitment):
        # from issue#10
        fee = int(uint32.max_int / self.fee * commitment.amount + 0.5)
        redeem_amount = commitment.amount - fee
        transfer(commitment.token, redeem_amount, commitment.sender)

    def send_back_commitment_proof(self, commitment_proof):
        # sign offer and send it back to maker/taker
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
        pass

    def broadcast_swap_completed(self, order_id):
        # send signed message to broadcast channel stating that swap is complete
        pass


class Commitment(object):

    def __init__(self, amount, offer, timeout, commitment_id, sender):
        self.amount = amount
        self.offer = offer
        self.timeout = timeout
        self.commitment_id = commitment_id
        self.sender = sender
