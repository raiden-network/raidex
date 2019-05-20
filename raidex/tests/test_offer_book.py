from raidex.raidex_node.offer_book import OfferDeprecated, OfferType


def test_ask_offer():
    ask_offer = OfferDeprecated(OfferType.SELL, 20, 40, offer_id=123, timeout=50)
    assert ask_offer.amount == 20
    assert ask_offer.price == 2.0


def test_bid_offer():
    bid_offer = OfferDeprecated(OfferType.BUY, 20, 10, offer_id=124, timeout=50)
    assert bid_offer.amount == 20
    assert bid_offer.price == 0.5
