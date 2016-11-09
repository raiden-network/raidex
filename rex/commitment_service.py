import rlp
import uint32
import time

from ethereum.utils import privtoaddr, sha3
from raiden.api import transfer
from raiden.encoding.signing import recover_publickey, GLOBAL_CTX
from raiden.encoding.signing import sign as _sign
from secp256k1 import PrivateKey, ALL_FLAGS

from rex.utils import ETHER_TOKEN_ADDRESS


def sign(messagedata, private_key):
    if not isinstance(private_key, PrivateKey):
        privkey_instance = PrivateKey(privkey=private_key, flags=ALL_FLAGS, ctx=GLOBAL_CTX)
    else:
        privkey_instance = private_key
    return _sign(messagedata, privkey_instance)


class CommitmentService(object):

    def __init__(self, private_key, fee_rate):
        self.private_key = private_key
        self.commitment_asset = ETHER_TOKEN_ADDRESS
        self.commited_offers = dict()
        self.fee_rate = fee_rate

    def address(self):
        return privtoaddr(self.private_key)

    def transfer_listener():
        # When transfer received trigger method
        # send_back_signed_offer()
        pass

    def maker_commitment_received(self, offer, commitment):
        # sign and send back commitment_proof = sign(commitment_sig, cs)
        commitment_proof = sign(commitment.signature, self.private_key)
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
            commitment_proof = sign(commitment.signature, self.private_key)
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
        # broadcast that swap was completed. If success returns remove order from dict
        del self.commited_offers[sha3(self._get_offer_by_id)]
        pass

    def broadcast_swap_completed(self, order_id):
        # send signed message to broadcast channel stating that swap is complete
        pass

    def _get_offer_by_id(offer_id):
        # look up the offer corresponding to an offer_id and return the offer
        # return offer
        pass


class Commitment(object):

    def __init__(self, amount, offer, timeout, commitment_id, sender):
        self.amount = amount
        self.offer = offer
        self.timeout = timeout
        self.commitment_id = commitment_id
        self.sender = sender
