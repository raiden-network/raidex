#!/usr/bin/python

'''This is the server component of a simple web chat client.'''

import json
from contextlib import contextmanager

from gevent.pywsgi import WSGIServer
from gevent import monkey
import bottle

# You *must* import the green version of zmq or things will
# block and nothing we will work and you will be sad.
from zmq import green as zmq

monkey.patch_all()
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

        events = dict(poll.poll())
        # events = dict(poll.poll(timeout))
        # if not events:
        #     return

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


@app.route('/debug')
def debug():
    '''This lets us see how many /sub requests are active.'''
    bottle.response.content_type = 'text/plain'

    # Using yield because this makes it easier to add
    # additional output.
    yield('polling = %d\n' % polling)

if __name__ == "__main__":
    WSGIServer(('', 8000), app).serve_forever()
