import random

import gevent
from exchange_task import MakerExchangeTask, TakerExchangeTask
from offer_book import OfferType, Offer
from raidex.utils import milliseconds


class OrderTask(gevent.Greenlet):
    """
    Spawns ExchangeTasks, in order to fill the user-initiated Order 'completely' (to be discussed)
    The OrderTask will first try to buy available Offers that match the market, desired price and don't exceed the amount.
    If the Order isn't filled after that, it will spawn MakerExchangeTasks to publish offers with a reversed asset_pair
    """

    def __init__(self, offer_book, type_, amount, price, address, commitment_service, message_broker, trader):
        self.offer_book = offer_book
        self.type_ = type_
        self.amount = amount
        self.price = price
        self.commitment_service = commitment_service
        self.message_broker = message_broker
        self.trader = trader
        self.tasks = []
        self.address = address
        gevent.Greenlet.__init__(self)

    def _run(self):
        bought = 0

        if self.type_ == OfferType.SELL:
            offers = reversed(list(self.offer_book.buys.values()))

        elif self.type_ == OfferType.BUY:
            offers = list(self.offer_book.sells.values())
        else:
            offers = []

        for offer in offers:
            if self.type_ is OfferType.SELL:
                if offer.price < self.price:
                    break
            elif self.type_ is OfferType.BUY:
                if offer.price > self.price:
                    break
            else:
                ValueError('Unknown OfferType')

            if bought + offer.amount > self.amount:
                continue

            bought += offer.amount
            task = TakerExchangeTask(offer, self.commitment_service, self.message_broker, self.trader)
            task.start()
            self.tasks.append(task)

        step = 2 * 10**18 # for ether
        while bought + step <= self.amount:
            bought += step
            offer = Offer(self.type_, step, int(self.price * step), random.randint(0, 1000000000),
                          milliseconds.time_plus(60))  # TODO generate better offer id
            task = MakerExchangeTask(offer, self.address, self.commitment_service, self.message_broker, self.trader)
            task.start()
            self.tasks.append(task)

        gevent.joinall(self.tasks)
