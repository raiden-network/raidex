class Commitment(object):
    """
    Abstraction from the messages.Commitment
    Purpose: don't mix messaging logic with internal logic

    Expect that the `protocol.send()` takes an instance of Commitment and constructs the message by itself.
    On incoming messages, the protocol will use the `Commitment.from_message(msg)` to construct a Commitment

    Bottom line: don't worry about messages, but use this class instead!

    """

    def __init__(self, amount, offer_id, timeout, signature, sender):
        self.amount = amount
        self.offer = offer_id
        self.timeout = timeout
        self.sender = sender
        self.signature = signature

    @classmethod
    def from_message(cls, message):
        offer_id = message.offer_id
        timeout = message.timeout
        amount = message.amount
        signature = message.signature
        sender = message.sender

        return cls(amount, offer_id, timeout, signature, sender)


class SwapExecution(object):
    """
    Abstraction from the messages.SwapExecution
    Purpose: don't mix messaging logic with internal logic

    Expect that the `protocol.send()` takes an instance of SwapExecution and constructs the message by itself.
    On incoming messages, the protocol will use the `SwapExecution.from_message(msg)` to construct a SwapExecution

    Bottom line: don't worry about messages, but use this class instead!

    """

    def __init__(self, offer_id, timestamp, sender):
        self.offer_id = offer_id
        self.timestamp = timestamp
        self.sender = sender

    @classmethod
    def from_message(cls, message):
        offer_id = message.offer_id
        timestamp = message.timestamp
        sender = message.sender
        return cls(offer_id, timestamp, sender)


