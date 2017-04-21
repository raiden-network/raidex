from collections import defaultdict
from ethereum.utils import sha3
from ethereum import slogging

import gevent
from gevent.event import AsyncResult

from raidex.messages import SwapOffer as OfferMsg, Commitment, CommitmentProof, ProvenOffer, ProvenCommitment
from raidex.message_broker.listeners import CommitmentProofListener, OfferTakenListener
from raidex.raidex_node.offer_book import OfferType, Offer
from raidex.utils.gevent_helpers import make_async
from raidex.utils import milliseconds,pex

log = slogging.get_logger('node.commitment_service')


class CommitmentService(object):
    """
    Interactions concerning the Commitment for Offers (maker) and ProvenOffers (taker).
    Handles the Commitment-Transfers in the Trader and the communication with the CS (Message-Broker)
    Methods will return the proper confirmation-messages of commitments (ProvenOffer/maker, ProvenCommitment/taker)
    """

    def __init__(self, node_address, token_pair, sign_func, trader_client, message_broker, commitment_service_address):
        self.node_address = node_address
        self.token_pair = token_pair
        self.commitment_service_address = commitment_service_address
        self.trader_client = trader_client
        self.message_broker = message_broker
        self._sign_func = sign_func
        self.commitment_proofs = defaultdict(AsyncResult)  # commitment_sig -> (AsyncResult<messages.CommitmentProof, False)>

    def start(self):
        TakenTask(self.commitment_proofs, OfferTakenListener(self.message_broker)).start()
        CommitmentProofTask(self.commitment_proofs, CommitmentProofListener(self.message_broker,
                                                                            topic=self.node_address)).start()

    @make_async
    def maker_commit_async(self, offer, commitment_amount):
        # type: (Offer) -> (bool, ProvenOffer)
        offermsg = self.create_offer_msg(offer)
        self._sign_func(offermsg)

        commitment = Commitment(offer.offer_id, offermsg.hash, offer.timeout, commitment_amount)
        self._sign_func(commitment)

        success = self.message_broker.send(self.commitment_service_address, commitment)
        # TODO better handling of unsuccessful sents (e.g. resend-queue)
        if success is False:
            log.debug('Message broker failed to send: {}'.format(commitment))
            return False

        commitment_proof_async_result = self.commitment_proofs[commitment.signature]

        transfer_async_result = self.trader_client.transfer(self.commitment_service_address, commitment_amount,
                                                            offer.offer_id)
        success = transfer_async_result.get()

        if success is False:
            log.debug('Trader failed to transfer commitment for offer: {}'.format(offer))
            return False

        # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
        timeout = milliseconds.seconds_to_timeout(offer.timeout)
        try:
            commitment_proof = commitment_proof_async_result.get(timeout=timeout)
        except gevent.Timeout:
            commitment_proof = False

        if commitment_proof is False:
            log.debug('CS didn\'t respond with a CommitmentProof')
            # TODO account for refunding, start task that waits on specific refunds
            return False

        assert isinstance(commitment_proof, CommitmentProof)
        assert commitment_proof.sender == self.commitment_service_address

        proven_offer = ProvenOffer(offermsg, commitment, commitment_proof)
        self._sign_func(proven_offer)
        return proven_offer

    @make_async
    def taker_commit_async(self, offer):
        # type: (Offer) -> (bool, ProvenCommitment)
        assert offer.hash
        assert offer.commitment_amount

        commitment = Commitment(offer.offer_id, offer.hash, offer.timeout, offer.commitment_amount)
        self._sign_func(commitment)

        success = self.message_broker.send(self.commitment_service_address, commitment)
        # TODO better handling of unsuccessful sents (e.g. resend-queue)
        if success is False:
            log.debug('Message broker failed to send: {}'.format(commitment))
            return False

        transfer_async_result = self.trader_client.transfer(self.commitment_service_address, offer.commitment_amount, offer.offer_id)
        success = transfer_async_result.get()

        if success is False:
            log.debug('Trader failed to transfer commitment for offer: {}'.format(offer))
            return False

        commitment_proof_async_result = self.commitment_proofs[commitment.signature]

        # if the offer timed out, we don't want to continue waiting on the proof (e.g. CS unresponsive)
        timeout = milliseconds.seconds_to_timeout(offer.timeout)
        try:
            commitment_proof = commitment_proof_async_result.get(timeout=timeout)
        except gevent.Timeout:
            commitment_proof = False

        if commitment_proof is False:
            log.debug('CS didn\'t respond with a CommitmentProof')
            # TODO account for refunding, start task that waits on specific refunds
            return False

        assert isinstance(commitment_proof, CommitmentProof)
        assert commitment_proof.sender == self.commitment_service_address

        proven_commitment = ProvenCommitment(commitment, commitment_proof)
        self._sign_func(proven_commitment)
        return proven_commitment

    def create_offer_msg(self, offer):
        # type: (Offer) -> OfferMsg
        if offer.type_ == OfferType.SELL:
            return OfferMsg(self.token_pair.counter_token, offer.counter_amount, self.token_pair.base_token,
                                 offer.base_amount, offer.offer_id, offer.timeout)
        else:
            return OfferMsg(self.token_pair.base_token, offer.base_amount, self.token_pair.counter_token,
                            offer.counter_amount, offer.offer_id, offer.timeout)


class CommitmentProofTask(gevent.Greenlet):
    def __init__(self, commitment_proofs, commitment_proof_listener):
        self.commitment_proofs = commitment_proofs
        self.commitment_proof_listener = commitment_proof_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.commitment_proof_listener.start()
        while True:
            commitment_proof = self.commitment_proof_listener.get()
            log.debug('Received commitment proof {}'.format(commitment_proof))
            assert isinstance(commitment_proof, CommitmentProof)
            async_result = self.commitment_proofs[commitment_proof.commitment_sig]
            async_result.set(commitment_proof)


class TakenTask(gevent.Greenlet):
    def __init__(self, proven_offers, taken_listener):
        self.proven_offers = proven_offers
        self.taken_listener = taken_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.taken_listener.start()
        while True:
            offer_id = self.taken_listener.get()
            # only set if we actually wait for it
            if offer_id in self.proven_offers:
                async_result = self.proven_offers[offer_id]
                async_result.set(False)