import argparse
import gevent
from gevent.event import Event
from ethereum import slogging

from raidex.raidex_node.api.app import APIServer
from raidex.raidex_node.raidex_node import RaidexNode
from raidex.raidex_node.trader.trader import Trader
from raidex.message_broker.message_broker import MessageBroker
from raidex.commitment_service.node import CommitmentService
from raidex.raidex_node.bots import LiquidityProvider, RandomWalker, Manipulator

slogging.configure(':WARNING,bots.manipulator:DEBUG')


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()

    parser.add_argument('--mock-networking', action='store_true',
                        help='In-Process Trader, MessageBroker and CommitmentService')
    parser.add_argument('--mock', action='store_true', help='Spawns mock offers to simulate trading activity"')
    parser.add_argument('--seed', type=str, default='raidex-node', help='Use the sha3 privkey from seed')
    parser.add_argument("--api", action='store_true', help='Run the REST-API')
    parser.add_argument("--api-port", type=int, help='Specify the port for the api, default is 5002', default=5002)
    parser.add_argument("--offer-lifetime", type=int, help='Lifetime of offers spawned by LimitOrders', default=10)
    parser.add_argument("--broker-host", type=str, help='Specify the host for the message broker, default is localhost',
                        default='localhost')
    parser.add_argument("--broker-port", type=int, help='Specify the port for the message broker, default is 5000',
                        default=5000)
    parser.add_argument("--trader-host", type=str, help='Specify the host for the trader mock, default is localhost',
                        default='localhost')
    parser.add_argument("--trader-port", type=int, help='Specify the port for the trader mock, default is 5001',
                        default=5001)
    parser.add_argument('--bots', nargs='+', help='Start a set of (/subset of) multiple trading bots.\
                                                  <Options:\"liquidity\", \"random\", \"manipulator\">')

    args = parser.parse_args()

    if args.mock_networking is True:
        message_broker = MessageBroker()
        trader = Trader()
        commitment_service = CommitmentService.build_from_mock('commitment_service', message_broker, trader)
        node = RaidexNode.build_from_mocks(message_broker, trader, commitment_service.address, privkey_seed=args.seed,
                                           offer_lifetime=args.offer_lifetime)
        commitment_service.start()
    else:
        node = RaidexNode.build_default_from_config(privkey_seed=args.seed,
                                                    message_broker_host=args.broker_host,
                                                    message_broker_port=args.broker_port, trader_host=args.trader_host,
                                                    trader_port=args.trader_port, mock_trading_activity=args.mock,
                                                    offer_lifetime=args.offer_lifetime)

    node.start()

    if args.api is True:
        api = APIServer('', args.api_port, node)
        api.start()

    bots = args.bots
    if bots:
        initial_price = 100.

        if 'liquidity' in bots:
            liquidity_provider = LiquidityProvider(node, initial_price)
            liquidity_provider.start()
        if 'random' in bots:
            gevent.sleep(5)  # give liquidity provider head start
            random_walker = RandomWalker(node, initial_price)
            random_walker.start()
        if 'maniplulator' in bots:
            if 'random' not in bots:
                gevent.sleep(5)  # give liquidity provider head start
            manipulator = Manipulator(node, initial_price)
            manipulator.start()

    stop_event.wait()  # runs forever


if __name__ == '__main__':
    main()
