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
          (click)="reinitialiseStockChart(30)">30 secs</button>
          <button class="btn btn-success btn-xs"
          (click)="reinitialiseStockChart(60)">1 min</button>
          <button class="btn btn-success btn-xs"
          (click)="reinitialiseStockChart(15 * 60)">15 mins</button>
          <button class="btn btn-success btn-xs"
          (click)="reinitialiseStockChart(30 * 60)">30 mins</button>
        </div>
        <rex-zingchart *ngFor="let chartObj of charts" [chart]="chartObj"></rex-zingchart>
        `,
})
export class ZingStockChartComponent implements OnInit {

    public charts: ZingChartModel[];
    public tradesArray: Array<any> = [];
    public stockChartDataArray: any[] = [];
    public volumeChartDataArray: any[] = [];
    public min_scale: number;
    public max_scale: number;
    public interval: number = 10; // interval in seconds
    public numberOfBars: number = 15;
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        setTimeout(() => this.initialiseStockChart(), 3000);
    }

    public initialiseStockChart(): void {
        this.raidexSubscription = this.raidexService.getPriceChart(this.numberOfBars, this.interval).subscribe(
            data => {
                console.log(data);
                this.tradesArray = data;
                let stockUtil = prepareStockChartData(data);
                this.stockChartDataArray = stockUtil.stock;
                this.volumeChartDataArray = stockUtil.volume;
                this.min_scale = stockUtil.min_price;
                this.max_scale = stockUtil.max_price;
                this.populateChartData();
            }
        );
    }

    public reinitialiseStockChart(interval?: number): void {
        this.raidexSubscription.unsubscribe();
        this.interval = interval;
        this.raidexSubscription = this.raidexService.getPriceChart(this.numberOfBars, this.interval).subscribe(
            data => {
                console.log(data);
                this.tradesArray = data;
                let stockUtil = prepareStockChartData(data);
                this.stockChartDataArray = stockUtil.stock;
                this.volumeChartDataArray = stockUtil.volume;
                this.min_scale = stockUtil.min_price;
                this.max_scale = stockUtil.max_price;
                this.populateChartData();
            }
        );
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
                    'min-value': this.min_scale.toString(),
                    'max-value': this.max_scale.toString(),
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

function prepareStockChartData(tradesArray: Array<any>) {
    let stockDataArray: Array<any> = [];
    let volumeDataArray: Array<any> = [];
    let chart_min_price = Infinity;
    let chart_max_price = 0;
    tradesArray.map((priceBin) => {
        // let timestamp = priceBin.timestamp ? priceBin.timestamp : 0;
        let amount = parseFloat(priceBin.amount);
        // ignore all bins with amount of 0
        if (amount > 0.) {
            volumeDataArray.push([priceBin.timestamp, amount]);
            let min_price = parseFloat(priceBin.min);
            let max_price = parseFloat(priceBin.max);

            stockDataArray.push(
                [priceBin.timestamp, [
                    parseFloat(priceBin.open),
                    max_price,
                    min_price,
                    parseFloat(priceBin.close),
                ]]);
            if (min_price < chart_min_price && min_price != 0) {
                chart_min_price = min_price;
            }
            if (max_price > chart_max_price) {
                chart_max_price = max_price;
            }
        }
    });

    return {stock: stockDataArray, volume: volumeDataArray, min_price: chart_min_price, max_price: chart_max_price};
}
