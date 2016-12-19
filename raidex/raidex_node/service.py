import time

from ethereum.utils import sha3, privtoaddr, big_endian_to_int, int_to_big_endian

from raidex import messages
from raidex.message_broker.client import BroadcastClient
from raidex.exceptions import UntradableAssetPair, UnknownCommitmentService, InsufficientCommitmentFunds

ERC20_ETH_ADDRESS = sha3('ETHER') # mock for now



def get_market_from_asset_pair(asset_pair):
    """
    Takes a 2-tuple of decoded assets and sorts them based on their int representation.
    This always returns a deterministic `market`-tuple, which is one of the two possible asset_pair permutations.

    The sorting algorithm  could always be changed later, it just has to be used consistently.

    :param asset_pair: decoded 2-tuple of ethereum assets
    :return: decoded 2-tuple of ethereum assets (the deterministic `market` tuple)
    """
    # assume that asset_pair is decoded!
    assert isinstance(asset_pair, tuple)
    assert len(asset_pair) == 2
    list_int = [big_endian_to_int(asset) for asset in asset_pair]

    # sort the int-converted list, so that higher values appear first
    sorted_list_int = sorted(list_int)
    market = tuple(int_to_big_endian(int_) for int_ in sorted_list_int)
    assert set(market) == set(asset_pair)

    return market


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
        self.private_key = private_key # FIXME store privkey somewhere else
        # use the raiden discovery/transport here, with port being `raiden_port + 1`
        self.protocol = protocol_cls(transport, raiden_discovery, self)
        transport.protocol = self.protocol

        # holds the broadcast client,
        self.broadcast = BroadcastClient(broadcast_protocol_cls, broadcast_transport, BroadcastMessageHandler(self))

        self.cs_balances = dict() # cs_address -> balance

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

    def get_offerbook_by_asset_pair(self, asset_pair):
        """
        Calculates the market for the unordered asset-pair-tuple
        and retrieves the according OrderBook instance from the Service

        :param asset_pair: 2-tuple of assets
        :return: <OfferBook>  The offerbook instance for the `market` of the asset-pair
        """

        market = get_market_from_asset_pair(asset_pair)
        if market not in self.offerbooks:
            raise UntradableAssetPair
        else:
            offerbook = self.offerbooks[market]
        return offerbook

    def ping(self, receiver_address):
        ping = messages.Signed()
        ping.sign(self.private_key)
        self.protocol.send(receiver_address, ping)

    def add_offerbook(self, market, offerbook):
        self.offerbooks[market] = offerbook

    def get_offerbook(self, market):
        # gets the OfferBook instace for a given market
        assert market in self.offerbooks
        return self.offerbooks[market]

    def get_trade_history(self, market):
        assert market in self.trade_history
        return self.trade_history[market]


    def maker_commit(self, commitment_service_address, offer_id, commitment_amount, timeout):
        """
        Handles the communication as well as the raiden transfers to a commitmentservice,
        in order to make commitment.

        NOTE: this strategy currently applies to the maker commitment only, see issue #16 and issue #5
        """

        # check if known CS
        if commitment_service_address not in self.cs_balances:
            raise UnknownCommitmentService()

        # check for insufficient funds
        balance = self.cs_balances[commitment_service_address]
        if not balance >= commitment_amount:
            raise InsufficientCommitmentFunds()

        ## construct the commitment message
        signature = None  # TODO
        commitment = messages.Commitment(commitment_amount, offer_id, timeout)

        # send the message to the commitment service
        # (Alternative: skip this step completely and send only a Raiden transfer) (discuss: see issue #16)
        self.protocol.send(commitment_service_address, commitment)

        ## Send the actual commitment as a raiden transfer, with the offer_id as the identifier
        self.raiden.transfer(commitment_service_address, commitment_amount, identifier=offer_id)

        # write changes to current balance
        balance -= commitment_amount
        self.cs_balances[commitment_service_address] = balance

        # TODO: only successful when CommitmentProof is emitted by the CS


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

        timestamp = time.time()
        swap_execution_confirmation = messages.SwapExecution(offer_id, timestamp)

        self.protocol.send(commitment_service_address, swap_execution_confirmation)

    def deposit(self, commitment_service_address, deposit_amount):
        """
        Deposits to a payment channel with a commitment service.

        :param commitment_service_address: the raiden address of the commitmentservice
        :param deposit_amount: the amount of tradeable ether that is locked in the Payment channel
        :return:
        """
        assert commitment_service_address in self.cs_balances
        asset_address = ERC20_ETH_ADDRESS

        # deposit to a channel through the Raiden API
        success = self.raiden.deposit(asset_address, commitment_service_address, deposit_amount)
        if not success == True:
           raise Exception('channel deposit not successful')

        self.cs_balances[commitment_service_address] += deposit_amount

    def open(self, commitment_service_address):
        """
        Opens a payment channel in raiden with the commitment service, where the asset is an ERC20-Ether contract

        :param commitment_service_address: the raiden address of the commitmentservice
        :return: None
        """
        assert commitment_service_address not in self.cs_balances
        asset_address = ERC20_ETH_ADDRESS

        # open the channel through the raiden API:
        success = self.raiden.open(asset_address, commitment_service_address)

        if not success == True:
            raise Exception('channel opening not successful')

        self.cs_balances[commitment_service_address] = 0  # set initial balance to 0


class BroadcastMessageHandler(object):
    """
    BroadcastMessageHandler determines the behaviour on incoming messages from the broadcast
    """
    def __init__(self, raidex_service):
        self.raidex = raidex_service

    def on_provenoffer(self, message):
        # fill the offerbook
        msg_pair = (message.bid_token, message.ask_token)
        try:
            offer_book = self.raidex.get_offerbook_by_asset_pair(msg_pair)
            offer_book.insert_from_msg(message)
        except UntradableAssetPair:
            # log.INFO('the client is registered to an unaccessible market')
            pass

    def on_commitmentserviceadvertisement(self, message):
        raise NotImplementedError

    def on_swapcompleted(self, message):
        # remove offer from the orderbook
        raise NotImplementedError
