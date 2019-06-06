from raidex.raidex_node.architecture.event_architecture import Processor
from raidex.raidex_node.transport.events import TransportEvent


class Transport(Processor):

    def __init__(self, message_broker_client, signer):
        super(Transport, self).__init__(TransportEvent)
        self.message_broker_client = message_broker_client
        self._sign = signer.sign

    def sign_message(self, message):
        self._sign(message)

    def send_message(self, send_message_event):
        self._send_message(send_message_event.target, send_message_event.message)

    def _send_message(self, target, message):
        self.message_broker_client.send(target, message)

