declare var Web3;
var web3 = new Web3();

export function convertToEther(amount: any) {
	var value = web3.fromWei(String(amount), 'ether');
    return parseFloat(value).toFixed(5);
}

export function formatCurrency(amount: any) {
	var value = parseFloat(amount)/1000;
	return value.toFixed(3);
}
