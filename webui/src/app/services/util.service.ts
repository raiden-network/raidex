import * as d3Array from 'd3-array';
import { OrderHistory } from '../model/order-history';
import { OrderBook } from '../model/order-book';
declare var Web3;
let web3 = new Web3();


export function convertToEther(amount: any) {
    let value = web3.fromWei(String(amount), 'ether');
    return Number(value).toFixed(2);
}

export function formatCurrency(price: any) {
    let value = parseFloat(price) / 1000;
    return Number(value).toFixed(2);
}

export function formatArray(orderArray: Array<any>) {
    let newArray = [];
    orderArray.forEach(function (element, index) {
        let obj = {};
        obj['amount'] = parseFloat(convertToEther(element.amount));
        obj['price'] = parseFloat(formatCurrency(element.price));
        newArray.push(obj);
    });
    return newArray;
}

export function cumulativeArray(orderArray: Array<any>) {
    let newArray = [];
    orderArray.forEach(function (element, index, arr) {
        let obj = {};
        obj['price'] = parseFloat(element.price);
        obj['amount'] = d3Array.sum(arr.slice(index), function (d) {
            return d.amount;
        });
        newArray.push(obj);
    });
    return newArray;
}

export function cumulativePoints(orderArray: Array<any>) {
    let newArray = [];
    orderArray.forEach(function (element, index, arr) {
        let arrPoint = [];
        arrPoint[0] = parseFloat(element.price);
        arrPoint[1] = d3Array.sum(arr.slice(index), function (d) {
            return d.amount;
        });
        newArray.push(arrPoint);
    });
    return newArray;
}

export function formatIntoPriceTimeSeries(orderHistoryArray: Array<any>) {
    let newArray = [];
    orderHistoryArray.forEach(function (element, index) {
        let arrPoint = [];
        arrPoint[0] = element.timestamp;
        arrPoint[1] = formatCurrency(element.price);
        newArray.push(arrPoint);
    });
    return newArray;
}

export function formatIntoVolumeTimeSeries(orderHistoryArray: Array<any>) {
    let tempArray = [];
    orderHistoryArray.forEach(function (element, index) {
        let arrPoint = [];
        arrPoint[0] = element.timestamp;
        arrPoint[1] = convertToEther(element.amount);
        tempArray.push(arrPoint);
    });
    return tempArray;
}

export function preprocessOrderHistory(orderHistoryArray: Array<any>): OrderHistory[] {
    let orderHistory: OrderHistory[] = [];
    orderHistoryArray.forEach(function (element, index) {
        orderHistory.push(new OrderHistory(
            element.timestamp,
            convertToEther(element.amount),
            formatCurrency(element.price),
            element.type
        ));
    });
    return orderHistory;
}

export function preprocessOrderBook(orderBookArray: Array<any>): OrderBook[] {
    let orderBook: OrderBook[] = [];
    orderBookArray.forEach(function (element, index) {
        orderBook.push(new OrderBook(
            convertToEther(element.amount),
            formatCurrency(element.price)
        ));
    });
    return orderBook;
}

export function prepareStockChartData(orderHistoryArray: Array<any>, interval) {
    let stockDataArray: Array<any> = [];
    let volumeDataArray: Array<any> = [];
    let filterArray: Array<any>;
    let firstIndex = 0;
    do {
        let firstTimestamp = orderHistoryArray[firstIndex].timestamp;
        filterArray = orderHistoryArray.filter(function (item) {
            return item.timestamp >= firstTimestamp &&
                item.timestamp < firstTimestamp + interval * 60000;
        });
        stockDataArray.push([firstTimestamp, [
            Number(formatCurrency(filterArray[0].price)), // open
            Number(formatCurrency(d3Array.max(filterArray, function (d) {
                return d.price;
            }))),
            Number(formatCurrency(d3Array.min(filterArray, function (d) {
                return d.price;
            }))),
            Number(formatCurrency(filterArray[filterArray.length - 1].price))
        ]
        ]);
        let sumVolume = Number(convertToEther(d3Array.sum(filterArray, function (d) {
            return d.amount;
        })));
        volumeDataArray.push([firstTimestamp, sumVolume]);
        firstIndex = firstIndex + filterArray.length - 1;
    } while (firstIndex !== orderHistoryArray.length - 1);
    let limits = calculateLimits(orderHistoryArray, volumeDataArray);
    return {stock: stockDataArray, volume: volumeDataArray, limits: limits};
}

function calculateLimits(orderHistoryArray: Array<any>, volumeDataArray: Array<any>) {
    let minPriceValue = Number(formatCurrency(d3Array.min(orderHistoryArray, function (d) {
        return d.price;
    })));
    minPriceValue = Math.floor(minPriceValue);
    let maxPriceValue = Number(formatCurrency(d3Array.max(orderHistoryArray, function (d) {
        return d.price;
    })));
    maxPriceValue = Math.ceil(maxPriceValue);
    let minAmountValue = Math.floor(d3Array.min(volumeDataArray,
        function (d) {
            return d[1];
        }));
    let maxAmountValue = Math.ceil(d3Array.max(volumeDataArray,
        function (d) {
            return d[1];
        }));
    return {
        minprice: minPriceValue,
        maxprice: maxPriceValue,
        minamount: minAmountValue,
        maxamount: maxAmountValue
    };
}
