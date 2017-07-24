from __future__ import print_function
import random

from gevent import monkey; monkey.patch_all()

from ethereum import slogging
from raidex.utils.mock import MockExchangeTask

from raidex.raidex_node.exchange_task import MakerExchangeTask, TakerExchangeTask
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.offer_book import OfferBook, Offer
from listener_tasks import OfferBookTask, OfferTakenTask, SwapCompletedTask
from raidex.raidex_node.order_task import LimitOrderTask
from raidex.raidex_node.trades import TradesView
from raidex.raidex_node.commitment_service.client import CommitmentServiceClient
from raidex.raidex_node.commitment_service.mock import CommitmentServiceClientMock, CommitmentServiceGlobal
from raidex.raidex_node.trader.trader import TraderClientMock, Trader
from raidex.message_broker.message_broker import MessageBroker
from raidex.utils import timestamp
from raidex.signing import Signer
log = slogging.get_logger('node')


class RaidexNode(object):

    def __init__(self, address, token_pair, commitment_service, message_broker, trader_client):
        self.token_pair = token_pair
        self.address = address
        self.message_broker = message_broker
        self.commitment_service = commitment_service
        self.trader_client = trader_client
        self.offer_book = OfferBook()
        self.trades = TradesView()
        self.order_tasks_by_id = {}
        self.next_order_id = 0

    def start(self):
        log.info('Starting raidex node')
        OfferBookTask(self.offer_book, self.token_pair, self.message_broker).start()
        OfferTakenTask(self.offer_book, self.trades, self.message_broker).start()
        SwapCompletedTask(self.trades, self.message_broker).start()

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
        order_task = LimitOrderTask(self.offer_book, self.trades, type_, amount, price, self.address,
                                    self.commitment_service,
                                    self.message_broker, self.trader_client).start()
        order_id = self.next_order_id
        self.order_tasks_by_id[order_id] = order_task
        self.next_order_id += 1
        return order_id

    def print_offers(self):
        print(self.offer_book)

    @classmethod
    def build_default_from_config(cls, privkey=None, cs_address=None, cs_fee_rate=0.01, base_token_addr=None, counter_token_addr=None,
                                  message_broker_endpoint=None, raiden_api_endpoint=None, mock_trading_activity=False):

        if privkey is None:
            signer = Signer.random()
        else:
            signer = Signer(privkey)

        if base_token_addr is None and counter_token_addr is None:
            token_pair = TokenPair.random()
        else:
            token_pair = TokenPair(base_token_addr, counter_token_addr)

        if message_broker_endpoint is None:
            # create mock broker when no endpoint is provided
            message_broker = MessageBroker()
        else:
            NotImplementedError("Message Broker can only be mocked at the moment.")

        # eventually create Trader singleton and construct the trader-client
        if raiden_api_endpoint is None:
            trader = Trader()
        else:
            NotImplementedError("Trader based on Raiden can only be mocked at the moment.")

        trader_client = TraderClientMock(signer.address, commitment_balance=10, trader=trader)  #pylint disable=used-before-assignment


        commitment_service_global = None
        # construct mock commitment-service-client
        if cs_address is None:
            commitment_service_global = CommitmentServiceGlobal()
            commitment_service_client = CommitmentServiceClientMock(signer, token_pair, message_broker, cs_fee_rate,
                                                                    commitment_service_global)
        # or construct commitment-service-client
        else:
            commitment_service_client = CommitmentServiceClient(signer, token_pair, trader_client,
                                                                message_broker, cs_address, fee_rate=cs_fee_rate)

        raidex_node = cls(signer.address, token_pair, commitment_service_client, message_broker, trader_client)


        if mock_trading_activity is True:
            initial_mock_market_price = 10
            nof_market_makers = 10

            commitment_service_mock_list = []

            # for consistency, set the mock-fee-rates the same as the node's fee rate
            mock_fee_rate = cs_fee_rate

            # build the market makers CommitmentServiceClientMock client instances
            for _ in range(0, nof_market_makers):
                commitment_service_mock_list.append(
                    CommitmentServiceClientMock(Signer.random(), token_pair, message_broker, mock_fee_rate,
                                                commitment_service_global)
            )

            # start the trading activity
            MockExchangeTask(initial_mock_market_price, commitment_service_mock_list,
                            message_broker, raidex_node.offer_book).start()

        return raidex_node
