from flask import Flask
from werkzeug.routing import BaseConverter

from raidex.client import ClientService, OfferBook, OfferManager
from raidex.api import API
from raidex.utils.mock import gen_orderbook_messages, ASSETS, ACCOUNTS


app = Flask(__name__)


class AssetPairConverter(BaseConverter):

    def to_python(self, value):
        pair = value.split('_')
        return tuple([asset.decode('hex') for asset in pair])

    def to_url(self, values):
        return '_'.join(BaseConverter.to_url(value)
                        for value in values)


def register_api_instance(app, api):
    app.add_url_rule('/api/orderbook/<assetpair:asset_pair>',
                     'get_order_book',
                     api.get_order_book,
                     methods=['GET'])
    app.add_url_rule('/api/orderbook/as_history/<assetpair:asset_pair>/<int:count>',
                     'get_trade_history',
                     api.get_trade_history,
                     methods=['GET'])
    app.add_url_rule('/api/order/limit/<assetpair:asset_pair>/<type>/<int:num_tokens>/<price>',
                     'limit_order',
                     api.limit_order,
                     methods=['POST'])
    app.add_url_rule('/api/order/market/<assetpair:asset_pair>/<type>/<int:num_tokens>/',
                     'market_order',
                     api.market_order,
                     methods=['POST'])
    app.add_url_rule('/api/order/<assetpair:asset_pair>/<order_id>',
                     'get_order_status',
                     api.get_order_status,
                     methods=['GET'])
    app.add_url_rule('/api/order/<assetpair:asset_pair>/<order_id>/',
                     'cancel_order',
                     api.cancel_order,
                     methods=['DEL'])
    app.add_url_rule('/api/assets/',
                     'get_available_assets',
                     api.get_available_assets,
                     methods=['GET'])


def register_type_converters(app):
    app.url_map.converters['assetpair'] = AssetPairConverter


if __name__ == '__main__':
    pair = (ASSETS[0], ASSETS[1])
    print ASSETS[0].encode('hex'), ASSETS[1].encode('hex')
    order_book = OfferBook(pair)
    messages = gen_orderbook_messages()
    order_ids = [order_book.insert_from_msg(msg) for msg in messages]
    order_manager = OfferManager()
    order_manager.add_offerbook(pair, order_book)
    client = ClientService(None, order_manager, None, None)
    api = API(client)
    register_type_converters(app)
    register_api_instance(app, api)
    app.run()  # XXX only for development purposes
    # TODO run as a gevent.wsgi.WSGIServer instead
