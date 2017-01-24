import gevent


class DummyNetwork(object):
    """ Store global state for an in process network, this won't use a real
    network protocol just greenlet communication.
    """

    on_send_cbs = []  # debugging

    def __init__(self):
        self.transports = dict()
        self.counter = 0

    def register(self, transport, host, port):
        """ Register a new node in the dummy network. """
        assert isinstance(transport, DummyTransport)
        self.transports[(host, port)] = transport

    def track_send(self, sender_address, host_port, bytes_):
        """ Register an attempt to send a packet. This method should be called
        everytime send() is used.
        """
        self.counter += 1
        for callback in self.on_send_cbs:
            callback(sender_address, host_port, bytes_)

    def send(self, sender, host_port, bytes_):
        # 'sender' is a raiden address
        self.track_send(sender, host_port, bytes_)
        receive_end = self.transports[host_port].receive
        gevent.spawn_later(0.00000000001, receive_end, bytes_)


class DummyTransport(object):
    """ Communication between inter-process nodes.
    Copied and modified from raiden
    """
    network = DummyNetwork()
    on_recv_cbs = []  # debugging

    def __init__(
            self,
            host,
            port,
            protocol=None):

        self.host = host
        self.port = port
        self.protocol = protocol

        self.network.register(self, host, port)

    def send(self, sender, host_port, bytes_):
        self.network.send(sender, host_port, bytes_)

    @classmethod
    def track_recv(cls, address, host_port, data):
        for callback in cls.on_recv_cbs:
            callback(address, host_port, data)

    def receive(self, data, host_port=None):
        self.track_recv(self.protocol.address, host_port, data)
        self.protocol.receive(data)

    def stop(self):
        pass