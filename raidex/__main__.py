import argparse
from gevent.event import Event
from ethereum import slogging

from raidex_node.api.app import APIServer
from raidex.raidex_node.raidex_node import RaidexNode

slogging.configure(':DEBUG')


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()

    parser.add_argument('--mock', action='store_true', help='Spawns mock offers to simulate trading activity"')
    parser.add_argument("--api", action='store_true', help='Run the REST-API')
    parser.add_argument("--api-port", type=int, help='Specify the port for the api, default is 5002', default=5002)

    args = parser.parse_args()


    # only mock usage at the moment, so no further argumnts are provided to default constructor:
    node = RaidexNode.build_default_from_config(mock_trading_activity=args.mock)
    node.start()

    if args.api is True:
        api = APIServer('', args.api_port, node)
        api.start()

    stop_event.wait()  # runs forever


if __name__ == '__main__':
    main()
