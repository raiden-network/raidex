#!/usr/bin/env python

"""
Note: We don't have floats.
Therefore the amount is expressed in the smallest denomination (e.g. Wei in Ethereum)
Price is actually the ratio of the amount_ask_tokens / amount_bid_tokens * 1000
Time is milliseconds
"""
import copy
import random
from collections import namedtuple

import gevent
from noise import pnoise1
from ethereum.utils import denoms, sha3, privtoaddr, encode_hex, big_endian_to_int

from raidex import messages
from raidex.commitment_service.mock import CommitmentServiceMock
from raidex.raidex_node.offer_book import Offer, OfferType
from raidex.utils import make_privkey_address, timestamp
from raidex.signing import Signer

ETH = denoms.ether


def _price(p):
    return int(p * 1000)


def _accounts():
    Account = namedtuple('Account', 'privatekey address')
    privkeys = [sha3("account:{}".format(i)) for i in range(2)]
    accounts = [Account(pk, privtoaddr(pk)) for pk in privkeys]
    return accounts


ASSETS = [privtoaddr(sha3("asset{}".format(i))) for i in range(2)]
ACCOUNTS = _accounts()


def gen_orders(start_price=10, max_amount=1000 * ETH, num_entries=10, max_deviation=0.01):
    assert isinstance(start_price, (int, long))
    orders = []
    price = start_price
    for _ in range(num_entries):
        factor = 1 + (2 * random.random() - 1) * max_deviation
        price *= factor
        amount = random.randrange(1, max_amount)
        address = encode_hex(sha3(price * amount))[:40]
        orders.append((address, _price(price), amount))
    return orders


def gen_orderbook_messages(market_price=10, max_amount=1000 * ETH, num_messages=200, max_deviation=0.01):
    assert isinstance(market_price, (int, long))
    offers = []
    asks_price = copy.deepcopy(market_price)
    bids_price = copy.deepcopy(market_price)

    for _ in range(num_messages):
        # odd i stands for bids
        if i % 2:  # asks
            factor = 1 + random.random() * max_deviation
            asks_price *= factor
            bid_amount = random.randrange(1, max_amount)
            ask_amount = int(bid_amount / asks_price)
        else:  # bids
            factor = 1 - random.random() * max_deviation
            bids_price *= factor
            bid_amount = random.randrange(2, max_amount)
            ask_amount = int(bid_amount / bids_price)

        maker = ACCOUNTS[num_messages % 2]
        offer = messages.SwapOffer(ASSETS[i % 2], ask_amount,
                                   ASSETS[1 - i % 2], bid_amount,
                                   sha3('offer {}'.format(i)),  # TODO better offer_ids
                                   int(timestamp.time() * 10000 + 1000 * random.randint(1, 10) + i))
        offers.append(offer)
    return offers


def gen_orderbook(start_price=10, max_amount=1000 * ETH, num_entries=100, max_deviation=0.01):
    orders = gen_orders(start_price, max_amount, num_entries * 2, max_deviation)
    orders.sort()
    return orders


def gen_orderbook_dict(start_price=10, max_amount=1000 * ETH, num_entries=100, max_deviation=0.01):
    orders = gen_orders(start_price, max_amount, num_entries * 2, max_deviation)
    bids = [dict(address=a, price=p, amount=am) for a, p, am in reversed(orders[:num_entries])]
    asks = [dict(address=a, price=p, amount=am) for a, p, am in orders[num_entries:]]
    return dict(buys=bids, sells=asks)


def gen_orderhistory(start_price=10, max_amount=1000 * ETH, num_entries=100, max_deviation=0.01):
    tstamp = timestamp.time()
    avg_num_orders_per_second = 0.01
    avg_gap_between_orders = 1 / avg_num_orders_per_second
    avg_gap_deviation = 2

    orders = []

    for address, price, amount in gen_orders(start_price, max_amount * ETH, num_entries, max_deviation):
        elapsed = avg_gap_between_orders + (random.random() * 2 - 1) * avg_gap_deviation
        tstamp += elapsed
        orders.append(dict(
            timestamp=int(1000 * tstamp), address=address, price=price, amount=amount, type=random.randint(0, 1)
        ))
    return orders


def gen_offer(magic_number, market_price=10.0, max_amount=1000 * ETH, max_deviation=0.01):
    price = market_price
    operator = [-1, 1]

    switch = random.choice((0, 1))
    type_ = OfferType(switch)
    for _ in range(magic_number):
            drift = random.random() * max_deviation * operator[switch]
            factor = 1 + drift
            price *= factor

    base_amount = random.randint(1, max_amount)
    counter_amount = int(base_amount * float(price))

    assert type_ in (OfferType.BUY, OfferType.SELL)
    offer = Offer(type_,
                  base_amount,
                  counter_amount,
                  # reuse random privkey generation for random offer-ids:
                  big_endian_to_int(make_privkey_address()[0]),
                  # timeout int 10-100 seconds
                  timestamp.time_plus(random.randint(10, 100))
                  )
    return offer


class MockExchangeTask(gevent.Greenlet):

    nof_accounts = 20  # number of accounts, doesn't do much apart from address variety
    max_price_movement = 0.02
    message_volume = 200  # mostly determines the highest/lowest spread

    def __init__(self, initial_market_price, token_pair, cs_global, cs_fee_rate, message_broker, offer_book):
        self.commitment_services = []
        # generate 10 different market-makers' cs_clients
        for _ in range(0, 10):
            self.commitment_services.append(
                CommitmentServiceMock(Signer(), token_pair, message_broker, cs_fee_rate, cs_global)
            )
        self.message_broker = message_broker
        self.offer_book = offer_book
        self.market_price = float(initial_market_price)
        self.time = 0.
        gevent.Greenlet.__init__(self)

    def _run(self):
        while True:
            current_commitment_service = random.choice(self.commitment_services)
            self.make_offer(self.market_price, current_commitment_service)
            # propagate perlin noise generator and set new market price target, always positive
            # TODO Fixme, optimize
            self.market_price = abs(self.market_price + self.max_price_movement * pnoise1(self.time))
            self.time += 0.01
            magic_number = random.randint(1, self.message_volume)
            # 20% of offers get taken, others should time out
            if magic_number <= int(round(self.message_volume * 0.2)):
                type_ = random.choice([OfferType.BUY, OfferType.SELL])
                offers = None
                if type_ == OfferType.SELL:
                    # FIXME, ugly
                    # FIXME Can be empty!!
                    offers = list(reversed(list(self.offer_book.buys.values())))

                elif type_ == OfferType.BUY:
                    offers = list(self.offer_book.sells.values())

                # threshold_index = int(self.message_volume * 0.2)
                threshold_index = int(len(offers) * 0.2)
                try:
                    # FIXME will most likely not succeed because of a lot of index errors
                    offer_to_take = random.choice(offers[0:threshold_index])
                    self.take_and_swap_offer(offer_to_take, current_commitment_service)
                except IndexError or TypeError:
                    pass
            # new activity every 1-5 seconds
            ttl = random.randint(1, 5)
            gevent.sleep(ttl)

    def make_offer(self, market_price, commitment_service_client):
        magic_number = random.randint(1, self.message_volume)
        offer = gen_offer(magic_number, market_price=market_price)
        proven_offer = commitment_service_client.maker_commit_async(offer).get()
        self.message_broker.broadcast(proven_offer)

    def take_and_swap_offer(self, offer, commitment_service_client):
        # skip taker-commitment since this is not broadcasted anyways
        offer_taken = commitment_service_client.create_taken(offer.offer_id)
        self.message_broker.broadcast(offer_taken)

        # spawn later randomly, but before timeout
        swap_completed = commitment_service_client.create_swap_completed(offer.offer_id)
        wait = int(round(offer.timeout - (random.random() * (offer.timeout - 100))))
        gevent.spawn_later(timestamp.to_seconds(wait), self.message_broker.broadcast, swap_completed)
