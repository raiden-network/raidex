import { Component, OnInit} from '@angular/core';
import { ZingChartModel } from '../model/zing-chart.model';
import { RaidexService } from '../services/raidex.service';
import { Subscription } from 'rxjs/Subscription';
import * as d3Array from 'd3-array';

@Component({
    selector: 'rex-zing-depthchart',
    template: `
        <div class="chart-title">Market Depth</div>
        <rex-zingchart *ngFor="let chartObj of charts" [chart]="chartObj"></rex-zingchart>
    `
})
export class ZingDepthChartComponent implements OnInit {

    public charts: ZingChartModel[];
    public bidArray: number[][] = [];
    public askArray: number[][] = [];
    private minValue: number;
    private maxValue: number;
    public raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        setTimeout(() => this.initialiseOrderChart(), 1000);
    }

    public calcMinMax(askArray: number[][], bidArray: number[][]){
        let maxAsk = askArray.slice(0, 1).pop();
        let minAsk = askArray.slice(-1).pop();
        let maxBid = bidArray.slice(-1).pop();
        let minBid = bidArray.slice(0, 1).pop();

        let min = Math.min.apply(Math, [minAsk, minBid].filter(val => Boolean(val)).map(offer => offer[0]));
        let max = Math.max.apply(Math, [maxAsk, maxBid].filter(val => Boolean(val)).map(offer => offer[0]));
        return {'max': max, 'min': min}
    }

    public initialiseOrderChart(): void {
        this.raidexSubscription = this.raidexService.getOffers().subscribe(
            (offer) => {
                // sells is sorted in descending order by (price, offer_id)
                this.askArray = cumulativePoints(offer.sells);
                // buys is sorted in ascending order by (price, offer_id)
                this.bidArray = cumulativePoints(offer.buys);
                let minMax = this.calcMinMax(this.askArray, this.bidArray);
                this.minValue = minMax.min;
                this.maxValue = minMax.max;
                this.populateChartData();
            });
    }

    public populateChartData(): void {
        let depth_chart = {
            id: 'depth-chart',
            data: {
                'type': 'area',
                'backgroundColor': 'transparent',
                'plot': {
                    'aspect': 'stepped',
                    'line-width': 2,
                    'marker': {
                        'size': 1,
                        'visible': false
                    },
                    'tooltip': {
                        'text': '<table border="0" rules=none>' +
                        '<col width="150">' +
                        '<tr align="left">' +
                        '<td>Cumulative Volume (ETH)</td>' +
                        '<td>%vt</td>' +
                        '</tr>' +
                        '<tr align="right">' +
                        '<td>Price (USD)</td>' +
                        '<td>%kt</td>' +
                        '</tr>' +
                        '</table>',
                        'html-mode': true,
                        'background-color': 'white',
                        'border-color': 'black',
                        'border-radius': '6px',
                        'font-color': 'black',
                        'alpha': 0.5,
                        'callout': true
                    }
                },
                'scale-y': {
                    // 'label': {'text': 'Cumulative Volume'}
                    'short': true,
                    'item': {
                        'font-color': '#f7f7f7',
                        'font-size': '11px',
                        'font-family': 'Roboto',
                    }
                },
                'plotarea': {
                    'adjust-layout': true /* For automatic margin adjustment. */
                },
                'scale-x': {
                    'step': .001,
                    'decimals': 3,
                    'item': {
                        'font-color': '#f7f7f7',
                        'font-size': '11px',
                        'font-family': 'Roboto',
                    }
                },
                'series': [
                    {
                        'scales': 'scale-x, scale-y',
                        'values': this.bidArray,
                        'line-color': '#4fef4a',
                        'background-color': '#4fef4a'
                    },
                    {
                        'scales': 'scale-x, scale-y',
                        'values': this.askArray,
                        'line-color': '#ef5439',
                        'background-color': '#ef5439'
                    }
                ],
            },
            height: '300px',
            width: '100%'
        };
        if (this.minValue){
            depth_chart.data['scale-x']['min-value'] = this.minValue;
        }
        if (this.maxValue){
            depth_chart.data['scale-x']['max-value'] = this.maxValue;
        }
        this.charts = [depth_chart]
    }

}

function cumulativePoints(orderArray: Array<any>) {
    return orderArray.map((element, index, arr) => [
        parseFloat(element.price),
        d3Array.sum(arr.slice(index), function (d) {
            return parseFloat(d.amount);
        })
    ]);
}
