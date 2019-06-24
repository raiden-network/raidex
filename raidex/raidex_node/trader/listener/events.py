from raidex.utils import pex


class RaidenListenerEvent:
    pass


class ExpectInboundEvent(RaidenListenerEvent):

    def __init__(self, initiator, identifier):
        self.initiator = initiator
        self.identifier = identifier


# Events coming from Raiden
class RaidenEvent(RaidenListenerEvent):
    pass


class PaymentReceivedEvent(RaidenEvent):

    def __init__(self, initiator, amount, identifier):
        self.initiator = initiator
        self.amount = amount
        self.identifier = identifier

    @property
    def type(self):
        return self.__class__.__name__

    @property
    def identifier_tuple(self):
        return self.initiator, self.identifier

    def as_dict(self):
        return dict(amount=self.amount, initiator=self.initiator, identifier=self.identifier)

    def __repr__(self):
        return "{}<initiator={}, amount={}, identifier={}>".format(
            self.__class__.__name__,
            pex(self.initiator),
            self.amount,
            self.identifier,
        )