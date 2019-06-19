class CommitmentServiceEvent:
    def __init__(self, offer):
        self.offer = offer


class CommitEvent(CommitmentServiceEvent):
    pass


class CommitmentProvedEvent(CommitmentServiceEvent):
    pass


class ReceivedInboundEvent(CommitmentServiceEvent):
    def __init__(self, offer, raiden_event):
        super(ReceivedInboundEvent, self).__init__(offer)
        self.raiden_event = raiden_event


class CancellationRequestEvent(CommitmentServiceEvent):
    pass
