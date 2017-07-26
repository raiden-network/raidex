import argparse

from gevent.event import Event
from ethereum import slogging

from raidex.commitment_service.node import CommitmentService
from raidex.message_broker.client import MessageBrokerClient
from raidex.raidex_node.trader.client import TraderClient
from raidex.signing import Signer

slogging.configure(':DEBUG')


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()
    parser.add_argument("--broker-host", type=str, help='Specify the host for the message broker, default is localhost',
                        default='localhost')
    parser.add_argument("--broker-port", type=int, help='Specify the port for the message broker, default is 5000',
                        default=5000)
    parser.add_argument("--trader-host", type=str, help='Specify the host for the trader mock, default is localhost',
                        default='localhost')
    parser.add_argument("--trader-port", type=int, help='Specify the port for the trader mock, default is 5001',
                        default=5001)

    args = parser.parse_args()

    signer = Signer.from_seed('test')
    commitment_service = CommitmentService(signer, MessageBrokerClient(host=args.broker_host, port=args.broker_port),
                                           TraderClient(signer.address, host=args.trader_host, port=args.trader_port),
                                           fee_rate=0.01)
    commitment_service.start()

    stop_event.wait()


if __name__ == '__main__':
    main()
