from __future__ import print_function

import json
import requests
from gevent import Greenlet
from gevent import monkey
from gevent.queue import Queue

from message_broker import Listener
import raidex.messages as messages


monkey.patch_socket()


class MessageBroker(object):
    """Handles the communication with other nodes"""

    def __init__(self):
        pass

    def send(self, topic, message):
        """Sends a message to all listeners of the topic

        Args:
            topic (str): the topic you want the message been send to
            message (Union[str, messages.Signed]): the message to send

        """
        body = {'message': encode(message)}
        result = requests.post('http://localhost:5000/api/topics/{0}'.format(topic), json=body)
        return result.json()['data']

    def listen_on(self, topic, transform=None):
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
            r = requests.get('http://localhost:5000/api/topics/{0}'.format(topic), stream=True)
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
        self.send('broadcast', message)

    def listen_on_broadcast(self, transform=None):
        """Starts listening for new messages on broadcast

            Args:
                transform : A function that filters and transforms the message
                            should return None if not interested in the message, message will not be returned,
                            otherwise should return the message in a format as needed

            Returns:
                Listener: an object gathering all settings of this listener

                """
        return self.listen_on('broadcast', transform)

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
