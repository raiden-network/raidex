class RaidexException(Exception):
    pass

class OrderTypeMismatch(RaidexException):
    pass

class InsufficientCommitmentFunds(RaidexException):
    pass

class UnknownCommitmentService(RaidexException):
    pass

class UntradableAssetPair(RaidexException):
    pass