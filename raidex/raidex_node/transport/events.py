

class TransportEvent:
    pass


class SendMessageEvent(TransportEvent):

    def __init__(self, topic, message):
        self.topic = topic
        self.message = message


class BroadcastEvent(SendMessageEvent):

    def __init__(self, message):
        super(BroadcastEvent, self).__init__('broadcast', message)


class SendProvenCommitmentEvent(TransportEvent):

    def __init__(self, target, offer):
        self.target = target
        self.offer = offer

