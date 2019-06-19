from raidex.utils import timestamp
from raidex.raidex_node.order.offer import OfferType, Offer
from raidex.raidex_node.market import TokenPair
import raidex.messages as message_format


class TransportEvent:
    pass


class SignMessageEvent:
    pass


class SendMessageEvent(TransportEvent):

    def __init__(self, target, message=None):
        self.target = target
        self._message = message

    @property
    def message(self):
        if self._message is None:
            self._message = self._generate_message()
        return self._message

    def _generate_message(self):
        raise NotImplementedError


class BroadcastEvent(SendMessageEvent):

    def __init__(self, message):
        super(BroadcastEvent, self).__init__('broadcast', message)

    def _generate_message(self):
        raise NotImplementedError


class SendProvenOfferEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, offer, market, target='broadcast'):
        target = target if target is not None else 'broadcast'
        super(SendProvenOfferEvent, self).__init__(target)
        self.offer = offer
        self.market = market

    def _generate_message(self):
        offer_msg = _create_offer_msg(self.offer, self.market)
        return message_format.ProvenOffer(offer_msg, self.offer.proof)


class CancellationEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, target, offer_id):
        super(CancellationEvent, self).__init__(target)
        self.offer_id = offer_id

    def _generate_message(self):
        return message_format.Cancellation(self.offer_id)


class CommitmentEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, target, offer, commitment_amount, market):
        super(CommitmentEvent, self).__init__(target)
        self.offer = offer
        self.market = market
        self.commitment_amount = commitment_amount

    def _generate_message(self):

        offer_msg = _create_offer_msg(self.offer, self.market)
        return message_format.Commitment(self.offer.offer_id,
                                         offer_msg.hash,
                                         self.offer.timeout_date,
                                         self.commitment_amount)


class SendExecutedEventEvent(SendMessageEvent, SignMessageEvent):

    def __init__(self, target, offer_id):
        super(SendExecutedEventEvent, self).__init__(target)
        self.offer_id = offer_id
        self.timestamp_ = timestamp.time_int()

    def _generate_message(self):
        return message_format.SwapExecution(self.offer_id, self.timestamp_)


def _create_offer_msg(offer, market):
    # type: (Offer, TokenPair) -> message_format.SwapOffer

    timeout = offer.timeout_date

    if offer.type == OfferType.SELL:
        return message_format.SwapOffer(market.quote_token,
                                        offer.quote_amount,
                                        market.base_token,
                                        offer.base_amount,
                                        offer.offer_id, timeout)
    else:
        return message_format.SwapOffer(market.base_token,
                                        offer.base_amount,
                                        market.quote_token,
                                        offer.quote_amount,
                                        offer.offer_id, timeout)