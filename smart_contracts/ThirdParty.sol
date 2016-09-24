//pragma solidity ^0.4.0;

contract ThirdParty {

    address owner;
    address thirdParty;
    uint commitmentDeposit;

    event ContractCreated(address trader, address ThirdParty, uint deposit);

    modifier onlyOwner(address _owner) {
        if(_owner != owner) throw;
        _;
    }

    // constructor
    function ThirdParty(address _thirdParty) payable {
        owner = msg.sender;
        thirdParty = _thirdParty;
        commitmentDeposit = msg.value;
        ContractCreated(msg.sender, thirdParty, msg.value);
    }

    // burn function in case exchange does not go through
    function burn(uint amount) private returns (bool) {
        return true;
    }

    // pay back function in case exchange goes through
    function payBack() private returns (bool) {
        return true;
    }

    // if dispute in settle
    function disputeSettlement() private returns (bool) {

    }

    // settle
    function settle() public onlyOwner {

    }

}
