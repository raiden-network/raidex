import structlog

from raidex import messages
from raidex.raidex_node.listener_tasks import ListenerTask

from raidex.raidex_node.architecture.state_change import CommitmentProofStateChange, CancellationProofStateChange
from raidex.raidex_node.architecture.event_architecture import dispatch_state_changes
log = structlog.get_logger('node.commitment_service.tasks')


class CommitmentProofTask(ListenerTask):
    def __init__(self,commitment_proof_listener):
        super(CommitmentProofTask, self).__init__(commitment_proof_listener)

    def process(self, data):
        commitment_proof = data
        log.debug('Received commitment proof: {}'.format(commitment_proof))
        assert isinstance(commitment_proof, (messages.CommitmentProof, messages.CancellationProof))

        if isinstance(commitment_proof, messages.CommitmentProof):
            commitment_event = CommitmentProofStateChange(commitment_proof.commitment_sig, commitment_proof)
            dispatch_state_changes(commitment_event)

        else:

            cancellation_state_change = CancellationProofStateChange(commitment_proof)
            dispatch_state_changes(cancellation_state_change)

