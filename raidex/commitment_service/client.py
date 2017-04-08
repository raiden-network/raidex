from ethereum.utils import encode_hex

from raidex.messages import Commitment, CommitmentProof, ProvenOffer, SwapOffer, SwapExecution
from raidex.message_broker.listeners import CheckedMessageListener
from raidex.utils.gevent_helpers import make_async
from raidex.utils import milliseconds
from raidex.raidex_node.offer_book import OfferType


class CommitmentService(object):
    """Is the view of a commitmentservice from a raidex node
    will handle making commitments
    """

    def __init__(self, token_pair, client_priv_key, commitmentservice_address, message_broker):
        self.token_pair = token_pair
        self.client_priv_key = client_priv_key
        self.message_broker = message_broker
        self.commitmentservice_address = commitmentservice_address

    @make_async
    def maker_commit_async(self, offer):
        offermsg = self.create_offer_msg(offer)
        offermsg.sign(self.client_priv_key)
        commitment = Commitment(offer.offer_id, offermsg.hash, offer.timeout, 42)
        commitment.sign(self.client_priv_key)
        self.message_broker.send(encode_hex(self.commitmentservice_address), commitment)
        # TODO send a transfer with the commitment
        commitment_proof = CheckedMessageListener(CommitmentProof, encode_hex(self.commitmentservice_address), self.message_broker, ).get_once()
        proven_offer = ProvenOffer(offermsg, commitment, commitment_proof)
        proven_offer.sign(self.client_priv_key)
        return proven_offer

    @make_async
    def taker_commit_async(self, offer):
        offermsg = self.create_offer_msg(offer)
        commitment = Commitment(offer.offer_id, offermsg.hash, offer.timeout, 42)
        commitment.sign(self.client_priv_key)
        self.message_broker.send(encode_hex(self.commitmentservice_address), commitment)
        # TODO send a transfer with the commitment
        # TODO seperate into Maker and Taker Commitment
        commitment_proof = CheckedMessageListener(CommitmentProof, encode_hex(self.commitmentservice_address),
                                                  self.message_broker, ).get_once()
        proven_offer = ProvenOffer(offermsg, commitment, commitment_proof)
        proven_offer.sign(self.client_priv_key)
        return proven_offer

    def create_offer_msg(self, offer):
        # type: (Offer) -> OfferMsg
        if offer.type_ == OfferType.SELL:
            return SwapOffer(self.token_pair.counter_token, offer.counter_amount, self.token_pair.base_token, offer.base_amount, offer.offer_id, offer.timeout)
        else:
            return SwapOffer(self.token_pair.base_token, offer.base_amount, self.token_pair.counter_token, offer.counter_amount, offer.offer_id, offer.timeout)

    def swap_executed(self, offer_id):
        # type: (int) -> None
        swap_execution = SwapExecution(offer_id, milliseconds.time())
        swap_execution.sign(self.client_priv_key)
        self.message_broker.send(encode_hex(self.commitmentservice_address), swap_execution)