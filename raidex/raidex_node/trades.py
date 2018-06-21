from collections import namedtuple

from sortedcontainers import SortedDict
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
        self._trades = SortedDict()

    def add_pending(self, offer):
        self.pending_offer_by_id[offer.offer_id] = offer

    def report_completed(self, offer_id, completed_timestamp):
        offer = self.pending_offer_by_id.get(offer_id)
        if offer is None:
            return False

        del self.pending_offer_by_id[offer_id]

        assert isinstance(offer, Offer)
        trade = Trade(offer, completed_timestamp)

        self._trades[(trade.timestamp, offer.offer_id)] = trade
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
        :param from_timestamp: first timestamp to include in result
        :param to_timestamp: first timestamp to exclude from result
        :return: list
        """
        if (from_timestamp, to_timestamp) is (None, None):
            return self._trades.values()

        min_key, max_key = None, None
        if from_timestamp is not None:
            min_key = (from_timestamp, 0)
        if to_timestamp is not None:
            max_key = (to_timestamp, 0)

        # FIXME prevent modifying (from report_completed()) while iterating
        trades = [self._trades[key] for key in self._trades.irange(minimum=min_key, maximum=max_key,
                                                                   inclusive=(True, False))]
        return list(trades)

    def values(self):
        # returns sorted list of all values
        return self._trades.values()
