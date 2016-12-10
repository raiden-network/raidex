import pytest
import gevent

from rex.messages import Ping, Envelope
from rex.utils import DEFAULT_RAIDEX_PORT

def test_discovery(clients):
    for c in clients:
        assert (c.protocol.transport.host, c.protocol.transport.port - 1) == \
               c.protocol.discovery.get(c.address)


# XXX no production unit test!
# TODO: split into more fine_grained test units
def test_ping(clients):
    client1 = clients[0]
    client2 = clients[1]

    assert client2.protocol.transport == client1.protocol.transport.network.transports[('1', DEFAULT_RAIDEX_PORT)]

    sent = [dict()]
    received = [dict()]
    recv_counter = [0]
    sent_counter = [0]

    def store_receives(rex, host_port, data):
        recv_counter[0] += 1
        # assert isinstance(host_port, tuple)
        # host, port = host_port
        # assert host in '0123456789'.split()
        # assert port == DEFAULT_RAIDEX_PORT
        print rex, host_port, data
        received[0][rex] = {data: host_port}


    def store_sents(sender, host_port, data):
        sent_counter[0] += 1
        # assert isinstance(host_port, tuple)
        # host, port = host_port
        # assert host in '0123456789'.split()
        # assert port == DEFAULT_RAIDEX_PORT
        print sender, host_port, data
        sent[0][sender] = {data: host_port}

    # no ACKs yet, so tap the receiving end with a callback
    # register global (howsitcalled) callback to transport

    client1.protocol.transport.on_recv_cbs.append(store_receives)
    client1.protocol.transport.network.on_send_cbs.append(store_sents)
    assert store_receives in client2.protocol.transport.on_recv_cbs

    ping1 = Ping(1)
    ping1.sign(client1.private_key)


    client1.protocol.send(client2.address, ping1)
    gevent.sleep(3)

    assert sent_counter[0] == 1
    assert recv_counter[0] == 1

    # unpack
    received = received[0]
    sent = sent[0]

    assert len(received.keys()) == 1
    assert len(sent.keys()) == 1
    client1_host_port = (client1.protocol.transport.host, client1.protocol.transport.port)
    client2_host_port = (client2.protocol.transport.host, client2.protocol.transport.port)
    assert received[client2][Envelope.envelop(ping1)]== None # doesn't make sense to check for None here
    assert sent[client1][Envelope.envelop(ping1)] == client2_host_port

@pytest.skipif(True, reason="Not implemented yet")
def test_broadcast(clients, commitment_services):
    pass
