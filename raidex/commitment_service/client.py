import gevent
from ethereum import slogging
from gevent.event import AsyncResult

from raidex import messages
from raidex.commitment_service.tasks import CommitmentProofTask, RefundReceivedTask
from raidex.message_broker.listeners import CommitmentProofListener
from raidex.raidex_node.offer_book import OfferType, Offer
from raidex.raidex_node.trader.trader import TransferReceivedListener
from raidex.utils import timestamp
from raidex.utils.gevent_helpers import make_async

log = slogging.get_logger('node.commitment_service')


class OfferIdentifierCollision(Exception):
    pass


class CommitmentServiceClient(object):
    """
    Interactions concerning the Commitment for Offers (maker) and ProvenOffers (taker).
    Handles the Commitment-Transfers in the Trader and the communication with the CS (Message-Broker)
    Methods will return the proper confirmation-messages of commitments (ProvenOffer/maker, ProvenCommitment/taker)
    """

    def __init__(self, signer, token_pair, trader_client, message_broker, commitment_service_address,
                 fee_rate):
        self.node_address = signer.address
        self.token_pair = token_pair
        self.commitment_service_address = commitment_service_address
        self.fee_rate = fee_rate
        self.trader_client = trader_client
        self.message_broker = message_broker
        self._sign = signer.sign
        self.commitment_proofs = dict()  # commitment_sig -> (AsyncResult<messages.CommitmentProof, False)>
        self.commitments = dict()  # offer_id -> commitment

    def start(self):
        RefundReceivedTask(self.commitment_service_address, self.fee_rate, self.commitments,
                           self.commitment_proofs, TransferReceivedListener(self.trader_client)).start()

        CommitmentProofTask(self.commitment_proofs, CommitmentProofListener(self.message_broker,
                                                                            topic=self.node_address)).start()

    @make_async
    def maker_commit_async(self, offer, commitment_amount):
        # type: (Offer) -> (ProvenOffer)
        offermsg = self.create_offer_msg(offer)
        # self._sign(offermsg)

        commitment = messages.Commitment(offer.offer_id, offermsg.hash, offer.timeout, commitment_amount)
        self._sign(commitment)

        # we shouldn't reuse offer_ids,
        if offer.offer_id in self.commitments:
            raise OfferIdentifierCollision("This offer-id is still being processed")
        # map offer_id -> commitment
        self.commitments[offer.offer_id] = commitment

        success = self.message_broker.send(self.commitment_service_address, commitment)
        # TODO better handling of unsuccessful sents (e.g. resend-queue)
        if success is False:
            log.debug('Message broker failed to send: {}'.format(commitment))
            return False

        commitment_proof_async_result = AsyncResult()

        # register the async result
        self.commitment_proofs[commitment.signature] = commitment_proof_async_result

        transfer_async_result = self.trader_client.transfer(self.commitment_service_address, commitment_amount,
                                                            offer.offer_id)
        success = transfer_async_result.get()

        if success is False:
            log.debug('Trader failed to transfer commitment for offer: {}'.format(offer))
            return None

        # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
        timeout = timestamp.seconds_to_timeout(offer.timeout)
        try:
            commitment_proof = commitment_proof_async_result.get(timeout=timeout)
        except gevent.Timeout:
            # don't set the AsyncResult, since we still should receive a Refund
            # but return None later on nevertheless
            commitment_proof = None

        if commitment_proof is None:
            log.debug('CS didn\'t respond with a CommitmentProof')
            return None

        assert isinstance(commitment_proof, messages.CommitmentProof)
        assert commitment_proof.sender == self.commitment_service_address

        proven_offer = messages.ProvenOffer(offermsg, commitment, commitment_proof)
        self._sign(proven_offer)
        return proven_offer

    @make_async
    def taker_commit_async(self, offer):
        # type: (Offer) -> (messages.ProvenCommitment)
        assert offer.commitment_amount
        offermsg = self.create_offer_msg(offer)

        commitment = messages.Commitment(offer.offer_id, offermsg.hash, offer.timeout, offer.commitment_amount)
        self._sign(commitment)

        # map offer_id -> commitment
        self.commitments[offer.offer_id] = commitment

        success = self.message_broker.send(self.commitment_service_address, commitment)
        if success is False:
            log.debug('Message broker failed to send: {}'.format(commitment))
            return None

        commitment_proof_async_result = AsyncResult()
        # register the AsyncResult:
        self.commitment_proofs[commitment.signature] = commitment_proof_async_result

        transfer_async_result = self.trader_client.transfer(self.commitment_service_address, offer.commitment_amount,
                                                            offer.offer_id)
        success = transfer_async_result.get()

        if success is False:
            log.debug('Trader failed to transfer commitment for offer: {}'.format(offer))
            commitment_proof_async_result.set(None)
            return None

        # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
        timeout = timestamp.seconds_to_timeout(offer.timeout)
        # TODO: check Timeout! and dict delection etc
        try:
            commitment_proof = commitment_proof_async_result.get(timeout=timeout)
        except gevent.Timeout:
            # don't set the AsyncResult, since we still should receive a Refund
            # but return None later on nevertheless
            commitment_proof = None

        if commitment_proof is None:
            log.debug('CS didn\'t respond with a CommitmentProof')
            return None

        assert isinstance(commitment_proof, messages.CommitmentProof)
        assert commitment_proof.sender == self.commitment_service_address

        proven_commitment = messages.ProvenCommitment(commitment, commitment_proof)
        self._sign(proven_commitment)
        return proven_commitment

    def create_offer_msg(self, offer):
        # type: (Offer) -> messages.SwapOffer
        if offer.type_ == OfferType.SELL:
            return messages.SwapOffer(self.token_pair.counter_token, offer.counter_amount, self.token_pair.base_token,
                                      offer.base_amount, offer.offer_id, offer.timeout)
        else:
            return messages.SwapOffer(self.token_pair.base_token, offer.base_amount, self.token_pair.counter_token,
                                      offer.counter_amount, offer.offer_id, offer.timeout)

    def create_taken(self, offer_id):
        # leave until the code using this method is changed
        raise NotImplementedError("Mock-CS functionality not available inside of CS-client implementation")

    def create_swap_completed(self, offer_id):
        # leave until the code using this method is changed
        raise NotImplementedError("Mock-CS functionality not available inside of CS-client implementation")

    def report_swap_executed(self, offer_id):
        # type: (int) -> None
        swap_execution = messages.SwapExecution(offer_id, timestamp.time_int())
        self._sign(swap_execution)
        self.message_broker.send(topic=self.commitment_service_address, message=swap_execution)
