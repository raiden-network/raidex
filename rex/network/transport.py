from raiden.network.transport import *

from rex.network.broadcast import DummyBroadcastNetwork


# module wrapper around the raiden.network.transport module
# imports all classes etc. and makes them available under the rex namespace

# NOTE: this is done solely for the purpose to make it futureproof once it gets
# refactored, extended or monkey_patched later


class DummyBroadcastTransport(DummyTransport):
    """
    Modifies the existing DummyTransport to support a 'topic' argument
    NOTE:
        there is no endpoint storing for now, since the broadcast network is
        not properly defined yet and only Dummy-Classes are used at the moment
    """

    network = DummyBroadcastNetwork()


    def publish(self, sender, topic, bytes_):
        self.network.publish(sender, topic, bytes_)

    # overload incompatible 'send' method
    send = publish

    @classmethod
    def track_recv(cls, rex, topic, data):
        for callback in cls.on_recv_cbs:
            callback(rex, topic, data)

    def receive(self, topic, data):
        self.track_recv(self.protocol.rex, topic, data)
        self.protocol.receive(topic, data)
