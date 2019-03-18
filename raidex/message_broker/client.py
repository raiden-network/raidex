from __future__ import print_function
import structlog
import json
import requests
import gevent
from gevent import monkey
from gevent.queue import Queue
from raidex.utils.address import encode_topic, decode_topic

from raidex.message_broker.message_broker import Listener
import raidex.messages as messages

monkey.patch_socket()
log = structlog.get_logger("TOPIC")


class StreamingRequestIterator(object):

    def __init__(self, response):
        self.response = response
        self._line_generator = response.iter_lines()
        self.closed = False

    def __next__(self):
        if self.closed is False:
            return next(self._line_generator)
        if self.closed is True:
            self.response.close()
            raise StopIteration

    def next(self):
        return self.__next__()

    def __iter__(self):
        return self

    # FIXME
    def close(self):
        self.closed = True


def iter_streaming_response(response):
    return StreamingRequestIterator(response)


class StreamingRequestTask(gevent.Greenlet):

    def __init__(self, api_url, topic, transform_func=None):
        self.listeners = []
        self.api_url = api_url
        self.topic = topic
        self.transform = transform_func
        self.response_iter = None
        gevent.Greenlet.__init__(self)

    @property
    def has_listeners(self):
        return bool(self.listeners)

    def _run(self):
        # this initially blocks until something is sent on that topic
        response = requests.get('{0}/topics/{1}'.format(self.api_url, self.topic), stream=True)
        self.response_iter = iter_streaming_response(response)
        for line in self.response_iter:
            # filter out keep-alive new lines
            if line:
                decoded_line = line.decode('utf-8')
                message = decode(json.loads(decoded_line)['data'])
                for listener in self.listeners:
                    message_for_listener = message
                    if listener.transform is not None:
                        message_for_listener = listener.transform(message_for_listener)
                    if message_for_listener is not None:
                        listener.message_queue_async.put(message_for_listener)

    def create_listener(self, transform=None):
        message_queue_async = Queue()
        listener = Listener(self.topic, message_queue_async, transform)
        self.listeners.append(listener)
        return listener

    def stop_listen(self, listener):
        self.listeners.remove(listener)

    # FIXME this isn't working yet,
    # we want the server to notice the closed connection
    # and the _run generator loop of the response to raise a StopIteration
    def stop(self):
        if self.response_iter is not None:
            self.response_iter.close()
            self.response_iter = None


class MessageBrokerClient(object):
    """Handles the communication with other nodes"""

    def __init__(self, host='localhost', port=5000):
        self.port = port
        self.host = host
        self.apiUrl = 'http://{}:{}/api'.format(host, port)
        self.topic_task_map = {}
        self.listener_task_map = {}

    def send(self, topic, message):
        # HACK, allow 'broadcast' as non-binary input, everything else should be
        # binary data/ decoded addresses
        encoded_topic = encode_topic(topic)
        return self._send(encoded_topic, message)

    def _send(self, topic, message):
        """Sends a message to all listeners of the topic

        Args:
            topic (str): the topic you want the message been send to
            message (Union[str, messages.Signed]): the message to send

        """

        body = {'message': encode(message)}
        result = requests.post('{0}/topics/{1}'.format(self.apiUrl, topic), json=body)
        return result.json()

    def listen_on(self, topic, transform=None):
        # HACK, allow 'broadcast' as non-binary input, everything else should be
        # binary data/ decoded addresses
        topic = encode_topic(topic)

        return self._listen_on(topic, transform)

    def _listen_on(self, topic, transform=None):
        """Starts listening for new messages on this topic

        Args:
            topic (str): The topic you want to listen too
            transform : A function that filters and transforms the message
                        should return None if not interested in the message, message will not be returned,
                        otherwise should return the message in a format as needed

        Returns:
            Listener: an object gathering all settings of this listener

        """
        task = self.topic_task_map.get(topic)
        if task is None:
            task = StreamingRequestTask(self.apiUrl, topic, transform)
            self.topic_task_map[topic] = task
            task.start()

        listener = task.create_listener(transform)
        self.listener_task_map[listener] = task

        return listener

    def broadcast(self, message):
        """Sends a message to all listeners of the special topic broadcast

            Args:
                message (Union[str, messages.Signed]): the message to send

        """
        self._send('broadcast', message)

    def stop_listen(self, listener):
        task = self.listener_task_map.get(listener)
        if task is None:
            raise Exception('Listener not found')
        task.stop_listen(listener)
        del self.listener_task_map[listener]
        if not task.has_listeners:
            task.stop()


def encode(message):
    if isinstance(message, str):
        return message
    elif isinstance(message, messages.Signed):
        return messages.Envelope.envelop(message)
    else:
        raise Exception("not supported type")


def decode(message):
    try:
        message = messages.Envelope.open(message)
    except ValueError:
        pass
    return message
