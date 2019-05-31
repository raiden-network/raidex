from raidex.raidex_node.architecture.event_architecture import Processor
from raidex.raidex_node.transport.events import TransportEvent
from raidex.raidex_node.order.offer import OfferType, Offer
import raidex.messages as message_format


class Transport(Processor):

    def __init__(self, message_broker_client, market, signer):
        super(Transport, self).__init__(TransportEvent)
        self.message_broker_client = message_broker_client
        self.market = market
        self._sign = signer.sign

    def proven_offer(self, target, offer, commitment_proof):
        offer_msg = self.create_offer_msg(offer)
        commitment_msg = self._create_taker_commitment_msg(offer, offer_msg.hash, 1)
        proven_commitment = message_format.ProvenCommitment(commitment_msg, commitment_proof)
        self._sign(proven_commitment)
        self._send_message(target, proven_commitment)

    def _create_proven_offer_msg(self, offer_msg, commitment_msg, commitment_proof_msg):
        proven_offer = message_format.ProvenOffer(offer_msg, commitment_msg, commitment_proof_msg)
        self._sign(proven_offer)
        return proven_offer

    def _create_taker_commitment_msg(self, offer, offer_hash, commitment_amount):
        timeout = offer.timeout_date

        commitment_msg = message_format.TakerCommitment(offer.offer_id, offer_hash, timeout, commitment_amount)
        self._sign(commitment_msg)
        return commitment_msg

    def create_offer_msg(self, offer):
        # type: ([Offer, Offer]) -> message_format.SwapOffer

        timeout = offer.timeout_date

        if offer.type == OfferType.SELL:
            return message_format.SwapOffer(self.market.quote_token,
                                            offer.quote_amount,
                                            self.market.base_token,
                                            offer.base_amount,
                                            offer.offer_id, timeout)
        else:
            return message_format.SwapOffer(self.market.base_token,
                                            offer.base_amount,
                                            self.market.quote_token,
                                            offer.quote_amount,
                                            offer.offer_id, timeout)

    def _create_cancellation_msg(self, offer_id):
        return message_format.Cancellation(offer_id)

    def cancellation(self, target, offer_id):
        message = self._create_cancellation_msg(offer_id)
        self._sign(message)
        self._send_message(target, message)

    def send_message(self, target, message):
        self._send_message(target, message)

    def _send_message(self, target, message):
        self.message_broker_client.send(target, message)

