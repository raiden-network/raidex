import argparse

from gevent.event import Event
import structlog

from raidex.commitment_service.node import CommitmentService

structlog.configure()


def main():
    stop_event = Event()

    parser = argparse.ArgumentParser()
    parser.add_argument('--keyfile',  type=argparse.FileType('r'), help='path to keyfile', required=True)
    parser.add_argument('--pwfile', type=argparse.FileType('r'), help='path to pw', required=True)
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

    commitment_service = CommitmentService.build_service(keyfile=args.keyfile,
                                                         pw_file=args.pwfile,
                                                         message_broker_host=args.broker_host,
                                                         message_broker_port=args.broker_port,
                                                         trader_host=args.trader_host,
                                                         trader_port=args.trader_port,
                                                         fee_rate=0)
    commitment_service.start()

    stop_event.wait()


if __name__ == '__main__':
    main()
