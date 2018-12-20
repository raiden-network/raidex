import random
from itertools import chain, repeat
from gevent import Greenlet, sleep
import structlog
from raidex.raidex_node.offer_book import OfferType

random.seed(0)

log = structlog.get_logger('bots')


class RandomWalker(Greenlet):
    """Bot that randomly buys or sells some amount."""

    def __init__(self, raidex_node, initial_price):
        """
        Args:
            raidex_node: the node that is used to place the orders
        """
        Greenlet.__init__(self)
        self.raidex_node = raidex_node
        self.initial_price = initial_price
        self.average_amount = int(10e18)  # average order amount
        self.average_frequency = 0.2  # trades per second
        self.urgency = 0.02  # percentag bot is willing to overpay to get its order filled quicker
        self.log = structlog.get_logger('bots.random_walker')

    def place_order(self, order_type):
        market_price = self.raidex_node.market_price() or self.initial_price
        offset = market_price * self.urgency
        price = market_price + offset if order_type is OfferType.BUY else market_price - offset
        amount = self.average_amount
        self.log.info('placing order', type=order_type.name, amount=amount * 1e-18,
                      market_price=market_price, price=price)
        self.raidex_node.limit_order(order_type, amount, price)

    def _run(self):
        while True:
            type_ = random.choice([OfferType.BUY, OfferType.SELL])
            self.place_order(type_)
            sleep(1. / self.average_frequency)


class Manipulator(Greenlet):

    def __init__(self, raidex_node, initial_price):
        Greenlet.__init__(self)
        self.raidex_node = raidex_node
        self.initial_price = initial_price
        self.log = structlog.get_logger('bots.manipulator')

        self.order_amount_average = int(2e18)
        self.order_frequency_average = 0.8

        self.goal_delta_average = 0.1  # percentage of current price
        self.goal_delta_sigma = self.goal_delta_average / 10  # percentage of current price

        self.overpay = 0.02

        self.goal = None
        self.set_new_goal()

    def set_new_goal(self):
        price = self.raidex_node.market_price() or self.initial_price
        delta = price * abs(random.normalvariate(self.goal_delta_average, self.goal_delta_sigma))
        sign = random.choice([+1, -1])
        self.goal = (price, sign * delta)
        self.log.info('new goal set', price_delta=self.goal[1], current_price=price)

    def is_goal_reached(self):
        delta_reached = (self.raidex_node.market_price() or self.initial_price) - self.goal[0]
        return ((self.goal[1] >= 0 and delta_reached >= self.goal[1]) or
                (self.goal[1] < 0 and delta_reached < self.goal[1]))

    def place_order(self):
        market_price = self.raidex_node.market_price() or self.initial_price
        # buy if price should increase, otherwise sell
        if self.goal[1] >= 0:
            order_type = OfferType.BUY
            order_price = market_price * (1 + self.overpay)
        else:
            order_type = OfferType.SELL
            order_price = market_price * (1 - self.overpay)
        self.raidex_node.limit_order(order_type, self.order_amount_average, order_price)
        self.log.debug('placed order', price=order_price, amount=self.order_amount_average)

    def _run(self):
        while True:
            if self.is_goal_reached():
                self.log.info('goal has been reached')
                self.set_new_goal()
            self.place_order()
            sleep(1. / self.order_frequency_average)


class LiquidityProvider(Greenlet):

    def __init__(self, raidex_node, initial_price):
        Greenlet.__init__(self)
        self.raidex_node = raidex_node
        self.initial_price = initial_price
        # range around the market price in which liquidity will be provided (as a percentage)
        self.range = 0.05
        # range around market price in which no orders will be placed (as a percentage)
        self.spread = 0.005  # 0.001
        # target slope of market depth curve (unit: amount / range)
        self.slope = 20e18 / 0.01
        # number of points per unit range where liquidity is checked
        self.homogenity = 10 * 2 / 0.01  # 10 / 0.01
        # overshoot percentage when replenishing offers
        self.overshoot = 0
        self.log = structlog.get_logger('bots.liquidity_provider')

    def calc_checkpoints(self, price):
        """Calculate points at which slope is checked.

        :param price: the current market price
        :returns: check points for sell and buy offers as 2-tuple
        """
        n_check_points = int(round(self.homogenity * (self.range - self.spread) / 2))
        assert self.range > self.spread
        check_point_distance = float(self.range - self.spread) / 2 * price / n_check_points
        check_points_sell = [price * (1 + self.spread / 2) + (i + 0.5) * check_point_distance
                             for i in range(n_check_points)]
        check_points_buy = [price * (1 - self.spread / 2) - (i + 0.5) * check_point_distance
                            for i in range(n_check_points)]
        return check_points_sell, check_points_buy

    def calc_target_amount(self, market_price, check_point):
        """Calculate the desired cumulative offered amount at a certain price."""
        delta = abs(market_price - check_point) / market_price
        if delta < self.spread / 2:
            return 0
        delta = min(delta, self.range / 2)
        amount = (delta - self.spread / 2) * self.slope
        assert amount >= 0
        return amount

    def integrate_offers_until(self, market_price, check_point):
        """Sum the amount of offers with prices between `market_price` and `check_point`."""
        if check_point >= market_price:
            # integrate sell offers (from low to high prices)
            offers = self.raidex_node.offer_book.sells
        else:
            # integrate buy offers (from high to low prices)
            offers = reversed(list(self.raidex_node.offer_book.buys))
        low = min(market_price, check_point)
        high = max(market_price, check_point)
        s = 0
        for _, offer_id in offers:
            offer = self.raidex_node.offer_book.get_offer_by_id(offer_id)
            if low <= offer.price <= high:
                s += offer.amount
            else:
                break
        return s

    def cancel_unattractive_orders(self, market_price):
        """Cancel orders that have prices with unrealistic prices."""
        high = market_price * (1 + self.range / 2)
        low = market_price * (1 - self.range / 2)
        n_canceled = 0
        for order in self.raidex_node.order_tasks_by_id.values():
            if order.price < low or order.price > high:
                order.cancel()
                n_canceled += 1
        left = self.raidex_node.open_orders
        self.log.info('canceled unattractive orders', n=n_canceled, left=left)

    def _run(self):
        while True:
            price = self.raidex_node.market_price() or self.initial_price
            # self.cancel_unattractive_orders(price)  # untested yet
            check_points_sell, check_points_buy = self.calc_checkpoints(price)
            check_point_diff = check_points_sell[1] - check_points_sell[0]
            orders = []
            additional_offers = {OfferType.BUY: 0, OfferType.SELL: 0}
            for type_, cp in chain(zip(repeat(OfferType.BUY), check_points_buy),
                                   zip(repeat(OfferType.SELL), check_points_sell)):
                offered = self.integrate_offers_until(price, cp) + additional_offers[type_]
                target = self.calc_target_amount(price, cp)
                if offered < target:
                    amount = int(round(target * (1 + self.overshoot) - offered))
                    order_price = cp + check_point_diff / 2 * (1 if type_ is OfferType.BUY else -1)
                    assert abs(price - order_price) < abs(price - cp)
                    assert 1 - self.range / 2 <= order_price / price <= 1 + self.range / 2
                    orders.append((type_, amount, order_price))
                    additional_offers[type_] += amount
            buys = len([o for o in orders if o[0] is OfferType.BUY])
            sells = len(orders) - buys
            self.log.info('replenishing offers', buys=buys, sells=sells, market_price=price)
            for type_, amount, order_price in orders:
                assert ((type_ is OfferType.BUY and order_price < price) or
                        (type_ is OfferType.SELL and order_price > price))
                if amount > 0:
                    self.raidex_node.limit_order(type_, amount, order_price)
            sleep(5)
