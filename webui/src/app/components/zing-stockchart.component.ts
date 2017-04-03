import { Component, OnInit, Input, AfterViewInit, ViewChild } from '@angular/core';
import { ZingChartModel } from '../model/zing-chart.model';
import { RaidexService } from '../services/raidex.service';
import { Subscription } from 'rxjs/Subscription';
import * as util from '../services/util.service';
import * as d3Array from 'd3-array';


@Component({
    selector: 'rex-zing-stockchart-component',
    template: `
        <zingchart *ngFor="let chartObj of charts" [chart]="chartObj"></zingchart>
        <div id="date-picker-container">
            <button class="btn btn-success btn-xs"
            (click)="reinitialiseStockChart(10)">10 mins</button>
            <button class="btn btn-success btn-xs"
            (click)="reinitialiseStockChart(15)">15 mins</button>
            <button class="btn btn-success btn-xs"
            (click)="reinitialiseStockChart(30)">30 mins</button>
        </div>

        `
})
export class ZingStockChartComponent implements OnInit, AfterViewInit {


    charts: ZingChartModel[];
    tradesArray: Array<any> = [];
    stockChartDataArray: any[] = [];
    volumeChartDataArray: any[] = [];
    interval: number = 15;
    numberOfBars: number = 20;
    limits: any;
    private raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {

    }

    ngOnInit(): void {
        setTimeout(() => this.initialiseStockChart(), 3000);
    }

    ngAfterViewInit() {

    }

    initialiseStockChart(): void {
        this.raidexSubscription = this.raidexService.getTrades().subscribe(
            data => {
                let tempArray: Array<any> = data;
                tempArray.sort(function (x, y) {
                    return d3Array.ascending(x.timestamp, y.timestamp);
                });
                this.tradesArray = tempArray;
                let stockUtil = util.prepareStockChartData(tempArray, this.interval, this.numberOfBars);
                this.stockChartDataArray = stockUtil.stock;
                this.volumeChartDataArray = stockUtil.volume;
                this.limits = stockUtil.limits;
                this.populateChartData(this.limits);
            }
        );
    }

    reinitialiseStockChart(interval?: number): void {
        this.interval = interval;
        let stockUtil = util.prepareStockChartData(this.tradesArray, this.interval, this.numberOfBars);
        this.stockChartDataArray = stockUtil.stock;
        this.volumeChartDataArray = stockUtil.volume;
        this.limits = stockUtil.limits;
        this.populateChartData(this.limits);
    }

    populateChartData(limits: any): void {
        this.charts = [{
            id: 'stockchart',
            data: {
                'type': 'mixed',
                'title': {
                    'text': 'Stock and Volume Chart',
                    'font-size': 14,
                    'offset-x': -200,
                    'offset-y': -10
                },

                'plotarea': {
                    'adjust-layout': true /* For automatic margin adjustment. */
                },
                'scale-y': { // for Stock Chart
                    'offset-start': '25%', // to adjust scale offsets.
                    // "values": "29:33:2",
                    'min-value': limits.minprice,
                    'max-value': limits.maxprice,
                    // "step": "10second",
                    'format': '$%v',
                    'label': {
                        'text': 'Prices'
                    },

                },
                'scale-y-2': { // for Volume Chart
                    'placement': 'default', // to move scale to default (left) side.
                    'blended': true, // to bind the scale to "scale-y".
                    'offset-end': '75%', // to adjust scale offsets.
                    // "values": "0:3:3",
                    'min-value': limits.minamount,
                    'max-value': limits.maxamount,
                    'format': '%vETH',
                    'label': {
                        'text': 'Volume'
                    }
                },
                plot: {
                    'aspect': 'candlestick',
                    'trend-up': { // Stock Gain
                        'background-color': 'green',
                        'line-color': 'green',
                        'border-color': 'green'
                    },
                    'trend-down': { // Stock Loss
                        'background-color': 'red',
                        'line-color': 'red',
                        'border-color': 'red'
                    },
                    'trend-equal': { // No gain or loss
                        'background-color': 'blue',
                        'line-color': 'blue',
                        'border-color': 'blue'
                    }
                },
                'scale-x': {
                    'min-value': this.stockChartDataArray[0][0],
                    'step': this.interval * 60000,
                    'zooming': true,
                    'zoom-to': [0, 20],
                    'transform': {
                        'type': 'date',
                        'all': '%g:%i'
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
            height: 275,
            width: '100%'
        }];
    }


}
