from rex.messages import Envelope

class RexProtocol(object):
    """ Everything will be blocking for the time being, simplifying the success
        notifications
    """

    # rex is here ClientService or CommitmentService
    # XXX make shure that interface is the same

    def __init__(self, transport, discovery, rex):
        self.transport = transport
        self.discovery = discovery  # use the raiden discovery
        self.rex = rex
        self.raiden = self.rex  # make compatible with raiden.network.DummyTransport

    def send(self, receiver_address, message):
        data = Envelope.envelop(message)
        self._send(receiver_address, data)
        # return success

    def _send(self, receiver_address, data):
        host, port = self.discovery.get(receiver_address)
        port += 1  # use the raiden discovery port + 1
        # XXX is the self.rex argument a problem? look at raiden.transport interface
        host_port = (host, port)
        self.transport.send(self.rex, host_port, data)

    def receive(self, data):
        # gets called by transport.receive()
        message = Envelope.open(data)
        # XXX call some on_receive() ?
        return message


class BroadcastProtocol(object):
    """
    Handles discovery and message encoding/decoding,
    connectis to the transport to hand on the decoded messages to the receiver
    """

    def __init__(self, transport, discovery, rex):
        self.transport = transport
        self.rex = rex
        self.raiden = self.rex  # make compatible with raiden.network.DummyTransport

    def publish(self, topic, message):
        data = Envelope.envelop(message)
        self.transport.publish(self.rex, topic, data)
        # return success

    def receive(self, topic, data):
        message = Envelope.open(data)
        return topic, message
