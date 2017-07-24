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
        # DEBUGGING check - provide log output to easily check if an expected listener is not listening
        # this is not always harmful but can help debugging
        if not queues:
            log.debug('DEBUG-CODE: no listener waiting on topic {}, msg={}'.format(pex(topic), message))
            # XXX: in the mock implementation we know if someone is listening or not,
            # even if it's a broadcasting scheme but in real life we don't know that
            # TODO: use direct communication without message-broker later on
            return False
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
