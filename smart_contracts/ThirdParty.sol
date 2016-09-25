//pragma solidity ^0.4.0;

contract ThirdParty {

    address owner;
    address thirdParty;
    uint commitmentDeposit;
    uint claimableDeposit;
    address burnAddress = 0x0;
    uint timeout;
    uint currentNonce;
    uint fee;
    bytes32 hashedOffer;
    address charityAddress;

    event ContractCreated(address trader, address ThirdParty, uint deposit);
    event PaidBack(address receiver, uint balance);
    event FeePaidOut(address receiver, uint balance);
    event Burned(address receiver, uint amount);

    enum PayoutStates { None, Fee, Deposit, Both }
    PayoutStates payState;
    PayoutStates constant defaultState = PayoutStates.None;

    modifier onlyOwner() {
        if(msg.sender != owner) throw;
        _//;
    }

    modifier onlyThirdParty() {
        if(msg.sender != thirdParty) throw;
        _//;
    }

    modifier beforeTimeout() {
        if(now > timeout) throw;
        _//;
    }

    modifier afterTimeout() {
        if(now <= timeout) throw;
        _//;
    }

    modifier afterPayout() {
        if(payState != PayoutStates.Both) throw;
        _//;
    }

    modifier notPaidOut() {
        if(payState == PayoutStates.Both) throw;
        _//;
    }

    // constructor
    //function ThirdParty(address _thirdParty) payable {
    function ThirdParty(address _thirdParty) {
        fee = msg.value / 100;
        owner = msg.sender;
        thirdParty = _thirdParty;
        commitmentDeposit = msg.value;
        ContractCreated(msg.sender, thirdParty, msg.value);
    }

    // burn function in case exchange does not go through
    function burnCommitment() private afterPayout {
        if(commitmentDeposit == 0) throw;
        uint amount = commitmentDeposit;
        commitmentDeposit = 0;
        if(!burnAddress.send(amount)) throw;
        Burned(burnAddress, amount);
    }

    // only owner can claim and withdraw remaining deposit
    function claimDeposit() onlyOwner afterTimeout notPaidOut {
        uint amount = claimableDeposit;
        claimableDeposit = 0;
        commitmentDeposit = commitmentDeposit - amount;
        if(!owner.send(amount)) throw;
        if(payState == PayoutStates.Fee) payState = PayoutStates.Both;
        PaidBack(msg.sender, amount);
    }

    function claimFees() onlyThirdParty afterTimeout notPaidOut {
        uint amount = fee;
        fee = 0;
        commitmentDeposit = commitmentDeposit - amount;
        if(!thirdParty.send(amount)) throw;
        if(payState == PayoutStates.Deposit) payState = PayoutStates.Both;
        FeePaidOut(msg.sender, amount);
    }

    function punishOwner() private {
        uint amount = claimableDeposit / 10;
        claimableDeposit = claimableDeposit - amount;
        commitmentDeposit = commitmentDeposit - amount;
        if(!charityAddress.send(amount)) throw;
    }

    // settle
    function settle(bytes lastTransfer) public onlyOwner {
        var(rawTransfer, signer) = getTransferRawAddress(lastTransfer);
        if(signer != owner) throw;
        var(offer, remainingDeposit, channelNonce, _timeout) = decodeTransfer(rawTransfer);
        if(channelNonce < currentNonce) throw;
        hashedOffer = offer;
        timeout = now + _timeout * 1 minutes;
        currentNonce = channelNonce;
        claimableDeposit = remainingDeposit;
    }

    function challenge(bytes challengeTransfer) public onlyThirdParty beforeTimeout {
        var(rawTransfer, signer) = getTransferRawAddress(challengeTransfer);
        if(signer != owner) throw;
        var(offer, remainingDeposit, channelNonce, _timeout) = decodeTransfer(rawTransfer);
        if(channelNonce <= currentNonce) throw;
        if(offer != hashedOffer) throw;

        currentNonce = channelNonce;
        claimableDeposit = remainingDeposit;

        punishOwner();
    }

    function decodeTransfer(bytes message) private returns (bytes32, uint, uint, uint) {
        // TODO use correct length
        if (message.length != 148) {  // raw message size (without signature)
            throw;
        }

        bytes32 offer;
        uint timeout;
        uint remainingDeposit;
        uint channelNonce;

        assembly {
            offer := mload(add(message, 32))
            timeout := mload(add(message, 64))
            remainingDeposit := mload(add(message, 96))
            channelNonce := mload(add(message, 128))
        }

        return (offer, remainingDeposit, channelNonce, timeout);
    }

    function getTransferRawAddress(bytes memory signedTransfer) private returns (bytes memory, address) {
        uint signatureStart;
        uint length;
        bytes memory signature;
        bytes memory transferRaw;
        bytes32 transferHash;
        address transferAddress;

        length = signedTransfer.length;
        signatureStart = length - 65;
        signature = slice(signedTransfer, signatureStart, length);
        transferRaw = slice(signedTransfer, 0, signatureStart);

        transferHash = sha3(transferRaw);
        var (r, s, v) = signatureSplit(signature);
        transferAddress = ecrecover(transferHash, v, r, s);

        return (transferRaw, transferAddress);
    }

    function signatureSplit(bytes signature) private returns (bytes32 r, bytes32 s, uint8 v) {
        // The signature format is a compact form of:
        //   {bytes32 r}{bytes32 s}{uint8 v}
        // Compact means, uint8 is not padded to 32 bytes.
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            // Here we are loading the last 32 bytes, including 31 bytes
            // of 's'. There is no 'mload8' to do this.
            //
            // 'byte' is not working due to the Solidity parser, so lets
            // use the second best option, 'and'
            v := and(mload(add(signature, 65)), 1)
        }
        // old geth sends a `v` value of [0,1], while the new, in line with the YP sends [27,28]
        if(v < 27) v += 27;
    }

    function slice(bytes a, uint start, uint end) private returns (bytes n) {
        if (a.length < end) {
            throw;
        }
        if (start < 0) {
            throw;
        }

        n = new bytes(end-start);
        for ( uint i = start; i < end; i ++) { //python style slice
            n[i-start] = a[i];
        }
    }
}
