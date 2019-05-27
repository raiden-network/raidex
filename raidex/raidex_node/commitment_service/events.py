class CommitmentServiceEvent:
    pass


class CommitEvent(CommitmentServiceEvent):

    def __init__(self, offer):
        self.offer = offer


class CommitmentProvedEvent(CommitmentServiceEvent):
    def __init__(self, offer):
        self.offer = offer


class ReceivedInboundEvent(CommitmentServiceEvent):
    def __init__(self, offer, raiden_event):
        self.offer = offer
        self.raiden_event = raiden_event