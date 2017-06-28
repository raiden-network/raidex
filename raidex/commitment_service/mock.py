from gevent.event import AsyncResult
from raidex import messages
from raidex.signing import Signer

from raidex.raidex_node.offer_book import OfferType, Offer
from raidex.utils import timestamp


class Swap(object):

    def __init__(self, maker_instance):
        self._maker = maker_instance
        self._taker = None
        self._maker_executed = False
        self._taker_executed = False

    def try_take(self, cs_instance):
        if self._taker is None:
            self._taker = cs_instance
            return True
        return False

    @property
    def is_completed(self):
        # no timeout comparison
        return self._maker_executed and self._taker_executed

    @property
    def is_taken(self):
        return (self._maker is not None) and (self._taker is not None)

    def report_executed(self, cs_instance):
        if self.is_completed:
            return False
        if not self._taker:
            return False
        if cs_instance not in (self._maker, self._taker):
            return False
        if cs_instance is self._maker:
            self._maker_executed = True
            return True
        if cs_instance is self._taker:
            self._taker_executed = True
            return True


class CommitmentServiceGlobal(object):
    """
    Serves as the brain of the CS-Server, that keeps track of all the reported swaps
    """
    def __init__(self, signer=None):
        if signer is None:
            signer = Signer.random()
        self.signer = signer
        self.swaps = {}

    @property
    def address(self):
        return self.signer.address

    def make_offer(self, cs_instance, offer_id):
        if offer_id in self.swaps:
            return False
        self.swaps[offer_id] = Swap(cs_instance)
        return True

    def report_swap_executed(self, cs_instance, offer_id):
        swap = self.swaps.get(offer_id)
        if swap is None:
            return False
        success = swap.report_executed(cs_instance)
        return success

    def try_take_offer(self, cs_instance, offer_id):
        swap = self.swaps.get(offer_id)
        if swap is None:
            return False
        success = swap.try_take(cs_instance)
        return success


class CommitmentServiceMock(object):
    """Mock for the CommitmentService
    Has the same interface as the CommitmentService client, but also includes the mocked CS-Node behaviour

    At the moment just creates the messages that you would get for a proper commitment.
    Every raidex node has its own with the same key
    """
    _cs_global = CommitmentServiceGlobal()

    def __init__(self, node_signer, token_pair, message_broker, fee_rate=0.1, cs_global=None):
        if cs_global is not None:
            self._cs_global = cs_global
        self._cs_sign = self._cs_global.signer.sign
        self.commitment_service_address = self._cs_global.address
        self.node_address = node_signer.address
        self.token_pair = token_pair
        self._sign = node_signer.sign
        self.fee_rate = fee_rate
        self.message_broker = message_broker

    def maker_commit_async(self, offer):
        # type: (Offer) -> AsyncResult
        result = AsyncResult()
        success = self._cs_global.make_offer(self, offer.offer_id)
        if success is False:
            result.set(None)
            return result
        offermsg = self.create_offer_msg(offer)
        # self._sign(offermsg)
        commitment = messages.Commitment(offer.offer_id, offermsg.hash, offer.timeout, 42)
        self._sign(commitment)

        commitment_proof = messages.CommitmentProof(commitment.signature)
        self._cs_sign(commitment_proof)
        proven_offer = messages.ProvenOffer(offermsg, commitment, commitment_proof)
        self._sign(proven_offer)
        result.set(proven_offer)
        return result

    def taker_commit_async(self, offer):
        # type: (Offer) -> AsyncResult
        result = AsyncResult()
        success = self._cs_global.try_take_offer(self, offer.offer_id)
        if success is False:
            result.set(None)
            return result
        offermsg = self.create_offer_msg(offer)
        commitment = messages.Commitment(offer.offer_id, offermsg.hash, offer.timeout, 42)
        self._sign(commitment)
        commitment_proof = messages.CommitmentProof(commitment.signature)
        self._cs_sign(commitment_proof)
        proven_commitment = messages.ProvenCommitment(commitment, commitment_proof)
        self._sign(proven_commitment)
        result.set(proven_commitment)
        self.message_broker.broadcast(self.create_taken(offer.offer_id))
        return result

    def create_taken(self, offer_id):
        # type: (int) -> OfferTaken
        msg = messages.OfferTaken(offer_id)
        self._cs_sign(msg)
        return msg

    def create_swap_completed(self, offer_id):
        # type: (int) -> SwapCompleted
        msg = messages.SwapCompleted(offer_id, timestamp.time())
        self._cs_sign(msg)
        return msg

    def create_offer_msg(self, offer):
        # type: (Offer) -> OfferMsg
        if offer.type_ == OfferType.SELL:
            return messages.SwapOffer(self.token_pair.counter_token, offer.counter_amount, self.token_pair.base_token,
                                      offer.base_amount, offer.offer_id, offer.timeout)
        else:
            return messages.SwapOffer(self.token_pair.base_token, offer.base_amount, self.token_pair.counter_token,
                                      offer.counter_amount, offer.offer_id, offer.timeout)

    def report_swap_executed(self, offer_id):
        # type: (int) -> None
        swap_completed = self._cs_global.report_swap_executed(self, offer_id)
        if swap_completed is True:
            swap_completed = self.create_swap_completed(offer_id)
            self.message_broker.broadcast(swap_completed)

    def start(self):
        # in order to provide the same interface as the client.CommitmentService
        # the actual tasks are not running because this is a failsafe mock without CS-interaction
        pass
