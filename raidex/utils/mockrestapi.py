#!flask/bin/python
import random
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from mock import gen_orderbook_dict, gen_orderhistory


app = Flask(__name__)
CORS(app)

# global to store the Orders from the WebUI
LIMIT_ORDERS = {}


@app.route('/api/<string:version>/markets/<string:market>/offers', methods=['GET'])
def get_offer_book(version, market):
    return jsonify({'data': gen_orderbook_dict()})


@app.route('/api/<string:version>/markets/<string:market>/trades', methods=['GET'])
def gen_order_history(version, market):
    return jsonify({'data': gen_orderhistory(10, 1000, 400, 0.1)})


@app.route('/api/<string:version>/markets/<string:market>/orders/limit', methods=['POST'])
def make_limit_order(version, market):
    if not request.json or not validate_order(request.json):
        abort(400)
    return jsonify({'data': save_limit_order(request.json)})


@app.route('/api/<string:version>/markets/<string:market>/orders/limit', methods=['GET'])
def get_limit_order(version, market):
    return jsonify({'data': query_limit_order()})


@app.route('/api/<string:version>/markets/<string:market>/orders/limit/<int:id>', methods=['DELETE'])
def cancel_limit_order(version, market, id):
    return jsonify({'data': cancel_order(id)})


def save_limit_order(limit_order):
    id_ = random.randint(1, 100000000)
    LIMIT_ORDERS[id_] = {'id': id_, 'price': limit_order['price'], 'amount': limit_order['amount'],
                         'type': limit_order['type'], 'filledAmount': 0}
    return id_


def query_limit_order():
    return [limit_order for limit_order in LIMIT_ORDERS.values()]


def cancel_order(id_):
    if id_ in LIMIT_ORDERS:
        del LIMIT_ORDERS[id_]
        return "success"


def validate_order(json):
    if {'type', 'amount', 'price'} <= set(json):
        return True
    else:
        return False


if __name__ == '__main__':
    app.run(port=5002, debug=True)