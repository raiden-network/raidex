from collections import namedtuple, defaultdict
from ethereum import slogging
from gevent.queue import Queue
from raidex.utils import pex

log = slogging.get_logger('message_broker.global')

Listener = namedtuple('Listener', 'topic message_queue_async transform')


class MessageBroker(object):

    def __init__(self):
        self.listeners = defaultdict(list)

    def send(self, topic, message):
        queues = self.listeners[topic]
        if not queues:
            log.debug('CODE: no listener waiting on topic {}'.format(pex(topic)))
        for listener in queues:
            topic, message_queue_async, transform = listener
            transformed_message = message
            if transform is not None:
                transformed_message = transform(transformed_message)
            if transformed_message is not None:
                log.debug('Sending message: msg={}, topic={}'.format(message, pex(topic)))
                message_queue_async.put(transformed_message)
        return True

    def listen_on(self, topic, transform=None):
        message_queue_async = Queue()
        listener = Listener(topic, message_queue_async, transform)
        self.listeners[topic].append(listener)
        return listener

    def broadcast(self, message):
        return self.send('broadcast', message)

    def listen_on_broadcast(self, transform=None):
        return self.listen_on('broadcast', transform)

    def stop_listen(self, listener):
        self.listeners[listener.topic].remove(listener)
