
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

    def __init__(self, address, protocol_cls, transport, message_handler):
        self.topics = set()  # dict with {topic: [messages]}
        broadcast_endpoint = None  # TODO

        self.protocol = protocol_cls(address, transport, message_handler)
        transport.protocol = self.protocol

    def add_topic(self, topic):
        self.topics.add(topic)

    def subscribe(self, topic):
        # TODO subscribe to topic on the server
        # self.add_topic(topic)
        pass

    def broadcast(self, topic, message):
        self.protocol.broadcast(topic, message)






