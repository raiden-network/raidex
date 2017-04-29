import argparse
from gevent.event import Event
from ethereum import slogging

from raidex_node.api.app import APIServer
from raidex.raidex_node.raidex_node import RaidexNode
from raidex.utils.mock import MockExchangeTask


slogging.configure(':DEBUG')


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()

    parser.add_argument('--mock', action='store_true', help='Spawns mock offers to simulate trading activity"')
    parser.add_argument("--api", action='store_true', help='Run the REST-API')
    parser.add_argument("--api-port", type=int, help='Specify the port for the api, default is 5002', default=5002)

    args = parser.parse_args()

    node = RaidexNode()
    node.start()

    if args.api:
        api = APIServer('', args.api_port, node)
        api.start()

    if args.mock:
        MockExchangeTask(10, node.commitment_service, node.message_broker, node.offer_book).start()

    stop_event.wait()  # runs forever


if __name__ == '__main__':
    main()
