from raidex.messages import Envelope


class RaidexProtocol(object):
    """ Everything will be blocking for the time being, simplifying the success
        notifications
    """

    def __init__(self, address, transport, discovery, message_handler):
        self.transport = transport
        self.discovery = discovery  # use the raiden discovery
        self.message_handler = message_handler
        self.address = address

    def send(self, receiver_address, message):
        data = Envelope.envelop(message)
        # query the raiden discovery for the raiden endpoint
        host, port = self.discovery.get(receiver_address)
        port += 1  # use the raiden endpoint port + 1 (this is a convention we defined for now!)

        host_port = (host, port)
        try:
            self.transport.send(self.address, host_port, data)
        except Exception as e:
            # TODO log(e)
            return False
        return True

    def receive(self, data):
        # gets called by transport.receive()
        message = Envelope.open(data)
        self.message_handler.on_message(message)


class BroadcastProtocol(object):
    """
    Handles discovery and message encoding/decoding,
    connects to the transport to hand on the decoded messages to the receiver
    """

    def __init__(self, address, transport, message_handler):
        self.address = address
        self.transport = transport
        self.message_handler = message_handler

    def publish(self, topic, message):
        data = Envelope.envelop(message)
        self.transport.publish(self.address, topic, data)

    def receive(self, topic, data):
        message = Envelope.open(data)
        self.message_handler.on_message(message)
