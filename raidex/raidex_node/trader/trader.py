from collections import namedtuple, defaultdict

import gevent
from gevent.event import AsyncResult
from gevent.queue import Queue

from ethereum import slogging

from raidex.raidex_node.offer_book import OfferType
from raidex.utils import timestamp, pex
from raidex.utils.gevent_helpers import make_async

log = slogging.get_logger('trader.client')
log_tglobal = slogging.get_logger('trader.global')


Listener = namedtuple('Listener', 'address event_queue_async transform')


class TransferReceivedEvent(object):

    def __init__(self, sender, amount, identifier):
        self.sender = sender
        self.amount = amount
        self.identifier = identifier

    def __repr__(self):
        return "{}<sender={}, amount={}, identifier={}>".format(
            self.__class__.__name__,
            pex(self.sender),
            self.amount,
            self.identifier,
        )


class TransferReceipt(object):

    def __init__(self, sender, amount, identifier, timestamp):
        self.sender = sender
        self.amount = amount
        self.identifier = identifier
        self.timestamp = timestamp

    def __repr__(self):
        return "{}<sender={}, amount={}, identifier={}, timestamp={}>".format(
            self.__class__.__name__,
            pex(self.sender),
            self.amount,
            self.identifier,
            self.timestamp
        )


class Trader(object):

    def __init__(self):
        self.expected = {}
        self.listeners = defaultdict(list)  # address -> list(listeners)

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

    @make_async
    def transfer(self, self_address, target_address, amount, identifier):
        transfer_received_event = TransferReceivedEvent(sender=self_address, amount=amount, identifier=identifier)
        log_tglobal.debug('Incoming transfer: target_address={}, identifier={}>'.format(pex(target_address), identifier))
        # for this mock-implementation:
        # a transfer can only go through when a listener is found
        try:
            listeners = self.listeners[target_address]
        except KeyError:
            log_tglobal.debug('No listener found for incoming transfer: target_address={}>'.format(pex(target_address)))
            return False
        # even if we don't raise a key error here, the 'transfer' will only properly go through,
        # when a TransferReceivedListener (for CS-specific task) and the balance_update_loop is listening for the events
        for listener in listeners:
            address, event_queue_async, transform = listener
            event = transfer_received_event
            # FIXME: look at bernds commit, can be None
            if transform is not None:
                event = transform(event)
            if event is not None:
                log_tglobal.debug('Put event in Queue: <address={}, transform={}>'.format(pex(address), transform))
                event_queue_async.put(event)
        return True

    def listen_for_events(self, address, transform=None):
        # log_tglobal.debug('Listener registered: <address={}, transform={}>'.format(pex(address), transform))
        event_queue_async = Queue()
        #TODO address not needed in Listener
        listener = Listener(address, event_queue_async, transform)
        self.listeners[address].append(listener)
        return listener

    def stop_listen(self, listener):
        # checkme
        del self.listeners[listener.address]


class TraderClient(object):
    """In memory mock for a trader client, which handles the actual asset swap

    IMPORTANT:
    Do NOT access the `trader` member as a static member from inside this class:

        def some_function_inside_test_client(self):
            TraderClient.trader

    the `trader`-member can be set from the constructor to enable flexibility for testing and proper teardown!

        def some_function_inside_test_client(self):
            self.trader
    """

    # Singleton Mock-Trader, can be overwritten by providing the trader kwarg to the constructor
    trader = Trader()

    def __init__(self, address, commitment_balance=10, trader=None):
        assert isinstance(address, str)
        self.address = address
        self.base_amount = 100
        self.counter_amount = 100
        self.commitment_balance = commitment_balance
        if trader is not None:
            self.trader = trader

        # HACK update balances with another TransferReceivedListener
        # no dedicated task but rather a function that gets spawned
        def _balance_update_loop(this):
            balance_received_listener = TransferReceivedListener(this)
            balance_received_listener.start()
            while True:
                transfer_receipt = balance_received_listener.get()
                this.commitment_balance += transfer_receipt.amount

        gevent.spawn(_balance_update_loop, self)

    def __repr__(self):
        return 'TraderClient<{}>'.format(pex(self.address), self.commitment_balance)

    @make_async
    def expect_exchange_async(self, type_, base_amount, counter_amount, target_address, identifier):
        trade_result_async = self.trader.expect_exchange_async(type_, base_amount, counter_amount, self.address,
                                                               target_address, identifier)
        successful = trade_result_async.get()
        if successful:
            self.execute_exchange(OfferType.opposite(type_), base_amount, counter_amount)
        return successful

    @make_async
    def exchange_async(self, type_, base_amount, counter_amount, target_address, identifier):

        trade_result_async = self.trader.exchange_async(type_, base_amount, counter_amount, self.address,
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

    @make_async
    def transfer(self, target_address, amount, identifier):
        if not self.commitment_balance >= amount:
            # insufficient funds
            return False
        transfer_result_async = self.trader.transfer(self.address, target_address, amount, identifier)
        successful = transfer_result_async.get()
        if successful:
            self.commitment_balance -= amount
            log.debug('{} transferred {} to {} for identifier {}'.format(self, amount, pex(target_address), identifier))
        return successful

    def listen_for_events(self, transform=None):
        # comply with interface, just forward to singleton trader
        return self.trader.listen_for_events(self.address, transform)

    def stop_listen(self, listener):
        # comply with interface, just forward to singleton trader
        self.trader.stop_listen(listener)


class EventListener(object):
    """Represents a listener currently listening for new messages"""

    def __init__(self, trader):
        self.trader = trader
        self.listener = None

    def _transform(self, event):
        """Filters and transforms events

        Should be overwritten by subclasses

        Args:
            event: The event to filter and transform

        Returns: The transformed event or None if it should be filtered out

        """
        return event

    def get(self, *args, **kwargs):
        """Gets the next event or blocks until there is one

        can only be called after start()
        For parameters see gevents AsyncResult.get()
        """
        return self.listener.event_queue_async.get(*args, **kwargs)

    def get_once(self):
        """starts the listener, returns one value, and stops"""
        self.start()
        result = self.get()
        # self.stop() not fully implemented yet
        return result

    def start(self):
        """Starts listening for new messages"""
        self.listener = self.trader.listen_for_events(self._transform)

    def stop(self):
        """Stops listening for new messages"""
        if self.listener is not None:
            self.trader.stop_listen(self.listener)


class TransferReceivedListener(EventListener):

    def _transform(self, event):
        if isinstance(event, TransferReceivedEvent):
            # transform event into receipt, with additional timestamp
            receipt = TransferReceipt(event.sender, event.amount, event.identifier, timestamp.time())
            return receipt
        else:
            return None
