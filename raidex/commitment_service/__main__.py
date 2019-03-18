import argparse

from gevent.event import Event
import structlog

from raidex.commitment_service.node import CommitmentService
from raidex.message_broker.client import MessageBrokerClient
from raidex.raidex_node.trader.client import TraderClient
from raidex.signing import Signer

structlog.configure()


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()
    parser.add_argument("--fee-rate", type=float, help='Specify how much percentage of the commitment amount will be '
                                                       'hold as a fee for a succesful trade', default=None)
    parser.add_argument("--broker-host", type=str, help='Specify the host for the message broker, default is localhost',
                        default='localhost')
    parser.add_argument("--broker-port", type=int, help='Specify the port for the message broker, default is 5000',
                        default=5000)
    parser.add_argument("--trader-host", type=str, help='Specify the host for the trader mock, default is localhost',
                        default='localhost')
    parser.add_argument("--trader-port", type=int, help='Specify the port for the trader mock, default is 5001',
                        default=5001)

    args = parser.parse_args()

    message_broker = MessageBrokerClient(host=args.broker_host, port=args.broker_port)
    commitment_service = CommitmentService.build_from_mock(message_broker, fee_rate=1)
    commitment_service.start()

    stop_event.wait()


if __name__ == '__main__':
    main()
