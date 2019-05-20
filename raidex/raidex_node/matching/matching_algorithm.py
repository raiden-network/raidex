

def match_limit(offer_book, order):

    matching_offers = offer_book.get_offers_by_price(order.price, order.order_type)
    matching_offers.sort(key=lambda x: x.base_amount, reverse=True)
    amount_left = order.amount
    take_offers = list()

    for offer in matching_offers:

        if amount_left >= offer.base_amount:
            take_offers.append(offer)
            amount_left -= offer.base_amount

    return take_offers, amount_left
