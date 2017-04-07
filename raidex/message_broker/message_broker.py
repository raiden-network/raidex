from collections import namedtuple, defaultdict

from gevent.queue import Queue

Listener = namedtuple('Listener', 'topic message_queue_async transform')


class MessageBroker(object):

    def __init__(self):
        self.listeners = defaultdict(list)

    def send(self, topic, message):
        for listener in self.listeners[topic]:
            topic, message_queue_async, transform = listener
            if transform is not None:
                data = transform(message)
                if data is not None:
                    message_queue_async.put(data)
            else:
                message_queue_async.put(message)
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
