from collections import defaultdict, namedtuple
from ethereum import slogging

import gevent
from gevent.event import AsyncResult

from raidex import messages
from raidex.message_broker.listeners import CommitmentProofListener, OfferTakenListener
from raidex.raidex_node.trader.trader import TransferReceivedListener
from raidex.raidex_node.offer_book import OfferType, Offer
from raidex.utils.gevent_helpers import make_async
from raidex.utils import timestamp
from raidex.tests.utils import float_isclose

log = slogging.get_logger('node.commitment_service')


class CommitmentService(object):
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
        # type: (Offer) -> (bool, ProvenOffer)
        offermsg = self.create_offer_msg(offer)
        # self._sign(offermsg)

        commitment = messages.Commitment(offer.offer_id, offermsg.hash, offer.timeout, commitment_amount)
        self._sign(commitment)

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
            return False

        # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
        timeout = timestamp.seconds_to_timeout(offer.timeout)
        try:
            commitment_proof = commitment_proof_async_result.get(timeout=timeout)
        except gevent.Timeout:
            # don't set the AsyncResult, since we still should receive a Refund
            # but return False later on nevertheless
            commitment_proof = False

        if commitment_proof is False:
            log.debug('CS didn\'t respond with a CommitmentProof')
            return False

        assert isinstance(commitment_proof, messages.CommitmentProof)
        assert commitment_proof.sender == self.commitment_service_address

        proven_offer = messages.ProvenOffer(offermsg, commitment, commitment_proof)
        self._sign(proven_offer)
        return proven_offer

    @make_async
    def taker_commit_async(self, offer):
        # type: (Offer) -> (bool, messages.ProvenCommitment)
        assert offer.hash
        assert offer.commitment_amount

        commitment = messages.Commitment(offer.offer_id, offermsg.hash, offer.timeout, offer.commitment_amount)
        self._sign(commitment)

        # map offer_id -> commitment
        self.commitments[offer.offer_id] = commitment

        success = self.message_broker.send(self.commitment_service_address, commitment)
        if success is False:
            log.debug('Message broker failed to send: {}'.format(commitment))
            return False

        commitment_proof_async_result = AsyncResult()
        # register the AsyncResult:
        self.commitment_proofs[commitment.signature] = commitment_proof_async_result

        transfer_async_result = self.trader_client.transfer(self.commitment_service_address, offer.commitment_amount,
                                                            offer.offer_id)
        success = transfer_async_result.get()

        if success is False:
            log.debug('Trader failed to transfer commitment for offer: {}'.format(offer))
            commitment_proof_async_result.set(False)
            return False

        # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
        timeout = timestamp.seconds_to_timeout(offer.timeout)
        # TODO: check Timeout! and dict delection etc
        try:
            commitment_proof = commitment_proof_async_result.get(timeout=timeout)
        except gevent.Timeout:
            # don't set the AsyncResult, since we still should receive a Refund
            # but return False later on nevertheless
            commitment_proof = False

        if commitment_proof is False:
            log.debug('CS didn\'t respond with a CommitmentProof')
            return False

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
        raise AttributeError("Mock-CS functionality not available inside of CS-client implementation")

    def create_swap_completed(self, offer_id):
        # leave until the code using this method is changed
        raise AttributeError("Mock-CS functionality not available inside of CS-client implementation")

    def swap_executed(self, offer_id):
        # type: (int) -> None
        swap_execution = messages.SwapExecution(offer_id, timestamp.time_int())
        self._sign(swap_execution)
        self.message_broker.send(topic=self.commitment_service_address, message=swap_execution)


class CommitmentProofTask(gevent.Greenlet):
    def __init__(self, commitment_proofs_dict, commitment_proof_listener):
        self.commitment_proofs = commitment_proofs_dict
        self.commitment_proof_listener = commitment_proof_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.commitment_proof_listener.start()
        while True:
            commitment_proof = self.commitment_proof_listener.get()
            log.debug('Received commitment proof {}'.format(commitment_proof))
            assert isinstance(commitment_proof, messages.CommitmentProof)

            async_result = self.commitment_proofs.get(commitment_proof.commitment_sig)
            if async_result:
                async_result.set(commitment_proof)
            else:
                # we should be waiting on the commitment-proof!
                # assume non-malicious actors:
                # if we receive a proof we are not waiting on, there is something wrong
                assert False


class RefundReceivedTask(gevent.Greenlet):

    def __init__(self, cs_address, fee_rate, commitments_dict, commitment_proofs_dict,
                 transfer_received_listener):
        self.commitments = commitments_dict
        self.commitment_proofs = commitment_proofs_dict
        self.transfer_received_listener = transfer_received_listener
        self.commitment_service_address = cs_address
        self.fee_rate = fee_rate
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.transfer_received_listener.start()
        while True:
            receipt = self.transfer_received_listener.get()
            try:
                commitment = self.commitments[receipt.identifier]
            except KeyError:
                # we're not waiting for this refund
                log.debug("Received unexpected Refund: {}".format(receipt))
                continue

            # assume non-malicious cs, so only asserting correctness for now:
            minus_fee = commitment.amount - commitment.amount * self.fee_rate
            assert float_isclose(commitment.amount, receipt.amount) or float_isclose(receipt.amount, minus_fee)
            assert receipt.identifier == commitment.offer_id
            assert receipt.sender == self.commitment_service_address

            # set the AsyncResult for the Commitment-Proof we are expecting
            async_result = self.commitment_proofs.get(commitment.signature)
            if async_result:
                async_result.set(False)
                log.debug("Refund received: {}".format(receipt))

                # once we receive a refund, everything is settled for us and we can delete the commitment
                del self.commitments[receipt.identifier]