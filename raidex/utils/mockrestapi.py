#!flask/bin/python
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from mock import gen_orderbook_dict, gen_orderhistory, save_limit_order


app = Flask(__name__)
CORS(app)


@app.route('/api/<string:version>/markets/<string:market>/offers/', methods=['GET'])
def get_offer_book(version, market):
    return jsonify({'data': gen_orderbook_dict()})


@app.route('/api/<string:version>/markets/<string:market>/trades/', methods=['GET'])
def gen_order_history(version, market):
    return jsonify({'data': gen_orderhistory(10, 1000, 400, 0.1)})


@app.route('/api/<string:version>/markets/<string:market>/orders/limit', methods=['POST'])
def make_limit_order(version, market):
    if not request.json or not validate_order(request.json):
        abort(400)
    return jsonify({'data': save_limit_order(request.json)})


def validate_order(json):
    if {'type', 'amount', 'price'}  <= set(json):
        return True
    else:
        return False



if __name__ == '__main__':
    app.run(debug=True)