from collections import namedtuple, defaultdict

import gevent
from gevent.event import AsyncResult
from gevent.queue import Queue

import structlog

from raidex.raidex_node.offer_book import OfferType
from raidex.raidex_node.listener_tasks import ListenerTask
from raidex.utils import timestamp, pex
from raidex.utils.gevent_helpers import make_async

log = structlog.get_logger('trader.client')
log_tglobal = structlog.get_logger('trader.global')


Listener = namedtuple('Listener', 'address event_queue_async transform')


class TransferReceivedEvent(object):

    def __init__(self, sender, amount, identifier):
        self.sender = sender
        self.amount = amount
        self.identifier = identifier

    @property
    def type(self):
        return self.__class__.__name__

    def as_dict(self):
        return dict(amount=self.amount, sender=self.sender, identifier=self.identifier)

    def __repr__(self):
        return "{}<sender={}, amount={}, identifier={}>".format(
            self.__class__.__name__,
            pex(self.sender),
            self.amount,
            pex(self.identifier),
        )


# TODO factor out, we don't really need the received timestamp,
class TransferReceipt(object):

    def __init__(self, sender, amount, identifier, received_timestamp):
        self.sender = sender
        self.amount = amount
        self.identifier = identifier
        self.timestamp = received_timestamp

    def __repr__(self):
        return "{}<sender={}, amount={}, identifier={}, timestamp={}>".format(
            self.__class__.__name__,
            pex(self.sender),
            self.amount,
            pex(self.identifier),
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

    def transfer(self, self_address, target_address, amount, identifier):
        transfer_received_event = TransferReceivedEvent(sender=self_address, amount=amount, identifier=identifier)
        # for this mock-implementation:
        # a transfer can only go through when a listener is found
        try:
            listeners = self.listeners[target_address]
        except KeyError:
            log_tglobal.debug('No listener found for incoming transfer: target_address={}>'.format(pex(target_address)))
            return False
        # NOTE: even if we don't raise a key error here, the 'transfer' will only properly go through,
        # when some TransferReceivedListener and a TraderClients BalanceUpdateTask is listening for the events
        # for that address
        #
        # In a non-Mocked scenario (with raiden) we expect to get a success notifcation, so we know if the transfer
        # went through or not
        for listener in listeners:
            address, event_queue_async, transform = listener
            event = transfer_received_event
            transformed_event = event
            if transform is not None:
                transformed_event = transform(transformed_event)
            if transformed_event is not None:
                event_queue_async.put(transformed_event)
        return True

    @make_async
    def transfer_async(self, self_address, target_address, amount, identifier):
        return self.transfer(self_address, target_address, amount, identifier)

    def listen_for_events(self, address, transform=None):
        event_queue_async = Queue()
        listener = Listener(address, event_queue_async, transform)
        self.listeners[address].append(listener)
        return listener

    def stop_listen(self, listener):
        listener_not_found = False
        if listener.address in self.listeners:
            listeners = self.listeners[listener.address]
            try:
                listeners.remove(listener)
            except ValueError:
                listener_not_found = True
        else:
            listener_not_found = True

        if listener_not_found is True:
            raise ValueError('Listener not found')


class TraderClientMock(object):
    trader = Trader()

    def __init__(self, address, commitment_balance=10, trader=None):
        assert isinstance(address, str)
        self.address = address
        self.base_amount = 100
        self.counter_amount = 100
        self.commitment_balance = commitment_balance
        if trader is not None:
            self.trader = trader
        self._is_running = False

    def __repr__(self):
        return 'TraderClient<{}>'.format(pex(self.address), self.commitment_balance)

    @property
    def is_running(self):
        return self._is_running

    def start(self):
        if not self.is_running:
            BalanceUpdateTask(self).start()
            self._is_running = True

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

    def transfer(self, target_address, amount, identifier):
        # type: (str, (int, long), (int, long)) -> bool

        if not self.commitment_balance >= amount:
            # insufficient funds
            return False
        successful = self.trader.transfer(self.address, target_address, amount, identifier)
        if successful is True:
            self.commitment_balance -= amount
            log.debug('{} transferred {} to {} for pex(id): {}'.format(self, amount, pex(target_address), pex(identifier)))
        return successful

    @make_async
    def transfer_async(self, target_address, amount, identifier):
        # type: (str, int, int) -> AsyncResult
        return self.transfer(target_address, amount, identifier)

    def listen_for_events(self, transform=None):
        # comply with interface, just forward to singleton trader
        return self.trader.listen_for_events(self.address, transform)

    def stop_listen(self, listener):
        # comply with interface, just forward to singleton trader
        self.trader.stop_listen(listener)


class EventListener(object):
    """Represents a listener currently listening for new event"""

    def __init__(self, trader_client):
        self.trader_client = trader_client
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
        """Starts listening for new events"""
        self.listener = self.trader_client.listen_for_events(self._transform)

    def stop(self):
        """Stops listening for new events"""
        if self.listener is not None:
            self.trader_client.stop_listen(self.listener)


class TransferReceivedListener(EventListener):

    def __init__(self, trader_client, sender=None):
        self.sender = sender
        super(TransferReceivedListener, self).__init__(trader_client)

    def _transform(self, event):
        if self.sender is not None:
            if event.sender != self.sender:
                return None
        if isinstance(event, TransferReceivedEvent):
            # transform event into receipt, with additional timestamp
            receipt = TransferReceipt(event.sender, event.amount, event.identifier, timestamp.time())
            return receipt
        else:
            return None


class BalanceUpdateTask(ListenerTask):

    def __init__(self, trader_client):
        self.trader_client = trader_client
        super(BalanceUpdateTask, self).__init__(TransferReceivedListener(trader_client))

    def process(self, data):
        transfer_receipt = data
        self.trader_client.commitment_balance += transfer_receipt.amount
