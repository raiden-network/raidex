import gevent
import structlog

from raidex.message_broker.listeners import OfferTakenListener, OfferListener, SwapCompletedListener
from raidex.raidex_node.architecture.state_change import OfferPublishedStateChange
from raidex.utils import timestamp, pex
from eth_utils import int_to_big_endian

log = structlog.get_logger('node.listener_tasks')


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
            log.debug('Offer {} is taken'.format(offer_id))
            offer = self.offer_book.get_offer_by_id(offer_id)
            self.trades.add_pending(offer)
            self.offer_book.remove_offer(offer_id)


class OfferBookTask(ListenerTask):

    def __init__(self, offer_book, market, message_broker, offer_event_queue):
        self.offer_book = offer_book
        self.offer_event_queue = offer_event_queue
        super(OfferBookTask, self).__init__(OfferListener(market, message_broker))

    def process(self, data):
        offer = data
        log.debug('New Offer: {}'.format(offer))
        #self.offer_book.insert_offer(offer)
        self.offer_event_queue.put(OfferPublishedStateChange(offer))

        def after_offer_timeout_func(offer_id):
            def func():
                if self.offer_book.contains(offer_id):
                    log.debug('Offer {} is timed out'.format(pex(int_to_big_endian(offer_id))))
                    self.offer_book.remove_offer(offer_id)
            return func

        #gevent.spawn_later(timestamp.seconds_to_timeout(offer.timeout_date), after_offer_timeout_func(offer.offer_id))


class SwapCompletedTask(ListenerTask):
    def __init__(self, trades, message_broker):
        self.trades = trades
        super(SwapCompletedTask, self).__init__(SwapCompletedListener(message_broker))

    def process(self, data):
        swap_completed = data
        log.debug('Offer {} has been successfully traded'.format(pex(int_to_big_endian(swap_completed.offer_id))))
        self.trades.report_completed(swap_completed.offer_id, swap_completed.timestamp)
