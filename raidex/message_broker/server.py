#!/usr/bin/python

'''This is the server component of a simple web chat client.'''

import json
from contextlib import contextmanager
from collections import defaultdict

from gevent.pywsgi import WSGIServer
from gevent import monkey; monkey.patch_all(),
from gevent import spawn_later
import bottle

# You *must* import the green version of zmq or things will
# block and nothing will work and you will be sad.
from zmq import green as zmq


# This lets us track how many clients are currently connected.
polling = 0

ctx = zmq.Context()
app = bottle.app()

pubsock = ctx.socket(zmq.PUB)
pubsock.bind('inproc://pub')


@app.route('/pub', method='POST')
def pub():
    '''The /pub endpoint accepts messages from clients and publishes them to
    pubsock (a ZMQ pub socket).'''
    global pubsock

    msg = bottle.request.json
    if verify(msg):
        pubsock.send_json(msg)
        return {'status': 'received'}
    else:
        return {'status': 'invalid'}


def verify(msg):
    return True


@contextmanager
def subcontext():
    '''This is a context manager that returns a ZMQ socket connected to the
    internal message bus.  It ensures that the socket is closed when it
    goes out of scope.'''

    subsock = ctx.socket(zmq.SUB)
    subsock.setsockopt(zmq.SUBSCRIBE, '')
    subsock.connect('inproc://pub')

    yield subsock

    subsock.close()


@contextmanager
def pollcounter():
    global polling
    polling += 1
    yield
    polling -= 1


def wait_for_message(rfile, timeout):
    '''Wait for a message on the message bus and return it to the
    client.'''

    with subcontext() as subsock:
        # This is like select.poll but understands ZMQ sockets as well as
        # any file-like object with a fileno() method.
        poll = zmq.Poller()
        poll.register(subsock, zmq.POLLIN)
        poll.register(rfile, zmq.POLLIN)

        events = dict(poll.poll(timeout))
        if not events:
            return

        # A POLLIN event on rfile indicates that the client
        # has disconnected.
        if rfile.fileno() in events:
            return

        # We only get this far is there's a message available on the bus.
        msg = subsock.recv_json()
        return msg


@app.route('/sub')
def sub():
    '''This is the endpoint for long poll clients.'''

    with pollcounter():
        # Make sure response will have the correct content type.
        bottle.response.content_type = 'application/json'

        # Allow cross-domain AJAX requests
        # (because polls will come in on an alternate port).
        bottle.response.headers['Access-Control-Allow-Origin'] = '*'

        # Because "rfile" is easier to write.
        rfile = bottle.request.environ['wsgi.input'].rfile
        while True:
            message = wait_for_message(rfile, 1000)
            if message:
                yield json.dumps(message) + '\n'
            else:
                pass


@app.route('/debug')
def debug():
    '''This lets us see how many /sub requests are active.'''
    bottle.response.content_type = 'text/plain'

    # Using yield because this makes it easier to add
    # additional output.
    yield('polling = %d\n' % polling)




class DummyBroadcastServer(object):
    """
    Based on the raiden.network.tansport.DummyNetwork
    Sends a message to every host (except the sending one)
    """

    on_send_cbs = []  # debugging

    def __init__(self):
        self.transports = dict()
        self.counter = 0
        self.subscriptions = defaultdict() # topic -> [host_port1, host_port2, ...]

        # TODO create topic messages for easier structuring/specification of topics
        # should include: serialisation/deserialisation like in messages.py

    def register(self, transport, host, port):
        """ Register a new node in the dummy network. """
        self.transports[(host, port)] = transport

    def subscribe(self, host_port, topic):
        assert isinstance(topic, str)
        subscriptions = self.subscriptions[topic]
        if host_port not in subscriptions:
            subscriptions.append(host_port)

    def unsubscribe(self, host_port, topic):
        subscriptions = self.subscriptions[topic]
        if host_port in subscriptions:
            subscriptions.remove(host_port)

    def track_send(self, sender, host_port, topic, bytes_):
        """ Register an attempt to send a packet. This method should be called
        everytime send() is used.
        """
        self.counter += 1
        for callback in self.on_send_cbs:
            callback(sender, host_port, topic, bytes_)

    def _send(self, sender, host_port, topic, bytes_):
        self.track_send(sender, host_port, topic, bytes_)
        receive_end = self.transports[host_port].receive
        # TODO modify Transport
        spawn_later(0.001, receive_end, topic, bytes_)

    def publish(self, sender, topic, bytes_):
        """
        Send the message to all subscribers to this topic
        send also to the original sender (if he is subcribed)
        this will serve as an indicator for the sender that the network got the message
        """
        # XXX should we require that the sender is also subscribed?
        subscribers = self.subscriptions[topic]
        for host_port in subscribers:
            self._send(sender, host_port, topic, bytes_)


class DummyBroadcastTransport():
    """
    Modifies the existing DummyTransport to support a 'topic' argument
    NOTE:
        there is no endpoint storing for now, since the broadcast network is
        not properly defined yet and only Dummy-Classes are used at the moment
    """

    network = DummyBroadcastServer()
    on_recv_cbs = []  # debugging

    def __init__(
            self,
            host,
            port,
            protocol=None):

        self.host = host
        self.port = port
        self.protocol = protocol

        self.network.register(self, host, port)

    def publish(self, sender, topic, bytes_):
        self.network.publish(sender, topic, bytes_)

    # overload incompatible 'send' method
    send = publish # TODO still needed?

    @classmethod
    def track_recv(cls, address, topic, data):
        for callback in cls.on_recv_cbs:
            callback(address, topic, data)

    def receive(self, topic, data):
        self.track_recv(self.protocol.rex, topic, data)
        self.protocol.receive(topic, data)


def main():
    WSGIServer(('', 8000), app).serve_forever()

if __name__ == "__main__":
    main()