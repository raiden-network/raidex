import structlog
import gevent
from gevent.event import AsyncResult
from eth_utils import int_to_big_endian, to_checksum_address

from raidex import messages
from raidex.raidex_node.commitment_service.tasks import CommitmentProofTask, RefundReceivedTask
from raidex.message_broker.listeners import CommitmentProofListener
from raidex.raidex_node.offer_book import OfferType, Offer
from raidex.raidex_node.trader.trader import TransferReceivedListener
from raidex.utils import timestamp, pex
from raidex.utils.gevent_helpers import make_async
from raidex.utils.address import binary_address


log = structlog.get_logger('node.commitment_service')
KOVAN_WETH_ADDRESS = '0xd0A1E359811322d97991E03f863a0C30C2cF029C'
KOVAN_RTT_ADDRESS = '0x92276aD441CA1F3d8942d614a6c3c87592dd30bb'


class OfferIdentifierCollision(Exception):
    pass


class MessageBrokerConnectionError(Exception):
    pass


class CommitmentServiceClient(object):
    """
    Interactions concerning the Commitment for Offers (maker) and ProvenOffers (taker).
    Handles the Commitment-Transfers in the Trader and the communication with the CS (Message-Broker)
    Methods will return the proper confirmation-messages of commitments (ProvenOffer/maker, ProvenCommitment/taker)
    """

    def __init__(self, signer, token_pair, trader_client, message_broker, commitment_service_address,
                 fee_rate):
        self.node_address = signer.checksum_address
        self.token_pair = token_pair
        self.commitment_service_address = binary_address(commitment_service_address)
        self.fee_rate = fee_rate
        self.trader_client = trader_client
        self.message_broker = message_broker
        self._sign = signer.sign
        self.commitment_proofs = dict()  # commitment_sig -> (AsyncResult<messages.CommitmentProof, False)>
        self.taker_commitments = dict()  # offer_id -> commitment
        self.maker_commitments = dict()  # offer_id -> commitment

    def start(self):
        RefundReceivedTask(self.commitment_service_address,
                           self.fee_rate,
                           self.maker_commitments,
                           self.taker_commitments,
                           self.commitment_proofs,
                           TransferReceivedListener(self.trader_client, initiator=self.commitment_service_address)).start()

        CommitmentProofTask(self.commitment_proofs, CommitmentProofListener(self.message_broker,
                                                                            topic=self.node_address)).start()

    def _create_taker_commitment_msg(self, offer, offer_hash, commitment_amount):
        if offer.offer_id in self.taker_commitments:
            raise OfferIdentifierCollision("This offer-id is still being processed")
        commitment_msg = messages.TakerCommitment(offer.offer_id, offer_hash, offer.timeout, commitment_amount)
        self._sign(commitment_msg)
        return commitment_msg

    def _create_maker_commitment_msg(self, offer, offer_hash, commitment_amount):
        if offer.offer_id in self.maker_commitments:
            raise OfferIdentifierCollision("This offer-id is still being processed")
        commitment_msg = messages.MakerCommitment(offer.offer_id, offer_hash, offer.timeout, commitment_amount)
        self._sign(commitment_msg)
        return commitment_msg

    def _create_proven_offer_msg(self, offer_msg, commitment_msg, commitment_proof_msg):
        proven_offer = messages.ProvenOffer(offer_msg, commitment_msg, commitment_proof_msg)
        self._sign(proven_offer)
        return proven_offer

    def _create_swap_execution_msg(self, offer_id, timestamp_):
        swap_execution = messages.SwapExecution(offer_id, timestamp_)
        self._sign(swap_execution)
        return swap_execution

    def _send_message_to_commitment_service(self, message):
        success = self.message_broker.send(topic=self.commitment_service_address, message=message)
        # FIXME in our current model, we don't have any guarantees, that a message arrived at the target
        # so we can't know for sure if it was successful here
        # TODO this should be raised in the message-broker
        if success is False:
            raise MessageBrokerConnectionError()

    def _send_commitment_msg(self, commitment_msg):
        # type: ([messages.TakerCommitment, messages.MakerCommitment]) -> AsyncResult

        if commitment_msg.signature in self.commitment_proofs:
            raise OfferIdentifierCollision()
        self._send_message_to_commitment_service(commitment_msg)
        commitment_proof_async_result = AsyncResult()
        self.commitment_proofs[commitment_msg.signature] = commitment_proof_async_result

        return commitment_proof_async_result

    def _send_transfer(self, token_address, offer_id, commitment_amount):
        return self.trader_client.transfer(token_address, self.commitment_service_address, commitment_amount,
                                           offer_id)

    def create_offer_msg(self, offer):
        # type: (Offer) -> messages.SwapOffer

        if offer.type == OfferType.SELL:
            return messages.SwapOffer(self.token_pair.counter_token, offer.counter_amount, self.token_pair.base_token,
                                      offer.base_amount, offer.offer_id, offer.timeout)
        else:
            return messages.SwapOffer(self.token_pair.base_token, offer.base_amount, self.token_pair.counter_token,
                                      offer.counter_amount, offer.offer_id, offer.timeout)

    def maker_commit(self, offer):
        # type: (Offer) -> (messages.ProvenOffer, None)

        commitment_amount = offer.commitment_amount
        offer_msg = self.create_offer_msg(offer)
        try:
            commitment_msg = self._create_maker_commitment_msg(offer, offer_msg.hash, commitment_amount)
        except OfferIdentifierCollision:
            return None
        self.maker_commitments[offer.offer_id] = commitment_msg

        try:
            commitment_proof_async_result = self._send_commitment_msg(commitment_msg)
        except MessageBrokerConnectionError:
            # FIXME later this shouldn't be caught here but higher above in the call hierarchy,
            log.debug('Message broker failed to send: {}'.format(commitment_msg))
            return None

        success = self._send_transfer(KOVAN_RTT_ADDRESS, offer.offer_id, commitment_amount)
        if not success:
            log.debug(
                'Trader failed to transfer maker-commitment for offer: pex(id)={}'.format(pex(int_to_big_endian(offer.offer_id))))
            return None

        seconds_to_timeout = timestamp.seconds_to_timeout(offer.timeout)
        try:
            commitment_proof_msg = commitment_proof_async_result.get(timeout=seconds_to_timeout)
        except gevent.Timeout:
            # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
            log.debug('CS didn\'t respond with a CommitmentProof or Refund')
            return None

        if commitment_proof_msg is None:
            # the async-result was set to None (triggered by a refund)
            log.debug('CS rejected the commitment!')
            return None

        assert isinstance(commitment_proof_msg, messages.CommitmentProof)
        assert commitment_proof_msg.sender == self.commitment_service_address
        proven_offer_msg = self._create_proven_offer_msg(offer_msg, commitment_msg, commitment_proof_msg)
        return proven_offer_msg

    @make_async
    def maker_commit_async(self, offer):
        return self.maker_commit(offer)

    def taker_commit(self, offer):
        # type: (Offer) -> (messages.ProvenCommitment, None)

        assert offer.commitment_amount is not None
        offer_msg = self.create_offer_msg(offer)

        try:
            commitment_msg = self._create_taker_commitment_msg(offer, offer_msg.hash, offer.commitment_amount)
        except OfferIdentifierCollision:
            return None
        self.taker_commitments[offer.offer_id] = commitment_msg

        try:
            commitment_proof_async_result = self._send_commitment_msg(commitment_msg)
        except MessageBrokerConnectionError:
            # FIXME later this shouldn't be caught here but higher above in the call hierarchy,
            log.debug('Message broker failed to send: {}'.format(commitment_msg))
            return None

        self.commitment_proofs[commitment_msg.signature] = commitment_proof_async_result

        success = self._send_transfer(offer.offer_id, offer.commitment_amount)
        if success is not True:
            log.debug(
                'Trader failed to transfer taker-commitment for offer: pex(id)={}'.format(pex(offer.offer_id)))
            return None

        seconds_to_timeout = timestamp.seconds_to_timeout(offer.timeout)
        try:
            commitment_proof_msg = commitment_proof_async_result.get(timeout=seconds_to_timeout)
        except gevent.Timeout:
            # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
            log.debug('CS didn\'t respond with a CommitmentProof or Refund')
            return None

        if commitment_proof_msg is None:
            # the async-result was set to None (triggered by a refund)
            log.debug('CS rejected the commitment!')
            return None

        assert isinstance(commitment_proof_msg, messages.CommitmentProof)
        assert commitment_proof_msg.sender == self.commitment_service_address
        proven_commitment = messages.ProvenCommitment(commitment_msg, commitment_proof_msg)
        self._sign(proven_commitment)
        return proven_commitment

    @make_async
    def taker_commit_async(self, offer):
        return self.taker_commit(offer)

    # TODO this should also wait for the final SwapCompleted from the CS and return that message
    def report_swap_executed(self, offer_id):
        # type: (int) -> None
        swap_execution = self._create_swap_execution_msg(offer_id, timestamp.time_int())
        self._send_message_to_commitment_service(swap_execution)

    def create_taken(self, offer_id):
        # leave until the code using this method is changed
        raise NotImplementedError("Mock-CS functionality not available inside of CS-client implementation")

    def create_swap_completed(self, offer_id):
        # leave until the code using this method is changed
        raise NotImplementedError("Mock-CS functionality not available inside of CS-client implementation")
