class third_party(object):

    def __init__(self, third_party_address, commitment_deposit):
        self.third_party_address = third_party_address
        self.commitment_deposit = commitment_deposit

    def transfer_listener():
        # When transfer received trigger method
        # send_back_signed_offer()

    def commitment_received():
        pass

    def setup_deposit():
        pass

    def redeem_deposit():
        pass

    def commit(id, timeout, depoit):
        pass

    def send_back_signed_offer():
        # sign offer and send it back to maker/taker

    def process_offer(offer):
        # get sender address from recovering signature of offer
        # wait for commitment to be received as a raiden transfer
        # When commitment is received, sign offer and send back to signee
