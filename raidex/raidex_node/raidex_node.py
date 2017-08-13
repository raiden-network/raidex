from __future__ import print_function
import random

from gevent import monkey; monkey.patch_all()

from ethereum import slogging

from raidex.raidex_node.exchange_task import MakerExchangeTask, TakerExchangeTask
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.offer_book import OfferBook, Offer
from listener_tasks import OfferBookTask, OfferTakenTask, SwapCompletedTask
from raidex.raidex_node.order_task import LimitOrderTask
from raidex.raidex_node.trades import TradesView
from raidex.raidex_node.commitment_service.client import CommitmentServiceClient
from raidex.raidex_node.trader.client import TraderClient
from raidex.message_broker.client import MessageBrokerClient
from raidex.utils import timestamp
from raidex.signing import Signer
from raidex.raidex_node.offer_grouping import group_offers, group_trades_from, make_price_bins, get_n_recent_trades
log = slogging.get_logger('node')


class RaidexNode(object):

    def __init__(self, address, token_pair, commitment_service, message_broker, trader_client):
        self.token_pair = token_pair
        self.address = address
        self.message_broker = message_broker
        self.commitment_service = commitment_service
        self.trader_client = trader_client
        self.offer_book = OfferBook()
        self._trades = TradesView()
        self.order_tasks_by_id = {}
        self.next_order_id = 0

    def start(self):
        log.info('Starting raidex node')
        OfferBookTask(self.offer_book, self.token_pair, self.message_broker).start()
        OfferTakenTask(self.offer_book, self._trades, self.message_broker).start()
        SwapCompletedTask(self._trades, self.message_broker).start()

        # start task for updating the balance of the trader:
        self.trader_client.start()
        # start the tasks for the commitment-service-client
        self.commitment_service.start()

    def make_offer(self, type_, amount, counter_amount):
        # TODO generate better offer id
        offer = Offer(type_, amount, counter_amount, random.randint(0, 1000000000), timestamp.time_plus(90))
        MakerExchangeTask(offer, self.address, self.commitment_service, self.message_broker, self.trader_client).start()

    def take_offer(self, offer_id):
        offer = self.offer_book.get_offer_by_id(offer_id)
        TakerExchangeTask(offer, self.commitment_service, self.message_broker, self.trader_client).start()

    def limit_order(self, type_, amount, price):
        log.info('Placing limit order')
        order_task = LimitOrderTask(self.offer_book, self._trades, type_, amount, price, self.address,
                                    self.commitment_service,
                                    self.message_broker, self.trader_client)
        order_task.start()
        order_id = self.next_order_id
        self.order_tasks_by_id[order_id] = order_task
        self.next_order_id += 1
        return order_id

    def print_offers(self):
        print(self.offer_book)

    @classmethod
    def build_default_from_config(cls, privkey_seed=None, cs_fee_rate=0.01, base_token_addr=None, counter_token_addr=None,
                                  message_broker_host='127.0.0.1', message_broker_port=5000, raiden_api_endpoint=None, mock_trading_activity=False,
                                  trader_host='127.0.0.1', trader_port=5001):

        if privkey_seed is None:
            signer = Signer.random()
        else:
            signer = Signer.from_seed(privkey_seed)

        if base_token_addr is None and counter_token_addr is None:
            token_pair = TokenPair.from_seed('test')
        else:
            token_pair = TokenPair(base_token_addr, counter_token_addr)

        trader_client = TraderClient(signer.address, host=trader_host, port=trader_port)
        message_broker = MessageBrokerClient(host=message_broker_host, port=message_broker_port)

        if raiden_api_endpoint is None:
            pass
        else:
            NotImplementedError("Trader based on Raiden can only be mocked at the moment.")

        cs_address = Signer.from_seed('test').address
        commitment_service_client = CommitmentServiceClient(signer, token_pair, trader_client,
                                                            message_broker, cs_address, fee_rate=cs_fee_rate)

        raidex_node = cls(signer.address, token_pair, commitment_service_client, message_broker, trader_client)

        if mock_trading_activity is True:
            raise NotImplementedError('Trading Mocking disabled a the moment')

        return raidex_node

    def buys(self):
        return self.offer_book.buys.values()

    def sells(self):
        return self.offer_book.sells.values()

    def grouped_buys(self):
        return group_offers(self.buys())

    def grouped_sells(self):
        return group_offers(self.sells())

    def trades(self, from_timestamp=None):
        return self._trades.trades(from_timestamp)

    def grouped_trades(self, from_timestamp=None):
        return group_trades_from(self._trades.trades, from_timestamp)

    def recent_grouped_trades(self, chunk_size):
        return get_n_recent_trades(self._trades, chunk_size)

    def price_chart_bins(self, nof_buckets, interval):
        if nof_buckets < 1 or interval < 0.:
            raise ValueError()
        return make_price_bins(self._trades.trades, nof_buckets, interval)

    def market_price(self, trade_count=20):
        """Calculate a market price based on the most recent trades.

        :param trade_count: number of redent trades to consider
        :returns: a market price, or `None` if no trades have happened yet
        """
        trades = self._trades.latest_trades(trade_count)
        if len(trades) == 0:
            return None
        else:
            assert sorted(trades, key=lambda t: -t.timestamp) == trades  # newest should be first
            total_volume = sum([t.offer.amount for t in trades])
            return sum([t.offer.price * t.offer.amount for t in trades]) / total_volume
