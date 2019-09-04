from flask import Blueprint
from raidex.raidex_node.api.v0_1.resources import Offers, LimitOrders, Trades, PriceChartBin, Channels
from raidex.raidex_node.api.v0_1.errors import bad_request, internal_error, not_found


def build_blueprint(raidex):

    blueprint = Blueprint('v01', __name__, url_prefix='/api/v01/markets/dummy')

    blueprint.add_url_rule('/trades', view_func=Trades.as_view('trades', raidex))
    blueprint.add_url_rule('/trades/price-chart', view_func=PriceChartBin.as_view('price_chart', raidex))
    blueprint.add_url_rule('/offers', view_func=Offers.as_view('offers', raidex))
    blueprint.add_url_rule('/orders/limit', view_func=LimitOrders.as_view('limit_orders', raidex), methods=['GET', 'POST'])
    blueprint.add_url_rule('/orders/limit/<int:order_id>', view_func=LimitOrders.as_view('limit_orders_id', raidex),
                           methods=['DELETE'])
    blueprint.add_url_rule('/channels', view_func=Channels.as_view('channels', raidex), methods=['GET'])

    blueprint.register_error_handler(400, bad_request)
    blueprint.register_error_handler(404, not_found)
    blueprint.register_error_handler(500, internal_error)

    return blueprint
