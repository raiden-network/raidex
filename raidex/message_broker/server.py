#!/usr/bin/env python

from gevent import monkey; monkey.patch_all()

import json

from flask import Flask, jsonify, request, Response
from gevent.pywsgi import WSGIServer

from eth_utils import decode_hex
from raidex.message_broker.message_broker import MessageBroker
from raidex.message_broker.listeners import MessageListener

import structlog

log = structlog.get_logger('message_broker.server')

app = Flask(__name__)
message_broker = MessageBroker()

nof_listeners = 0


@app.route('/api/topics/<string:topic>', methods=['GET'])
def messages_for(topic):
    global nof_listeners

    listener = MessageListener(message_broker, topic)
    listener.start()

    def generate():
        while True:
            yield json.dumps({'data': listener.get()}) + '\n'

    def on_close():  # stop listener on closed connection
        global nof_listeners
        nof_listeners -= 1
        print('Nof-listeners: {}'.format(nof_listeners))
        listener.stop()

    r = Response(generate(), content_type='application/x-json-stream')
    nof_listeners += 1
    print('Nof-listeners: {} new for topic: {}'.format(nof_listeners, topic))
    r.call_on_close(on_close)
    return r


@app.route('/api/topics/<string:topic>', methods=['POST'])
def send_message(topic):

    message = request.json.get('message')
    status = message_broker.send(topic, message)
    return jsonify({'data': status})


def make_error_obj(status_code, message):
    return {
        'status': status_code,
        'message': message,
    }


def make_error(status_code, message):
    response = jsonify(make_error_obj(status_code, message))
    response.status_code = status_code
    return response


@app.errorhandler(404)
def not_found(error):
    return make_error(404, 'The resource was not found on the server: ' + str(error))


@app.errorhandler(500)
def internal_error(error):
    return make_error(500,
                      'The server encountered an internal error and was unable to complete your request: ' + str(error))

if __name__ == '__main__':
    http_server = WSGIServer(('', 5000), app)
    http_server.serve_forever()
