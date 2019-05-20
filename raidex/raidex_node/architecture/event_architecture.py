from gevent.greenlet import Greenlet
from gevent.queue import Queue


class Processor:

    def __init__(self, event_types):
        self.event_types = event_types


class Consumer(Greenlet):
    __slots__ = [
        'consumer',
        'queue',
        'on_event'
    ]

    def __init__(self, queue: Queue, consumer: Processor, on_event):
        Greenlet.__init__(self)
        self.queue = queue
        self.consumer = consumer
        self.on_event = on_event

    def _run(self):
        while True:
            event = self.queue.get()
            print(f'EVENT: {event}, {self.__name__}')
            self.on_event(self.consumer, event)

    def get_types(self):
        return self.consumer.event_types


class Dispatch:

    consumer_tasks = list()

    @staticmethod
    def connect_consumer(consumer: Processor, handle_event):
        Dispatch.consumer_tasks.append(Consumer(Queue(), consumer, handle_event))

    @staticmethod
    def start_consumer_tasks():
        for consumer in Dispatch.consumer_tasks:
            consumer.start()


event_dispatch = Dispatch()
state_change_dispatch = Dispatch()


def dispatch_events(events):
    _dispatch(event_dispatch, events)


def dispatch_state_change(state_changes):
    _dispatch(state_change_dispatch, state_changes)


def _dispatch(handler, events):
    for state_change in events:
        for consumer in handler.consumer_tasks:
            if isinstance(state_change, consumer.get_types()):
                consumer.queue.put(state_change)




