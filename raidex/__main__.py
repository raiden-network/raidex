import argparse
import gevent
from gevent.event import Event
import structlog

from raidex.raidex_node.api.app import APIServer
from raidex.app import App
from raidex.message_broker.message_broker import MessageBroker
from raidex.commitment_service.node import CommitmentService
from raidex.raidex_node.bots import LiquidityProvider, RandomWalker, Manipulator

structlog.configure()
#':WARNING,bots.manipulator:DEBUG'

KOVAN_WETH_ADDRESS = '0xd0A1E359811322d97991E03f863a0C30C2cF029C'
CS_ADDRESS = '0xEDC5f296a70096EB49f55681237437cbd249217A'


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()

    parser.add_argument('--mock-networking', action='store_true',
                        help='In-Process Trader, MessageBroker and CommitmentService')
    parser.add_argument('--mock', action='store_true', help='Spawns mock offers to simulate trading activity"')
    parser.add_argument('--seed', type=str, default='raidex-node', help='Use the keccak privkey from seed')
    parser.add_argument('--keyfile', type=argparse.FileType('r'), help='path to keyfile')
    parser.add_argument('--pwfile', type=argparse.FileType('r'), help='path to pw')
    parser.add_argument("--api", action='store_true', help='Run the REST-API')
    parser.add_argument("--api-port", type=int, help='Specify the port for the api, default is 50001', default=50001)
    parser.add_argument("--offer-lifetime", type=int, help='Lifetime of offers spawned by LimitOrders', default=30)
    parser.add_argument("--broker-host", type=str, help='Specify the host for the message broker, default is localhost',
                        default='localhost')
    parser.add_argument("--broker-port", type=int, help='Specify the port for the message broker, default is 5000',
                        default=5000)
    parser.add_argument("--trader-host", type=str, help='Specify the host for the trader mock, default is localhost',
                        default='localhost')
    parser.add_argument("--trader-port", type=int, help='Specify the port for the trader mock, default is 5001',
                        default=5001)
    parser.add_argument('--bots', nargs='+', help='Start a set of (/subset of) multiple tradi'
                                                  'ng bots.\
                                                  <Options:\"liquidity\", \"random\", \"manipulator\">')
    parser.add_argument('--token-address', type=str, help='Token address of token to trade against WETH on kovan',
                        default='0x92276aD441CA1F3d8942d614a6c3c87592dd30bb')

    args = parser.parse_args()

    if args.mock_networking is True:
        message_broker = MessageBroker()
        commitment_service = CommitmentService.build_service(message_broker, fee_rate=1)
        raidex_app = App.build_from_mocks(message_broker,
                                          commitment_service.address,
                                          base_token_addr=args.token_address,
                                          quote_token_addr=KOVAN_WETH_ADDRESS,
                                          keyfile=args.keyfile,
                                          pw_file=args.pwfile,
                                          offer_lifetime=args.offer_lifetime)
        commitment_service.start()
    else:
        raidex_app = App.build_default_from_config(keyfile=args.keyfile,
                                                   pw_file=args.pwfile,
                                                   cs_address=CS_ADDRESS,
                                                   base_token_addr=args.token_address,
                                                   quote_token_addr=KOVAN_WETH_ADDRESS,
                                                   message_broker_host=args.broker_host,
                                                   message_broker_port=args.broker_port,
                                                   trader_host=args.trader_host,
                                                   trader_port=args.trader_port,
                                                   offer_lifetime=args.offer_lifetime)

    raidex_app.start()

    if args.api is True:
        api = APIServer('', args.api_port, raidex_app.raidex_node)
        api.start()

    bots = args.bots
    if bots:
        initial_price = 100.

        if 'liquidity' in bots:
            liquidity_provider = LiquidityProvider(raidex_app, initial_price)
            liquidity_provider.start()
        if 'random' in bots:
            gevent.sleep(5)  # give liquidity provider head start
            random_walker = RandomWalker(raidex_app, initial_price)
            random_walker.start()
        if 'maniplulator' in bots:
            if 'random' not in bots:
                gevent.sleep(5)  # give liquidity provider head start
            manipulator = Manipulator(raidex_app, initial_price)
            manipulator.start()

    stop_event.wait()  # runs forever


if __name__ == '__main__':
    main()
