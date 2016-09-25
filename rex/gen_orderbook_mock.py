"""
Note: We don't have floats.
Therefore the amount is expressed in the smallest denomination (e.g. Wei in Ethereum)
Price is actually the ratio of the amount_ask_tokens / amount_bid_tokens * 1000
Time is milliseconds
"""
import time
import random
import json
from ethereum.utils import denoms


ETH = denoms.ether


def _price(p):
    return int(p * 1000)


def gen_orders(start_price=10, max_amount=1000 * ETH, num_entries=10, max_deviation=0.01):
    assert isinstance(start_price, (int, long))
    orders = []
    price = start_price
    for i in range(num_entries):
        factor = 1 + (2 * random.random() - 1) * max_deviation
        price = factor * price
        amount = random.randrange(1, max_amount)
        orders.append((_price(price), amount))
    return orders


def gen_orderbook(start_price=10, max_amount=1000 * ETH, num_entries=100, max_deviation=0.01):
    orders = gen_orders(start_price, max_amount, num_entries * 2, max_deviation)
    orders.sort()
    return orders


def gen_orderhistory(start_price=10, max_amount=1000 * ETH, num_entries=100, max_deviation=0.01):
    timestamp = time.time()
    avg_num_orders_per_second = 1.
    avg_gap_between_orders = 1 / avg_num_orders_per_second
    avg_gap_deviation = 2.

    orders = []

    for price, amount in gen_orders(start_price, max_amount, num_entries, max_deviation):
        elapsed = avg_gap_between_orders + (random.random() * 2 - 1) * avg_gap_deviation
        timestamp += elapsed
        orders.append(dict(timestamp=int(1000 * timestamp), price=price, amount=amount))
    return orders


def main():
    data = dict(order_book=gen_orderbook(num_entries=50),
                order_history=gen_orderhistory(num_entries=500))
    return json.dumps(data, indent=4)


if __name__ == '__main__':
    print main()
