declare var Web3;
var web3 = new Web3();
import * as d3Array from 'd3-array';
export function convertToEther(amount: any) {
	var value = web3.fromWei(String(amount), 'ether');
    return parseFloat(value).toFixed(5);
}

export function formatCurrency(price: any) {
	var value = parseFloat(price)/1000;
	return value.toFixed(3);
}

export function formatArray(orderArray: Array<any>){
	var newArray = [];
	orderArray.forEach(function(element, index){
		var obj = {};
		obj['amount'] = parseFloat(convertToEther(element.amount));
		obj['price'] = parseFloat(formatCurrency(element.price));
		newArray.push(obj);
	});	
	return newArray;
}

export function cumulativeArray(orderArray:Array<any>){
	var newArray = [];
	orderArray.forEach(function(element, index, arr){
		var obj={};
		obj['price'] = parseFloat(element.price);
		obj['amount'] = parseFloat(d3Array.sum(arr.slice(index),function(d){
							return d.amount;
						}));
		newArray.push(obj);
	});
	return newArray;
}
