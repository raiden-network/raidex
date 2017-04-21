from message_broker import MessageBroker
from raidex import messages
from raidex.raidex_node.offer_book import OfferType, Offer
from raidex.raidex_node.trades import SwapCompleted


class MessageListener(object):
    """Represents a listener currently listening for new messages"""

    def __init__(self, message_broker, topic='broadcast'):
        # type: (MessageBroker, str) -> None
        self.message_broker = message_broker
        self.topic = topic
        self.listener = None

    def _transform(self, message):
        """Filters and transforms messages

        Should be overwritten by subclasses

        Args:
            message: The message to filter and transform

        Returns: The transformed message or None if it should be filtered out

        """
        return message

    def get(self, *args, **kwargs):
        """Gets the next message or blocks until there is one

        can only be called after start()
        For parameters see gevents AsyncResult.get()
        """
        return self.listener.message_queue_async.get(*args, **kwargs)

    def get_once(self):
        """starts the listener, returns one value, and stops"""
        self.start()
        result = self.get()
        # self.stop() not fully implemented yet
        return result

    def start(self):
        """Starts listening for new messages"""
        self.listener = self.message_broker.listen_on(self.topic, self._transform)

    def stop(self):
        """Stops listening for new messages"""
        if self.listener is not None:
            self.message_broker.stop_listen(self.listener)


class TakerListener(MessageListener):
    """Listens for the Taker of the offer"""

    def __init__(self, offer, message_broker, topic='broadcast'):
        self.offer = offer
        MessageListener.__init__(self, message_broker, topic)

    def _transform(self, message):
        if isinstance(message,
                      messages.ProvenOffer) and message.offer.offer_id == self.offer.offer_id:  # TODO check more
            return message.sender
        else:
            return None


class OfferListener(MessageListener):
    """Listens for new offers"""

    def __init__(self, market, message_broker, topic='broadcast'):
        self.market = market
        MessageListener.__init__(self, message_broker, topic)

    def _transform(self, message):
        if not isinstance(message, messages.ProvenOffer):
            return None
        offer_msg = message.offer
        commitment_msg = message.commitment
        commitment_proof_msg = message.commitment_proof
        if self.market == (offer_msg.ask_token, offer_msg.bid_token):
            type_ = OfferType.BUY
            base_amount, counter_amount = offer_msg.ask_amount, offer_msg.bid_amount
        elif self.market == (offer_msg.bid_token, offer_msg.ask_token):
            type_ = OfferType.SELL
            base_amount, counter_amount = offer_msg.bid_amount, offer_msg.ask_amount
        else:
            raise AssertionError("unknown market pair")

        offer = Offer(type_, base_amount, counter_amount, offer_id=offer_msg.offer_id, timeout=offer_msg.timeout,
                      maker_address=message.sender)
        # set the information that's important for Committing at the CommitmentService
        offer.set_offer_hash(commitment_msg.offer_hash)
        offer.set_commitment_amount(commitment_msg.amount)
        return offer


class OfferTakenListener(MessageListener):
    """Listens for Taken Messages"""

    def _transform(self, message):
        if not isinstance(message, messages.OfferTaken):
            return None
        return message.offer_id


class SwapExecutionListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, messages.SwapExecution):
            return None
        return message


class CommitmentListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, messages.Commitment):
            return None
        return message


class SwapCompletedListener(MessageListener):
    """ Listens for Completed Swaps to fill the Trade-book"""

    def _transform(self, message):
        if not isinstance(message, messages.SwapCompleted):
            return None
        return SwapCompleted(message.offer_id, message.timestamp)


class CommitmentProofListener(MessageListener):

    def _transform(self, message):
        if not isinstance(message, messages.CommitmentProof):
            return None
        return message
