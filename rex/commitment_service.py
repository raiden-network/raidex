class CommitmentService(object):

    def __init__(self, cs_address):
        self.cs_address = cs_address

    commited_offers = dict()

    def transfer_listener():
        # When transfer received trigger method
        # send_back_signed_offer()
        pass

    def maker_commitment_received(commitment):
        # when commitment is received for a given offer sign it and return to sender
        pass

    def taker_commitment_received(commitment):
        # if offer timed out return commitment
        # if offer already taken return commitment
        # when commitment is received matching a given offer sign it and return to sender
        commited_offers[hashlock] = commitment

    def redeem_deposit():
        pass

    def send_back_signed_offer():
        # sign offer and send it back to maker/taker
        pass

    def process_offer(offer):
        # wait for commitment to be received as a raiden transfer
        # When commitment is received, sign offer and send back to signee
        pass

    def swap_executed(message):
        # decode message and match with commitment
        # register sender
        # if only one or none notify burn / keep deposits
        # if both maker and taker notify of successful swap within timeout
        # redeem deposits (keep a small fee) and broadcast swap completed
        pass

    def broadcast_swap_completed(order_id):
        # send signed message to broadcast channel stating that swap is complete
        pass


class Commitment(object):

    def __init__(self, amount, offer, timeout, commitment_id, taker, maker):
        self.amount = amount
        self.offer = offer
        self.timeout = timeout
        self.commitment_id = commitment_id


# this might be part of messages.py
# class Offer(object):

    # def __init__(self, bid_token, bid_amount, ask_token, ask_amount, offer_id):
        # self.bid_token = bid_token
        # self.bid_amount = bid_amount
        # self.ask_token = ask_token
        # self.ask_amount = ask_amount
        # self.offer_id = offer_id
