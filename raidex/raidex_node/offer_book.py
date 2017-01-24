from bintrees import FastRBTree

from raidex.utils import get_market_from_asset_pair
from raidex.exceptions import RaidexException

class OfferMismatch(RaidexException):
    pass

class OfferType(object):
    BID = 0
    ASK = 1


class Offer(object):
    """

    Represents an Offer from the Broadcast.
    the broadcasted offer_message stores absolute information (bid_token, ask_token, bid_amount, ask_amount)
    the Offer stores it's information relative to it's market (type_,  price)


    Internally we work with relative values because:
        1) we want to easily compare prices (prices are the ultimate ordering criterion)
        2) we want to separate BIDs from ASKs
        3) traders are used to this!

    In the broadcast we work with absolute values because:
        1) asset swaps cannot be fractional
        2) we don't want to fix the permutation of the 'market' asset-pair on the message level.


    Note: protocol.send() takes an offer-msg (`messages.Offer`).
    To construct an offer-msg, please use the `messages.Offer.from_offer(offer)` classmethod

    """

    def __init__(self, market, type_, amount, price, timeout, offer_id):
        self.market = market
        self.offer_id = offer_id
        self.type_ = type_
        self.amount = amount
        self.timeout = timeout
        self.price = price

    def __cmp__(self, other):
        if self.price == other.price and self.timeout == other.timeout:
            return 0
        elif self.price < other.price or (
                self.price == other.price and self.timeout < other.timeout):
            return -1
        else:
            return 1

    def __repr__(self):
        return "Order<order_id={} amount={} price={} type={} market={}>".format(
                self.offer_id, self.amount, self.price, self.type_, self.market)


    @classmethod
    def from_message(cls, offer_msg):
        """
        Constructs an Offer out of an offer_message (e.g. retrieved from the broadcast).
        It converts the absolute values of the message to the values relative to the fixed market

        :param offer_msg: an Offer message retrieved from the broadcast
        :param market: the market's fixed asset pair in which the offer is traded - to calculate the price and offer_type
        :return: an Offer instance
        """

        msg_pair = (offer_msg.bid_token, offer_msg.ask_token)
        market = get_market_from_asset_pair(msg_pair)

        if msg_pair == market:
            type_ = OfferType.BID #XXX checkme
            price = float(offer_msg.bid_amount) / offer_msg.ask_amount
            amount = offer_msg.bid_amount
        elif msg_pair[::-1] == market:
            type_ = OfferType.ASK #XXX checkme
            price = float(offer_msg.bid_amount) / offer_msg.ask_amount
            amount = offer_msg.ask_amount
        else:
            raise Exception('Wrong market')
        offer_id = offer_msg.offer_id
        return cls(market, type_, amount, price, offer_id, offer_msg.timeout / 1000.0)


class OfferView(object):
    """
    Holds a collection of Offers in an RBTree for faster search.
    One OfferView instance holds either BIDs or ASKs, as denoted by the `type_` field

    """

    def __init__(self, market, type_):
        self.market = market
        self.type_ = type_
        self.offers = FastRBTree()
        self.offer_by_id = dict()

    def add_offer(self, offer):
        assert isinstance(offer, Offer)

        if offer.type_ != self.type_ or offer.market != self.market:
            raise OfferMismatch

        # inserts in the RBTree
        self.offers.insert(offer, offer)

        #inserts in the dict for retrieval by offer_id
        self.offer_by_id[offer.offer_id] = offer

        return offer.offer_id

    def remove_offer(self, offer_id):
        if offer_id in self.offer_by_id:
            offer = self.offer_by_id[offer_id]

            # remove from the RBTree
            self.offers.remove(offer)

            # remove from the dict
            del self.offer_by_id[offer_id]

    def get_offer_by_id(self, offer_id):
        return self.offer_by_id.get(offer_id)

    def __len__(self):
        return len(self.offers)

    def __iter__(self):
        # when iterating over the OfferView, this iterates over the RBTree!
        # self.offers = <FastRBTree>
        return iter(self.offers)


class OfferBook(object):

    def __init__(self, market):
        self.market = market
        self.bids = OfferView(market, type_=OfferType.BID)
        self.asks = OfferView(market, type_=OfferType.ASK)
        self.tasks = dict()

    def insert_offer(self, offer):

        if offer.type_ is OfferType.BID:
            self.bids.add_offer(offer)
        elif offer.type_ is OfferType.ASK:
            self.asks.add_offer(offer)
        else:
            raise RaidexException('unsupported offer-type')

        return offer.offer_id

    def get_offer_by_id(self, offer_id):
        offer = self.bids.get_offer_by_id(offer_id)
        if offer is None:
            offer = self.asks.get_offer_by_id(offer_id)
        return offer

    def remove_offer(self, offer_id):
        if offer_id in self.bids:
            offer_view = self.bids
        elif offer_id in self.asks:
            offer_view = self.asks
        else:
            raise RaidexException('offer_id not found')

        offer_view.remove_offer(offer_id)

    def __repr__(self):
        return "OfferBook<bids={} asks={}>".format(len(self.bids), len(self.asks))
