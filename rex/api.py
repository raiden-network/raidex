#!/usr/bin/env python
from __future__ import print_function
from flask import jsonify, request, abort, make_response
from flask import send_file
from rex.client import OrderBook



class API(object):

    def __init__(self, client):
        self.client = client

    def get_order_book(self, asset_pair, count=None):
        assert isinstance(asset_pair, tuple)
        assert len(asset_pair) == 2

        orderbook = self.client.get_orderbook_by_asset_pair(asset_pair)
        assert isinstance(orderbook, OrderBook)
        bids = [dict(price=p, amount=a) for p, a in list(orderbook.bids)]
        asks = [dict(price=p, amount=a) for p, a in list(orderbook.asks)]
        return jsonify(dict(bids=bids, asks=asks))

    def get_trade_history(self, asset_pair, count):
        raise NotImplementedError

    def limit_order(self, asset_pair, type, num_tokens, price): # returns internal order_id
        raise NotImplementedError

    def market_order(self, asset_pair, type, num_tokens): # returns internal order_id
        raise NotImplementedError

    def get_order_status(self, asset_pair, order_id):
        raise NotImplementedError

    def cancel_order(self, asset_pair, order_id):
        raise NotImplementedError

    def get_available_assets(self):
        raise NotImplementedError
