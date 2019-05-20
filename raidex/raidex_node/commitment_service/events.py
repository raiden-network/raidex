class CommitmentServiceEvent:
    pass


class CommitEvent(CommitmentServiceEvent):

    def __init__(self, offer):
        self.offer = offer


class CommitmentProvedEvent(CommitmentServiceEvent):
    def __init__(self, offer):
        self.offer = offer
