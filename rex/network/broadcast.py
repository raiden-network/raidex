from collections import defaultdict

class BroadcastClient(object):
    """
    listenes to and publishes to the pubsub network layer.
    The Broadcast class will:

        - listen for Offers, CSAs on the PubSub network layer
        - post Offers to the PubSub (Client, Taker)
        - post CSAs, SwapComplete to the PubSub (CS)

        - fill/update the OrderBooks on new or expired/completed offers
        - fill the CommitmentManager with CSes on CSAs

        - manage/update the Subscribed Topics when new assets are added etc
        - XXX note: when a new topic is freshly subscribed to it takes some
            time to fill the broadcast buffer with enough information to be 'usable'

    for now:
        keeps the whole broadcast in it's history

    """

    def __init__(self, protocol_cls, transport):
        raise NotImplementedError  # not finished yet

        self.msgs_by_topic = dict() # dict with {topic: [messages]}
        # define data structure, maybe a deque
        broadcast_endpoint = None  # TODO
        self.protocol = protocol_cls(self, transport, broadcast_endpoint)
        transport.protocol =  self.protocol

    @classmethod
    def from_previous_state(cls, protocol_cls, transport, state):
        cls(protocol, transport)
        # filter messages by topic
        # fill data from state
        # state can be a superset of all message
        # eventually used for mock data or a saved state

    def add_topic(self, topic):
        if topic not in self.msgs_by_topic:
            self.msgs_by_topic[topic] = []

    def on_receive(self, topic, message):
        # queue the message
        self.msgs_by_topic[topic].put(message)

    def broadcast(self, topic, message):
        self.protocol.send(topic, message)


class DummyBroadcastNetwork(object):
    """
    Based on the raiden.network.tansport.DummyNetwork
    Sends a message to every host (except the sending one)
    """

    on_send_cbs = []  # debugging

    def __init__(self):
        self.transports = dict()
        self.counter = 0
        self.subscriptions = defaultdict() # topic -> [host_port1, host_port2, ...]

        # TODO create topic messages for easier structuring/specification of topics
        # should include: serialisation/deserialisation like in messages.py

    def register(self, transport, host, port):
        """ Register a new node in the dummy network. """
        assert isinstance(transport, DummyTransport)
        self.transports[(host, port)] = transport

    def subscribe(self, host_port, topic):
        assert isinstance(topic, str)
        subscriptions = self.subscriptions[topic]
        if host_port not in subscriptions:
            subscriptions.append(host_port)

    def unsubscribe(self, host_port, topic):
        subscriptions = self.subscriptions[topic]
        if host_port in subscriptions:
            subscriptions.remove(host_port)

    def track_send(self, sender, host_port, topic, bytes_):
        """ Register an attempt to send a packet. This method should be called
        everytime send() is used.
        """
        self.counter += 1
        for callback in self.on_send_cbs:
            callback(sender, host_port, topic, bytes_)

    def _send(self, sender, host_port, topic, bytes_):
        self.track_send(sender, host_port, topic, bytes_)
        receive_end = self.transports[host_port].receive
        # TODO modify Transport
        gevent.spawn_later(0.00000000001, receive_end, topic, bytes_)

    def publish(self, sender, topic, bytes_):
        """
        Send the message to all subscribers to this topic
        send also to the original sender (if he is subcribed)
        this will serve as an indicator for the sender that the network got the message
        """
        # XXX should we require that the sender is also subscribed?
        subscribers = self.subscriptions[topic]
        for host_port in subscribers:
            self._send(sender, host_port, topic, bytes_)
