import gevent
import structlog

from raidex.message_broker.listeners import OfferTakenListener, OfferListener, SwapCompletedListener
from raidex.utils import timestamp, pex


log = slogging.get_logger('node.listener_tasks')


class ListenerTask(gevent.Greenlet):

    def __init__(self, listener):
        self.listener = listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.listener.start()
        while True:
            data = self.listener.get()
            self.process(data)

    def process(self, data):
        raise NotImplementedError


class OfferTakenTask(ListenerTask):
    def __init__(self, offer_book, trades, message_broker):
        self.trades = trades
        self.offer_book = offer_book
        super(OfferTakenTask, self).__init__(OfferTakenListener(message_broker))

    def process(self, data):
        offer_id = data
        if self.offer_book.contains(offer_id):
            log.debug('Offer {} is taken'.format(pex(offer_id)))
            offer = self.offer_book.get_offer_by_id(offer_id)
            self.trades.add_pending(offer)
            self.offer_book.remove_offer(offer_id)


class OfferBookTask(ListenerTask):

    def __init__(self, offer_book, market, message_broker):
        self.offer_book = offer_book
        super(OfferBookTask, self).__init__(OfferListener(market, message_broker))

    def process(self, data):
        offer = data
        log.debug('New Offer: {}'.format(offer))
        self.offer_book.insert_offer(offer)

        def after_offer_timeout_func(offer_id):
            def func():
                if self.offer_book.contains(offer_id):
                    log.debug('Offer {} is timed out'.format(pex(offer_id)))
                    self.offer_book.remove_offer(offer_id)
            return func

        gevent.spawn_later(timestamp.seconds_to_timeout(offer.timeout), after_offer_timeout_func(offer.offer_id))


class SwapCompletedTask(ListenerTask):
    def __init__(self, trades, message_broker):
        self.trades = trades
        super(SwapCompletedTask, self).__init__(SwapCompletedListener(message_broker))

    def process(self, data):
        swap_completed = data
        log.debug('Offer {} has been successfully traded'.format(pex(swap_completed.offer_id)))
        self.trades.report_completed(swap_completed.offer_id, swap_completed.timestamp)
