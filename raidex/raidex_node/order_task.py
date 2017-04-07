import random

import gevent
from gevent.event import AsyncResult
from ethereum import slogging

from exchange_task import MakerExchangeTask, TakerExchangeTask
from offer_book import OfferType, Offer
from raidex.utils import milliseconds

log = slogging.get_logger('node.order')


class LimitOrderTask(gevent.Greenlet):
    """
    Spawns ExchangeTasks, in order to fill the user-initiated Order 'completely' (to be discussed)
    The OrderTask will first try to buy available Offers that match the market, desired price and
    don't exceed the amount.
    If the Order isn't filled after that, it will spawn MakerExchangeTasks to publish offers with a reversed asset_pair
    """

    def __init__(self, offer_book, trades, type_, amount, price, address, commitment_service, message_broker, trader,
                 offer_size=2 * 10 ** 18,  # for ether
                 offer_lifetime=10):
        self.offer_book = offer_book
        self.trades = trades
        self.type_ = type_
        self.amount = amount
        self.price = price
        self.commitment_service = commitment_service
        self.message_broker = message_broker
        self.trader = trader
        self.running_exchange_tasks = []
        self.running_bundled_tasks = []
        self.address = address
        self.amount_traded = 0
        self.canceled = False
        self.offer_size = offer_size
        self.offer_lifetime = offer_lifetime
        self.done_async = AsyncResult()
        gevent.Greenlet.__init__(self)

    def _run(self):
        next_amount = self.amount
        while not self.canceled:
            # try to trade next_amount of tokens and add the bundled tasks to the running tasks
            if next_amount > 0:
                self.running_bundled_tasks += self._trade(next_amount)
            # get next bundle of finished tasks
            bundled_tasks = gevent.wait(self.running_bundled_tasks, count=1)
            assert len(bundled_tasks) == 1
            for bundled_task in bundled_tasks:
                next_amount = self._process_task_termination(bundled_task)
                if self.finished:
                    return True
        gevent.wait(self.running_exchange_tasks + self.running_bundled_tasks)  # wait for all tasks to finish
        return False

    def _process_task_termination(self, bundled_task):
        # type: (BundleTask) -> int
        # process the end of some tasks and updates the internals accordingly
        self.running_bundled_tasks.remove(bundled_task)
        tasks = bundled_task.get(block=False)
        not_traded = 0
        for exchange_task in tasks:
            self.running_exchange_tasks.remove(exchange_task)
            success = exchange_task.get(block=False)
            if success:
                self.amount_traded += exchange_task.amount
                assert self.amount_traded <= self.amount
                log.debug('Traded amount is ({}/{})'.format(self.amount_traded, self.amount))
            else:
                not_traded += exchange_task.amount
        return not_traded

    def _trade(self, amount):
        # type: (int) -> object
        # try to trade amount tokens
        log.debug('Try to trade {} tokens'.format(amount))
        amount_taken, bundle_takes = self._take_offers(amount)
        amount_made, bundle_makes = self._make_offers(amount - amount_taken)
        assert amount_taken + amount_made == amount
        return bundle_takes + bundle_makes

    def _take_offers(self, amount):
        # type: (int) -> object
        amount_open = 0
        bundle_tasks = []

        if self.type_ == OfferType.SELL:
            offers = list(reversed(list(self.offer_book.buys.values())))
        elif self.type_ == OfferType.BUY:
            offers = list(self.offer_book.sells.values())
        else:
            raise ValueError('Unknown OfferType')

        log.debug('Available offers: {}'.format(offers))

        for offer in offers:
            if self.type_ is OfferType.SELL:
                if offer.price < self.price:
                    break
            elif self.type_ is OfferType.BUY:
                if offer.price > self.price:
                    break
            else:
                ValueError('Unknown OfferType')

            if amount_open + offer.amount > amount:
                continue
            amount_open += offer.amount
            log.debug('Take offer of {} tokens'.format(offer.amount))
            bundle_task = BundleTask([self._take_offer(offer)])
            bundle_task.start()
            bundle_tasks.append(bundle_task)

        return amount_open, bundle_tasks

    def _make_offers(self, amount):
        # type: (int) -> object
        offer_size = self.offer_size
        amount_open = 0
        tasks = []
        while amount_open + offer_size <= amount:
            amount_open += offer_size
            log.debug('Make offer of {} tokens'.format(self.offer_size))
            tasks.append(self._make_offer(offer_size))
        offer_amount = amount - amount_open
        if offer_amount > 0:
            amount_open += offer_amount
            log.debug('Make offer of {} tokens'.format(offer_amount))
            tasks.append(self._make_offer(offer_amount))
        bundle_task = BundleTask(tasks)
        bundle_task.start()
        bundle_tasks = [bundle_task]
        return amount_open, bundle_tasks

    def _make_offer(self, amount):
        # type: (int) -> MakerExchangeTask
        offer = Offer(self.type_, amount, int(self.price * amount), random.randint(0, 1000000000),
                      milliseconds.time_plus(self.offer_lifetime))  # TODO generate better offer id
        task = MakerExchangeTask(offer, self.address, self.commitment_service, self.message_broker, self.trader)
        task.start()
        self.running_exchange_tasks.append(task)
        return task

    def _take_offer(self, offer):
        # type: (Offer) -> TakerExchangeTask
        self.offer_book.remove_offer(offer.offer_id)
        self.trades.add_pending(offer)
        task = TakerExchangeTask(offer, self.commitment_service, self.message_broker, self.trader)
        task.start()
        self.running_exchange_tasks.append(task)
        return task

    def cancel(self):
        self.canceled = True

    @property
    def number_open_trades(self):
        return len(self.running_exchange_tasks)

    @property
    def finished(self):
        return self.amount_traded == self.amount


class BundleTask(gevent.Greenlet):
    """Represents a list of tasks which termination should be processed at once"""

    def __init__(self, tasks):
        gevent.Greenlet.__init__(self)
        self.tasks = tasks

    def _run(self):
        gevent.wait(self.tasks)
        return self.tasks
