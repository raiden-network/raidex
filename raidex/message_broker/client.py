from __future__ import print_function

import json
import requests
from gevent import Greenlet
from gevent import monkey; monkey.patch_socket()
from gevent.queue import Queue

from ethereum.utils import encode_hex

from raidex.message_broker.message_broker import Listener
import raidex.messages as messages


class MessageBrokerClient(object):
    """Handles the communication with other nodes"""

    def __init__(self, host='localhost', port=5000):
        self.port = port
        self.host = host
        self.apiUrl = 'http://{}:{}/api'.format(host, port)

    def send(self, topic, message):
        # HACK, allow 'broadcast' as non-binary input, everything else should be
        # binary data/ decoded addresses
        if topic == 'broadcast':
            return self.broadcast(message)
        return self._send(encode_hex(topic), message)

    def _send(self, topic, message):
        """Sends a message to all listeners of the topic

        Args:
            topic (str): the topic you want the message been send to
            message (Union[str, messages.Signed]): the message to send

        """
        body = {'message': encode(message)}
        result = requests.post('{0}/topics/{1}'.format(self.apiUrl, topic), json=body)
        return result.json()['data']

    def listen_on(self, topic, transform=None):
        # HACK, allow 'broadcast' as non-binary input, everything else should be
        # binary data/ decoded addresses
        if topic == 'broadcast':
            return self.listen_on_broadcast(transform)
        return self._listen_on(encode_hex(topic), transform)

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
        message_queue_async = Queue()

        listener = Listener(topic, message_queue_async, transform)

        def run():
            r = requests.get('{0}/topics/{1}'.format(self.apiUrl, topic), stream=True)
            for line in r.iter_lines():
                # filter out keep-alive new lines
                if line:
                    decoded_line = line.decode('utf-8')
                    message = decode(json.loads(decoded_line)['data'])
                    if transform is not None:
                        message = transform(message)
                    if message is not None:
                        message_queue_async.put(message)
        Greenlet.spawn(run)

        return listener

    def broadcast(self, message):
        """Sends a message to all listeners of the special topic broadcast

            Args:
                message (Union[str, messages.Signed]): the message to send

        """
        self._send('broadcast', message)

    def listen_on_broadcast(self, transform=None):
        """Starts listening for new messages on broadcast

            Args:
                transform : A function that filters and transforms the message
                            should return None if not interested in the message, message will not be returned,
                            otherwise should return the message in a format as needed

            Returns:
                Listener: an object gathering all settings of this listener

                """
        return self._listen_on('broadcast', transform)

    def stop_listen(self, listener):
        raise NotImplementedError


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
