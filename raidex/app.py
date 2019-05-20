from gevent import Greenlet

from raidex.account import Account
from raidex.signing import Signer
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.commitment_service.client import CommitmentServiceClient
from raidex.raidex_node.commitment_service.events import CommitmentServiceEvent
from raidex.raidex_node.trader.client import TraderClient
from raidex.raidex_node.trader.events import TraderEvent
from raidex.raidex_node.transport.client import MessageBrokerClient
from raidex.raidex_node.transport.events import TransportEvent
from raidex.utils.address import binary_address
from raidex.raidex_node.raidex_node import RaidexNode
from raidex.raidex_node.architecture.event_architecture import event_dispatch, state_change_dispatch
from raidex.raidex_node.handle_state_change import handle_state_change


class App(Greenlet):

    def __init__(self, trader, cs_client, transport, market, raidex_node):

        self.trader = trader
        self.cs_client = cs_client
        self.transport = transport
        self.market = market
        self.raidex_node = raidex_node

        self._setup_event_handling()
        self._setup_state_change_handling()

    def _setup_event_handling(self):
        event_dispatch.connect_consumer(self.trader, TraderEvent)
        event_dispatch.connect_consumer(self.cs_client, CommitmentServiceEvent)
        event_dispatch.connect_consumer(self.transport, TransportEvent)

    def _setup_state_change_handling(self):
        state_change_dispatch.connect_consumer(self.raidex_node, handle_state_change)

    def _run(self):
        self.raidex_node.start()
        # start task for updating the balance of the trader:
        self.trader.start()
        # start the tasks for the commitment-service-client
        self.cs_client.start()
        event_dispatch.start_consumer_tasks()
        state_change_dispatch.start_consumer_tasks()

    @classmethod
    def build_default_from_config(cls,
                                  keyfile=None,
                                  pw_file=None,
                                  privkey_seed=None,
                                  cs_address=None,
                                  cs_fee_rate=0.01,
                                  base_token_addr=None,
                                  quote_token_addr=None,
                                  message_broker_host='127.0.0.1',
                                  message_broker_port=5000,
                                  mock_trading_activity=False,
                                  trader_host='127.0.0.1',
                                  trader_port=5001,
                                  offer_lifetime=None):

        if keyfile is not None and pw_file is not None:
            pw = pw_file.read()
            pw = pw.splitlines()[0]
            acc = Account.load(file=keyfile, password=pw)
            signer = Signer.from_account(acc)

        elif privkey_seed is None:
            signer = Signer.random()
        else:
            signer = Signer.from_seed(privkey_seed)

        if base_token_addr is None and quote_token_addr is None:
            token_pair = TokenPair.from_seed('test')
        else:
            token_pair = TokenPair(base_token=binary_address(base_token_addr), base_decimal=3,
                                   quote_token=binary_address(quote_token_addr), quote_decimal=18)

        trader_client = TraderClient(signer.checksum_address, host=trader_host, port=trader_port, market=token_pair)
        message_broker = MessageBrokerClient(host=message_broker_host, port=message_broker_port,
                                             address=signer.checksum_address)

        commitment_service_client = CommitmentServiceClient(signer, token_pair, trader_client,
                                                            message_broker, cs_address, fee_rate=cs_fee_rate)

        raidex_node = RaidexNode(signer.address, token_pair, commitment_service_client, message_broker, trader_client)

        # if mock_trading_activity is True:
        #    raise NotImplementedError('Trading Mocking disabled a the moment')

        if offer_lifetime is not None:
            raidex_node.default_offer_lifetime = offer_lifetime

        app = App(trader_client, commitment_service_client, message_broker, token_pair, raidex_node)
        return app

    @classmethod
    def build_from_mocks(cls, message_broker, cs_address, keyfile=None, pw_file=None, privkey_seed=None,
                         cs_fee_rate=0.01, base_token_addr=None,
                         quote_token_addr=None, offer_lifetime=None):

        if keyfile is not None and pw_file is not None:
            pw = pw_file.read()
            pw = pw.splitlines()[0]
            acc = Account.load(file=keyfile, password=pw)
            signer = Signer.from_account(acc)

        elif privkey_seed is None:
            signer = Signer.random()
        else:
            signer = Signer.from_seed(privkey_seed)

        if base_token_addr is None and quote_token_addr is None:
            token_pair = TokenPair.from_seed('test')
        else:
            token_pair = TokenPair(base_token_addr, quote_token_addr)

        trader_client = TraderClient(signer.address, host='localhost', port=5001, api_version='v1',
                                     commitment_amount=10)

        commitment_service_client = CommitmentServiceClient(signer, token_pair, trader_client,
                                                            message_broker, cs_address, fee_rate=cs_fee_rate)

        raidex_node = RaidexNode(signer.address, token_pair, commitment_service_client, message_broker, trader_client)

        if offer_lifetime is not None:
            raidex_node.default_offer_lifetime = offer_lifetime

        app = App(trader_client, commitment_service_client, message_broker, token_pair, raidex_node)
        return app
