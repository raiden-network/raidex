import structlog

from raidex import messages
from raidex.utils import pex
from raidex.raidex_node.listener_tasks import ListenerTask
from raidex.tests.utils import float_isclose


log = slogging.get_logger('node.commitment_service.tasks')


class CommitmentProofTask(ListenerTask):
    def __init__(self, commitment_proofs_dict, commitment_proof_listener):
        self.commitment_proofs = commitment_proofs_dict
        super(CommitmentProofTask, self).__init__(commitment_proof_listener)

    def process(self, data):
        commitment_proof = data
        log.debug('Received commitment proof: {}'.format(commitment_proof))
        assert isinstance(commitment_proof, messages.CommitmentProof)

        async_result = self.commitment_proofs.get(commitment_proof.commitment_sig)
        if async_result:
            async_result.set(commitment_proof)
        else:
            # we should be waiting on the commitment-proof!
            # assume non-malicious actors:
            # if we receive a proof we are not waiting on, there is something wrong
            log.debug('Received unexpected commitment proof {}'.format(commitment_proof))


class RefundReceivedTask(ListenerTask):

    def __init__(self, cs_address, fee_rate, maker_commitments_dict, taker_commitments_dict, commitment_proofs_dict,
                 transfer_received_listener):
        self.maker_commitments = maker_commitments_dict
        self.taker_commitments = taker_commitments_dict
        self.commitment_proofs = commitment_proofs_dict
        self.transfer_received_listener = transfer_received_listener
        self.commitment_service_address = cs_address
        self.fee_rate = fee_rate
        super(RefundReceivedTask, self).__init__(transfer_received_listener)

    def process(self, data):
        receipt = data
        taker_commitment = self.taker_commitments.get(receipt.identifier)
        maker_commtiment = self.maker_commitments.get(receipt.identifier)
        found = [commitment for commitment in [taker_commitment, maker_commtiment] if commitment is not None]
        if len(found) == 0:
            # we're not waiting for this refund
            log.debug("Received unexpected Refund: {}".format(receipt))
            return
        commitment = found.pop()

        # assert internals
        assert receipt.identifier == commitment.offer_id
        if not receipt.sender == self.commitment_service_address:
            log.debug("Received expected refund-id from unexpected sender")
            # do nothing and keep the money
            return

        commitment_minus_fee = commitment.amount - commitment.amount * self.fee_rate
        if not float_isclose(receipt.amount, commitment_minus_fee) and not float_isclose(commitment.amount, receipt.amount):
            print(commitment.amount, receipt.amount)
            log.debug("Received refund that didn't match expected amount")

        async_result = self.commitment_proofs.get(commitment.signature)
        if async_result:
            if async_result.ready():
                assert isinstance(async_result.get_nowait(), messages.CommitmentProof)
                log.debug("Refund received for pex(id) {} (proven): {}".format(pex(commitment.offer_id), receipt))
            else:
                log.debug("Refund received for pex(id) {} (unproven): {}".format(pex(commitment.offer_id), receipt))

            async_result.set(None)

            if isinstance(commitment, messages.MakerCommitment):
                del self.maker_commitments[receipt.identifier]
            if isinstance(commitment, messages.TakerCommitment):
                del self.taker_commitments[receipt.identifier]
