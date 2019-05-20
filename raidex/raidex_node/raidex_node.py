from __future__ import print_function
from gevent import monkey
import structlog

from raidex.raidex_node.architecture.event_architecture import Processor
from raidex.raidex_node.architecture.state_change import StateChange
from raidex.raidex_node.offer_book import OfferBook
from raidex.raidex_node.listener_tasks import OfferBookTask, OfferTakenTask, SwapCompletedTask
from raidex.raidex_node.trades import TradesView
from raidex.raidex_node.offer_grouping import group_offers, group_trades_from, make_price_bins, get_n_recent_trades
from raidex.raidex_node.architecture.data_manager import DataManagerTask, DataManager
from gevent.queue import Queue

monkey.patch_all()
log = structlog.get_logger('node')


class RaidexNode(Processor):

    def __init__(self, address, token_pair, commitment_service, message_broker, trader_client):
        super(RaidexNode, self).__init__(StateChange)
        self.token_pair = token_pair
        self.address = address
        self.message_broker = message_broker
        self.commitment_service = commitment_service
        self.trader_client = trader_client
        self.offer_book = OfferBook()
        # don't make this accessible in the constructor args for now, set attribute instead if needed
        self.default_offer_lifetime = 30
        self._trades_view = TradesView()
        self.order_tasks_by_id = {}
        self.user_order_tasks_by_id = {}
        self._nof_successful_orders = 0
        self._nof_unsuccessful_orders = 0
        self._max_open_orders = 0

        self._get_trades = self._trades_view.trades
        self.state_change_q = Queue()
        self.data_manager = DataManager(self.state_change_q, self.offer_book)
        self.data_manager_task = DataManagerTask(self.data_manager, self.state_change_q)
        self.commitment_service.add_event_queue(self.state_change_q)

    def start(self):
        log.info('Starting raidex node')
        OfferBookTask(self.offer_book, self.token_pair, self.message_broker, self.state_change_q).start()
        OfferTakenTask(self.offer_book, self._trades_view, self.message_broker).start()
        SwapCompletedTask(self._trades_view, self.message_broker).start()
        self.data_manager_task.start()

    def _process_finished_limit_order(self, order_task):
        value = order_task.get(block=False)
        if value is True:
            self._nof_successful_orders += 1
        elif value is False:
            self._nof_unsuccessful_orders += 1
        return self.user_order_tasks_by_id.pop(order_task.order_id, None)

    @property
    def successful_orders(self):
        return self._nof_successful_orders

    @property
    def unsuccessful_orders(self):
        return self._nof_unsuccessful_orders

    @property
    def open_orders(self):
        return self._nof_started_orders - self.finished_orders

    @property
    def finished_orders(self):
        return self._nof_successful_orders + self._nof_unsuccessful_orders

    @property
    def initiated_orders(self):
        return self.user_order_tasks_by_id.values()

    def limit_orders(self):
        # we only keep a reference of user-initiated LimitOrders at the moment
        raise NotImplementedError()

    def cancel_limit_order(self, order_id):
        log.info('Cancel limit order')
        self.user_order_tasks_by_id[order_id].cancel()

    def print_offers(self):
        print(self.offer_book)

    def buys(self):
        return self.offer_book.buys.values()

    def sells(self):
        return self.offer_book.sells.values()

    def grouped_buys(self):
        return group_offers(self.buys())

    def grouped_sells(self):
        return group_offers(self.sells())

    def trades(self, from_timestamp=None):
        return self._get_trades(from_timestamp=from_timestamp)

    def grouped_trades(self, from_timestamp=None):
        return group_trades_from(self._get_trades, from_timestamp)

    def recent_grouped_trades(self, chunk_size):
        return get_n_recent_trades(self.trades(), chunk_size)

    def price_chart_bins(self, nof_buckets, interval):
        if nof_buckets < 1 or interval < 0.:
            raise ValueError()
        return make_price_bins(self._get_trades, nof_buckets, interval)

    def market_price(self, trade_count=20):
        """Calculate a market price based on the most recent trades.

        :param trade_count: number of redent trades to consider
        :returns: a market price, or `None` if no trades have happened yet
        """
        trades_list = self._get_trades(trade_count)
        trades = list(reversed(trades_list[-trade_count:]))

        if len(trades) == 0:
            return None
        else:
            assert sorted(trades, key=lambda t: -t.timestamp) == trades  # newest should be first
            total_volume = sum([t.offer.amount for t in trades])
            return sum([t.offer.price * t.offer.amount for t in trades]) / total_volume

