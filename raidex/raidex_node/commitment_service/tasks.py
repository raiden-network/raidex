from ethereum import slogging

from raidex import messages
from raidex.raidex_node.listener_tasks import ListenerTask
from raidex.tests.utils import float_isclose


log = slogging.get_logger('node.commitment_service')


class CommitmentProofTask(ListenerTask):
    def __init__(self, commitment_proofs_dict, commitment_proof_listener):
        self.commitment_proofs = commitment_proofs_dict
        super(CommitmentProofTask, self).__init__(commitment_proof_listener)

    def process(self, data):
        commitment_proof = data
        log.debug('Received commitment proof {}'.format(commitment_proof))
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

    def __init__(self, cs_address, fee_rate, commitments_dict, commitment_proofs_dict,
                 transfer_received_listener):
        self.commitments = commitments_dict
        self.commitment_proofs = commitment_proofs_dict
        self.transfer_received_listener = transfer_received_listener
        self.commitment_service_address = cs_address
        self.fee_rate = fee_rate
        super(RefundReceivedTask, self).__init__(transfer_received_listener)

    def process(self, data):
        receipt = data
        try:
            commitment = self.commitments[receipt.identifier]
        except KeyError:
            # we're not waiting for this refund
            log.debug("Received unexpected Refund: {}".format(receipt))
            return
        # assert internals
        assert receipt.identifier == commitment.offer_id
        if not receipt.sender == self.commitment_service_address:
            log.debug("Received expected refund-id from unexpected sender")
            # do nothing and keep the money
            return

        commitment_minus_fee = commitment.amount - commitment.amount * self.fee_rate
        if not float_isclose(commitment.amount, receipt.amount) or float_isclose(receipt.amount, commitment_minus_fee):
            log.debug("Received refund that didn't match expected amount")
            # if the refund doesn't comply with the expected amount, do nothing and keep the money
            return

        async_result = self.commitment_proofs.get(commitment.signature)
        if async_result:
            async_result.set(None)
            log.debug("Refund received: {}".format(receipt))

            del self.commitments[receipt.identifier]