from gevent.greenlet import Greenlet
from gevent.queue import Queue

from raidex.raidex_node.order.offer_manager import OfferManager
from raidex.raidex_node.matching.matching_engine import MatchingEngine
from raidex.raidex_node.handle_state_change import handle_state_change
from raidex.raidex_node.order.limit_order import LimitOrder
from raidex.raidex_node.matching.match import MatchFactory
from raidex.constants import MATCHING_ALGORITHM


class DataManager:

    def __init__(self, state_change_q, offer_book):

        self.state_change_q = state_change_q
        self.offer_manager = OfferManager(state_change_q)
        self.matching_engine = MatchingEngine(offer_book, MATCHING_ALGORITHM)
        self.orders = dict()
        self.matches = dict()

    def process_order(self, order: LimitOrder):
        self.orders[order.order_id] = order
        matching_offer_entries, amount_left = self.matching_engine.match_new_order(order)

        for offer_entry in matching_offer_entries:
            take_offer = self.offer_manager.create_take_offer(offer_entry.offer)
            taker_match = MatchFactory.taker_match(take_offer, offer_entry)
            self.matches[take_offer.offer_id] = taker_match
            take_offer.initiating()

        if amount_left > 0:
            make_offer = self.offer_manager.create_make_offer(order, amount_left)
            make_offer.initiating()


class DataManagerTask(Greenlet):

    __slots__ = [
        'data_manager',
        'state_change_q'
    ]

    def __init__(self, data_manager: DataManager, state_change_q: Queue):
        Greenlet.__init__(self)
        self.data_manager = data_manager
        self.state_change_q = state_change_q

    def _run(self):
        while True:
            state_change = self.state_change_q.get()
            print(f'STATE_CHANGE: {state_change}, {self.__class__}')
            self.on_state_change(state_change)

    def on_state_change(self, event):
        handle_state_change(self.data_manager, event)