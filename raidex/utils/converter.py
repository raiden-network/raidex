

ETH_TO_WEI = 18


def convert(amount, decimals):
    return amount * 10 ** decimals


def eth_to_wei(eth_amount):
    return convert(eth_amount, ETH_TO_WEI)