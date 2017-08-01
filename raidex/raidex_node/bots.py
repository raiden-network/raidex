import math
import random
import logging
from gevent import Greenlet, sleep
from gevent.event import Event
from ethereum import slogging
from raidex.raidex_node.offer_book import OfferType

random.seed(0)

log = slogging.get_logger('bots')


class RandomWalker(Greenlet):
    """Bot that randomly buys or sells some amount."""

    def __init__(self, raidex_node, average_volume):
        """
        Args:
            raidex_node: the node that is used to place the orders
        """
        Greenlet.__init__(self)
        self.raidex_node = raidex_node
        self.average_volume = average_volume
        self.log = slogging.get_logger('bots.random_walker')

    def _run(self):
        while True:
            # counter intuitive: type_ is offer type to take (so SELL means buy something)
            type_ = random.choice([OfferType.BUY, OfferType.SELL])
            #type_ = OfferType.SELL
            offer_book = self.raidex_node.offer_book
            try:
                if type_ is OfferType.BUY:
                    view = offer_book.buys
                    _, offer_id = next(reversed(list(offer for offer in view)))
                else:
                    view = offer_book.sells
                    _, offer_id = next(offer for offer in view)
            except StopIteration:
                self.log.warning('did not find offer', type=type_.name)
            else:
                offer = self.raidex_node.offer_book.get_offer_by_id(offer_id)
                self.log.info('taking offer', type=type_.name, amount=offer.amount / 1e18,
                              price=offer.price)
                self.raidex_node.take_offer(offer_id)
            sleep(1)


class LiquidityProvider(Greenlet):
    """Bot that sets both buy and sell orders around a given price.

    This provides liquidity for other market participants and fills the market depth graph. It has
    an indefinite amount of funds.
    """

    def __init__(self, raidex_node, price):
        """
        Args:
            raidex_node: the node that is used to place the offers
            price: the initial price
        """
        Greenlet.__init__(self)
        self.raidex_node = raidex_node
        self.initial_price = float(price)
        self.average_price_delta = price * 0.01
        self.average_volume = int(10 * 1e18)
        self.buy_orders = []  # sorted, highest price first
        self.sell_orders = []  # sorted, lowest price first
        self.log = slogging.get_logger('bots.liquidity_provider')

    def random_volume(self):
        """Return a random non-negative number averaging to `self.average_volume`."""
        return self.average_volume
        # return int(round(random.expovariate(1. / self.average_volume)))

    def random_price_delta(self):
        """Calculate a random non-negative number averaging to `self.average_price_delta`."""
        return self.average_price_delta
        # return random.expovariate(1. / self.average_price_delta)

    def place_buy_order(self, price):
        """Place a buy order."""
        volume = self.random_volume()
        order_id = self.raidex_node.limit_order(OfferType.BUY, volume, price)
        self.buy_orders.append(self.raidex_node.order_tasks_by_id[order_id])
        self.buy_orders.sort(key=lambda o: o.price, reverse=True)

    def place_sell_order(self, price):
        """Place a buy order."""
        volume = self.random_volume()
        order_id = self.raidex_node.limit_order(OfferType.SELL, volume, price)
        print volume, price
        self.sell_orders.append(self.raidex_node.order_tasks_by_id[order_id])
        self.sell_orders.sort(key=lambda o: o.price, reverse=False)
        self.log.debug(len(self.sell_orders))

    def place_initial_orders(self):
        # place buy orders
        count = 0
        price = self.initial_price
        while price > self.initial_price * 0.9:
            price -= self.random_price_delta()
            self.place_buy_order(price)
            count += 1
        min_price = price
        # place sell orders
        price = self.initial_price
        while price < self.initial_price * 1.1:
            price += self.random_price_delta()
            self.place_sell_order(price)
            count += 1
        max_price = price
        self.log.info('placed initial orders', count=count, max_price=max_price,
                      min_price=min_price)

    def _run(self):
        self.place_initial_orders()
        while True:
            order_taken = Event()
            order_taken.clear()
            for order in self.raidex_node.order_tasks_by_id.values():
                order.link(lambda _: order_taken.set())
            order_taken.wait()  # wait for an order to be taken

            # for every taken sell order
            for order in self.sell_orders:
                if not order.finished:
                    continue
                assert order.number_open_trades == 0
                self.log.info('replacing fulfilled order', type=OfferType.BUY.name)
                # place sell offer at higher price
                sell_price = self.sell_orders[-1].price + self.random_price_delta()
                self.place_sell_order(sell_price)
                # place buy offer at higher price
                buy_price = self.buy_orders[0].price + self.random_price_delta()
                self.place_buy_order(buy_price)
                # cancel worst buy offer
                self.buy_orders[-1].cancel()

            # for every taken buy order
            for order in self.buy_orders:
                if not order.finished:
                    continue
                assert order.number_open_trades == 0
                self.log.info('replacing fulfilled order', type=OfferType.SELL.name)
                # place buy offer at lower price
                buy_price = self.buy_orders[-1].price - self.random_price_delta()
                self.place_buy_order(buy_price)
                # place sell offer at lower price
                sell_price = self.sell_orders[0].price - self.random_price_delta()
                self.place_sell_order(sell_price)
                # cancel worst sell offer
                self.sell_orders[-1].cancel()

            # remove finished orders
            self.buy_orders = [o for o in self.buy_orders if not (o.finished or o.canceled)]
            self.sell_orders = [o for o in self.sell_orders if not (o.finished or o.canceled)]
