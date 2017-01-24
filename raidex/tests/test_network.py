from collections import namedtuple

import pytest
import gevent

from raidex.utils import DEFAULT_RAIDEX_PORT
from raidex.network import DummyTransport
from raidex.messages import Ping, Envelope
from raidex.message_broker.server import DummyBroadcastTransport
from raidex.protocol import RaidexProtocol, BroadcastProtocol
from raidex.raidex_node.service import RaidexService


@pytest.fixture()
def clients(accounts, dummy_discovery):
    Raiden = namedtuple('Raiden', ['api'] )
    clients = []
    for i, acc in enumerate(accounts):
        host, port = '{}'.format(i), DEFAULT_RAIDEX_PORT
        dummy_transport = DummyTransport(host=host, port=port)
        raiden = Raiden(None) # only to satisfy the argument
        # TODO: create a DummyRaiden for easy client-CS interaction
        client = RaidexService(
            raiden,
            acc.privatekey,
            RaidexProtocol,
            dummy_transport,
            dummy_discovery,
            DummyBroadcastTransport(host, port),
            BroadcastProtocol
        )
        # emulate the raiden port-mapping here
        dummy_discovery.register(client.address, host, port - 1)
        clients.append(client)
    return clients


def test_discovery(clients):
    for c in clients:
        assert (c.protocol.transport.host, c.protocol.transport.port - 1) == \
               c.protocol.discovery.get(c.address)


def test_ping_pong(clients):
    client1 = clients[0]
    client2 = clients[1]

    assert client2.protocol.transport == client1.protocol.transport.network.transports[('1', DEFAULT_RAIDEX_PORT)]

    # circumvent absence of nonlocal in py2
    sent = [[]]
    received = [[]]
    recv_counter = [0]
    sent_counter = [0]

    def store_receives(address, host_port, data):
        dict_ = dict(address=address, host_port=host_port, data=data)
        received[0].append(dict_)
        recv_counter[0] += 1


    def store_sents(address, host_port, data):
        dict_ = dict(address=address, host_port=host_port, data=data)
        sent[0].append(dict_)
        sent_counter[0] += 1

    # no ACKs yet, so tap the receiving end with a callback

    client1.protocol.transport.on_recv_cbs.append(store_receives)
    client1.protocol.transport.network.on_send_cbs.append(store_sents)
    assert store_receives in client2.protocol.transport.on_recv_cbs

    ping1 = Ping(42342341)
    ping1 = ping1.sign(client1.private_key)

    client1.protocol.send(client2.address, ping1)
    gevent.sleep(1)

    # assert that ping + pong was sent, ping + pong was received
    assert sent_counter[0] == 2
    assert recv_counter[0] == 2

    # sent from client1
    ping_sent_dict = sent[0][0]
    # received by client2
    ping_received_dict = received[0][0]

    assert ping_sent_dict['data'] == ping_received_dict['data']

    # sent by client2
    pong_sent_dict = sent[0][1]
    # received by client1
    pong_received_dict = received[0][1]

    assert pong_sent_dict['data'] == pong_received_dict['data']

    raw_ping = Envelope.open(ping_received_dict['data'])
    raw_pong = Envelope.open(pong_received_dict['data'])
    assert raw_ping.nonce == raw_pong.nonce



