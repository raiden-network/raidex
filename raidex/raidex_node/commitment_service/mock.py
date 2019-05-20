from gevent.event import AsyncResult
from raidex import messages
from raidex.signing import Signer
from raidex.raidex_node.offer_book import OfferDeprecated
from raidex.raidex_node.order.offer import OfferType
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
            signer = Signer()
        self.signer = signer
        self.swaps = {}

    @property
    def address(self):
        return self.signer.address

    def make_offer(self, commitment_service_client, offer_id):
        if offer_id in self.swaps:
            return False
        self.swaps[offer_id] = Swap(commitment_service_client)
        return True

    def try_take_offer(self, commitment_service_client, offer_id):
        swap = self.swaps.get(offer_id)
        if swap is None:
            return False
        success = swap.try_take(commitment_service_client)
        return success

    def report_swap_executed(self, commitment_service_client, offer_id):
        swap = self.swaps.get(offer_id)
        if swap is None:
            return False
        success = swap.report_executed(commitment_service_client)
        return success

    def swap_is_completed(self, offer_id):
        swap = self.swaps.get(offer_id)
        if swap is None:
            return False
        if swap.is_completed:
            return True
        else:
            return False



class NonFailingCommitmentServiceGlobal(object):
    """
    Replacement of CommitmentServiceGlobal
    This has no inherent logic and always returns True for all methods.
    This makes sense to use, when no Taker/Maker matchmaking logic should be present
    and the CommitmentService Clients are only being used to construct and broadcast the
    correct messages, signed by the CS.
    """
    def __init__(self, signer=None):
        if signer is None:
            signer = Signer.random()
        self.signer = signer

    @property
    def address(self):
        return self.signer.address

    def make_offer(self, commitment_service_client, offer_id):
        return True

    def try_take_offer(self, commitment_service_client, offer_id):
        return True

    def report_swap_executed(self, commitment_service_client, offer_id):
        return True

    def swap_is_completed(self, offer_id):
        return True


class CommitmentServiceClientMock(object):
    """Mock for the CommitmentService
    Has the same interface as the CommitmentService client, but also includes the mocked CS-Node behaviour

    At the moment just creates the messages that you would get for a proper commitment.
    Every raidex node has its own with the same key
    """
    _commitment_service_global = NonFailingCommitmentServiceGlobal()

    def __init__(self, node_signer, token_pair, message_broker, fee_rate=0.1, commitment_service_global=None):
        if commitment_service_global is not None:
            self._commitment_service_global = commitment_service_global
        self._global_sign = self._commitment_service_global.signer.sign
        self.commitment_service_address = self._commitment_service_global.address
        self.node_address = node_signer.address
        self.token_pair = token_pair
        self._sign = node_signer.sign
        self.fee_rate = fee_rate
        self.message_broker = message_broker

    def maker_commit_async(self, offer):
        # type: (OfferDeprecated) -> AsyncResult
        result = AsyncResult()
        success = self._commitment_service_global.make_offer(self, offer.offer_id)
        if success is False:
            result.set(None)
            return result
        offer_msg = self.create_offer_msg(offer)
        commitment_msg = messages.MakerCommitment(offer.offer_id, offer_msg.hash, offer.timeout_date, 42)
        self._sign(commitment_msg)

        commitment_proof_msg = messages.CommitmentProof(commitment_msg.signature)
        self._global_sign(commitment_proof_msg)
        proven_offer_msg = messages.ProvenOffer(offer_msg, commitment_msg, commitment_proof_msg)
        self._sign(proven_offer_msg)
        result.set(proven_offer_msg)
        return result

    def taker_commit_async(self, offer):
        # type: (OfferDeprecated) -> AsyncResult
        result = AsyncResult()
        success = self._commitment_service_global.try_take_offer(self, offer.offer_id)
        if success is False:
            result.set(None)
            return result
        offer_msg = self.create_offer_msg(offer)
        commitment_msg = messages.TakerCommitment(offer.offer_id, offer_msg.hash, offer.timeout_date, 42)
        self._sign(commitment_msg)
        commitment_proof_msg = messages.CommitmentProof(commitment_msg.signature)
        self._global_sign(commitment_proof_msg)
        proven_commitment_msg = messages.ProvenCommitment(commitment_msg, commitment_proof_msg)
        self._sign(proven_commitment_msg)
        result.set(proven_commitment_msg)
        self.message_broker.broadcast(self.create_taken(offer.offer_id))
        return result

    def create_taken(self, offer_id):
        # type: (int) -> OfferTaken
        offer_taken_msg = messages.OfferTaken(offer_id)
        self._global_sign(offer_taken_msg)
        return offer_taken_msg

    def create_swap_completed(self, offer_id):
        # type: (int) -> SwapCompleted
        swap_completed_msg = messages.SwapCompleted(offer_id, timestamp.time())
        self._global_sign(swap_completed_msg)
        return swap_completed_msg

    def create_offer_msg(self, offer):
        # type: (OfferDeprecated) -> OfferMsg
        if offer.type == OfferType.SELL:
            return messages.SwapOffer(self.token_pair.quote_token, offer.quote_amount, self.token_pair.base_token,
                                      offer.base_amount, offer.offer_id, offer.timeout_date)
        else:
            return messages.SwapOffer(self.token_pair.base_token, offer.base_amount, self.token_pair.quote_token,
                                      offer.quote_amount, offer.offer_id, offer.timeout_date)

    def report_swap_executed(self, offer_id):
        # type: (int) -> None
        success = self._commitment_service_global.report_swap_executed(self, offer_id)
        if success is True and self._commitment_service_global.swap_is_completed(offer_id):
            swap_completed_msg = self.create_swap_completed(offer_id)
            self.message_broker.broadcast(swap_completed_msg)

    def start(self):
        # in order to provide the same interface as the client.CommitmentService
        # the actual tasks are not running because this is a failsafe mock without CS-interaction
        pass
