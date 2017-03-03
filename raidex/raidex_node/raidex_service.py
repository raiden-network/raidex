from __future__ import print_function

import random

import gevent
import raidex.utils.milliseconds as milliseconds
from ethereum import slogging
from ethereum.utils import sha3, privtoaddr
from exchange_task import MakerExchangeTask, TakerExchangeTask
from market import TokenPair
from offer_book import OfferBook, OfferBookTask, Offer, TakenTask
from order_task import OrderTask
from raidex.commitment_service.commitment_service import CommitmentService
from raidex.message_broker.client import MessageBroker
from raidex.message_broker.listeners import OfferListener, TakenListener
from raidex.raidex_node.trader.client import TraderClient

slogging.configure(':DEBUG')

class Raidex(object):
    """just to try it out
    """

    def __init__(self, client):
        self.priv_key = sha3(client)
        self.address = privtoaddr(self.priv_key)
        self.message_broker = MessageBroker()
        self.token_pair = TokenPair(privtoaddr(sha3('beer')), privtoaddr(sha3('ether')))
        self.commitment_service = CommitmentService(self.token_pair, self.priv_key)
        self.trader = TraderClient(self.address)
        self.offer_book = OfferBook()

    def start(self):
        OfferBookTask(self.offer_book, OfferListener(self.token_pair, self.message_broker)).start()
        TakenTask(self.offer_book, TakenListener(self.message_broker)).start()

    def make_offer(self, type_, amount, counter_amount):
        # TODO generate better offer id
        offer = Offer(type_, amount, counter_amount, random.randint(0, 1000000000), milliseconds.time_plus(90))
        MakerExchangeTask(offer, self.address, self.commitment_service, self.message_broker, self.trader).start()
        gevent.sleep(0.001)

    def take_offer(self, offer_id):
        offer = self.offer_book.get_offer_by_id(offer_id)
        TakerExchangeTask(offer, self.commitment_service, self.message_broker, self.trader).start()
        gevent.sleep(0.001)

    def limit_order(self, type_, amount, price):
        OrderTask(self.offer_book, type_, amount, price, self.address, self.commitment_service, self.message_broker, self.trader).start()
        gevent.sleep(0.001)

    def print_offers(self):
        gevent.sleep(0.001)
        print(self.offer_book)
