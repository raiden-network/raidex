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
        self._trades = FastRBTree()

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
        self._trades.insert((trade.timestamp, offer.offer_id), trade)

        # inserts in the dict for retrieval by offer_id
        self.trade_by_id[offer.offer_id] = trade

        return offer.offer_id

    def get_trade_by_id(self, offer_id):
        return self.trade_by_id.get(offer_id)

    def get_pending_by_id(self, offer_id):
        return self.pending_offer_by_id.get(offer_id)

    def __len__(self):
        return len(self._trades)

    def __iter__(self):
        return iter(self._trades)

    def trades(self, from_timestamp=None, to_timestamp=None):
        """
        returns a generator object for all trades
        :param from_timestamp: first timestamp to include in result
        :param to_timestamp: first timestamp to exclude from result
        :return: generator object for the values of the RBtree
        """
        if (from_timestamp, to_timestamp) is (None, None):
            return self.values()

        min_key = None
        if from_timestamp is not None:
            try:
                min_key, _ = self._trades.ceiling_item((from_timestamp, 0))
            except KeyError:
                pass

        max_key = None
        if to_timestamp is not None:
            try:
                key = self._trades.floor_key((to_timestamp, 0))
                max_key, _ = self._trades.succ_item(key)
            except KeyError:
                pass

        if (min_key, max_key) is (None, None):
            # return empty generator
            return iter(())

        return self._trades.value_slice(min_key, max_key)

    def latest_trades(self, trade_count=5):
        # returns list of n-latest trades
        return [trade for key, trade in self._trades.nlargest(trade_count)]

    def values(self, reverse=False):
        return self._trades.values(reverse)

    def keys(self):
        return self._trades.keys()
