from __future__ import print_function

import gevent
from bintrees import FastRBTree
from enum import Enum
from ethereum import slogging
from raidex.utils import timestamp, pex


log = slogging.get_logger('node.offer_book')


class OfferType(Enum):
    BUY = 0
    SELL = 1

    @classmethod
    def opposite(cls, type_):
        return OfferType((type_.value + 1) % 2)


class Offer(object):
    """

    Represents an Offer from the Broadcast.
    the broadcasted offer_message stores absolute information (bid_token, ask_token, bid_amount, ask_amount)
    the Offer stores it's information relative to it's market (type_,  price)


    Internally we work with relative values because:
        1) we want to easily compare prices (prices are the ultimate ordering criterion)
        2) we want to separate BUYs from SELLs
        3) traders are used to this!

    In the broadcast we work with absolute values because:
        1) asset swaps cannot be fractional
        2) we don't want to fix the permutation of the 'market' asset-pair on the message level.

    """

    def __init__(self, type_, base_amount, counter_amount, offer_id, timeout,
                 maker_address=None, taker_address=None):
        assert isinstance(type_, OfferType)
        assert isinstance(base_amount, (int, long))
        assert isinstance(counter_amount, (int, long))
        assert isinstance(offer_id, (int, long))
        assert isinstance(timeout, (int, long))
        self.offer_id = offer_id
        self.type_ = type_
        self.base_amount = base_amount
        self.counter_amount = counter_amount
        self.timeout = timeout
        self.maker_address = maker_address
        self.taker_address = taker_address

        # FIXME hash is only known after creating the message, but maker creates the offer instance before \
        # serializing to a msg
        # This members will only be set when you are not the maker!
        # Information from the associated commitment:
        self.hash = None
        self.commitment_amount = None

    # make setting of msg hash more explicit
    def set_offer_hash(self, hash_):
        self.hash = hash_

    # make setting of commitment_amount more explicit
    def set_commitment_amount(self, amount):
        self.commitment_amount = amount

    @property
    def amount(self):
        return self.base_amount

    @property
    def price(self):
        return float(self.counter_amount) / self.base_amount

    def __repr__(self):
        return "Offer<offer_id={} amount={} price={} type={} hash={}>".format(
                self.offer_id, self.amount, self.price, self.type_, pex(self.hash))


class OfferView(object):
    """
    Holds a collection of Offers in an RBTree for faster search.
    One OfferView instance holds either BUYs or SELLs

    """

    def __init__(self):
        self.offers = FastRBTree()
        self.offer_by_id = dict()

    def add_offer(self, offer):
        assert isinstance(offer, Offer)

        # inserts in the RBTree
        self.offers.insert((offer.price, offer.offer_id), offer)

        # inserts in the dict for retrieval by offer_id
        self.offer_by_id[offer.offer_id] = offer

        return offer.offer_id

    def remove_offer(self, offer_id):
        if offer_id in self.offer_by_id:
            offer = self.offer_by_id[offer_id]

            # remove from the RBTree
            self.offers.remove((offer.price, offer.offer_id))

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

    def values(self):
        return self.offers.values()


class OfferBook(object):

    def __init__(self):
        self.buys = OfferView()
        self.sells = OfferView()
        self.tasks = dict()

    def insert_offer(self, offer):
        assert isinstance(offer.type_, OfferType)
        if offer.type_ is OfferType.BUY:
            self.buys.add_offer(offer)
        elif offer.type_ is OfferType.SELL:
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


class TakenTask(gevent.Greenlet):
    def __init__(self, offer_book, trades, taken_listener):
        self.offer_book = offer_book
        self.trades = trades
        self.taken_listener = taken_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.taken_listener.start()
        while True:
            offer_id = self.taken_listener.get()
            if self.offer_book.contains(offer_id):
                log.debug('Offer {} is taken'.format(offer_id))
                offer = self.offer_book.get_offer_by_id(offer_id)
                self.trades.add_pending(offer)
                self.offer_book.remove_offer(offer_id)


class OfferBookTask(gevent.Greenlet):

    def __init__(self, offer_book, offer_listener):
        self.offer_book = offer_book
        self.offer_listener = offer_listener
        gevent.Greenlet.__init__(self)

    def _run(self):
        self.offer_listener.start()

        while True:
            offer = self.offer_listener.get()
            log.debug('New Offer: {}'.format(offer))
            self.offer_book.insert_offer(offer)

            def after_offer_timeout_func(offer_id):
                def func():
                    if self.offer_book.contains(offer_id):
                        log.debug('Offer {} timed out'.format(offer_id))
                        self.offer_book.remove_offer(offer_id)
                return func

            gevent.spawn_later(timestamp.seconds_to_timeout(offer.timeout), after_offer_timeout_func(offer.offer_id))
