import argparse
import gevent
from gevent.pywsgi import WSGIServer

import raidex.raidex_node.api.v0_1 as raidex_api_v_0_1
from raidex.raidex_node.market import TokenPair
from raidex.raidex_node.raidex_service import Raidex, ASSETS
from raidex.message_broker.server import app as message_app
from raidex.raidex_node.raidex_service import app as node_app
from raidex.utils.mock import MockExchangeTask


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    parser_mock = subparsers.add_parser('mock', help='Spawns mock offers to simulate trading activity"')
    parser_mock.set_defaults(mock=True)

    parser.add_argument("--api", action="store_true", help="Run the REST-API on port 5001")
    args = parser.parse_args()

    node = Raidex(token_pair=TokenPair(ASSETS[0], ASSETS[1]))

    if args.api:
        # build blueprints for desired rest versions:
        bbp_v0_1 = raidex_api_v_0_1.build_blueprint(node)
        node_app.register_blueprint(bbp_v0_1)

        # run the rest-server
        rest_server = WSGIServer(('', 5001), node_app)
        rest_server.start()

    if args.mock:
        message_broker_server = WSGIServer(('', 5000), message_app)
        message_broker_server.start()
        MockExchangeTask(10, node.commitment_service, node.message_broker, node.offer_book).start()

    node.start()
    while True:
        gevent.sleep(0.01)


if __name__ == '__main__':
    main()
