import * as d3Array from 'd3-array';


declare var Web3;
let web3 = new Web3();


export function convertToEther(amount: any) {
		let value = web3.fromWei(String(amount), 'ether');
    return parseFloat(value).toFixed(5);
}

export function formatCurrency(price: any) {
		let value = parseFloat(price) / 1000;
		return value.toFixed(3);
}

export function formatArray(orderArray: Array<any>) {
		let newArray = [];
		orderArray.forEach(function(element, index){
				let obj = {};
				obj['amount'] = parseFloat(convertToEther(element.amount));
				obj['price'] = parseFloat(formatCurrency(element.price));
				newArray.push(obj);
		});
		return newArray;
}

export function cumulativeArray(orderArray: Array<any>) {
		let newArray = [];
		orderArray.forEach(function(element, index, arr){
				let obj = {};
				obj['price'] = parseFloat(element.price);
				obj['amount'] = d3Array.sum(arr.slice(index), function(d){
														return d.amount;
												});
				newArray.push(obj);
		});
		return newArray;
}

export function cumulativePoints(orderArray: Array<any>) {
		let newArray = [];
		orderArray.forEach(function(element, index, arr){
				let arrPoint = [];
				arrPoint[0] = parseFloat(element.price);
				arrPoint[1] = d3Array.sum(arr.slice(index), function(d){
														return d.amount;
												});
				newArray.push(arrPoint);
		});
		return newArray;
}

export function formatIntoPriceTimeSeries(orderHistoryArray: Array<any>) {
		let newArray = [];
		orderHistoryArray.forEach(function(element, index) {
				let arrPoint = [];
				arrPoint[0] = element.timestamp;
				arrPoint[1] = formatCurrency(element.price);
				newArray.push(arrPoint);
		});
		return newArray;
}

export function formatIntoVolumeTimeSeries(orderHistoryArray: Array<any>) {
		let tempArray = [];
		orderHistoryArray.forEach(function(element, index) {
				let arrPoint = [];
				arrPoint[0] = element.timestamp;
				arrPoint[1] = convertToEther(element.amount);
				tempArray.push(arrPoint);
		});
		return tempArray;
}
