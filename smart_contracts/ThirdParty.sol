//pragma solidity ^0.4.0;

contract ThirdParty {

    address owner;
    address thirdParty;
    uint commitmentDeposit;
    uint claimableDeposit;
    address burnAddress = 0x0;

    event ContractCreated(address trader, address ThirdParty, uint deposit);
    event PaidBack(uint balance);
    event Burned(uint amount);

    modifier onlyOwner() {
        if(msg.sender != owner) throw;
        _//;
    }

    modifier hasBalance(uint amount) {
        if(this.balance < amount) throw;
        _//;
    }

    // constructor
    function ThirdParty(address _thirdParty) payable {
        owner = msg.sender;
        thirdParty = _thirdParty;
        commitmentDeposit = msg.value;
        ContractCreated(msg.sender, thirdParty, msg.value);
    }

    // burn function in case exchange does not go through
    function burnCommitment(uint amount) private hasBalance(amount) returns (bool) {
        burnAddress.send(amount);
        Burned(amount);
        return true;
    }

    // pay back function in case exchange goes through
    function payBack(uint amount) private hasBalance(amount) returns (uint) {
        claimableDeposit = amount;
        return claimableDeposit;
    }

    function claimDeposit() onlyOwner {
        owner.send(claimableDeposit);
        PaidBack(claimableDeposit);
    }

    // settle
    function settle(bytes message) public onlyOwner {
        // decode message and recover
        // if swap unsuccessfull burnCommitment(someAmount)
        // if swap successfull payBack(someAmount)
    }
}
