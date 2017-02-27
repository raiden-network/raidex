from gevent.event import AsyncResult

from raidex.raidex_node.offer_book import OfferType
from raidex.utils.gevent_helpers import make_async


class Trader(object):

    def __init__(self):
        self.expected = {}
        pass

    def expect_exchange_async(self, type_, base_amount, counter_amount, self_address, target_address, identifier):
        result_async = AsyncResult()
        key = hash(
            str(type_) + str(base_amount) + str(counter_amount) + str(target_address) + str(self_address) + str(
                identifier))
        self.expected[key] = (result_async, self)
        return result_async

    def exchange_async(self, type_, base_amount, counter_amount, self_address, target_address, identifier):
        result_async = AsyncResult()
        key = hash(str(type_) + str(base_amount) + str(counter_amount) + str(self_address) + str(target_address) + str(
            identifier))
        if key in self.expected:
            self.expected[key][0].set(True)
            result_async.set(True)
            del self.expected[key]
        else:
            result_async.set(False)
        return result_async


class TraderClient(object):
    """In memory mock for a trader client, which handles the actual asset swap"""

    trader = Trader()

    def __init__(self, address):
        self.address = address
        self.base_amount = 100
        self.counter_amount = 100
        pass

    @make_async
    def expect_exchange_async(self, type_, base_amount, counter_amount, target_address, identifier):
        trade_result_async = TraderClient.trader.expect_exchange_async(type_, base_amount, counter_amount, self.address,
                                                                       target_address, identifier)
        successful = trade_result_async.get()
        if successful:
            self.execute_exchange(OfferType.opposite(type_), base_amount, counter_amount)
        return successful

    @make_async
    def exchange_async(self, type_, base_amount, counter_amount, target_address, identifier):

        trade_result_async = TraderClient.trader.exchange_async(type_, base_amount, counter_amount, self.address,
                                                                target_address, identifier)

        successful = trade_result_async.get()
        if successful:
            self.execute_exchange(type_, base_amount, counter_amount)
        return successful

    def execute_exchange(self, type_, base_amount, counter_amount):
        if type_ == OfferType.SELL:
            self.base_amount -= base_amount
            self.counter_amount += counter_amount
        else:
            self.base_amount += base_amount
            self.counter_amount -= counter_amount
