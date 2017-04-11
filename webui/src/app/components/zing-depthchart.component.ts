import { Component, OnInit, OnChanges, Input, SimpleChanges } from '@angular/core';
import { ZingChartModel } from '../model/zing-chart.model';
import { RaidexService } from '../services/raidex.service';
import { Subscription } from 'rxjs/Subscription';
import * as util from '../services/util.service';
import * as d3Array from 'd3-array';

@Component({
    selector: 'rex-zing-depthchart-component',
    template: `
        <zingchart *ngFor="let chartObj of charts" [chart]="chartObj"></zingchart>
    `
})
export class ZingDepthChartComponent implements OnInit {

    public charts: ZingChartModel[];
    public bidArray: any[] = [];
    public askArray: any[] = [];
    public isLoaded: boolean = false;
    public raidexSubscription: Subscription;

    constructor(private raidexService: RaidexService) {}

    public ngOnInit(): void {
        setTimeout(() => this.initialiseOrderChart(), 1000);
    }

    public initialiseOrderChart(): void {
        this.raidexSubscription = this.raidexService.getOffers().subscribe(
            (order) => {
                let tempArray = order.data.buys;
                tempArray.sort(function(x, y) {
                    return d3Array.ascending(x.price, y.price);
                });
                tempArray = util.formatArray(tempArray);
                this.bidArray = util.cumulativePoints(tempArray);
                tempArray = order.data.sells;
                tempArray.sort(function(x, y) {
                    return d3Array.descending(x.price, y.price);
                });
                tempArray = util.formatArray(tempArray);
                this.askArray = util.cumulativePoints(tempArray);
                this.populateChartData(this.bidArray[0][0],
                    this.askArray[0][0],
                    0.01);
            });
    }

    public populateChartData(minValue: number, maxValue: number, step: number): void {
        this.charts = [{
            id: 'depth-chart',
            data: {
                'type': 'area',
                'plot': {
                    'line-width': 2,
                    'marker': {
                        'size': 1,
                        'visible': false
                    },
                    'tooltip': {
                        'text': '<table border="0" rules=none>' +
                        '<col width="150">' +
                        '<tr align="left">' +
                        '<td>Cumulative Volume</td>' +
                        '<td>%kt</td>' +
                        '</tr>' +
                        '<tr align="right">' +
                        '<td>Price</td>' +
                        '<td>%vt</td>' +
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
                'title': {
                    'text': 'Market Depth',
                    'font-size': 14,
                    'offset-x': -200,
                    'offset-y': -10
                },
                'scaleY': {
                    'label': {'text': 'Cumulative Volume'}
                },
                'plotarea': {
                    'adjust-layout': true /* For automatic margin adjustment. */
                },
                'scale-x': {
                    'auto-fit': true,
                    'min-value': minValue,
                    'max-value': maxValue,
                    'step': .001,
                    'decimals': 2,
                    'label': {
                        'text': 'Price'
                    }
                },
                'series': [
                    {
                        'values': this.bidArray,
                        'text': 'Red'
                    },
                    {
                        'values': this.askArray,
                        'text': 'Blue'
                    }
                ],
            },
            height: 300,
            width: '100%'
        }];
    }
}
