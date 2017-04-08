from ethereum.utils import sha3, privtoaddr
from gevent.event import AsyncResult

from raidex.messages import SwapOffer, Commitment, CommitmentProof, ProvenOffer, OfferTaken
from raidex.raidex_node.offer_book import OfferType, Offer


class CommitmentService(object):
    """Mock for the CommitmentService
    At the moment just creates the messages that you would get for a proper commitment.
    Every raidex node has its own with the same key
    """

    def __init__(self, token_pair, client_priv_key):
        self.priv_key = sha3('simplecommitmentservice')
        self.token_pair = token_pair
        self.client_priv_key = client_priv_key
        self.address = privtoaddr(self.priv_key)

    def maker_commit_async(self, offer):
        # type: (Offer) -> AsyncResult
        offermsg = self.create_offer_msg(offer)
        offermsg.sign(self.client_priv_key)
        commitment = Commitment(offer.offer_id, offermsg.hash, offer.timeout, 42)
        commitment.sign(self.client_priv_key)
        commitment_proof = CommitmentProof(commitment.signature)
        commitment_proof.sign(self.priv_key)
        proven_offer = ProvenOffer(offermsg, commitment, commitment_proof)
        proven_offer.sign(self.client_priv_key)
        result = AsyncResult()
        result.set(proven_offer)
        return result

    def taker_commit_async(self, offer):
        # type: (Offer) -> AsyncResult
        offermsg = self.create_offer_msg(offer)
        commitment = Commitment(offer.offer_id, offermsg.hash, offer.timeout, 42)
        commitment.sign(self.client_priv_key)
        commitment_proof = CommitmentProof(commitment.signature)
        commitment_proof.sign(self.priv_key)
        proven_offer = ProvenOffer(offermsg, commitment, commitment_proof)
        proven_offer.sign(self.client_priv_key)
        result = AsyncResult()
        result.set(proven_offer)
        return result

    def create_taken(self, offer_id):
        # type: (int) -> OfferTaken
        msg = OfferTaken(offer_id)
        msg.sign(self.priv_key)
        return msg

    def create_offer_msg(self, offer):
        # type: (Offer) -> OfferMsg
        if offer.type_ == OfferType.SELL:
            return SwapOffer(self.token_pair.counter_token, offer.counter_amount, self.token_pair.base_token, offer.base_amount, offer.offer_id, offer.timeout)
        else:
            return SwapOffer(self.token_pair.base_token, offer.base_amount, self.token_pair.counter_token, offer.counter_amount, offer.offer_id, offer.timeout)

    def swap_executed(self, offer_id):
        # type: (int) -> None
        pass
