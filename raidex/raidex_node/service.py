import time

from ethereum.utils import sha3, privtoaddr, big_endian_to_int, int_to_big_endian

from raidex_service import messages
from raidex_service.message_broker.client import BroadcastClient
from raidex_service.exceptions import UntradableAssetPair, UnknownCommitmentService, InsufficientCommitmentFunds
from raidex_service.raidex_node.offer_book import Offer
from raidex_service.utils import get_market_from_asset_pair

ERC20_ETH_ADDRESS = sha3('ETHER') # mock for now

class RaidexService(object):

    def __init__(
            self,
            raiden_api,
            private_key,
            protocol_cls,
            transport,
            raiden_discovery,
            broadcast_transport,
            broadcast_protocol_cls):

        self.raiden = raiden_api
        self.private_key = private_key

        # use the raiden discovery/transport here, with the raidex port being `raiden_port + 1`
        self.protocol = protocol_cls(self.address, transport, raiden_discovery, MessageHandler(self), )
        transport.protocol = self.protocol

        # holds the broadcast client,
        self.broadcast = BroadcastClient(self.address, broadcast_protocol_cls, broadcast_transport, BroadcastMessageHandler(self))

        # markets that the Node knows of // or is interested in
        self.markets = list()

        self.offerbooks = dict()
        self.trade_history = dict()


    @property
    def assets(self):
        raise NotImplementedError

    @property
    def address(self):
        return privtoaddr(self.private_key)

    def ping(self, receiver_address):
        ping = messages.Signed()
        ping.sign(self.private_key)
        self.protocol.send(receiver_address, ping)

    def add_offerbook(self, market, offerbook):
        self.offerbooks[market] = offerbook

    def get_offerbook(self, market):
        # gets the OfferBook instace for a given market
        if market not in self.offerbooks:
            raise UntradableAssetPair()
        else:
            return self.offerbooks[market]

    def get_trade_history(self, market):
        if market not in self.trade_history:
            raise UntradableAssetPair()
        return self.trade_history[market]


    def maker_commit(self, commitment_service_address, offer_id, commitment_amount, timeout):
        """
        Handles the communication as well as the raiden transfers to a commitmentservice,
        in order to make commitment.

        NOTE: this strategy currently applies to the maker commitment only, see issue #16 and issue #5
        """


    def taker_commit(self, commitment_service_address, offer_id, commitment_amount, timeout):
        # differs from maker commit (see issue #16)
        pass

    def notify_swap_execution(self, commitment_service_address, offer_id):
        """
        Sends a SwapExecution message to the CommitmentService.
        When the CS receives a SwapExecution from both commited parties, it will refund the commitment to both participants.

        :param commitment_service_address: the raiden address of the commitmentservice
        :param offer_id: the unique offer_id
        :return:
        """


    def deposit(self, commitment_service_address, deposit_amount):
        """
        Deposits to a payment channel with a commitment service.

        :param commitment_service_address: the raiden address of the commitmentservice
        :param deposit_amount: the amount of tradeable ether that is locked in the Payment channel
        :return:
        """

    def open(self, commitment_service_address):
        """
        Opens a payment channel in raiden with the commitment service, where the asset is an ERC20-Ether contract

        :param commitment_service_address: the raiden address of the commitmentservice
        :return: None
        """

class MessageHandler(object):

    def __init__(self, raidex_service):
        self.raidex = raidex_service

    def on_message(self, message):
        # TODO make 'on_' methods snake_case
        # retrieve the name of the method to call based on the message type:
        method = 'on_{}'.format(message.__class__.__name__.lower())

        # call the method with the message as argument:
        try:
            getattr(self, method)(message)
        except AttributeError as e:
            # log.INFO('No method for incoming message found in message handler) TODO
            pass

    def on_ping(self, message):
        nonce = message.nonce

        ping_sender_address = message.sender

        # respond with a pong, having the same nonce as the ping
        pong_msg = messages.Pong(nonce)
        pong_msg.sign(self.raidex.private_key)

        self.raidex.protocol.send(ping_sender_address, pong_msg)

    def on_commitmentproof(self, message):
        raise NotImplementedError()


class BroadcastMessageHandler(object):
    """
    BroadcastMessageHandler determines the behaviour on incoming messages from the broadcast
    """
    def __init__(self, raidex_service):
        self.raidex = raidex_service

    def on_message(self, message):
        # TODO make 'on_' methods snake_case
        # retrieve the name of the method to call based on the message type:
        method = 'on_{}'.format(message.__class__.__name__.lower())

        # call the method with the message as argument:
        try:
            getattr(self, method)(message)
        except AttributeError as e:
            # log.INFO('No method for incoming message found in message handler) TODO
            pass

    def on_provenoffer(self, message):
        # fill the offerbook
        asset_pair = (message.bid_token, message.ask_token)
        market = get_market_from_asset_pair(asset_pair)
        try:
            offer_book = self.raidex.get_offerbook(market)
            offer = Offer.from_message(message)
            offer_book.insert_offer(offer)
        except UntradableAssetPair:
            # log.INFO('the client is registered to an unaccessible market')
            pass

    def on_commitmentserviceadvertisement(self, message):
        raise NotImplementedError()

    def on_swapcompleted(self, message):
        # remove offer from the orderbook
        raise NotImplementedError()
