
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

    def __init__(self, protocol_cls, transport, message_handler):
        self.handler = message_handler
        self.topics = set()  # dict with {topic: [messages]}
        broadcast_endpoint = None  # TODO

        self.protocol = protocol_cls(self, transport, broadcast_endpoint)
        transport.protocol = self.protocol

    def add_topic(self, topic):
        self.topics.add(topic)

    def subscribe(self, topic):
        # TODO subscribe to topic on the server
        # self.add_topic(topic)
        pass

    def on_message(self, topic, message):
        #
        assert topic in self.topics
        # FIXME make 'on_' methods snake_case
        method = 'on_%s' % message.__class__.__name__.lower()

        # call the 'on_<message_type>' method from the message handler
        getattr(self.handler, method)(message)

    def broadcast(self, topic, message):
        self.protocol.send(topic, message)






