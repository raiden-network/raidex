from __future__ import print_function
import random

from gevent import monkey; monkey.patch_all()

from ethereum import slogging
from ethereum.utils import sha3, privtoaddr

from raidex.raidex_node.exchange_task import MakerExchangeTask, TakerExchangeTask
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.offer_book import OfferBook, Offer
from listener_tasks import OfferBookTask, OfferTakenTask, SwapCompletedTask
from raidex.raidex_node.order_task import LimitOrderTask
from raidex.raidex_node.trader.client import TraderClient
from raidex.raidex_node.trades import TradesView
from raidex.message_broker.client import MessageBroker
from raidex.commitment_service.commitment_service import CommitmentService
import raidex.utils.milliseconds as milliseconds

log = slogging.get_logger('node')


class RaidexNode(object):

    def __init__(self, token_pair=None):
        if token_pair is None:
            token_pair = TokenPair(privtoaddr(sha3('ether')), privtoaddr(sha3('usd')))
        self.token_pair = token_pair
        self.priv_key = sha3('secret'+str(random.randint(0, 1000000000)))
        self.address = privtoaddr(self.priv_key)
        self.message_broker = MessageBroker()
        self.commitment_service = CommitmentService(self.token_pair, self.priv_key, self.message_broker)
        self.trader = TraderClient(self.address)
        self.offer_book = OfferBook()
        self.trades = TradesView()
        self.order_tasks_by_id = {}
        self.next_order_id = 0

    def start(self):
        log.info('Starting raidex node')
        OfferBookTask(self.offer_book, self.token_pair, self.message_broker).start()
        OfferTakenTask(self.offer_book, self.trades, self.message_broker).start()
        SwapCompletedTask(self.trades, self.message_broker).start()

    def make_offer(self, type_, amount, counter_amount):
        # TODO generate better offer id
        offer = Offer(type_, amount, counter_amount, random.randint(0, 1000000000), milliseconds.time_plus(90))
        MakerExchangeTask(offer, self.address, self.commitment_service, self.message_broker, self.trader).start()

    def take_offer(self, offer_id):
        offer = self.offer_book.get_offer_by_id(offer_id)
        TakerExchangeTask(offer, self.commitment_service, self.message_broker, self.trader).start()

    def limit_order(self, type_, amount, price):
        log.info('Placing limit order')
        order_task = LimitOrderTask(self.offer_book, self.trades, type_, amount, price, self.address,
                                    self.commitment_service,
                                    self.message_broker, self.trader).start()
        order_id = self.next_order_id
        self.order_tasks_by_id[order_id] = order_task
        self.next_order_id += 1
        return order_id

    def print_offers(self):
        print(self.offer_book)
