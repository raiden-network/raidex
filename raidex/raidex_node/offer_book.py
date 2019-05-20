from __future__ import print_function
import random

from sortedcontainers import SortedDict
import structlog
from raidex.utils import pex
from raidex.utils.timestamp import to_str_repr
from raidex.raidex_node.order.offer import OfferType

from eth_utils import int_to_big_endian


log = structlog.get_logger('node.offer_book')


def generate_random_offer_id():
    # generate random offer-id in the 32byte int range
    return int(random.randint(0, 2 ** 256 - 1))


class OfferDeprecated(object):
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

    def __init__(self, type_, base_amount, quote_amount, offer_id, timeout_date,
                 maker_address=None, taker_address=None, commitment_amount=1):
        assert isinstance(type_, OfferType)
        assert isinstance(base_amount, int)
        assert isinstance(quote_amount, int)
        assert isinstance(offer_id, int)
        assert isinstance(timeout_date, int)
        assert base_amount > 0
        assert quote_amount > 0
        self.offer_id = offer_id
        self.type = type_
        self.base_amount = base_amount
        self.quote_amount = quote_amount
        self.timeout_date = timeout_date
        self.maker_address = maker_address
        self.taker_address = taker_address

        self.commitment_amount = commitment_amount

    @property
    def amount(self):
        return self.base_amount

    @property
    def price(self):
        return float(self.quote_amount) / self.base_amount

    def __repr__(self):
        return "Offer<pex(id)={} amount={} price={} type={} timeout_date={}>".format(
            pex(int_to_big_endian(self.offer_id)),
            self.amount,
            self.price,
            self.type,
            to_str_repr(self.timeout_date))


class OfferBookEntry:

    def __init__(self, offer, commitment, commitment_proof):
        self.offer = offer
        self.commitment = commitment
        self.commitment_proof = commitment_proof

    @property
    def offer_id(self):
        return self.offer.offer_id

    @property
    def base_amount(self):
        return self.offer.base_amount

    @property
    def quote_amount(self):
        return self.offer.quote_amount

    @property
    def price(self):
        return self.offer.price

    @property
    def timeout_date(self):
        return self.offer.timeout_date


class OfferView(object):
    """
    Holds a collection of Offers in an RBTree for faster search.
    One OfferView instance holds either BUYs or SELLs

    """

    def __init__(self):
        self.offer_entries = SortedDict()
        self.offer_entries_by_id = dict()

    def add_offer(self, entry):
        assert isinstance(entry, OfferBookEntry)

        offer_id = entry.offer_id
        offer_price = entry.price

        # inserts in the SortedDict
        self.offer_entries[(offer_price, offer_id)] = entry

        # inserts in the dict for retrieval by offer_id
        self.offer_entries_by_id[offer_id] = entry

        return offer_id

    def remove_offer(self, offer_id):
        if offer_id in self.offer_entries_by_id:
            entry = self.offer_entries_by_id[offer_id]

            # remove from the SortedDict
            del self.offer_entries[(entry.price, entry.offer_id)]

            # remove from the dict
            del self.offer_entries_by_id[offer_id]

    def get_offer_by_id(self, offer_id):
        return self.offer_entries_by_id.get(offer_id)

    def get_offers_by_price(self, price):

        matched_offers = list()

        for offer in self.offer_entries.values():
            if offer.price == price:
                matched_offers.append(offer)
            if offer.price > price:
                break

        return matched_offers

    def __len__(self):
        return len(self.offer_entries)

    def __iter__(self):
        return iter(self.offer_entries)

    def values(self):
        # returns list of all offers, sorted by (price, offer_id)
        return self.offer_entries.values()


class OfferBook(object):

    def __init__(self):
        self.buys = OfferView()
        self.sells = OfferView()
        self.tasks = dict()

    def insert_offer(self, offer_entry):
        offer = offer_entry.offer
        assert isinstance(offer.type, OfferType)
        if offer.type is OfferType.BUY:
            self.buys.add_offer(offer_entry)
        elif offer.type is OfferType.SELL:
            self.sells.add_offer(offer_entry)
        else:
            raise Exception('unsupported offer-type')

        return offer_entry.offer_id

    def get_offer_by_id(self, offer_id):
        offer = self.buys.get_offer_by_id(offer_id)
        if offer is None:
            offer = self.sells.get_offer_by_id(offer_id)
        return offer

    def contains(self, offer_id):
        return offer_id in self.buys.offer_entries_by_id or offer_id in self.sells.offer_entries_by_id

    def remove_offer(self, offer_id):
        if offer_id in self.buys.offer_entries_by_id:
            offer_view = self.buys
        elif offer_id in self.sells.offer_entries_by_id:
            offer_view = self.sells
        else:
            raise Exception('offer_id not found')

        offer_view.remove_offer(offer_id)

    def get_offers_by_price(self, price, offer_type):
        offer_list = self.buys if offer_type == OfferType.SELL else self.sells
        return offer_list.get_offers_by_price(price)

    def __repr__(self):
        return "OfferBook<buys={} sells={}>".format(len(self.buys), len(self.sells))
