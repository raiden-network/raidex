from raidex.raidex_node.offer_book import OfferBookEntry


class EventIterator:

    def __init__(self, event):
        self.event = event
        self.iterated = False

    def __next__(self):
        if not self.iterated:
            self.iterated = True
            return self.event
        else:
            raise StopIteration


class StateChange:

    def __iter__(self):
        return EventIterator(self)


class NewLimitOrderStateChange(StateChange):

    def __init__(self, data):
        self.data = data


class CancelLimitOrderStateChange(StateChange):

    def __init__(self, data):
        self.data = data


class OfferStateChange(StateChange):

    def __init__(self, offer_id):
        self.offer_id = offer_id


class OfferTimeoutStateChange(OfferStateChange):

    def __init__(self, offer_id, timeout_date):
        super(OfferTimeoutStateChange, self).__init__(offer_id)
        self.timeout_date = timeout_date


class CommitmentProofStateChange(OfferStateChange):

    __slots__ = [
        'commitment_signature',
        'commitment_proof'
    ]

    def __init__(self, commitment_signature, commitment_proof):
        super(CommitmentProofStateChange, self).__init__(commitment_proof.offer_id)
        self.commitment_signature = commitment_signature
        self.commitment_proof = commitment_proof


class CancellationProofStateChange(OfferStateChange):

    def __init__(self, cancellation_proof):
        super(CancellationProofStateChange, self).__init__(cancellation_proof.offer_id)
        self.cancellation_proof = cancellation_proof


class TakerCallStateChange(StateChange):

    def __init__(self, offer_id, initiator, commitment_proof):
        self.offer_id = offer_id
        self.initiator = initiator
        self.commitment_proof = commitment_proof


class OfferPublishedStateChange(StateChange):

    def __init__(self, offer_entry: OfferBookEntry):
        self.offer_entry = offer_entry


class PaymentFailedStateChange(StateChange):

    def __init__(self, offer_id, response):
        self.offer_id = offer_id
        self.response = response


class TransferReceivedStateChange(StateChange):
    def __init__(self, raiden_event):
        self.raiden_event = raiden_event