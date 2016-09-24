pragma solidity ^0.4.0;

contract ThirdParty {

    address owner;
    address thirdParty;
    uint commitmentDeposit;

    event ContractCreated(address trader, address ThirdParty, uint deposit);

    // constructor
    function ThirdParty(address _thirdParty) {
        owner = msg.sender;
        thirdParty = _thirdParty;
        commitmentDeposit = msg.value;
        ContractCreated(msg.sender, thirdParty, msg.value);
    }

    // burn function in case exchange does not go through
    function burn() private returns (bool) {return true;}

    // pay back function in case exchange goes through
    function payBack() private returns (bool) {return true;}

    function disputeSettlement() returns (bool) {}

}
