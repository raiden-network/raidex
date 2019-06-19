from eth_utils import keccak
from raidex.raidex_node.matching.matching_algorithm import match_limit

EMPTY_SECRET = bytes(32)
EMPTY_SECRET_KECCAK = keccak(EMPTY_SECRET)

DEFAULT_OFFER_LIFETIME = 60
# seconds until timeout  external offer is seen as valid
OFFER_THRESHOLD_TIME = 10


RAIDEN_POLL_INTERVAL = 0.75

MATCHING_ALGORITHM = match_limit


KOVAN_WETH_ADDRESS = '0xd0A1E359811322d97991E03f863a0C30C2cF029C'
KOVAN_RTT_ADDRESS = '0x92276aD441CA1F3d8942d614a6c3c87592dd30bb'