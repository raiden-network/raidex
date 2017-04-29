from collections import namedtuple

from bintrees import FastRBTree
import gevent
from ethereum import slogging

from offer_book import Offer


log = slogging.get_logger('node.trades')


SwapCompleted = namedtuple('SwapCompleted', 'offer_id timestamp')


class Trade(object):

    def __init__(self, offer, timestamp):
        self.offer = offer
        self.timestamp = timestamp


class TradesView(object):

    def __init__(self):
        self.pending_offer_by_id = {}
        self.trade_by_id = {}
        self.trades = FastRBTree()

    def add_pending(self, offer):
        self.pending_offer_by_id[offer.offer_id] = offer

    def report_completed(self, offer_id, completed_timestamp):
        offer = self.pending_offer_by_id.get(offer_id)
        if offer is None:
            return False

        assert isinstance(offer, Offer)
        trade = Trade(offer, completed_timestamp)

        # inserts in the RBTree
        self.trades.insert((trade.timestamp, offer.offer_id), trade)

        # inserts in the dict for retrieval by offer_id
        self.trade_by_id[offer.offer_id] = trade

        return offer.offer_id

    def get_trade_by_id(self, offer_id):
        return self.trade_by_id.get(offer_id)

    def get_pending_by_id(self, offer_id):
        return self.pending_offer_by_id.get(offer_id)

    def __len__(self):
        return len(self.trades)

    def __iter__(self):
        # when iterating over the OfferView, this iterates over the RBTree!
        # self.offers = <FastRBTree>
        return iter(self.trades)

    def values(self):
        return self.trades.values()


class SwapCompletedTask(gevent.Greenlet):
    def __init__(self, trades, swap_completed_listener):
        self.trades = trades
        self.swap_completed_listener = swap_completed_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.swap_completed_listener.start()
        while True:
            swap_completed = self.swap_completed_listener.get()
            log.debug('Offer {} has been successfully traded'.format(swap_completed.offer_id))
            self.trades.report_completed(swap_completed.offer_id, swap_completed.timestamp)
