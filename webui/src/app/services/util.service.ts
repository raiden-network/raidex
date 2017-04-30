import * as d3Array from 'd3-array';


export function prepareStockChartData(tradesArray: Array<any>, interval, numberOfBars) {
    let stockDataArray: Array<any> = [];
    let volumeDataArray: Array<any> = [];
    let filterArray: Array<any>;
    let firstIndex = 0;
    let count = 0;
    do {
        let firstTimestamp = tradesArray[firstIndex].timestamp;
        filterArray = tradesArray.filter(function(item) {
            return item.timestamp >= firstTimestamp &&
                item.timestamp < firstTimestamp + interval * 60000;
        });
        stockDataArray.push([firstTimestamp, [
            Number(formatCurrency(filterArray[0].price)), // open
            Number(formatCurrency(d3Array.max(filterArray, function(d) {
                return d.price;
            }))),
            Number(formatCurrency(d3Array.min(filterArray, function(d) {
                return d.price;
            }))),
            Number(formatCurrency(filterArray[filterArray.length - 1].price))
        ]
        ]);
        let sumVolume = Number(convertToEther(d3Array.sum(filterArray, function(d) {
            return d.amount;
        })));
        volumeDataArray.push([firstTimestamp, sumVolume]);
        firstIndex = firstIndex + filterArray.length - 1;
        count = count + 1;
    } while (firstIndex !== tradesArray.length - 1 ); // && count < numberOfBars
    let limits = calculateLimits(tradesArray, volumeDataArray);
    return {stock: stockDataArray, volume: volumeDataArray, limits: limits};
}


