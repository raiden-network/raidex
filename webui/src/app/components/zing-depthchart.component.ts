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
    public bidArray: any[] = [];
    public askArray: any[] = [];
    private minValue: number = 0.;
    private maxValue: number = 0.;
    public raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        setTimeout(() => this.initialiseOrderChart(), 1000);
    }

    public initialiseOrderChart(): void {
        this.raidexSubscription = this.raidexService.getOffers().subscribe(
            (offer) => {
                this.bidArray = cumulativePoints(offer.buys);
                this.askArray = cumulativePoints(offer.sells);
                this.minValue = Math.min(this.bidArray[0][0], this.askArray[this.askArray.length - 1][0]);
                this.maxValue = Math.max(this.bidArray[this.bidArray.length - 1][0], this.askArray[0][0]);
                this.populateChartData();
            });
    }

    public populateChartData(): void {
        this.charts = [{
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
                    // 'auto-fit': true,
                    // 'label': {
                    //     'text': 'Price'
                    // },
                    'min-value': this.minValue,
                    'max-value': this.maxValue,
                    // 'zooming': true,
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
        }];
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
