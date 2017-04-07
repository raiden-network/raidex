from collections import namedtuple

from bintrees import FastRBTree
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

        del self.pending_offer_by_id[offer_id]

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
        # when iterating over the TradesView, this iterates over the RBTree!
        # self.trades = <FastRBTree>
        return iter(self.trades)

    def values(self):
        return self.trades.values()
