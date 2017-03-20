#!flask/bin/python
from flask import Flask, jsonify
from flask_cors import CORS
from mock import gen_orderbook_dict, gen_orderhistory


app = Flask(__name__)
CORS(app)


@app.route('/api/<string:version>/markets/<string:market>/offers/', methods=['GET'])
def get_offer_book(version, market):
    return jsonify({'data': gen_orderbook_dict()})


@app.route('/api/<string:version>/markets/<string:market>/trades/', methods=['GET'])
def gen_order_history(version, market):
    return jsonify({'data': gen_orderhistory(10, 1000, 300, 0.1)})


if __name__ == '__main__':
    app.run(debug=True)