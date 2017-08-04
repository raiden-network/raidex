import { Component, OnInit } from '@angular/core';
import { ZingChartModel } from '../model/zing-chart.model';
import { RaidexService } from '../services/raidex.service';
import { Subscription } from 'rxjs/Subscription';
import * as d3Array from 'd3-array';

@Component({
    selector: 'rex-zing-stockchart',
    template: `
        <div class="chart-title">
          Stock and Volume
        </div>
        <div class="chart-filter">
          <button class="btn btn-success btn-xs"
          (click)="reinitialiseStockChart(1. / 6)">10 secs</button>
          <button class="btn btn-success btn-xs"
          (click)="reinitialiseStockChart(10)">10 mins</button>
          <button class="btn btn-success btn-xs"
          (click)="reinitialiseStockChart(15)">15 mins</button>
          <button class="btn btn-success btn-xs"
          (click)="reinitialiseStockChart(30)">30 mins</button>
        </div>
        <rex-zingchart *ngFor="let chartObj of charts" [chart]="chartObj"></rex-zingchart>
        `,
})
export class ZingStockChartComponent implements OnInit {

    public charts: ZingChartModel[];
    public tradesArray: Array<any> = [];
    public stockChartDataArray: any[] = [];
    public volumeChartDataArray: any[] = [];
    public interval: number = 15;
    public numberOfBars: number = 20;
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        setTimeout(() => this.initialiseStockChart(), 3000);
    }

    public initialiseStockChart(): void {
        this.raidexSubscription = this.raidexService.getTrades().subscribe(
            data => {
                let tempArray: Array<any> = data;
                tempArray.sort(function (x, y) {
                    return d3Array.ascending(x.timestamp, y.timestamp);
                });
                this.tradesArray = tempArray;
                let stockUtil = prepareStockChartData(tempArray, this.interval, this.numberOfBars);
                this.stockChartDataArray = stockUtil.stock;
                this.volumeChartDataArray = stockUtil.volume;
                this.populateChartData();
            }
        );
    }

    public reinitialiseStockChart(interval?: number): void {
        this.interval = interval;
        let stockUtil = prepareStockChartData(this.tradesArray, this.interval, this.numberOfBars);
        this.stockChartDataArray = stockUtil.stock;
        this.volumeChartDataArray = stockUtil.volume;
        this.populateChartData();
    }

    public populateChartData(): void {
        this.charts = [{
            id: 'stockchart',
            data: {
                'type': 'mixed',
                'backgroundColor': 'transparent',
                // 'title': {
                //     'text': 'Stock and Volume Chart',
                //     'font-size': 14,
                //     'color': '#f7f7f7',
                //     'background-color': '#333333',
                //     'offset-x': -200,
                //     'offset-y': -20
                // },

                'plotarea': {
                    'adjust-layout': true /* For automatic margin adjustment. */
                },
                'scale-y': { // for Stock Chart
                    'offset-start': '35%', // to adjust scale offsets.
                    // "values": "29:33:2",
                    // "step": "10second",
                    'format': '$%v',
                    // 'label': {
                    //     'text': 'Prices'
                    // },
                    'item': {
                        'font-color': '#f7f7f7',
                        'font-size': '11px',
                        'font-family': 'Roboto',
                    }

                },
                'scale-y-2': { // for Volume Chart
                    'placement': 'default', // to move scale to default (left) side.
                    'blended': true, // to bind the scale to "scale-y".
                    'offset-end': '75%', // to adjust scale offsets.
                    // "values": "0:3:3",
                    'short': true,
                    // 'format': '%vETH',
                    // 'label': {
                    //     'text': 'Volume'
                    // }
                    'item': {
                        'font-color': '#f7f7f7',
                        'font-size': '11px',
                        'font-family': 'Roboto',
                    }
                },
                plot: {
                    'aspect': 'candlestick',
                    'trend-up': { // Stock Gain
                        'background-color': '#4fef4a',
                        'line-color': '#4fef4a',
                        'border-color': '#4fef4a'
                    },
                    'trend-down': { // Stock Loss
                        'background-color': '#ef5439',
                        'line-color': '#ef5439',
                        'border-color': '#ef5439'
                    },
                    'trend-equal': { // No gain or loss
                        'background-color': 'blue',
                        'line-color': 'blue',
                        'border-color': 'blue'
                    }
                },
                'scale-x': {
                    'transform': {
                        'type': 'date',
                        'all': '%g:%i'
                    },
                    'item': {
                        'font-color': '#f7f7f7',
                        'font-size': '11px',
                        'font-family': 'Roboto',
                    }
                },
                'scroll-x': {},
                'series': [
                    {
                        'type': 'stock', // Stock Chart
                        'scales': 'scale-x,scale-y', // to set applicable scales.
                        'values': this.stockChartDataArray
                    },
                    {
                        'type': 'bar', // Volume Chart
                        'scales': 'scale-x,scale-y-2', // to set applicable scales.
                        'background-color': '#03a9f4',
                        'values': this.volumeChartDataArray
                    }
                ]
            },
            height: 300,
            width: '100%'
        }];
    }

}

function prepareStockChartData(tradesArray: Array<any>, interval, numberOfBars) {
    let stockDataArray: Array<any> = [];
    let volumeDataArray: Array<any> = [];
    let filterArray: Array<any>;
    let firstIndex = 0;
    let startTimestamp = tradesArray[firstIndex] ? tradesArray[firstIndex].timestamp : 0;
    let lastTimestamp = tradesArray[tradesArray.length - 1] ? tradesArray[tradesArray.length - 1].timestamp : 0;
    do {
        let endTimestamp = startTimestamp + interval * 60000;
        filterArray = tradesArray.filter( (item) => {
            return item.timestamp >= startTimestamp &&
                item.timestamp < endTimestamp;
        });
        if (filterArray.length > 0) {
            stockDataArray.push([startTimestamp, [
                parseFloat(filterArray[0].price), // open
                d3Array.max(filterArray, (d) => {
                    return d.price;
                }),
                d3Array.min(filterArray, (d) => {
                    return d.price;
                }),
                parseFloat(filterArray[filterArray.length - 1].price)
        ]
        ]);
        }
        let sumVolume = d3Array.sum(filterArray, (d) => {
            return d.amount;
        });
        volumeDataArray.push([startTimestamp, sumVolume]);
        startTimestamp = endTimestamp;
    } while (startTimestamp <= lastTimestamp); // && count < numberOfBars
    return {stock: stockDataArray, volume: volumeDataArray};
}
