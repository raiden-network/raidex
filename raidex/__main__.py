import argparse
import gevent
from gevent.event import Event
from ethereum import slogging

from raidex.raidex_node.api.app import APIServer
from raidex.raidex_node.raidex_node import RaidexNode
from raidex.raidex_node.bots import LiquidityProvider, RandomWalker

slogging.configure(':DEBUG')


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()

    parser.add_argument('--mock', action='store_true', help='Spawns mock offers to simulate trading activity"')
    parser.add_argument("--api", action='store_true', help='Run the REST-API')
    parser.add_argument("--api-port", type=int, help='Specify the port for the api, default is 5002', default=5002)
    parser.add_argument("--broker-host", type=str, help='Specify the host for the message broker, default is localhost',
                        default='localhost')
    parser.add_argument("--broker-port", type=int, help='Specify the port for the message broker, default is 5000',
                        default=5000)
    parser.add_argument("--trader-host", type=str, help='Specify the host for the trader mock, default is localhost',
                        default='localhost')
    parser.add_argument("--trader-port", type=int, help='Specify the port for the trader mock, default is 5001',
                        default=5001)
    parser.add_argument('--bots', action='store_true', help='Start a set of trading bots')

    args = parser.parse_args()

    node = RaidexNode.build_default_from_config(message_broker_host=args.broker_host,
                                                message_broker_port=args.broker_port, trader_host=args.trader_host,
                                                trader_port=args.trader_port, mock_trading_activity=args.mock)
    node.start()

    if args.api is True:
        api = APIServer('', args.api_port, node)
        api.start()

    if args.bots:
        initial_price = 100.
        liquidity_provider = LiquidityProvider(node, initial_price)
        random_walker = RandomWalker(node, initial_price)
        liquidity_provider.start()
        gevent.sleep(5)  # give liquidity provider head start
        random_walker.start()

    stop_event.wait()  # runs forever


if __name__ == '__main__':
    main()
