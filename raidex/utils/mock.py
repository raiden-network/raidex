#!/usr/bin/env python

"""
Note: We don't have floats.
Therefore the amount is expressed in the smallest denomination (e.g. Wei in Ethereum)
Price is actually the ratio of the amount_ask_tokens / amount_bid_tokens * 1000
Time is milliseconds
"""
import time
import random
import json
import math
import copy
from collections import namedtuple

from ethereum.utils import denoms, sha3, encode_hex, privtoaddr

from rex.messages import Offer

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


def gen_orderbook_messages(market_price=10, max_amount=1000 * ETH, num_messages=200, max_deviation=0.01):
    assert isinstance(market_price, (int, long))
    offers = []
    asks_price = copy.deepcopy(market_price)
    bids_price = copy.deepcopy(market_price)

    for i in range(num_messages):
        # odd i stands for bids
        if i % 2:  # asks
            factor = 1 + random.random()* max_deviation
            asks_price = factor * asks_price
            bid_amount = random.randrange(1, max_amount)
            ask_amount = int(bid_amount / asks_price)
        else:  # bids
            factor = 1 - random.random() * max_deviation
            bids_price = factor * bids_price
            bid_amount = random.randrange(2, max_amount)
            ask_amount = int(bid_amount / bids_price)

        maker = ACCOUNTS[num_messages % 2]
        offer = Offer(ASSETS[i % 2], ask_amount,
                      ASSETS[1 - i % 2], bid_amount,
                      sha3('offer {}'.format(i)), # TODO better offer_ids
                      int(time.time() * 10000 + 1000 * random.randint(1,10) + i)
                      )
        offer.sign(maker.privatekey)
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
    return dict(bids=bids, asks=asks)


def gen_orderhistory(start_price=10, max_amount=1000 * ETH, num_entries=100, max_deviation=0.01):
    timestamp = time.time()
    avg_num_orders_per_second = 1.
    avg_gap_between_orders = 1 / avg_num_orders_per_second
    avg_gap_deviation = 2.

    orders = []

    for address, price, amount in gen_orders(start_price, max_amount, num_entries, max_deviation):
        elapsed = avg_gap_between_orders + (random.random() * 2 - 1) * avg_gap_deviation
        timestamp += elapsed
        orders.append(dict(
            timestamp=int(1000 * timestamp), address=address, price=price, amount=amount
        ))
    return orders
