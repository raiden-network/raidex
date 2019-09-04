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


class MakeChannelEvent(TraderEvent):

    def __init__(self, partner_address, token_address, total_deposit):
        self.partner_address = partner_address
        self.token_address = token_address
        self.total_deposit = total_deposit


