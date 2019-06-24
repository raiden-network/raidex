class TraderEvent:
    pass


class TransferEvent(TraderEvent):

    def __init__(self, token, target, amount, identifier):
        self.token = token
        self.target = target
        self.amount = amount
        self.identifier = identifier


class SwapInitEvent(TraderEvent):

    def __init__(self, match):
        self.match = match



