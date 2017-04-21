import json

from ethereum import slogging
from flask import Flask, jsonify, request, Response
from gevent.pywsgi import WSGIServer

from raidex.raidex_node.offer_book import OfferType
from raidex.raidex_node.trader.trader import Trader, EventListener, TransferReceivedEvent

log = slogging.get_logger('trader.server')


app = Flask(__name__)
trader = Trader()


@app.route('/api/expect', methods=['POST'])
def expect():
    type_ = OfferType(request.json.get('type'))
    base_amount = request.json.get('baseAmount')
    counter_amount = request.json.get('counterAmount')
    self_address = request.json.get('selfAddress')
    target_address = request.json.get('targetAddress')
    identifier = request.json.get('identifier')
    log.debug('expect trade: ', type_=type_, base_amount=base_amount, counter_amount=counter_amount,
              self_address=self_address, target_address=target_address, identifier=identifier)
    success_async = trader.expect_exchange_async(type_, base_amount, counter_amount, self_address, target_address,
                                                 identifier)
    success = success_async.get()
    return jsonify({'data': success})


@app.route('/api/exchange', methods=['POST'])
def exchange():
    type_ = OfferType(request.json.get('type'))
    base_amount = request.json.get('baseAmount')
    counter_amount = request.json.get('counterAmount')
    self_address = request.json.get('selfAddress')
    target_address = request.json.get('targetAddress')
    identifier = request.json.get('identifier')
    log.debug('execute trade: ', type_=type_, base_amount=base_amount, counter_amount=counter_amount,
              self_address=self_address, target_address=target_address, identifier=identifier)
    success_async = trader.exchange_async(type_, base_amount, counter_amount, self_address, target_address, identifier)
    success = success_async.get()
    return jsonify({'data': success})


@app.route('/api/transfer', methods=['POST'])
def transfer():
    self_address = request.json.get('selfAddress')
    target_address = request.json.get('targetAddress')
    amount = request.json.get('amount')
    identifier = request.json.get('identifier')
    log.debug('transfer: ', amount=amount, self_address=self_address, target_address=target_address, identifier=identifier)
    success = trader.transfer(self_address, target_address, amount, identifier)
    return jsonify({'data': success})


@app.route('/api/events/<string:address', methods=['GET'])
def events_for(address):

    listener = EventListener(trader, address)
    listener.start()

    def generate():
        while True:
            event = listener.get()
            yield json.dumps({'data': decode(event), 'type': get_typename_of(event)}) + '\n'

    def on_close():  # stop listener on closed connection
        # FIXME this gets called so that the Trader object doesn't save events for the address anymore, desired here?
        listener.stop()

    r = Response(generate(), content_type='application/x-json-stream')
    r.call_on_close(on_close)
    return r


def decode(event_object):
    if isinstance(event_object, TransferReceivedEvent):
        return dict(amount=event_object.amount, sender=event_object.sender, identifier=event_object.identifier)


def get_typename_of(event_object):
    return event_object.__class__.__name__


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


def main():
    slogging.configure(':DEBUG')
    WSGIServer(('', 5001), app).serve_forever()


if __name__ == '__main__':
    main()
