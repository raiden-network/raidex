from __future__ import print_function
import random

from sortedcontainers import SortedDict
from enum import Enum
import structlog
from raidex.utils import pex

from eth_utils import int_to_big_endian


log = structlog.get_logger('node.offer_book')


class OfferType(Enum):
    BUY = 0
    SELL = 1

    @classmethod
    def opposite(cls, type_):
        return OfferType((type_.value + 1) % 2)


def generate_random_offer_id():
    # generate random offer-id in the 32byte int range
    return int(random.randint(0, 2 ** 256 - 1))


class Offer(object):
    """

    Represents an Offer from the Broadcast.
    the broadcasted offer_message stores absolute information (bid_token, ask_token, bid_amount, ask_amount)
    the Offer stores it's information relative to it's market (type,  price)


    Internally we work with relative values because:
        1) we want to easily compare prices (prices are the ultimate ordering criterion)
        2) we want to separate BUYs from SELLs
        3) traders are used to this!

    In the broadcast we work with absolute values because:
        1) asset swaps cannot be fractional
        2) we don't want to fix the permutation of the 'market' asset-pair on the message level.

    """

    def __init__(self, type_, base_amount, counter_amount, offer_id, timeout,
                 maker_address=None, taker_address=None, commitment_amount=1):
        assert isinstance(type_, OfferType)
        assert isinstance(base_amount, int)
        assert isinstance(counter_amount, int)
        assert isinstance(offer_id, int)
        assert isinstance(timeout, int)
        assert base_amount > 0
        assert counter_amount > 0
        self.offer_id = offer_id
        self.type = type_
        self.base_amount = base_amount
        self.counter_amount = counter_amount
        self.timeout = timeout
        self.maker_address = maker_address
        self.taker_address = taker_address

        self.commitment_amount = commitment_amount

    @property
    def amount(self):
        return self.base_amount

    @property
    def price(self):
        return float(self.counter_amount) / self.base_amount

    def __repr__(self):
        return "Offer<pex(id)={} amount={} price={} type={}>".format(
                pex(int_to_big_endian(self.offer_id)), self.amount, self.price, self.type)


class OfferView(object):
    """
    Holds a collection of Offers in an RBTree for faster search.
    One OfferView instance holds either BUYs or SELLs

    """

    def __init__(self):
        self.offers = SortedDict()
        self.offer_by_id = dict()

    def add_offer(self, offer):
        assert isinstance(offer, Offer)

        # inserts in the SortedDict
        self.offers[(offer.price, offer.offer_id)] = offer

        # inserts in the dict for retrieval by offer_id
        self.offer_by_id[offer.offer_id] = offer

        return offer.offer_id

    def remove_offer(self, offer_id):
        if offer_id in self.offer_by_id:
            offer = self.offer_by_id[offer_id]

            # remove from the SortedDict
            del self.offers[(offer.price, offer.offer_id)]

            # remove from the dict
            del self.offer_by_id[offer_id]

    def get_offer_by_id(self, offer_id):
        return self.offer_by_id.get(offer_id)

    def __len__(self):
        return len(self.offers)

    def __iter__(self):
        return iter(self.offers)

    def values(self):
        # returns list of all offers, sorted by (price, offer_id)
        return self.offers.values()


class OfferBook(object):

    def __init__(self):
        self.buys = OfferView()
        self.sells = OfferView()
        self.tasks = dict()

    def insert_offer(self, offer):
        assert isinstance(offer.type, OfferType)
        if offer.type is OfferType.BUY:
            self.buys.add_offer(offer)
        elif offer.type is OfferType.SELL:
            self.sells.add_offer(offer)
        else:
            raise Exception('unsupported offer-type')

        return offer.offer_id

    def get_offer_by_id(self, offer_id):
        offer = self.buys.get_offer_by_id(offer_id)
        if offer is None:
            offer = self.sells.get_offer_by_id(offer_id)
        return offer

    def contains(self, offer_id):
        return offer_id in self.buys.offer_by_id or offer_id in self.sells.offer_by_id

    def remove_offer(self, offer_id):
        if offer_id in self.buys.offer_by_id:
            offer_view = self.buys
        elif offer_id in self.sells.offer_by_id:
            offer_view = self.sells
        else:
            raise Exception('offer_id not found')

        offer_view.remove_offer(offer_id)

    def __repr__(self):
        return "OfferBook<buys={} sells={}>".format(len(self.buys), len(self.sells))
