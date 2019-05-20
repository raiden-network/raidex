
class StateChange:
    pass


class NewLimitOrderStateChange(StateChange):

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


class ProvenOfferStateChange:

    def __init__(self, proven_offer_message):
        self.proven_offer_message = proven_offer_message


class OfferPublishedStateChange:

    def __init__(self, offer):
        self.offer = offer


class PaymentFailedStateChange:

    def __init__(self, offer_id, response):
        self.offer_id = offer_id
        self.response = response


