

class OfferStateChange:

    __slots__ = [
        'offer_id',
    ]

    def __init__(self, offer_id):
        self.offer_id = offer_id


class OfferTimeoutEvent(OfferStateChange):

    __slots__ = [
        'timeout_date'
    ]

    def __init__(self, offer_id, timeout_date):
        super(OfferTimeoutEvent, self).__init__(offer_id)
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
