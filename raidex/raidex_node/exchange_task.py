import gevent

from raidex import messages
from raidex.raidex_node.offer_book import Offer


class MakerExchangeTask(gevent.Greenlet):
    """
    Spawns and manages one offer & handles/initiates the acording commitment,
    when a taker is found, it executes the token swap and reports the execution

    """

    def __init__(self, offer, cs_address, commitment_amount):
        assert isinstance(offer, Offer)
        self.offer = offer

        # where should the commitment be made
        self.cs_address = cs_address

        # how much should be committed
        self.commitment_amount = commitment_amount

    def _run(self):
        pass


class TakerExchangeTask(gevent.Greenlet):
    """
    Tries to take a specific offer:
        matches
        it will first try to initiate a commitment at the `offer.commitment_service`
        when successful, it will initiate /coordinate the assetswap with the maker
    """

    def __init__(self, offer, maker_commitment_proof):
        assert isinstance(offer, Offer)
        self.offer = offer

        # we only want to engage in a trade if the maker also provided a viable commitment-proof
        # the cs_address can be retrieved out of the commitment-proof
        assert isinstance(maker_commitment_proof, messages.CommitmentProof)
        self.proof = maker_commitment_proof
        pass


    def _run(self):
        pass
