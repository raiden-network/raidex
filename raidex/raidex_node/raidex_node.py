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
from raidex.raidex_node.trades import TradesView
from raidex.commitment_service.client import CommitmentService
from raidex.commitment_service.commitment_service import CommitmentService as CommitmentServiceMock
from raidex.raidex_node.trader.trader import TraderClient, Trader
from raidex.message_broker.message_broker import MessageBroker
from raidex.utils import timestamp
log = slogging.get_logger('node')


class RaidexNode(object):

    def __init__(self, base_token_addr, counter_token_addr, priv_key, cs_address, cs_fee_rate, message_broker,
                 trader):
        self.token_pair = TokenPair(base_token=base_token_addr, counter_token=counter_token_addr)
        self.priv_key = priv_key
        self.address = privtoaddr(self.priv_key)
        self.message_broker = message_broker
        self.trader_client = TraderClient(self.address, commitment_balance=10, trader=trader)
        self.commitment_service = CommitmentService(self.address, self.token_pair, self._sign, self.trader_client,
                                                    self.message_broker, cs_address, fee_rate=cs_fee_rate)
        self.offer_book = OfferBook()
        self.trades = TradesView()
        self.order_tasks_by_id = {}
        self.next_order_id = 0

    def start(self):
        log.info('Starting raidex node')
        OfferBookTask(self.offer_book, self.token_pair, self.message_broker).start()
        OfferTakenTask(self.offer_book, self.trades, self.message_broker).start()
        SwapCompletedTask(self.trades, self.message_broker).start()

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
        order_task = LimitOrderTask(self.offer_book, self.trades, type_, amount, price, self.address,
                                    self.commitment_service,
                                    self.message_broker, self.trader_client).start()
        order_id = self.next_order_id
        self.order_tasks_by_id[order_id] = order_task
        self.next_order_id += 1
        return order_id

    def print_offers(self):
        print(self.offer_book)

    def _sign(self, message):
        message.sign(self.priv_key)


def raidex_node_builder(cs_address='', cs_fee_rate=0.01, message_broker=None, trader=None):
    """
    Convenience function to easily construct a default raidex-node
    - eventually initialises missing objects if no arguments are provided.

    :param cs_address: the address under which an existing CS is listening for messages and transfers
    :param cs_fee_rate: the corresponding fee-rate for said CS
    :param message_broker: the singleton message_broker object
    :param trader: the singleton trader object
    :return:
    """
    priv_key = sha3('secret'+str(random.randint(0, 1000000000)))
    base_token_addr = privtoaddr(sha3('ether'))
    counter_token_addr = privtoaddr(sha3('usd'))
    if message_broker is None:
        message_broker = MessageBroker()
    if trader is None:
        trader = Trader()

    if cs_address:
        node = RaidexNode(base_token_addr, counter_token_addr, priv_key, cs_address, cs_fee_rate,
                          message_broker, trader)

    # if no commitment_service address is provided, use the CS mock-implementation:
    else:
        # only for eventually complying with typechecks etc.
        cs_address = privtoaddr(sha3('mock'))
        node = RaidexNode(base_token_addr, counter_token_addr, priv_key, cs_address, cs_fee_rate,
                          message_broker, trader)
        # overwrite member from node initialisation with mock-commitment-service
        node.commitment_service = CommitmentServiceMock(node.token_pair, node.priv_key, node.message_broker)

    return node
